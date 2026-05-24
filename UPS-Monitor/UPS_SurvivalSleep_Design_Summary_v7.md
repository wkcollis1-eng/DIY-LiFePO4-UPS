# UPS Monitor — Survival Sleep Feature Design Summary
## Engineering Basis Document v7

**Document scope:** Power budget, timing, entry/exit logic, data-integrity, and
implementation rationale for the ESP32-C3 survival sleep feature on the DIY
LiFePO4 UPS Monitor PCB (UPS-Monitor-THT v3 / UPS-Monitor-V2).

**Date:** May 2026
**Revision:** v7 — Consolidated to the deployed firmware **V1.8**. v7 raises the
survival-sleep exit threshold from 12.8 V to 13.0 V (decoupling it from the BP-65
hardware reconnect) and reconciles the exit rationale with the *unmeasured* post-trip
resting OCV. The design is otherwise unchanged from the V1.7 consolidation, which
replaced the iterative v3–v5 history with a single coherent statement of the final
design and the reasoning behind each choice. Where an earlier approach was
abandoned, the rationale is given once (not the blow-by-blow).
**Status:** Implemented — firmware **V1.8** (`ups-monitor-v18.yaml`)
**Requirement:** ESP survives a multi-day grid outage without tripping the BMS
hard cutoff, and resumes automatically when AC returns.

---

## 0. Design Intent (why the design looks the way it does)

The operational requirement is narrow and was deliberately kept narrow:

> Save the battery from BMS cutoff during an extended outage, and recover
> automatically when AC returns.

Everything in V1.7 follows from prioritizing, in order:

1. **Never brick** — the device must always be able to return to normal operation
   on AC restoration, with no manual intervention.
2. **Always auto-recover** — recovery is a cold boot on AC return; it requires no
   network, no "report," and no preserved RAM state.
3. **Reduce post-LVD drain** — sleep through the deep-discharge tail rather than
   draining the pack awake.
4. **Protect the pack from BMS cutoff.**
5. **Accept imperfect telemetry / runtime accounting** — exact reserve Ah is not
   operationally important and is explicitly out of scope as a *requirement*.

The single most important consequence of this ordering: **every threshold in the
survival path must fail safe.** Entry fails toward sleep; wake fails toward exit.
No threshold may be able to strand the device awake (→ drains to cutoff) or asleep
(→ bricks). This principle, more than any individual number, is the design.

An earlier line of work treated the feature as a measurement-grade outage
recorder (precise post-trip voltage modelling, conversion-ready polling,
entry-threshold tuning, exact outage-Ah fidelity). That was over-engineered for
the requirement above and, in one case, actively dangerous (see §5.1). V1.7 strips
it back to the deterministic core.

---

## 1. Requirements

| ID | Requirement |
|---|---|
| R-1 | ESP survives an extended grid outage without BMS hard cutoff (≥10-day design target) |
| R-2 | ESP detects AC restoration and resumes HA telemetry automatically |
| R-3 | No hardware changes to the UPS-Monitor-THT v3 PCB |
| R-4 | No BMS trip during extended outage |
| R-5 | Implementation uses proven ESPHome mechanisms |
| R-6 | *(best-effort, not a hard requirement)* Per-outage Ah/Wh and min-voltage records remain meaningful across the sleep cycle |
| R-7 | No dependence on network or telemetry during the outage; the design fails toward recovery (cold boot) and, on entry, toward sleep |

R-6 was a hard requirement in earlier revisions. It is downgraded to best-effort:
the arm-time snapshot preserves the full-outage figure cheaply, but no design
decision may trade robustness for Ah fidelity. R-7 is the governing principle.

---

## 2. Hardware Constraints

### 2.1 PCB GPIO Availability

| GPIO | Assignment |
|---|---|
| GPIO6 | I2C SDA → INA260 |
| GPIO7 | I2C SCL → INA260 |
| GPIO10 | 1-Wire → DS18B20 |
| GPIO20 | INA260 ALERT (wired, unused in V1.7) |

