# UPS Monitor — Survival Sleep Feature Design Summary

## Engineering Basis Document v11

**Document scope:** Power budget, timing, entry/exit logic, data-integrity, and
implementation rationale for the ESP32-C3 survival sleep feature on the DIY
LiFePO4 UPS Monitor, as built on the **UPS-Monitor-THT Rev 1** carrier PCB.

**Date:** June 2026
**Revision:** v11 — **Tracks firmware through V1.13.** Builds on the two v10
pre-sign-off fixes (FIX 1, FIX 2, below) and adds the items surfaced by later
review passes. The survival entry/exit logic is byte-for-byte the V1.9.2/V1.11
design (validated against the May 6 event); everything below was caught *during
review, before sign-off*, per the code-review standard.

**Added since v10:**
- **V1.12 hardening (3 items, robustness — no behaviour change on the validated
  paths):** (5) `on_battery` `on_press` single-guard refactor — the integrator
  resets moved *inside* the guarded lambda so a future edit cannot separate the
  guard from the reset (behaviour-identical); (7) **mid-outage-reboot data
  integrity** — `on_press` now early-returns when `outage_start_uptime != 0`
  (already in an outage this boot-session), and `on_release` clears it on a clean
  outage end, so a brown-out/crash reboot during the *awake* pre-trip outage no
  longer lets `on_press` reset the restore:true Ah/Wh or double-count the outage
  (closes the gap §8 previously left to priority -100 alone); (10) `on_press`
  discharge guard fails **closed** on a NaN current (`isnan(i) || i > -0.05f`).