**Constraint:** ESP32-C3 deep-sleep GPIO wakeup is restricted to the RTC-domain
pins (GPIO0–GPIO5). GPIO10 and GPIO20 are outside that domain and cannot wake the
chip from deep sleep. Event-driven wake via the INA260 ALERT line on GPIO20 is
therefore impossible on this PCB without hardware modification.

**Source:** ESP32-C3 Technical Reference Manual §6; Seeed XIAO ESP32-C3 wiki
(wake-up pins D0–D3 = GPIO2–GPIO5 only).

**Implication:** Timer-based deep sleep is the only viable wakeup mechanism on
this hardware. (A hardware ALERT-wake path on a future PCB is noted in §14.)

### 2.2 XIAO ESP32-C3 Module Sleep Current

The XIAO ESP32-C3 uses the chip's built-in USB-Serial controller — there is no
external USB bridge to add quiescent draw. The board is powered via the XIAO 3V3
pin from the D24V7F3 buck; the XC6210 LDO's input (the 5V/USB path) is unpowered
in production, so the LDO contributes little. Two cases are carried:

| Case | XIAO module sleep | Basis |
|---|---|---|
| Best (LDO bypassed) | ~10 µA | ESP32-C3 die only |
| Worst (LDO active) | ~45 µA | Full module, measured (Seeed forum) |

### 2.3 INA260 Power-Down Mode

Configuration Register (0x00) bits 2–0 = 000 places the INA260 in power-down.

| Parameter | Typical | Maximum | Unit |
|---|---|---|---|
| IQ active (mode 111) | 310 | 420 | µA |
| IQ power-down (mode 000) | 0.5 | **2** | µA |

The INA260 stays powered (via D24V7F3) and retains register values across the
ESP32-C3 deep sleep. On every boot the priority-600 block writes 0x00 = 0x6127 to
restore continuous mode, followed by a **10 ms delay** that guarantees at least
one full conversion (1.1 ms min) completes before any read. This delay alone
satisfies the freshness requirement — see §9.2 on why conversion-ready polling was
removed.

**Register-map reference (for any future hardware alert):** the INA260 Mask/Enable
register is **0x06** (alert-function select; CNVR bit 10; CVRF bit 3) and the Alert
Limit register is **0x07** (threshold value). Verified against TI SBOS656C §8.6 and
`Adafruit_INA260.h`. (Firmware prior to V1.6 had these two swapped, which is why
its conversion-ready mode never actually engaged.)

### 2.4 Sleep-Current Stack

| Component | Active (µA) | Power-down (µA) |
|---|---|---|
| ESP32-C3 deep sleep | — | 5–10 |
| XIAO LDO (XC6210) | — | 0 (bypassed) / 35 (active) |
| INA260 | 330 | **2** |
| D24V7F3 quiescent | 35 | 35 |
| DS18B20 standby | 1 | 1 |
| **Total** | | **43 (best) / 83 (worst)** |

This board-level figure — not the INA260's 2 µA alone — is the correct sleep
floor for the power budget (§6). Conflating the two is the most common error in
runtime estimation for this device (see §6.5).

---

## 3. Measured System Data

All figures from the INA260 coulomb-counted May 6 2026 outage test
(`UPS_Report_2026-05-06`).

### 3.1 Battery & Load

| Parameter | Value |
|---|---|
| Usable capacity at 1.18 A (to LVD) | 4.18 Ah / 53.3 Wh |
| Typical load current | 1.18 A |
| Typical load power | 14.9 W (DC) |
| Float voltage | ~13.23 V |
| BP-65 LVD trip voltage (observed) | 11.675 V |

**Load composition (drives the shutdown-margin framing):** the protected DC load
is XB7-dominated — XB7 ≈ 12.2 W of ~15 W total; HA Green ≈ 0.8 W. The XB7 is *not*
gated by HA shutdown — it draws until the BP-65 disconnects it. So the graceful HA
shutdown sheds no meaningful load and does not extend runtime; its only job is
letting HA Green sync its filesystem before the BP-65 cuts power.

### 3.2 Discharge Phases (at 1.18 A, from Voltage.csv)

| Phase | Band | Duration |
|---|---|---|
| Settling | 13.00–13.15 V | ~5 min |
| Plateau | 12.65–13.00 V | ~142 min |
| Knee | 12.40–12.65 V | ~49 min |
| Cliff | < 12.40 V | ~17 min |
| **Total to LVD** | | **~213 min** |

### 3.3 Shutdown Timeline & Margin

| Event | Voltage | Time (UTC) |
|---|---|---|
| `cliff_imminent` fires (graceful shutdown trigger) | 12.43 V | 13:39:41 |
| `hassio.host_shutdown` called | — | 13:40:11 |
| Last HA sample | — | 13:40:17 |
| 11.80 V threshold crossed | 11.80 V | 13:56:27 |
| **BP-65 LVD actual trip** | ~11.675 V | **~13:58:30 ±15 s** |

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
removed, ESP-only) is also unobserved: the May 6 event's telemetry blackout
(4 min 44 s — the WiFi AP rides on the XB7, which the BP-65 cuts at the trip, so the
streamed log cannot see past the load collapse) spans exactly that window. This
unmeasured resting OCV is what gates the exit-threshold choice in §5.2.

| Parameter | Estimate | Basis |
|---|---|---|
| Capacity remaining below LVD at 1.18 A | ~0.5 Ah | Rate-effect estimate; not measured |
| Effectively available for survival sleep | **~0.41–0.5 Ah** | Design basis (see note) |

V1.7 arms survival sleep *at the BP-65 trip* rather than after draining a further
175 mV awake (the old 11.50 V scheme spent ~0.088 Ah awake first). Arming at the
trip therefore makes nearly the full ~0.5 Ah available rather than ~0.41 Ah. The
budget (§6) reports **0.41 Ah / ~15 days as the conservative floor** and
**~0.5 Ah / ~18 days as the upside**; both rest on the same unmeasured capacity and
both clear the 10-day target with margin.

---

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
             Each wake: power up INA260, +10 ms, direct I2C read, decide.
             Implausible read → exit (fail-safe boot).  V ≥ 13.0 V (×2) → exit.
             > max cycles (~15 days) → exit.  Else → re-sleep.

AC restored: PSU drives V > 13.0 V within minutes (CC step jumps ~11.7→13.1 V in
             < 4 s). Next wake confirms ≥ 13.0 V twice → clears the flag,
             finalizes the outage record, normal boot. ESP is networkless ~4–5 min
             while the XB7 AP boots (benign; non-blocking; covered by wifi
             reboot_timeout 15 min). Telemetry resumes — no network needed during
             sleep.