- **V1.13 (INA260 config simplification + data-path correction):** the ESPHome
  `ina260` platform is now the **sole** chip configurator; the priority-600 manual
  `0x6127` (AVG=1) restore + its 10 ms delay are **removed** (the platform's
  reset+reconfigure ran after that block and overwrote it every boot anyway — see
  §2.3). The survival decision at priority -150 now owns the freshness wait,
  widened to **20 ms**. This also corrected a long-standing doc/firmware error: the
  chip has in fact been running at **AVG=4** (the platform's `0x0307`), not the
  AVG=1 prior revisions documented.

(1) **FIX 1 — `deep_sleep` brick (CRITICAL).** V1.11 set `sleep_duration` only inside
the two `deep_sleep.enter` actions, **not on the `deep_sleep` component**. The
`run_duration` watchdog auto-sleep calls `begin_sleep(manual=false)`, and on the C3
`deep_sleep_()` enables the timer wake only `if (sleep_duration_.has_value())` (there
is no `wakeup_pin`). The watchdog fires precisely on the boots where no
`deep_sleep.enter` has run — dead-INA entry, fail-safe-exit mid-outage — so in V1.11
that auto-sleep enabled **no wake source at all** → permanent, wakeup-less deep sleep
= a **silent brick that does not auto-recover on AC return**, in the exact dead-sensor
cases the watchdog exists to bound. This *inverted* the watchdog's purpose. V1.12 adds
`sleep_duration: ${survival_sleep_interval}` to the component, so the auto-sleep wakes
on the 120 s timer and delivers the intended ~60 s-awake / 120 s-asleep ride-out
(§6.7). Confirmed in the generated `main.cpp` (`set_sleep_duration(120000)` now emitted
on the component). Normal operation is unchanged — sleep is entered only via
`begin_sleep` (run_duration timeout, blocked by `prevent`; or explicit `enter`);
`sleep_duration` sets only *how long*, never *when*.

(2) **FIX 2 — snapshot integrity (§8).** The arm-time snapshot is meant to be
authoritative on a survival recovery, protected by `outage_was_survival`. But priority
-150 *clears* that flag at boot, and the recovery CC sample (~13.093 V) is *below* the
13.15 V `on_battery` threshold, so `on_battery` can latch ON then release and fire
`on_release` minutes later — by which time the flag is cleared, so the protective
branch is bypassed and `on_release` overwrites `last_outage_ah/wh` from live counters.
V1.12 guards the recompute with `if (outage_start_uptime > 0)`; on a survival recovery
that global is 0 (transient; -100 skipped while armed), so a stray `on_release` is a
no-op for the snapshot while a genuine awake-tracked outage recomputes as before.

(Prior context — **v9** backed out the V1.10 event-wake feature and reverted the
survival path to the bench-validated V1.9.2 timer-wake design, then added the Tier-1
`run_duration` watchdog. See §6.6/§14 for why event-wake was retired.) All entry/exit
thresholds, fail-safes, and measured data are unchanged from v7/v8/v9.

**Status:** Implemented — firmware **V1.13** (`ups-monitor-v1_13.yaml`) on the
UPS-Monitor-THT Rev 1 PCB. The survival path is the validated V1.9.2 logic; the
`run_duration` watchdog (V1.11), the two V1.12 fixes, the three V1.12 hardening
items, and the V1.13 config simplification are the only changes.
**Validation to date:** config valid + full ESPHome **codegen clean on 2026.5.3**
(the review verified the brick fix, both V1.12 guards, and the V1.13 changes in the
generated source, with no C++/codegen error). **Remaining sign-off gates:** the final on-host `esphome
compile` (link) + flash, and the §13 bench measurement of the single unmeasured input
that gates R-1 (below-LVD reserve / per-wake burst / sleep floor), which is unchanged
and still open.
**Requirement:** ESP survives a multi-day grid outage without tripping the BMS
hard cutoff, and resumes automatically when AC returns.

-----

## 0. Design Intent (why the design looks the way it does)

The operational requirement is narrow and was deliberately kept narrow:

> Save the battery from BMS cutoff during an extended outage, and recover
> automatically when AC returns.

Everything in V1.7 follows from prioritizing, in order:

1. **Never brick** — the device must always be able to return to normal operation
   on AC restoration, with no manual intervention.
1. **Always auto-recover** — recovery is a cold boot on AC return; it requires no
   network, no “report,” and no preserved RAM state.
1. **Reduce post-LVD drain** — sleep through the deep-discharge tail rather than
   draining the pack awake.
1. **Protect the pack from BMS cutoff.**
1. **Accept imperfect telemetry / runtime accounting** — exact reserve Ah is not
   operationally important and is explicitly out of scope as a *requirement*.

The single most important consequence of this ordering: **every threshold in the
survival path must fail safe.** Entry fails toward sleep; wake fails toward exit.
No threshold may be able to strand the device awake (→ drains to cutoff) or asleep
(→ bricks). This principle, more than any individual number, is the design.

> **v10 note — the FIX 1 brick is a direct instance of this principle.** The V1.11
> watchdog auto-sleep, lacking a wake source, could strand the device *asleep* (a
> brick) in the failure tail — the very outcome this section forbids. The fix is one
> line (component-level `sleep_duration`); the lesson is that the auto-sleep wake
> source is a *fail-safe invariant*, not a tuning parameter, and is now documented as
> such in §9.3.

An earlier line of work treated the feature as a measurement-grade outage
recorder (precise post-trip voltage modelling, conversion-ready polling,
entry-threshold tuning, exact outage-Ah fidelity). That was over-engineered for
the requirement above and, in one case, actively dangerous (see §5.1). V1.7 strips
it back to the deterministic core.

-----

## 1. Requirements

|ID |Requirement                                                                                                                      |
|---|---------------------------------------------------------------------------------------------------------------------------------|
|R-1|ESP survives an extended grid outage without BMS hard cutoff (≥10-day design target)                                             |
|R-2|ESP detects AC restoration and resumes HA telemetry automatically                                                                |
|R-3|No *further* hardware changes required on the UPS-Monitor-THT Rev 1 PCB (the firmware runs on the board as fabricated)           |
|R-4|No BMS trip during extended outage                                                                                               |
|R-5|Implementation uses proven ESPHome mechanisms                                                                                    |
|R-6|*(best-effort, not a hard requirement)* Per-outage Ah/Wh and min-voltage records remain meaningful across the sleep cycle        |
|R-7|No dependence on network or telemetry during the outage; the design fails toward recovery (cold boot) and, on entry, toward sleep|

R-6 was a hard requirement in earlier revisions. It is downgraded to best-effort:
the arm-time snapshot preserves the full-outage figure cheaply, but no design
decision may trade robustness for Ah fidelity. R-7 is the governing principle.

-----

## 2. Hardware Constraints

### 2.0 As-Built Carrier PCB — UPS-Monitor-THT Rev 1

The breadboard build is superseded by a fabricated 2-layer THT carrier PCB
(`UPS-Monitor-THT.kicad_pcb`, KiCad 10, 44 × 77 mm, OSH Park, June 3 2026). It is a
socketed carrier — no surface-mount work — built around four modules plus passives:

|Ref   |Part                                        |Role                                                |
|------|--------------------------------------------|----------------------------------------------------|
|U1    |XIAO ESP32-C3                               |MCU                                                 |
|U2    |Adafruit INA260 breakout, in an 8-pin socket|V/I/P sense (VCC / GND / SCL / SDA / ALERT)         |
|U3    |Pololu D24V7F3                              |12 V → 3.3 V buck (pin 1 VOUT, pin 2 GND, pin 3 VIN)|
|—     |DS18B20                                     |temperature, on TB2                                 |
|F1    |5 × 20 mm 1 A slow-blow (Würth 696108003002)|board-supply fuse                                   |
|R2    |10 kΩ 1/4 W axial                           |ALERT pull-up to 3V3                                |
|C1    |10 µF 25 V ceramic                          |3V3 bulk                                            |
|C2, C3|0.1 µF 50 V ceramic                         |3V3 decoupling                                      |
|C4    |47 µF 50 V aluminium electrolytic           |VIN bulk                                            |
|C5    |0.1 µF 50 V ceramic                         |VIN decoupling                                      |
|TB1   |2-pin Phoenix MKDS-3.81                     |BATTERY in (+/−)                                    |
|TB2   |3-pin JST-XH                                |DS18B20 (3V3 / DQ / GND)                            |
|H1–H4 |M3 mounting holes                           |                                                    |
|TPs   |Vin, 3V3, GND, SDA, SCL, ALERT              |bring-up test points                                |

**Board-supply path:** TB1 BATTERY(+) → **F1 (1 A slow-blow)** → C4 (47 µF) /
C5 (0.1 µF) → D24V7F3 VIN; VOUT (3.3 V) → 3V3 rail → XIAO 3V3 + INA260 VCC, with
C1 (10 µF) + C2/C3 (0.1 µF) decoupling. The board draws only its own ~35 mA here.
**The metered ~1.2 A load current does NOT flow through PCB copper** — it runs
externally in 16 AWG through the INA260 breakout’s own VIN+/VIN− screw terminals.
F1 protects only the board-supply tap, not the metered path.

> **v10 note (HW dependency, A-2):** the entire survival *entry* logic assumes the
> board stays powered after the BP-65 disconnects the XB7 load, and that the ESP’s own
> ~40 mA reads as a small negative current through the INA shunt post-trip. That is a
> topology fact (the open low-side/high-side shunt + DC−-to-chassis-bond verification),
> not something firmware can enforce. A-2 is marked “confirmed for this build”; it is
> nonetheless the top item on the bench list because all of §5.1 is contingent on it.

**INA260 / INA228 socket:** U2 is a generic 8-pin socket; the silkscreen reads
“Adafruit INA260” and this build is INA260 (the validated capacity data and the
firmware register access are INA260-specific). The same socket footprint fits an
Adafruit INA228 breakout, but an INA228 remaps a socket pin (VBUS where the INA260
has ALERT) and changes R2’s role — it is **not** a drop-in for this firmware. The
I2C address is set by the populated module’s A0 jumper, not the PCB (this build:
A0 bridged → 0x41).

**Known PCB-side issue (surfaced, not blocking firmware):** the silkscreen
board-size note contains literal `{dblquote}` tokens (`1 3/4{dblquote} x 3{dblquote}`)
where the inch double-prime was intended — they will render as the text
“{dblquote}” on the silk. Cosmetic; clear before any re-fab. (An earlier draft of
this section also claimed the two copper pours were unassigned / GND not net-tied —
that was wrong, a KiCad-10 net-format misread. Both pours **are** tied to GND, and
the GND net connects all expected pads; there is no connectivity issue.)

### 2.1 PCB GPIO Availability

|GPIO  |XIAO pin|Assignment                                                                                      |
|------|--------|------------------------------------------------------------------------------------------------|
|GPIO6 |D4      |I2C SDA → INA260                                                                                |
|GPIO7 |D5      |I2C SCL → INA260                                                                                |
|GPIO10|D10     |1-Wire → DS18B20 (TB2)                                                                          |
|GPIO3 |D1      |INA260 ALERT (R2 10 kΩ pull-up to 3V3; passive fault-monitor input — not a wake source in V1.11+)|
|GPIO20|D7      |spare (was the breadboard ALERT pin; unconnected on the PCB)                                    |

**Change from the breadboard build:** ALERT moved from GPIO20 (D7) to **GPIO3
(D1)**. This matters because ESP32-C3 deep-sleep GPIO wakeup is restricted to the
RTC-domain pins (GPIO0–GPIO5). GPIO20 is outside that domain and **cannot** wake
the chip from deep sleep; **GPIO3 is inside it and can.** The breadboard’s
“timer-wake is the only option” constraint therefore no longer holds in hardware.

**Source:** ESP32-C3 Technical Reference Manual §6; Seeed XIAO ESP32-C3 wiki
(wake-up pins D0–D3 = GPIO2–GPIO5; D1 = GPIO3). Independently confirmed that GPIO2
and GPIO3 wake the ESP32-C3 from deep sleep (espressif/arduino-esp32 #6656; #8510
uses GPIO3 as the wake interrupt with a 10 kΩ resistor — the same role as R2 here).

**Implication:** Timer-based deep sleep is the *implemented* wakeup mechanism
(V1.13 survival logic is byte-for-byte V1.9.2/V1.8 — see §6, §7). Event-driven
ALERT-wake on GPIO3 is a hardware *capability* of this board, and V1.10 implemented
it — but V1.11 **backed it out** (§6.6, §14): the cosmetic recovery-latency gain did
not justify making GPIO3 a recovery-critical SPOF, and it cost more energy at the
chosen backstop than plain timer-wake. GPIO3 remains wired to ALERT with R2, but the
firmware uses it only as a passive fault-monitor input — **not** a wake source.

### 2.2 XIAO ESP32-C3 Module Sleep Current

The XIAO ESP32-C3 uses the chip’s built-in USB-Serial controller — there is no
external USB bridge to add quiescent draw. The board is powered via the XIAO 3V3
pin from the D24V7F3 buck; the XC6210 LDO’s input (the 5V/USB path) is unpowered
in production, so the LDO contributes little. Two cases are carried:

|Case               |XIAO module sleep|Basis                              |
|-------------------|-----------------|-----------------------------------|
|Best (LDO bypassed)|~10 µA           |ESP32-C3 die only                  |
|Worst (LDO active) |~45 µA           |Full module, measured (Seeed forum)|

### 2.3 INA260 Power-Down Mode

Configuration Register (0x00) bits 2–0 = 000 places the INA260 in power-down.

|Parameter               |Typical|Maximum|Unit|
|------------------------|-------|-------|----|
|IQ active (mode 111)    |310    |420    |µA  |
|IQ power-down (mode 000)|0.5    |**2**  |µA  |

The INA260 stays powered (via D24V7F3) and retains register values across the
ESP32-C3 deep sleep. **As of V1.13 the firmware does not write the INA260 config
register at boot.** The ESPHome `ina260` platform is the sole configurator: its
`setup()` resets the chip (`0x8000`), then writes config `0x0307` — continuous mode,
**hardware averaging AVG=4**, VBUSCT 1.1 ms, ISHCT 140 µs. That write runs at
setup_priority `DATA` (600), and by the stable setup sort + registration order
(the `on_boot`-600 `StartupTrigger` is registered before the `ina260` component, and
ties keep registration order) it runs **after** the `on_boot`-600 block. The
priority-600 manual `0x6127`/AVG=1 restore present through V1.12 was therefore
overwritten by the platform on every boot — it never governed the chip — so V1.13
removes it. The chip has in fact always run at **AVG=4**, not the AVG=1 documented
through v10. On a survival wake the platform's `0x8000` reset also brings the chip
out of the `0x6120` power-down set on entry, so no manual restore is needed for that
either.

**Data path (two averaging stages).** Published bus-voltage / current / power are
*not* the raw chip register — they pass through two stages: (1) **chip** AVG=4
hardware average (~5 ms / 4 conversions, updating the register); (2) the platform
reads that register at **1 Hz**, and each of V/I/P carries a **`throttle_average:
5s`** software filter, so the value published to HA every 5 s is the mean of the ~5
one-second samples. The 5 s software mean is the dominant noise reducer for stored
data and feeds **all** normal-operation logic — discharge current/power, the Ah/Wh
integration, the voltage slope and cliff detection, the `on_battery` test, and the
survival arm condition all read the filtered `.state`. The chip's AVG=4 is a
complementary anti-aliasing layer (it cleans each 1 Hz sample before the software
averages five of them) whose one *direct* consumer is the survival decision at
priority **-150**, which reads bus voltage with a single raw `write_read` (no
software filter) and a **20 ms** freshness wait — comfortably past the ~5 ms an AVG=4
averaged conversion needs (4 × (1.1 ms + 0.14 ms)). Higher chip averaging
(AVG=128–1024) is *not* pursued: stored data is already 5 s-averaged; the Ah/Wh
integral self-cancels sparse-sample aliasing (the load bursts are asynchronous to the
1 Hz poll); voltage has little to alias; and AVG ≥ ~16 would blow the 20 ms survival
freshness budget. AVG=4 is the resting point. *Accepted residual:* if the platform's
reset write itself fails on a survival wake, -150 reads a stale value — but that value
is always a sub-13 V survival reading, so it can only force a re-sleep (never a false
exit or brick), self-correcting on the next wake; worst case is one 120 s cycle of
delayed recovery, invisible against the modem-bound ~3–4 min recovery.

**Register-map reference (for any future hardware alert):** the INA260 Mask/Enable
register is **0x06** (alert-function select; CNVR bit 10; CVRF bit 3) and the Alert
Limit register is **0x07** (threshold value). Verified against TI SBOS656C §8.6 and
`Adafruit_INA260.h`. (Firmware prior to V1.6 had these two swapped, which is why
its conversion-ready mode never actually engaged.)

### 2.4 Sleep-Current Stack

|Component          |Active (µA)|Power-down (µA)           |
|-------------------|-----------|--------------------------|
|ESP32-C3 deep sleep|—          |5–10                      |
|XIAO LDO (XC6210)  |—          |0 (bypassed) / 35 (active)|
|INA260             |330        |**2**                     |
|D24V7F3 quiescent  |35         |35                        |
|DS18B20 standby    |1          |1                         |
|**Total**          |           |**43 (best) / 83 (worst)**|

This board-level figure — not the INA260’s 2 µA alone — is the correct sleep
floor for the power budget (§6). Conflating the two is the most common error in
runtime estimation for this device (see §6.5).

-----

## 3. Measured System Data

All figures from the INA260 coulomb-counted May 6 2026 outage test
(`UPS_Report_2026-05-06`).

### 3.1 Battery & Load

|Parameter                         |Value            |
|----------------------------------|-----------------|
|Usable capacity at 1.18 A (to LVD)|4.18 Ah / 53.3 Wh|
|Typical load current              |1.18 A           |
|Typical load power                |14.9 W (DC)      |
|Float voltage                     |~13.23 V         |
|BP-65 LVD trip voltage (observed) |11.675 V         |

**Load composition (drives the shutdown-margin framing):** the protected DC load
is XB7-dominated — XB7 ≈ 12.2 W of ~15 W total; HA Green ≈ 0.8 W. The XB7 is *not*
gated by HA shutdown — it draws until the BP-65 disconnects it. So the graceful HA
shutdown sheds no meaningful load and does not extend runtime; its only job is
letting HA Green sync its filesystem before the BP-65 cuts power.

### 3.2 Discharge Phases (at 1.18 A, from Voltage.csv)

|Phase           |Band         |Duration    |
|----------------|-------------|------------|
|Settling        |13.00–13.15 V|~5 min      |
|Plateau         |12.65–13.00 V|~142 min    |
|Knee            |12.40–12.65 V|~49 min     |
|Cliff           |< 12.40 V    |~17 min     |
|**Total to LVD**|             |**~213 min**|

### 3.3 Shutdown Timeline & Margin

|Event                                             |Voltage  |Time (UTC)         |
|--------------------------------------------------|---------|-------------------|
|`cliff_imminent` fires (graceful shutdown trigger)|12.43 V  |13:39:41           |
|`hassio.host_shutdown` called                     |—        |13:40:11           |
|Last HA sample                                    |—        |13:40:17           |
|11.80 V threshold crossed                         |11.80 V  |13:56:27           |
|**BP-65 LVD actual trip**                         |~11.675 V|**~13:58:30 ±15 s**|

The actual trip is ~13:58:30, not the 11.80 V crossing at 13:56:27: the Victron
BP-65 adds a 102 s alarm-plus-disconnect delay (12 s + 90 s), and the last
under-load sample at 13:58:17 still showed the load drawing (I = −1.216 A).

**Margin:** shutdown call (13:40:11) → power loss (~13:58:30) = **~18 min** of
runway. HAOS completes a clean shutdown in ~2 min (HA returned online cleanly post-
recovery, confirming the shutdown completed). The margin is therefore ~16–18 min,
not the ~1 min implied by an earlier conservative model that assumed a 15-min HAOS
shutdown and placed the trip at the 11.80 V crossing. No change to the
`cliff_imminent` trigger is warranted: even if the cliff slope steepened to the
§7.2-class watch threshold of −70 mV/min, 755 mV ÷ 70 ≈ 10.8 min − ~2 min shutdown
≈ 9 min margin remains, and the steepening would be flagged first.

### 3.4 Capacity Below LVD (binding unmeasured input)

**Uncertainty flag:** there is no measured data below 11.675 V on this pack at any
current. These are estimates. The same gap means the *post-trip resting OCV* (load
removed, ESP-only) is also unobserved: the May 6 event’s telemetry blackout
(4 min 44 s — the WiFi AP rides on the XB7, which the BP-65 cuts at the trip, so the
streamed log cannot see past the load collapse) spans exactly that window. This
unmeasured resting OCV is what gates the exit-threshold choice in §5.2.

|Parameter                               |Estimate        |Basis                             |
|----------------------------------------|----------------|----------------------------------|
|Capacity remaining below LVD at 1.18 A  |~0.5 Ah         |Rate-effect estimate; not measured|
|Effectively available for survival sleep|**~0.41–0.5 Ah**|Design basis (see note)           |

V1.7 arms survival sleep *at the BP-65 trip* rather than after draining a further
175 mV awake (the old 11.50 V scheme spent ~0.088 Ah awake first). Arming at the
trip therefore makes nearly the full ~0.5 Ah available rather than ~0.41 Ah. The
budget (§6) reports **0.41 Ah / ~15 days as the conservative floor** and
**~0.5 Ah / ~18 days as the upside**; both rest on the same unmeasured capacity and
both clear the 10-day target with margin.

-----

## 4. Operational Timeline (extended outage)

```
T+0          Grid fails. on_battery fires (delayed_on 10s). Outage notification.
T+142 min    Plateau exhausted (~12.65 V).
T+191 min    Knee exhausted (~12.40 V) — voltage_warning fires.
T+196 min    cliff_imminent fires (~12.43 V, slope-based) — graceful shutdown.
~T+213 min   BP-65 trips (~11.675 V). XB7 + HA Green unpowered.
             Current collapses ~1.2 A → ~-0.04 A (ESP sole load). V rebounds.

~T+213.5 min Survival sleep arms (load-collapse signature, §5.1):
             on_battery == true AND -0.30 A < I < +0.20 A, sustained 30 s.
             Final snapshot written (counters intact). survival_mode_active set
             in NVS — within ~1 min of the trip, before the 30-min api
             reboot_timeout can fire. INA260 powered down. Deep sleep, 120 s wake.

Survival sleep active: 120 s wake cycles.
             Each wake: platform reconfigures INA260 (AVG=4), +20 ms settle,
             direct I2C read, decide.
             Implausible read → exit (fail-safe boot).  V ≥ 13.0 V (×2) → exit.
             > max cycles (~15 days) → exit.  Else → re-sleep.

AC restored: PSU drives V > 13.0 V within minutes (CC step jumps ~11.7→13.1 V in
             < 4 s). Next wake confirms ≥ 13.0 V twice → clears the flag,
             finalizes the outage record, normal boot. ESP is networkless ~4–5 min
             while the XB7 AP boots (benign; non-blocking; covered by wifi
             reboot_timeout 15 min). Telemetry resumes — no network needed during
             sleep.
```

-----

## 5. Entry / Exit Logic

### 5.1 Entry — load-collapse at the BP-65 trip (fail toward sleep)

**Arm when `on_battery == true` AND `−0.30 A < I < +0.20 A`, sustained 30 s.**

The design “shadows” the BP-65: it sleeps when the BP-65 cuts the load. Once the
BP-65 opens, HA Green and the XB7 are unpowered — there is no AP, no API client,
nothing to stay awake for — so arming at the trip is correct, and it sets the NVS
flag within ~1 min of the trip (which is what makes the data-integrity issues of
§8 structurally impossible rather than merely guarded).

**Why there is no voltage gate.** An intermediate design gated entry on a post-trip
voltage estimate (`V < 12.5 V`). That threshold was *unmeasured*, and its failure
mode was the worst available: had the real post-trip rebound exceeded the gate,
survival sleep would *never arm* and the ESP would drain the pack to BMS cutoff —
the one outcome the feature exists to prevent. Since the gate’s only benefit was
Ah-fidelity (out of scope), it was pure downside and was removed. The entry logic
now contains no threshold that can block sleep.

**Why the current is a window, not a floor:**

- **Lower bound −0.30 A** must clear the ESP’s own WiFi-Tx transient, not just its
  ~40 mA base. A C3 transmit burst (~350 mA at 3.3 V, through the ~85 %-efficient
  buck, reflected to 12 V ≈ 113 mA) plus the ~40 mA base gives a ~153 mA peak. A
  −0.15 A floor would sit *inside* that envelope; with the modem dead the C3
  reconnects aggressively, so frequent Tx spikes would reset the 30 s timer and
  arming might never complete — a field-only failure (benign on the bench, where
  an AP is present). −0.30 A clears the spike by ~150 mA and stays ~900 mA below
  the ~1.2 A XB7-connected load.
- **Upper bound +0.20 A** rejects the recovery/charging case. On AC return the
  current goes strongly positive (~+4.5 A); without an upper bound, a current-only
  floor could false-arm during early recovery while `on_battery` is still inside
  its 60 s `delayed_off`. Post-trip current (~−0.04 A) is far below +0.20 A, so the
  upper bound can never block legitimate sleep — it only excludes charging.
- **`on_battery == true`** confirms we are actually in an outage, so the window
  cannot arm on a normal-operation current excursion at float.

**Fail-toward-sleep:** post-trip current sits comfortably inside the window, so a
slightly mis-reading sensor still arms. Arming a little early or late around the
trip is harmless; *not* arming would drain to cutoff. This is the only entry
assumption, and it is robust.

### 5.2 Exit — 13.0 V, single confirmed (fail toward exit)

**Exit when `V ≥ 13.0 V`** (V1.8; was 12.8 V), confirmed by a single re-read
(50 ms apart) as I2C-glitch insurance.

The threshold is chosen to **bracket** the recovery transition rather than to track
the BP-65 reconnect (which V1.7 conflated with the exit):

- **Above the post-trip resting OCV.** A depleted 4S LFP pack at the trip is
  *estimated* to relax to ~12.8–13.0 V at ~10 % residual (the flat part of the LFP
  curve), but this is **unmeasured** — see §3.4. 13.0 V is set at the top of that
  estimated band so a resting pack does not cross it. This both lowers the chance of
  a spurious wake-exit during an outage and, because the re-arm loop is
  self-limiting (it walks the OCV down to the threshold and then settles into normal
  sleep), shrinks the runtime cost if one ever does occur. Raising from 12.8 V to
  13.0 V buys margin on a number nobody has measured.
- **Below the recovery charging voltage.** The May 6 recovery is the relevant
  bound here: on AC return the PSU goes to CC and the first observed sample was
  **13.093 V at +4.59 A**, climbing to 13.30 V float. 13.0 V sits ~90 mV under that,
  so a genuine recovery is still caught on the first wake (worst case the second, if
  a wake lands in the first ~30–60 s of CC while V is still climbing through 13.0 V).
  One extra 120 s cycle is invisible against the modem-bound ~3–4 min AP boot, so the
  raise is **not** consequential to recovery timing.

> **v10 note (interacts with FIX 2):** because the first recovery CC sample
> (13.093 V) is *below* the 13.15 V `on_battery` threshold, `on_battery` can briefly
> latch ON during the CC ramp on a survival recovery and then release as V climbs to
> float — firing `on_release`. The earlier claim that “`on_battery` may not toggle at
> recovery, so finalization happens only in -150” is therefore *not* universally true;
> see §8 / §9.2 for the FIX 2 guard that makes a stray `on_release` harmless.

Note the distinction the earlier draft blurred: the *“11.7 → 13.09 V within 4 s of
CC onset”* figure is the **recovery (charging) transient** — it bounds the recovery
*ceiling* (why 13.0 V still catches recovery), and says nothing about the *resting*
OCV. The resting OCV is the unobserved quantity (§3.4). Because 13.0 V is set above
its estimate, the earlier dual-read + 200 mV hysteresis machinery remains
unnecessary and stays removed; the single confirm re-read is kept purely as
I2C-glitch insurance.

The BP-65’s own reconnect (V > 12.8 V for 30 s) is independent and unchanged; with
the ESP exit now at 13.0 V, the ESP wakes *at or after* the BP-65 has begun
restoring the load — benign, since recovery is modem-bound regardless.

**Residual:** this is a reasoned hedge, not a verified bound. If the true resting
OCV ever exceeds 13.0 V, the device re-arms rather than bricking (the loop
self-recovers), but runtime degrades. One out-of-band rest reading closes it — see
§13.

### 5.3 Wake Fail-Safe (fail toward exit; never re-sleep on doubt)

`survival_mode_active` is NVS-persisted, so a sensor that always reads low would
otherwise force re-sleep forever — a brick recoverable only by physical reflash.
The cost asymmetry is decisive: a false exit just re-arms and re-sleeps in ~30 s
(~1–4 mAh); a wrong re-sleep bricks. Therefore:

- **Implausible wake read** (raw register 0x0000/0xFFFF, or V < 5.0 V or V > 16.0 V)
  → clear the flag, boot normally.
- **Max-cycle backstop** (`survival_max_cycles`, ~15 days) → force exit on a
  stuck-but-plausible-low sensor.

Neither path “reports” anything — recovery is simply telemetry reappearing in HA
on the cold boot. Plausibility is checked on the *value* (the read buffer is
pre-zeroed, so a failed read reads as 0x0000), which is more robust than trusting
an I2C return code.

-----

## 6. Power Budget

### 6.1 Wake-Cycle Model

Two boot scenarios occur during survival sleep:

- **Scenario A — AP absent (dominant):** WiFi finds no AP; the wake decision
  completes and `deep_sleep.enter` re-sleeps. Short active window. This is the vast
  majority of cycles, because the modem is unpowered for the entire outage.
- **Scenario B — recovery:** the PSU has restored, V ≥ 13.0 V, the device exits.
  This is the terminal cycle. Scenario B essentially cannot span multiple wake
  cycles: at the 4.5 A CC charge rate, terminal voltage jumps ~1.17 V (I × Ri) on
  PSU restoration, crossing 13.0 V within seconds (worst case one extra 120 s cycle
  if a wake lands in the first ~30–60 s of CC). (It is also structurally impossible for
  the XB7’s AP to be present before the pack has charged past the BP-65 reconnect,
  since the XB7 sits behind the BP-65.)

### 6.2 Runtime

Using the worst-case board sleep floor (83 µA) and a conservative short active
window, the blended average is ≈ **1.151 mA**, dominated entirely by Scenario A.

```
Conservative floor:  0.41 Ah ÷ 1.151 mA = 356 h = ~14.8 days   (48% margin)
Upside (arm-at-trip): ~0.5 Ah ÷ 1.151 mA = 434 h = ~18 days
```

Report **~15 days / 0.41 Ah as the design floor** and **~18 days / ~0.5 Ah as the
upside**. The two differ only in the below-LVD capacity, which is unmeasured; both
clear the 10-day target with margin. Do **not** report the two as if they were
independent, and do **not** cite the much larger figures (32–64 days) that appear
when an INA260-only 2 µA floor is mistakenly used in place of the ~43–83 µA board
floor (§2.4, §6.5).

### 6.3 Capacity Sensitivity (the binding constraint)

```
0.41 Ah (design floor):  0.41  ÷ 1.151 mA = 14.8 days   ✓  48% margin
0.30 Ah:                 0.30  ÷ 1.151 mA = 10.9 days    ✓   9% margin
0.276 Ah:                0.276 ÷ 1.151 mA = 10.0 days   ←  break-even (the 10-day target)
0.27 Ah:                 0.27  ÷ 1.151 mA =  9.8 days    ✗  (just under)
0.25 Ah:                 0.25  ÷ 1.151 mA =  9.1 days    ✗
```

The below-LVD capacity is the only input that meaningfully gates whether the
10-day target is met. Everything else (scenario split, interval) has negligible
effect at realistic Scenario-A dominance.

### 6.4 Why the Interval Choice Is Robust to the Unmeasured Floor

Because Scenario A dominates, runtime is driven by the sleep floor and the per-wake
burst energy — not by interval length directly. But the interval *does* set how
often the burst energy is paid, and that sensitivity depends on the sleep floor,
which is unmeasured. The interval is selected (§7) so the 10-day target is met even
at the *pessimistic* end of the floor range — i.e. without needing the measurement.

### 6.5 The 2 µA Trap

A circulating table shows 32–64 days by using the INA260’s 2 µA shutdown current
as the *sleep floor*. That is wrong: during sleep the battery powers the whole
board (C3 deep sleep + buck quiescent + INA260), which §2.4 puts at ~43–83 µA — 20–
40× higher. The 2 µA figure is the INA260 term *within* that stack, not the stack.
A single µA-meter reading on the battery lead during one sleep cycle resolves this
definitively (§13) and is the highest-value remaining measurement.

### 6.6 Event-Wake: Evaluated and Backed Out (V1.10 → V1.11)

V1.10 kept the INA260 awake to assert a recovery ALERT and demoted the timer to a
10 min backstop. **V1.11 backs this out.** The reasoning that retired it:

1. **It is strictly more energy at equal interval.** Event-wake = (same-interval
   timer-wake burst energy) **+** a continuous ~310–420 µA INA-awake floor. At the
   600 s backstop it averaged ~0.57–0.72 mA vs the 120 s timer-wake’s 1.151 mA — but
   that apparent win comes entirely from the 5× *longer interval*, not from event-wake
   itself. A plain 600 s timer-wake would average **less** (it pays the burst every
   600 s with the INA powered down at ~2 µA, no 310 µA floor). So event-wake never
   saves energy at a given interval; it only ever costs.
1. **Its sole benefit is cosmetic.** End-to-end recovery is modem-bound (~3–4 min XB7
   AP boot, §7) and the XB7 load is restored by the BP-65 reconnect independent of the
   ESP. Waking the ESP faster than the timer only resumes its *local* telemetry a
   minute or two sooner — invisible against the modem floor.
1. **It added real failure surface.** GPIO3 became a recovery-critical SPOF; a
   shared-pin `allow_other_uses` coupling; the INA pinned awake; a BOL register dance
   armed/cleared in three places; and a standing `-rc` validation burden (its gating
   bench checks never passed).

**Latest survival estimate (V1.13) is the §6.2 timer-wake figure: ~15 days at the
0.41 Ah design floor (~18 days at 0.50 Ah)**, average draw ≈ 1.151 mA, dominated by
the per-wake burst (≈ 1.07–1.11 mA) over the 43–83 µA floor. Every term still carries
the §3.4 / §2.4 *unmeasured* flag; the estimate is **burst-dominated**, so it hinges
almost entirely on the per-wake active window. If the real window is ~2× the ~1.6 s
the model assumes, average draw ≈ 2.2 mA and runtime falls to **~7.5 days — under
R-1.** That single sensitivity, not event-wake, is what the §13 measurement must
settle before sign-off.

### 6.7 `run_duration` Watchdog — Failure-Tail Bound (V1.11; corrected V1.12)

The watchdog does **not** change the §6.2 normal-survival estimate. On a healthy
survival wake the device explicit-sleeps at priority -150 within ~50 ms–3 s, long
before `run_duration` (60 s) could fire, so it adds **zero** energy to the normal
path. It governs only the failure tail:

- **Guarantee:** no sensor/pin/bus failure can strand the device *awake*. After
  `run_duration` awake, `deep_sleep` auto-sleeps unless normal operation was
  positively confirmed (priority -160: a *plausible* INA read ⇒ normal logic in
  control; **or** WiFi association ⇒ AC present, the AP being behind the BP-65). Both
  are independent; either suffices. Verified against `deep_sleep_component.cpp`:
  `begin_sleep(manual)` runs `if (prevent_ && !manual) return;`, so `prevent` blocks
  only the `run_duration` auto-sleep, never an explicit `deep_sleep.enter` (survival
  re-sleep/entry are `manual=true` and always sleep). The watchdog can neither strand
  awake nor block a survival sleep.

- **⚠ The auto-sleep MUST have a wake source — FIX 1 (V1.12).** The “auto-sleep
  re-sleeps it” guarantee above is only real if the watchdog auto-sleep actually has a
  way to wake. On the C3, `deep_sleep_()` (verified in `deep_sleep_esp32.cpp`,
  ESPHome 2026.5.3) enables the timer wake only `if (sleep_duration_.has_value())`,
  and there is no `wakeup_pin`. The `run_duration` auto-sleep calls
  `begin_sleep(manual=false)` on the boots where **no** `deep_sleep.enter` has run
  (dead-INA entry; fail-safe-exit mid-outage) — so the component must carry its own
  `sleep_duration`. **V1.11 set `sleep_duration` only inside the `deep_sleep.enter`
  actions, not on the component**, so the watchdog auto-sleep enabled no wake source
  → permanent, wakeup-less deep sleep = a silent brick with no auto-recovery on AC
  return, in exactly the failure cases this watchdog targets. **V1.12 adds
  `sleep_duration: ${survival_sleep_interval}` to the `deep_sleep` component**
  (confirmed in generated `main.cpp` as `set_sleep_duration(120000)`), so the
  auto-sleep wakes on the 120 s timer and the ride-out below is what actually
  happens. This is a fail-safe invariant, recorded in §9.3.

- **Improvement over V1.9.2:** the old “fail-safe EXIT then can’t re-arm → drain”
  case (a hung INA mid-sleep) now re-sleeps via the watchdog and rides out the outage.
- **Honest scope — does NOT give multi-day survival on a dead sensor.** In a true
  dead-INA ride-out the device waits the full `run_duration` awake each cycle (~60 s
  awake / 120 s asleep, ~33% duty), so it bounds the drain *rate*, not the total: it
  extends drain-to-cutoff from ~5 h (fully awake) to **~1 day**, an intervention
  window for the human to notice (device offline / INA-unhealthy in HA) — not 10 days.
  There is also a residual ≤~30 min window where a device already booted in normal
  operation (sleep prevented) then loses its INA *at the trip* won’t re-evaluate until
  the `api reboot_timeout` reboots it. True dead-sensor survival needs the Tier-4
  independent ADC (§14) — a board change, not firmware. **Not claimed closed here.**

-----

## 7. Wake Interval: 120 s (timer-wake, primary)

> **V1.11+:** event-wake is removed (§6.6), so the timer is again the *primary* and
> only wake source, tuned for recovery responsiveness against the modem floor.
> `survival_sleep_interval` = 120 s; `survival_max_cycles` = 10800 (15-day
> stuck-sensor backstop, 10800 × 120 s). 120 s is intentional — runtime is not the
> binding constraint, so the interval is not over-provisioned, and at 120 s the NVS
> write rate is a non-issue over the device’s life given how rare outages are. In
> V1.12 the same value is *also* the `deep_sleep` component `sleep_duration` (§6.7,
> §9.3), so the watchdog auto-sleep wakes on the same 120 s timer.

The interval became a free variable once runtime cleared the 10-day target with
margin — at that point reserve is over-provisioned and the interval should be tuned
for recovery responsiveness, not hoarded reserve. Three candidates:

|Interval |Recovery latency|10-day coverage                                                                 |Verdict                                                             |
|---------|----------------|--------------------------------------------------------------------------------|--------------------------------------------------------------------|
|300 s    |~5 min          |months of reserve                                                               |Over-provisioned; wastes the free variable                          |
|60 s     |~1 min          |*contingent on the unmeasured floor* (≈6.8 days at 0.41 Ah / worst-case ~2.5 mA)|Risky — makes 10-day coverage depend on a number nobody has measured|
|**120 s**|**~2 min**      |**clears 10 days under the pessimistic stack (~11+ days)**                      |**Selected (V1.11+) — robust to the missing measurement**           |

`survival_max_cycles = 10800` held the ~15-day fail-safe backstop at 120 s
(10800 × 120 s = 15.0 days) — restored in V1.11 from the 4320 × 600 s V1.10 value.

**Note on responsiveness:** end-to-end *system* recovery is modem-bound — the XB7
takes ~3–4 min to boot its AP after the BP-65 reconnects — so waking faster than
~2 min does not get Home Assistant back any sooner; it only resumes the ESP’s local
telemetry marginally earlier. 60 s would therefore cost the most reserve for the
least *practical* recovery gain. 120 s captures essentially all the responsiveness
the modem floor allows while staying robust on runtime.

-----

## 8. Data Integrity

The data-integrity concerns that drove several earlier guard-based fixes are, in
V1.7, **structurally** resolved by arming at the trip:

- Because `survival_mode_active` is set within ~1 min of the trip — before the
  30-min `api reboot_timeout` can fire its first reboot — there is no window in
  which a watchdog reboot can reset the per-outage counters. No `outage_in_progress`
  flag and no `reboot_timeout` change are needed for integrity; `reboot_timeout`
  stays at 30 min for normal-operation self-heal.

The mechanisms actually present (V1.13):

|Mechanism                                         |Purpose                                                                                                                                                                                                                                                                                     |
|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|Snapshot at arm time                              |`last_outage_ah/wh/min_v/start_v/duration` written at the trip while counters are intact → captures the true full-outage figure.                                                                                                                                                            |
|`outage_was_survival` (NVS)                       |Set at arm; cleared at the deterministic recovery instant (priority -150), which is where the survival outage is finalized.                                                                                                                                                                  |
|**`outage_start_uptime > 0` guard on `on_release` (FIX 2, V1.12)**|**The authoritative protection for the snapshot.** Priority -150 clears `outage_was_survival` at boot, and the recovery CC sample (~13.093 V) is *below* the 13.15 V `on_battery` threshold, so `on_battery` *can* latch ON then release on a survival recovery and fire `on_release` minutes later — after the flag is cleared. The recompute is therefore gated on `outage_start_uptime > 0`: on a survival recovery that global is 0 (transient; -100 is skipped while armed), so `on_release` does not touch `last_outage_ah/wh/duration` (the arm-time snapshot stands). On a genuine awake-tracked outage (start>0) it recomputes exactly as before. Recharge-peak capture stays unconditional (the CC peak only develops during the recovery the snapshot couldn’t see).|
|Priority -100 counter preservation                |A mid-outage reboot keeps the `restore: true` counters from NVS and only re-anchors missing timing; discharge-direction guarded (I < −0.05 A).                                                                                                                                              |
|**`on_press` in-outage guard (item 7, V1.12)**    |**Backs up priority -100 on a mid-outage reboot.** On such a reboot, -100 re-anchors `outage_start_uptime` at +6 s; `on_press` then early-returns when `outage_start_uptime != 0` (it fires ~+10 s), so it does **not** reset the `restore: true` Ah/Wh or double-increment `total_outage_count`. The companion `on_release` clear of `outage_start_uptime` on a clean outage end keeps consecutive outages recording normally. Relies on the `on_battery` `delayed_on` (10 s) > the -100 delay (6 s) ordering. Closes the gap §8 previously left to -100 alone.|
|Discharge-direction guard on `on_battery on_press`|A false outage cannot be counted while charging (I must be < −0.05 A). **Item 10 (V1.12):** the guard fails **closed** on a NaN current (`isnan(i) || i > -0.05f`), so a bad/absent read no longer falls through to count a phantom outage.|
|100 ms NVS flush on entry *and* re-sleep          |Guarantees the arm snapshot and the `survival_cycle_count` increment commit before deep sleep cuts power.                                                                                                                                                                                   |

> **v10 correction.** v9 stated the snapshot “is never overwritten by post-cold-boot
> values” because finalization is in -150 and “recovery’s `on_battery` may not
> toggle.” The review showed `on_battery` *can* toggle on a survival recovery (the CC
> sample is below the threshold), so `on_release` could fire and overwrite the
> snapshot via its normal path — the `if (outage_was_survival)` branch that was
> supposed to protect it is unreachable once -150 has cleared the flag. The FIX 2
> `start>0` guard is what now makes the snapshot robust regardless of `on_battery`
> timing; -150 remains the finalizer.

-----

## 9. Implementation — Firmware V1.13

### 9.1 Substitutions (survival)

|Key                        |Value  |Note                                                                                                                                                                                |
|---------------------------|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|`survival_entry_current_lo`|`-0.30`|Arm when I > this (load gone; above Tx peak)                                                                                                                                        |
|`survival_entry_current_hi`|`0.20` |AND I < this (rejects charging)                                                                                                                                                     |
|`survival_exit_v`          |`13.0` |Exit at/above. Above the estimated resting OCV, below the observed recovery CC (13.093 V); decoupled from the BP-65’s 12.8 V reconnect                                              |
|`survival_sleep_interval`  |`120s` |**Timer-wake, primary** (reverted from the 600 s V1.10 backstop). Also the `deep_sleep` component `sleep_duration` (FIX 1, §9.3) so the watchdog auto-sleep wakes on the same timer |
|`survival_max_cycles`      |`10800`|15-day stuck-sensor guard at 120 s (10800 × 120 s)                                                                                                                                  |
|`survival_run_duration`    |`60s`  |**V1.11 watchdog**: max awake-per-boot before auto-sleep, unless normal op is confirmed. > the 30 s arm window so a healthy-INA post-trip reboot arms instead of racing the watchdog|

### 9.2 Boot Blocks

- **Priority 600** — **wake-cause log only** (timer vs cold — validation aid). As of
  V1.13 there is **no INA260 config write here**: the `ina260` platform resets and
  configures the chip (continuous, AVG=4) at its own setup, which runs after this
  block (§2.3). **No BOL alert writes** (event-wake removed; the 0x06/0x07 map is
  retained only as a reference comment).
- **Priority -100** — reboot-during-outage recovery: preserves counters from NVS,
  re-anchors timing only, guarded by `!survival_mode_active && I < −0.05 A`.
- **`on_battery` `on_press`** — outage-start recorder. Guards run in order: survival
  suppression → discharge/NaN guard (V1.12 item 10: `isnan(i) || i > -0.05f`, fails
  closed) → **in-outage guard** (V1.12 item 7: early-return if `outage_start_uptime
  != 0`, so a mid-outage reboot does not re-record) → record + reset the integrators
  (V1.12 item 5: the resets sit *inside* the guarded lambda).
- **Priority -150** — survival wake decision: **20 ms settle** (V1.13 — now the sole
  freshness wait; sized for a fresh AVG=4 conversion, §2.3), direct 0x02 read,
  value-plausibility fail-safe, max-cycle backstop, 13.0 V dual-read exit,
  deterministic survival-outage finalization (clears `survival_mode_active` and
  `outage_was_survival`, logs the survival OUTAGE END). The re-sleep path **powers the
  INA260 down** (0x00 = 0x6120, ~2 µA) and includes a 100 ms NVS flush before
  `deep_sleep.enter` (120 s). No per-exit BOL writes (nothing is armed).
- **`on_battery` `on_release` (FIX 2 + item 7, V1.12)** — the normal-outage finalizer;
  its `last_outage_ah/wh/duration` recompute is gated on `outage_start_uptime > 0` so a
  stray survival-recovery `on_release` (see §8) cannot overwrite the arm-time snapshot,
  and it **clears `outage_start_uptime` on a clean outage end** so the next outage's
  `on_press` records normally (the companion to the item-7 in-outage guard).
  Recharge-peak capture is unconditional.
- **Priority -160 (watchdog confirm)** — if `!survival_mode_active`, do a fresh
  raw 0x02 read; if **plausible** (sensor working ⇒ normal/survival logic in
  control), call `deep_sleep.prevent` to disarm the `run_duration` auto-sleep. If
  not plausible, do not prevent — WiFi `on_connect` may still confirm; otherwise
  `run_duration` sleeps the device (bounded awake drain). Runs after -150, so a
  survival re-sleep (explicit `deep_sleep.enter`) never reaches it.
- **Priority -200** — boot-complete log (“timer-wake + run_duration watchdog”).

### 9.3 `run_duration` Watchdog Wiring (V1.11; FIX 1 in V1.12)

- `deep_sleep:` declares **`run_duration: ${survival_run_duration}`**, **`sleep_duration:
  ${survival_sleep_interval}`** (FIX 1), and **no `wakeup_pin`** (GPIO3 removed from
  the wake path). On every boot the component schedules an auto-sleep after
  `run_duration`; it fires only if sleep was not prevented, and — because
  `sleep_duration` is now on the component — it wakes on the 120 s timer rather than
  sleeping with no wake source.
  - **Invariant (do not remove):** the component-level `sleep_duration` is the wake
    source for the watchdog auto-sleep. Without it the auto-sleep is wakeup-less on the
    C3 (no timer, no `wakeup_pin`) → permanent deep sleep. The two `deep_sleep.enter`
    actions set `sleep_duration` at call time and so are unaffected, which is exactly
    why the V1.11 omission went unnoticed until the dead-sensor path was traced.
- **Two independent confirmations call `deep_sleep.prevent`** (either alone
  suffices): priority -160 (plausible INA read, §9.2) and the **`wifi:` `on_connect`**
  lambda (association to the home AP ⇒ AC present, INA-independent — the XB7 sits
  behind the BP-65). Both are guarded by `!survival_mode_active`.
- **Verified against `deep_sleep_component.cpp` / `deep_sleep_esp32.cpp` (ESPHome
  2026.5.3):** `begin_sleep(bool manual)` runs `if (this->prevent_ && !manual) {
  next_enter_deep_sleep_ = true; return; }`; the `run_duration` auto-sleep calls it
  with `manual=false` (so `prevent` blocks it), while an explicit `deep_sleep.enter`
  passes `manual=true` and sleeps **regardless** of `prevent`. And `deep_sleep_()`
  enables the timer wake only `if (sleep_duration_.has_value())` — the basis for FIX 1.
  Therefore a stray WiFi-connect can never block a survival re-sleep, the watchdog can
  never strand the device awake, and (with FIX 1) it can never strand it asleep
  either. (Validation: source review + config valid + full codegen clean on 2026.5.3,
  with `set_sleep_duration(120000)` confirmed in the generated `main.cpp`. The final
  on-host `esphome compile` (link) + flash is the remaining gate — §13.)
- `ina260_alert` binary_sensor is retained as a **single-owner** passive input
  (`allow_other_uses` removed); it logs an unexpected sustained ALERT-low (>200 ms)
  as a possible INA/I2C fault — nothing in V1.13 should ever assert it.

### 9.4 Survival Sleep Armed (binary sensor)

Template lambda: `on_battery.state && I > −0.30 && I < +0.20`; `delayed_on: 30s`.
On press: reset `survival_cycle_count`, write the final snapshot, set
`survival_mode_active` + `outage_was_survival`; then 100 ms flush, **power the INA260
down** (0x00 = 0x6120, ~2 µA), `deep_sleep.enter` (120 s timer-wake). The explicit
`deep_sleep.enter` is `manual=true`, so it sleeps regardless of any watchdog prevent.

### 9.5 Globals (survival)

`survival_mode_active` (NVS), `survival_should_sleep` (transient),
`survival_cycle_count` (NVS), `outage_was_survival` (NVS).

-----

## 10. Risk Register

|Risk                                                                                        |Severity                   |Status                                                                                                                                                                                                                                                              |
|--------------------------------------------------------------------------------------------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|ESP stays awake after BP-65 trip → drains to BMS cutoff                                     |High                       |Mitigated — entry fails toward sleep; no blocking threshold                                                                                                                                                                                                         |
|Indefinite re-sleep brick on stuck-low sensor                                               |High                       |Mitigated — fail-toward-exit + max-cycle backstop                                                                                                                                                                                                                   |
|False-arm into recovery                                                                     |Medium                     |Mitigated — +0.20 A upper bound rejects charging                                                                                                                                                                                                                    |
|Tx-spike resets the arm timer                                                               |Medium                     |Mitigated — −0.30 A lower bound clears the ~153 mA peak                                                                                                                                                                                                             |
|Lost NVS write before sleep                                                                 |Low                        |Mitigated — 100 ms flush on entry and re-sleep                                                                                                                                                                                                                      |
|Below-LVD capacity unmeasured                                                               |Low (for the 10-day target)|Accepted — only affects *how long* sleep lasts; 120 s clears 10 days at the pessimistic end                                                                                                                                                                         |
|Exit threshold below post-trip resting OCV → spurious wake-exit / re-arm loop (faster drain)|Medium                     |Reduced — exit raised to 13.0 V (V1.8), above the estimated ~12.8–13.0 V resting band; loop is self-limiting and re-arms rather than bricking. Residual: resting OCV unmeasured — §5.2, §13                                                                         |
|Survival path never run in a real outage                                                    |—                          |Open — see §13                                                                                                                                                                                                                                                      |
|**`run_duration` auto-sleep has no wake source → silent wakeup-less brick (V1.11)**         |**High (was latent)**      |**FIXED (V1.12, FIX 1) — `sleep_duration` added to the `deep_sleep` component; the auto-sleep now wakes on the 120 s timer. Verified `set_sleep_duration(120000)` in generated `main.cpp`. Caught in review before sign-off (§0, §6.7, §9.3).**                       |
|Any sensor/pin/bus failure strands the device AWAKE → drains                                |High                       |Mitigated (V1.11 watchdog, made real by FIX 1) — `run_duration` auto-sleeps unless normal op is confirmed by an INA-plausible read OR WiFi. Cannot strand awake (verified `manual` semantics, §9.3), and with FIX 1 cannot strand asleep. Bounds drain RATE, not total|
|Mid-sleep INA hang → fail-safe EXIT then can’t re-arm → drains awake (the V1.9.2 gap)       |Medium                     |Mitigated (V1.11 + FIX 1) — neither watchdog confirmation fires (INA hung + AP down) → auto-sleeps (now with a wake source) and rides out the outage in 120 s cycles                                                                                                |
|**Survival-recovery `on_release` overwrites the arm-time snapshot (V1.11)**                  |**Low–Medium (was latent)**|**FIXED (V1.12, FIX 2) — `on_release` recompute gated on `outage_start_uptime > 0`; on a survival recovery (start==0) the snapshot is untouched. §8 / §9.2.**                                                                                                       |
|**Mid-outage reboot (awake) lets `on_press` reset Ah/Wh + double-count (V1.12)**             |**Low (was latent)**       |**FIXED (V1.12, item 7) — `on_press` early-returns when `outage_start_uptime != 0`; `on_release` clears it on a clean end. Best-effort R-6 data only, no safety impact, but it contradicted §8's "counters preserved" claim. §8 / §9.2.**                            |
|**`on_press` discharge guard counts a phantom outage on a NaN read (V1.12)**                 |**Low (was latent)**       |**FIXED (V1.12, item 10) — guard fails closed: `isnan(i) || i > -0.05f`. Matches the isnan guards at priority -100.**                                                                                                                                                |
|**Doc/firmware said AVG=1; chip actually ran AVG=4; manual config write was dead (V1.13)**   |**Low (correctness)**      |**RESOLVED (V1.13) — the `ina260` platform is the sole configurator (reset + 0x0307, continuous AVG=4) and runs after the overwritten priority-600 0x6127 restore, which is removed. Freshness wait moved into the -150 decision (20 ms). Data path is two-stage (chip AVG=4 → 1 Hz read → 5 s `throttle_average`). No power or runtime impact. §2.3 / §9.2.**|
|**Platform reset fails on a survival wake → -150 reads stale value (V1.13)**                 |**Low**                    |**Accepted — the stale value is always a sub-13 V survival reading, so it forces a re-sleep only (never a false exit/brick), self-correcting on the next wake. One-cycle (120 s) recovery delay, invisible vs modem-bound ~3–4 min recovery. §2.3.**                  |
|Dead INA gives no multi-day survival (watchdog bounds rate only)                            |Medium                     |**Accepted / not closed** — dead-sensor ride-out extends drain-to-cutoff ~5 h → ~1 day (intervention window), not 10 days. Plus a ≤~30 min reassert window if the INA dies at the trip after a healthy boot. True fix = Tier-4 independent ADC (§14), a board change|
|Watchdog spuriously sleeps the device in normal operation                                   |Low                        |Mitigated — a healthy INA confirms in ~50 ms (plausibility-gated, not voltage-gated), and `run_duration` (60 s) > the 30 s arm window so a post-trip reboot arms properly. WiFi blips don’t sleep it (INA already confirmed)                                        |
|`esphome compile` not yet run on host                                                       |Low–Medium                 |**Reduced** — config valid + full codegen clean on ESPHome 2026.5.3 (FIX 1, both V1.12 guards, and the V1.13 changes all confirmed in generated `main.cpp`), no C++/codegen error. **Open:** the final on-host link + flash (the toolchain link step was not run in review) — §13                              |

The open survival-path failures remain *runtime degradation* modes (re-arm loop;
dead-sensor ride-out bounding rate not total); no open threshold can strand the
device asleep (it self-recovers toward exit; FIX 1 gives the watchdog auto-sleep a
wake source), and the `run_duration` watchdog closes the “stranded awake” class. The
residual is *duration* on a fully dead INA (§6.7), which is a hardware item (§14),
not a firmware threshold.

-----

## 11. Assumptions

- **A-1:** Below-LVD capacity ≈ 0.41–0.5 Ah. Unmeasured; binding input for runtime
  *duration* (not for whether the feature engages).
- **A-2:** ESP stack senses its own ~40 mA through the INA260 shunt (confirmed for
  this build). Post-trip current reads ≈ −0.04 A, inside the entry window. (HW
  dependency — see §2.0 note; the entry logic is wholly contingent on it.)
- **A-3:** Board sleep floor 43–83 µA (§2.4). Unmeasured; resolvable with one meter
  reading (§13). 120 s was chosen so the 10-day target holds at the 83 µA end.
- **A-4:** Post-trip resting OCV stays below the 13.0 V exit threshold. Unmeasured
  (§3.4); the threshold is set above the ~12.8–13.0 V estimate with margin and below
  the observed recovery CC (13.093 V). Binding for *exit safety*: if violated, the
  device re-arms (self-recovers) but runtime degrades — it does not strand or brick.

The *entry* logic uses no voltage threshold, so there is no entry-side post-trip
voltage assumption. The only post-trip voltage assumption is A-4 on the *exit* side.

-----

## 12. Uncertainties

|Uncertainty                     |Effect                                                                                    |Resolver                                       |
|--------------------------------|------------------------------------------------------------------------------------------|-----------------------------------------------|
|Board sleep current (43–83 µA)  |Sets actual runtime; the 2 µA-vs-board-floor confusion produces wildly different estimates|One µA-meter reading during a sleep cycle (§13)|
|Below-LVD capacity (0.41–0.5 Ah)|Sets runtime *duration*                                                                   |Deep-discharge bench test (now optional)       |

Both affect *how long* survival sleep lasts, not *whether* it engages or recovers.

-----

## 13. Validation Plan

The entry voltage gate’s removal collapses validation to behavioral checks plus one
recommended measurement:

|Item                                           |Method                                                                                                                                                                                                                                                                                                                                               |Priority                                          |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
|Board sleep current                            |µA-meter on the battery lead during one sleep cycle. Resolves all competing runtime estimates; cheap (steady-state, no deep discharge).                                                                                                                                                                                                              |**Recommended**                                   |
|Post-trip resting OCV (exit safety)            |DMM on the battery through one controlled discharge-to-trip; log rest V for ~5–10 min after the load collapses. The only thing that confirms resting OCV < 13.0 V (the A-4 / §5.2 hedge). Cheap; does NOT require discharge to BMS cutoff. Must be **out-of-band** (DMM, or an AP not behind the BP-65) — streamed logs die with the XB7 at the trip.|**Recommended**                                   |
|Arm fires at trip                              |Confirm `survival_sleep_armed` asserts within ~30 s of the load collapse                                                                                                                                                                                                                                                                             |High                                              |
|Does NOT arm on recovery                       |Confirm the +0.20 A bound prevents arming when charging begins                                                                                                                                                                                                                                                                                       |High                                              |
|13.0 V exit on recovery                        |Restore AC; confirm exit on first wake seeing ≥ 13.0 V ×2                                                                                                                                                                                                                                                                                            |High                                              |
|**Snapshot survives a survival recovery (FIX 2)**|Run a survival cycle, restore AC, and confirm `last_outage_ah/wh/duration` still hold the arm-time snapshot after `on_release` fires (i.e. the start>0 guard held). Watch for the absence of a clobbered (near-zero or re-derived) Ah on the recovery boot.                                                                                          |High                                              |
|Fail-safe exit                                 |Disconnect INA260 mid-sleep; confirm boot-normal, not re-sleep                                                                                                                                                                                                                                                                                       |High                                              |
|Deep-discharge capacity                        |Discharge to BMS cutoff; measure below-LVD Ah                                                                                                                                                                                                                                                                                                        |Optional (refines runtime; does not gate function)|
|**`esphome compile` clean — host link (V1.13)**|Config + full **codegen are confirmed clean on ESPHome 2026.5.3** (FIX 1, both V1.12 guards, the item-5/7/10 hardening, and the V1.13 config simplification all present in generated `main.cpp`). Remaining: run the final `esphome compile` (C++ link) on the build host and flash. (Review could not run the link — the toolchain download was unavailable in that environment.)                                                       |**Gating for V1.13 sign-off**                     |
|**Survival wake reads a fresh AVG=4 value (V1.13)**|On a survival wake, confirm the -150 decision read returns a plausible, fresh bus voltage with the platform as sole configurator and the 20 ms settle — i.e. the removed priority-600 restore is not missed. (Bench check; the platform's reset+0x0307 must run before -150 as analysed in §2.3.)                                                |Medium                                            |
|**Watchdog disarms in normal op (V1.11)**      |Boot on AC; confirm priority -160 logs “INA usable … watchdog disarmed” within ~50 ms and the device stays awake (does not sleep at `run_duration`).                                                                                                                                                                                                 |High                                              |
|**Watchdog re-sleeps on a dead sensor — wakes again (FIX 1)**|Hold the INA in reset with no AP reachable; confirm the device sleeps at `run_duration` **and wakes again ~120 s later** (the ride-out), rather than either staying awake or sleeping permanently. This is the direct check that FIX 1 worked on hardware.                                                                            |High                                              |
|**Survival re-sleep ignores prevent (V1.11)**  |Force a survival wake while WiFi is associating; confirm the explicit `deep_sleep.enter` still sleeps (the `manual=true` path).                                                                                                                                                                                                                      |Medium                                            |

**Standing caveat:** survival sleep has not yet run in a real outage — the May 6
event (217 min) never reached arming. The pre-LVD chain and the recovery side
(now validated against that event’s 13.093 V CC step, comfortably above the 13.0 V
exit) are well-validated; the deep-sleep path is validated by design, source review,
and codegen, not yet by a field event or an on-host link/flash. Note the post-trip
resting OCV remains unobserved on that event (the 4 min 44 s telemetry blackout,
§3.4) — which is why the out-of-band rest reading above is the highest-value
exit-safety measurement. The one µA-meter reading remains the highest-value
measurement overall: it settles the sleep floor *and* the burst-dominated runtime
that gates whether R-1 is actually met (§6.6).

-----

## 14. Hardware Path for a Complete Solution — Status and Next Step

**Event-wake (V1.10) — implemented, then backed out (V1.11).** The “future PCB”
anticipated in earlier revisions *is* the UPS-Monitor-THT Rev 1 board (§2.0): it
routes the INA260 ALERT to GPIO3 (D1), an RTC-domain pin, with R2. V1.10 used that
to wake the ESP on a recovery ALERT. V1.11 removed it (§6.6): the gain was cosmetic
(recovery is modem-bound), it cost more energy than timer-wake at the same interval,
and it made GPIO3 a recovery-critical SPOF. The board capability remains; the
firmware no longer uses it. This is a deliberate “tried it, measured the trade,
reverted” — not an unexplored option.

**The actual open item is sensor redundancy, not wake latency.** Every survival
decision — entry, re-sleep, exit — funnels through the *single* INA260. Firmware
fail-safes and the watchdog (§6.7, made whole by FIX 1) ensure a dead INA cannot
*brick* the device and cannot *strand it awake*, but they cannot manufacture a
voltage reading: on a fully dead INA the device can only ride out the outage at a
bounded drain *rate* (~1 day to cutoff), not survive the full ~15 days. Closing that
requires a **second, independent battery-voltage sense** the firmware can fall back on.

**Tier-4 — independent ADC battery sense (the complete-solution hardware path).**
Add a divider from BATT+ to a spare **ADC1** pin (ESP32-C3 ADC1 = GPIO0–GPIO4;
factory-calibrated; Wi-Fi-safe, unlike ADC2/GPIO5). GPIO4 (D2) is the natural
candidate — GPIO2 is a boot strap pin and is best avoided. With it, the survival
logic can cross-check or replace the INA reading, so a dead INA degrades to reduced
accuracy rather than to a bounded-drain ride-out. This is a **board change** (a
divider + a routed ADC pin), out of scope for V1.13 firmware, and is the recommended
content of the next PCB revision (it also aligns with the INA228/V2 direction, where
the ALERT/ADC pin map is being reconsidered anyway).

**Net effect (V1.13):** survival is the validated ~15-day timer-wake design at the
0.41 Ah floor (§6.2), the safety case rests on the deterministic fail-safe core
(§0, §5) plus the watchdog’s stranded-awake guarantee (§6.7, now with a real wake
source after FIX 1), and the one remaining *complete-solution* gap — survival on a
dead sensor — is correctly identified as a hardware item (Tier-4 ADC), not papered
over in firmware.

-----

## 15. References

- TI INA260 datasheet SBOS656C (§7.5 supply current; §8.6 register map).
- `Adafruit_INA260.h` — register definitions (0x06 Mask/Enable, 0x07 Alert Limit).
- ESP32-C3 Technical Reference Manual §6 (power management; RTC-domain wake pins).
- Seeed XIAO ESP32-C3 wiki and forum (#276444, #284207) — module sleep current.
- Victron BP-65 datasheet — LVD timer chain (12 s alarm + 90 s disconnect; 30 s
  reconnect holdoff at >12.8 V).
- `UPS_Report_2026-05-06` — coulomb-counted outage test; recovery transient; the
  post-trip log gap establishing post-trip V/I as unmeasured.
- ESPHome `i2c` / `deep_sleep` / `globals` component documentation; and the
  installed `deep_sleep_component.cpp` / `deep_sleep_esp32.cpp` (ESPHome 2026.5.3),
  source for the FIX 1 wake-source semantics (`esp_sleep_enable_timer_wakeup()` runs
  only `if (sleep_duration_.has_value())`) and the `begin_sleep(manual)` `prevent_`
  behaviour.
- `UPS-Monitor-THT.kicad_pcb` — UPS-Monitor-THT Rev 1 carrier PCB (KiCad 10;
  2-layer; 44 × 77 mm; OSH Park; June 3 2026). Source of the §2.0 as-built notes.
- ESP32-C3 deep-sleep GPIO wake confirmation: espressif/arduino-esp32 issues #6656
  (GPIO2/GPIO3 wake the C3 from deep sleep) and #8510 (GPIO3 as the wake interrupt,
  10 kΩ resistor) — supports the §2.1 / §14 GPIO3-wake claim.