```

---

## 5. Entry / Exit Logic

### 5.1 Entry — load-collapse at the BP-65 trip (fail toward sleep)

**Arm when `on_battery == true` AND `−0.30 A < I < +0.20 A`, sustained 30 s.**

The design "shadows" the BP-65: it sleeps when the BP-65 cuts the load. Once the
BP-65 opens, HA Green and the XB7 are unpowered — there is no AP, no API client,
nothing to stay awake for — so arming at the trip is correct, and it sets the NVS
flag within ~1 min of the trip (which is what makes the data-integrity issues of
§8 structurally impossible rather than merely guarded).

**Why there is no voltage gate.** An intermediate design gated entry on a post-trip
voltage estimate (`V < 12.5 V`). That threshold was *unmeasured*, and its failure
mode was the worst available: had the real post-trip rebound exceeded the gate,
survival sleep would *never arm* and the ESP would drain the pack to BMS cutoff —
the one outcome the feature exists to prevent. Since the gate's only benefit was
Ah-fidelity (out of scope), it was pure downside and was removed. The entry logic
now contains no threshold that can block sleep.

**Why the current is a window, not a floor:**
- **Lower bound −0.30 A** must clear the ESP's own WiFi-Tx transient, not just its
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

Note the distinction the earlier draft blurred: the *"11.7 → 13.09 V within 4 s of
CC onset"* figure is the **recovery (charging) transient** — it bounds the recovery
*ceiling* (why 13.0 V still catches recovery), and says nothing about the *resting*
OCV. The resting OCV is the unobserved quantity (§3.4). Because 13.0 V is set above
its estimate, the earlier dual-read + 200 mV hysteresis machinery remains
unnecessary and stays removed; the single confirm re-read is kept purely as
I2C-glitch insurance.

The BP-65's own reconnect (V > 12.8 V for 30 s) is independent and unchanged; with
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

Neither path "reports" anything — recovery is simply telemetry reappearing in HA
on the cold boot. Plausibility is checked on the *value* (the read buffer is
pre-zeroed, so a failed read reads as 0x0000), which is more robust than trusting
an I2C return code.

---

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
  the XB7's AP to be present before the pack has charged past the BP-65 reconnect,
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

A circulating table shows 32–64 days by using the INA260's 2 µA shutdown current
as the *sleep floor*. That is wrong: during sleep the battery powers the whole
board (C3 deep sleep + buck quiescent + INA260), which §2.4 puts at ~43–83 µA — 20–
40× higher. The 2 µA figure is the INA260 term *within* that stack, not the stack.
A single µA-meter reading on the battery lead during one sleep cycle resolves this
definitively (§13) and is the highest-value remaining measurement.

---

## 7. Wake Interval: 120 s

The interval became a free variable once runtime cleared the 10-day target with
margin — at that point reserve is over-provisioned and the interval should be tuned
for recovery responsiveness, not hoarded reserve. Three candidates:

| Interval | Recovery latency | 10-day coverage | Verdict |
|---|---|---|---|
| 300 s | ~5 min | months of reserve | Over-provisioned; wastes the free variable |
| 60 s | ~1 min | *contingent on the unmeasured floor* (≈6.8 days at 0.41 Ah / worst-case ~2.5 mA) | Risky — makes 10-day coverage depend on a number nobody has measured |
| **120 s** | **~2 min** | **clears 10 days under the pessimistic stack (~11+ days)** | **Selected — robust to the missing measurement** |

`survival_max_cycles = 10800` holds the ~15-day fail-safe backstop at 120 s
(10800 × 120 s = 15.0 days).

**Note on responsiveness:** end-to-end *system* recovery is modem-bound — the XB7
takes ~3–4 min to boot its AP after the BP-65 reconnects — so waking faster than
~2 min does not get Home Assistant back any sooner; it only resumes the ESP's local
telemetry marginally earlier. 60 s would therefore cost the most reserve for the
least *practical* recovery gain. 120 s captures essentially all the responsiveness
the modem floor allows while staying robust on runtime.

---

## 8. Data Integrity

The data-integrity concerns that drove several earlier guard-based fixes are, in
V1.7, **structurally** resolved by arming at the trip:

- Because `survival_mode_active` is set within ~1 min of the trip — before the
  30-min `api reboot_timeout` can fire its first reboot — there is no window in
  which a watchdog reboot can reset the per-outage counters. No `outage_in_progress`
  flag and no `reboot_timeout` change are needed for integrity; `reboot_timeout`
  stays at 30 min for normal-operation self-heal.

The mechanisms actually present in V1.7:

| Mechanism | Purpose |
|---|---|
| Snapshot at arm time | `last_outage_ah/wh/min_v/start_v/duration` written at the trip while counters are intact → captures the true full-outage figure. |
| `outage_was_survival` (NVS) | Set at arm; checked at the deterministic recovery instant (priority -150) so the snapshot is never overwritten by post-cold-boot values. (Recovery's `on_battery` may not toggle, because the pack is charging hard at boot, so finalization is done in priority -150, not in `on_release`.) |
| Priority -100 counter preservation | A mid-outage reboot keeps the `restore: true` counters from NVS and only re-anchors missing timing; discharge-direction guarded (I < −0.05 A). |
| Discharge-direction guard on `on_battery on_press` | A false outage cannot be counted while charging (I must be < −0.05 A). |
| 100 ms NVS flush on entry *and* re-sleep | Guarantees the arm snapshot and the `survival_cycle_count` increment commit before deep sleep cuts power. |

---

## 9. Implementation — Deployed Firmware V1.8

### 9.1 Substitutions (survival)

| Key | Value | Note |
|---|---|---|
| `survival_entry_current_lo` | `-0.30` | Arm when I > this (load gone; above Tx peak) |
| `survival_entry_current_hi` | `0.20` | AND I < this (rejects charging) |
| `survival_exit_v` | `13.0` | Exit at/above. V1.8 (was 12.8): above the estimated resting OCV, below the observed recovery CC (13.093 V); decoupled from the BP-65's 12.8 V reconnect |
| `survival_sleep_interval` | `120s` | Wake interval |
| `survival_max_cycles` | `10800` | ~15-day fail-safe backstop at 120 s |

### 9.2 Boot Blocks

- **Priority 600** — restore INA260 continuous mode (0x6127) + 10 ms freshness
  delay. The conversion-ready (CNVR) configuration and the wake-side CVRF poll were
  removed: the 10 ms delay already guarantees a fresh conversion and the wake
  plausibility check catches a bad read, so the poll was latent state for no
  benefit under the V1.7 requirement. (GPIO20 ALERT is consequently unused; the
  `INA260 Alert` sensor is retained but idle.)
- **Priority -100** — reboot-during-outage recovery: preserves counters from NVS,
  re-anchors timing only, guarded by `!survival_mode_active && I < −0.05 A`.
- **Priority -150** — survival wake decision: 10 ms settle, direct 0x02 read,
  value-plausibility fail-safe, max-cycle backstop, 13.0 V dual-read exit,
  deterministic survival-outage finalization. Re-sleep path powers down the INA260
  and includes a 100 ms NVS flush before `deep_sleep.enter`.

### 9.3 Survival Sleep Armed (binary sensor)

Template lambda: `on_battery.state && I > −0.30 && I < +0.20`; `delayed_on: 30s`.
On press (single merged lambda): reset `survival_cycle_count`, write the final
snapshot, set `survival_mode_active` + `outage_was_survival`; then 100 ms flush,
INA260 power-down, `deep_sleep.enter` (120 s).

### 9.4 Globals (survival)

`survival_mode_active` (NVS), `survival_should_sleep` (transient),
`survival_cycle_count` (NVS), `outage_was_survival` (NVS).

---

## 10. Risk Register

| Risk | Severity | Status |
|---|---|---|
| ESP stays awake after BP-65 trip → drains to BMS cutoff | High | Mitigated — entry fails toward sleep; no blocking threshold |
| Indefinite re-sleep brick on stuck-low sensor | High | Mitigated — fail-toward-exit + max-cycle backstop |
| False-arm into recovery | Medium | Mitigated — +0.20 A upper bound rejects charging |
| Tx-spike resets the arm timer | Medium | Mitigated — −0.30 A lower bound clears the ~153 mA peak |
| Lost NVS write before sleep | Low | Mitigated — 100 ms flush on entry and re-sleep |
| Below-LVD capacity unmeasured | Low (for the 10-day target) | Accepted — only affects *how long* sleep lasts; 120 s clears 10 days at the pessimistic end |
| Exit threshold below post-trip resting OCV → spurious wake-exit / re-arm loop (faster drain) | Medium | Reduced — exit raised to 13.0 V (V1.8), above the estimated ~12.8–13.0 V resting band; loop is self-limiting and re-arms rather than bricking. Residual: resting OCV unmeasured — §5.2, §13 |
| Survival path never run in a real outage | — | Open — see §13 |

The only open survival-path failure is *runtime degradation* (the re-arm loop if
resting OCV exceeds the exit threshold); no open threshold can strand the device
awake indefinitely or asleep (it self-recovers toward exit).

---

## 11. Assumptions

- **A-1:** Below-LVD capacity ≈ 0.41–0.5 Ah. Unmeasured; binding input for runtime
  *duration* (not for whether the feature engages).
- **A-2:** ESP stack senses its own ~40 mA through the INA260 shunt (confirmed for
  this build). Post-trip current reads ≈ −0.04 A, inside the entry window.
- **A-3:** Board sleep floor 43–83 µA (§2.4). Unmeasured; resolvable with one meter
  reading (§13). 120 s was chosen so the 10-day target holds at the 83 µA end.

- **A-4:** Post-trip resting OCV stays below the 13.0 V exit threshold. Unmeasured
  (§3.4); the threshold is set above the ~12.8–13.0 V estimate with margin and below
  the observed recovery CC (13.093 V). Binding for *exit safety*: if violated, the
  device re-arms (self-recovers) but runtime degrades — it does not strand or brick.

The *entry* logic uses no voltage threshold, so there is no entry-side post-trip
voltage assumption. The only post-trip voltage assumption is A-4 on the *exit* side.

---

## 12. Uncertainties

| Uncertainty | Effect | Resolver |
|---|---|---|
| Board sleep current (43–83 µA) | Sets actual runtime; the 2 µA-vs-board-floor confusion produces wildly different estimates | One µA-meter reading during a sleep cycle (§13) |
| Below-LVD capacity (0.41–0.5 Ah) | Sets runtime *duration* | Deep-discharge bench test (now optional) |

Both affect *how long* survival sleep lasts, not *whether* it engages or recovers.

---

## 13. Validation Plan

The entry voltage gate's removal collapses validation to behavioral checks plus one
recommended measurement:

| Item | Method | Priority |
|---|---|---|
| Board sleep current | µA-meter on the battery lead during one sleep cycle. Resolves all competing runtime estimates; cheap (steady-state, no deep discharge). | **Recommended** |
| Post-trip resting OCV (exit safety) | DMM on the battery through one controlled discharge-to-trip; log rest V for ~5–10 min after the load collapses. The only thing that confirms resting OCV < 13.0 V (the A-4 / §5.2 hedge). Cheap; does NOT require discharge to BMS cutoff. Must be **out-of-band** (DMM, or an AP not behind the BP-65) — streamed logs die with the XB7 at the trip. | **Recommended** |
| Arm fires at trip | Confirm `survival_sleep_armed` asserts within ~30 s of the load collapse | High |
| Does NOT arm on recovery | Confirm the +0.20 A bound prevents arming when charging begins | High |
| 13.0 V exit on recovery | Restore AC; confirm exit on first wake seeing ≥ 13.0 V ×2 | High |
| Fail-safe exit | Disconnect INA260 mid-sleep; confirm boot-normal, not re-sleep | High |
| Snapshot integrity | Confirm `last_outage_*` hold sensible values after a survival cycle | Medium |
| Deep-discharge capacity | Discharge to BMS cutoff; measure below-LVD Ah | Optional (refines runtime; does not gate function) |

**Standing caveat:** survival sleep has not yet run in a real outage — the May 6
event (217 min) never reached arming. The pre-LVD chain and the recovery side
(now validated against that event's 13.093 V CC step, comfortably above the 13.0 V
exit) are well-validated; the deep-sleep path is validated by design and bench
checks, not yet by a field event. Note the post-trip resting OCV remains unobserved
on that event (the 4 min 44 s telemetry blackout, §3.4) — which is why the
out-of-band rest reading above is the highest-value exit-safety measurement.

---

## 14. Hardware Path for a Complete Solution

A future PCB revision routing the INA260 ALERT line to an RTC-domain pin
(GPIO2–GPIO5) would enable event-driven wake (sub-second recovery latency) and
remove the timer-poll entirely. That would re-introduce a CNVR/ALERT configuration
using the register map preserved in §2.3. The V1.7 fail-safe, snapshot, and
entry/exit logic carry forward unchanged to such a design.

---

## 15. References

- TI INA260 datasheet SBOS656C (§7.5 supply current; §8.6 register map).
- `Adafruit_INA260.h` — register definitions (0x06 Mask/Enable, 0x07 Alert Limit).
- ESP32-C3 Technical Reference Manual §6 (power management; RTC-domain wake pins).
- Seeed XIAO ESP32-C3 wiki and forum (#276444, #284207) — module sleep current.
- Victron BP-65 datasheet — LVD timer chain (12 s alarm + 90 s disconnect; 30 s
  reconnect holdoff at >12.8 V).
- `UPS_Report_2026-05-06` — coulomb-counted outage test; recovery transient; the
  post-trip log gap establishing post-trip V/I as unmeasured.
- ESPHome `i2c` / `deep_sleep` / `globals` component documentation.
