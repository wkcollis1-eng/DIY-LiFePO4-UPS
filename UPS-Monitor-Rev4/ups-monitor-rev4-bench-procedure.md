# UPS Monitor Rev 4: bench commissioning procedure

**Firmware:** V4.1, commit 8cafe2e, ESPHome 2026.10.2.

**Requirements:** design doc revision 9, section 8. The findings (F01 to F19) are in
`ups-monitor-rev4-v4.1-review.md`.

**Evidence tags:**
- [S] read from a source file or datasheet;
- [D] derived;
- [I] inferred, not yet measured.

| Board / serial | | XIAO MAC | |
|---|---|---|---|
| Operator | | Date | |
| Build flashed (B / P) | | Commit | |

---

## How to use this procedure

- Run T1 to T10 on the bench rig (§1) and T11 on the real system. Each test starts on a new
  page.
- ☐ means do the step and tick it. Write measured values in the blanks. Circle PASS or FAIL.
- **Where each expected line appears:**
  - **UART** is the bench build's serial log (Build B, §2). It is the only place where the
    boot-time and survival-wake lines can be seen.
  - **NET** is `esphome logs ups-monitor-rev4.yaml` or the HA device log, and it is live only.
    The API does not replay lines logged before it connected [S: api_server.cpp:766–774]. So
    no line from `on_boot`, and none from a survival wake, ever reaches it.
  - **HA** is an entity's state, in Home Assistant or the ESPHome dashboard.
  - **SCOPE** is a trace.
- **Log line format.** Each line is `[L][tag:NNN]: message` [S: logger/log_buffer.h:63–103].
  - `L` is I, W, E or D.
  - `NNN` is the YAML line of the call, and changes with every edit. Match on the tag and the
    text, not the number.
  - The `esphome logs` CLI adds a time stamp in front.
  - `…` stands for a value; its expected range is given beside it.
- **What is not logged.** The logger runs at INFO, and ESP-IDF's own logs at ERROR
  (`CONFIG_LOG_DEFAULT_LEVEL=1`). So entity state changes are not logged: read them in HA.

---

## 1. Bench rig

| Item | Use | Notes |
|---|---|---|
| Supply A, "battery" | 10–14 V into the INA260's battery terminal (VIN−), current limit 3 A | Fit a series Schottky (≥ 5 A) so the PSU can never back-feed it. Set it by HA "Battery Voltage", not by the supply's display: the diode drops about 0.3–0.5 V [I]. |
| Supply B, "PSU_SENSE" | 0–14 V into TB2 pad 4 only, not onto the bus | 13.60 V = mains present; 0 V = mains absent. |
| HDR-60-12 and Pololu #5382 | Real mains on the bus, with its PSU_SENSE lead | Used for T2, T6 and T7, in place of supply B. |
| Modem load | The XB7, or 12 Ω ≥ 25 W on the MODEM terminal | 12 V ÷ 12 Ω = 1.0 A, 12 W [D]. |
| Survival blocker | 22 Ω ≥ 10 W across BUS and GND | 11.75 V ÷ 22 Ω = 0.53 A, 6.3 W [D]. It holds the battery current below −0.30 A, so survival sleep cannot start while you watch the latch. |
| Bench Wi-Fi AP | Same SSID and password as production | The XB7's AP dies at every shed; the bench AP does not, so NET and HA keep working. |
| USB–UART adapter | 3.3 V logic, RX and GND only, 115200 8N1 | Do **not** connect its VCC. It goes on XIAO D6 = GPIO21 = Rev 4 pad 7, reached at the socket tail on the back [D: design doc 4.7]. No net is routed there; meter it first. |
| Scope, 2 channels | CH1 GPIO5 (MODEM_OFF), CH2 MODEM_EN | Ground at TB2 pad 3. |
| DMM | Divider calibration, U4 output | — |

| Signal | Probe point |
|---|---|
| GPIO5 / MODEM_OFF | XIAO pad 4 (D3) |
| MODEM_EN | U4 pad 1 joint, on the back (design doc 4.4) |
| U4 output | U4 pad 5 joint, on the back (open item 13) |
| PSU_SENSE | TB2 pad 4 |
| GND | TB2 pad 3 |
| UART TX | XIAO pad 7 (D6, GPIO21), socket tail on the back |

---

## 2. Builds and flashing

- **Build P** is `ups-monitor-rev4.yaml` V4.1 as committed. Its serial log is off
  (`baud_rate: 0`).
- **Build B** is Build P with the two bench-only edits in Appendix A: the logger on UART0 at
  115200, and a "BENCH INA260 Power-Down" button. It compiled clean on ESPHome 2026.10.2
  (0 errors) on 2026-11-15. **Never ship it.**
- **First flash.** Nothing ESPHome is on the XIAO yet, so the first flash must be over USB.
  Take the XIAO out of its socket, or leave BUS unpowered: the board feeds the XIAO's 3V3
  from U3, and USB would set the XIAO's own regulator against it [I]. Use OTA after that.
- **Build B runs slower.** Each UART log line adds about 9 ms
  [D: 100 characters × 10 bits ÷ 115200 baud], so Build B's awake windows are longer than
  Build P's.
- **The bench leaves counts behind.** It adds to Total Outages, Modem Shed Count, Shed Hold
  Lost Count, the lifetime Ah/Wh and the Ri entities, and some of these have no reset
  button. The close-out (§5) erases them.

---

## T1. First power and divider calibration

**Covers:** open item 13, `psu_divider_ratio`, a normal boot.

**Build:** B.

**Rig:**
- Supply B at 13.60 V on, **before** power-up, so this is a boot on mains.
- Supply A set for Battery Voltage ≈ 13.00 V.
- Modem load on.

☐ 1. Connect the UART adapter and open a terminal at 115200.

☐ 2. Power supply A.

| ☐ | When | Where | Expected line |
|---|---|---|---|
| ☐ | power-up | UART | ROM: `rst:0x1` (power-on) [S: rom/rtc.h; the ROM's text format is I] |
| ☐ | < 1 s | UART | `[I][ups.survival:…]: Boot wake cause = 0 (cold/reset)` |
| ☐ | < 1 s | UART | `[I][deep_sleep:…]: Scheduling in 60000 ms` |
| ☐ | < 1 s | UART | `[I][ups.watchdog:…]: INA usable (13.0… V) — normal/survival logic in control; run_duration watchdog disarmed` |
| ☐ | < 1 s | UART | `[I][main:…]: UPS Monitor Rev 4 V4.1 boot complete -- INA260 @ 0x40 …` |
| ☐ | Wi-Fi up | UART | `[I][ups.watchdog:…]: Normal operation confirmed by WiFi association — run_duration watchdog disarmed` |

**Must not appear:** `INA UNUSABLE`, `SURVIVAL`, `MODEM SHED`, `Booted during outage`.

☐ 3. **U4 output.** DMM from U4 pad 5 to GND: ________ V. Pass: 11.52–12.48 V
[S: design doc 1.4].

☐ 4. **Entities.** Check in HA:
- after 10 s, Mains Present **ON**;
- INA260 Healthy ON; INA260 Data Fresh ON; DS18B20 Healthy ON;
- MODEM_OFF Readback Fault OFF; Modem Shed OFF; Modem Shed Ineffective OFF.

☐ 5. **Read the divider.**
- DMM at TB2 pad 4 to pad 3: V_DMM = ________ V.
- HA "PSU Sense Voltage", three readings 5 s apart: ______ / ______ / ______. Mean
  V_HA = ________ V.

☐ 6. **Set the ratio.**
- New `psu_divider_ratio` = 6.556 × V_DMM ÷ V_HA = ________.
- Edit it, OTA, then re-read: PSU Sense Voltage = ________ V.

☐ 7. *Optional linearity check:* supply B at 12.00 V. DMM ________ V, HA ________ V.

**Pass:**
- every expected line above, and no forbidden line;
- U4's output in band;
- after step 6, |V_HA − V_DMM| ≤ 0.05 V [I: design doc 4.5 expects tens of mV once
  calibrated].

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T2. HDR-60-12 output decay (open item 6)

**Covers:** open item 6 and F05. This test sets `mains_debounce_polls` and
`plausibility_alert_delay`.

**Build:** B.

**Rig:**
- HDR-60-12 and #5382 on the bus, with the HDR's PSU_SENSE lead on TB2 pad 4. Supply B
  disconnected.
- Supply A set for Battery Voltage ≈ 13.30 V. That is below the HDR's 13.571–13.587 V
  [D: design doc 1.5], so the HDR carries the load on mains.
- Modem load on.
- **Scope:** CH1 on PSU_SENSE, CH2 on the bus. Start at 1 s/div, single trigger on CH1
  falling through 13.0 V. Call that instant t0.

☐ 1. HDR on for ≥ 2 min. HA: Mains Present ON, Battery Current ≈ 0 A.

☐ 2. Switch the HDR's AC off.

| ☐ | When | Where | Expected line or state |
|---|---|---|---|
| ☐ | about 0.5 s after the bus drops | NET | `[I][ups.onset:…]: ONSET Ri \| Vf=… Vl=… I=… -> R=… mOhm \| T=…F \| q=…`. Ignore the value on this rig: R is the Schottky and the leads. |
| ☐ | first poll below 7.0 V | NET | `[I][ups.mains:…]: PSU sense … V < 7.0 V, … s after the INA260 load step (HDR decay, open item 6)` |
| ☐ | 10 polls later | HA | Mains Present OFF; On Battery ON 10 s after that |
| ☐ | throughout | HA | PSU Running Bus Not Fed stays **OFF** |

☐ 3. From the trace, and HA "PSU Decay To Threshold"; then restore AC and wait 2 min.
Repeat for three runs:

| Run | t(7.0 V) − t0 | t(3.3 V) − t0 | t(3.0 V) − t0 | PSU Decay To Threshold |
|---|---|---|---|---|
| 1 | ______ s | ______ s | ______ s | ______ s |
| 2 | ______ s | ______ s | ______ s | ______ s |
| 3 | ______ s | ______ s | ______ s | ______ s |

On each AC restore, expect:
- Mains Present ON after 10 polls;
- On Battery OFF 60 s later;
- NET `[I][ups:…]: OUTAGE END #… | … min | … Ah | … Wh | Start V: … V | Min V: … V | Peak chrg: … A`.

Supply A cannot take charge, so no `AC return detected` and no `RECHARGE Ri` line on this rig.

☐ 4. **Decide** (these replace placeholders):
- `mains_debounce_polls` = ________. It must exceed the decay (design doc 8).
- `plausibility_alert_delay` = ________. It must exceed t(7.0 V) + `mains_debounce_polls` s,
  plus margin [D: review §3.5].

**Pass:**
- the three runs are recorded;
- PSU Decay To Threshold agrees with t(7.0 V) within about 1.2 s;
- PSU Running Bus Not Fed never turns ON.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T3. GPIO5 at boot (item 28: the priority-900 lambda runs first)

**Build:** B.

**Rig:**
- Supply A set for Battery Voltage ≈ 12.50 V.
- Supply B at 0 V. With mains absent, a HIGH would really shed.
- Modem load on.
- **Scope:** CH1 GPIO5, CH2 MODEM_EN, 5 ms/div. Normal trigger on CH2 falling through 2 V;
  repeat with a trigger on CH1 rising through 1 V.

For each event, arm the scope, do it, then record the trigger and the ROM line:

| Event | CH2 trigger? | CH1 trigger? | UART ROM line |
|---|---|---|---|
| ☐ a. power-cycle supply A (off 5 s) | ______ | ______ | expect `rst:0x1` |
| ☐ b. HA "Restart" | ______ | ______ | expect `rst:0x3` or `rst:0xc` (software) [I] |
| ☐ c. OTA of Build B | ______ | ______ | as b |
| ☐ d. the XIAO's RESET button | ______ | ______ | expect `rst:0x1` [I] |

After each boot, expect:

| ☐ | When | Where | Expected line |
|---|---|---|---|
| ☐ | < 1 s | UART | `[I][ups.survival:…]: Boot wake cause = 0 (cold/reset)` |
| ☐ | ≈ 9.5 s | UART/NET | `[W][ups:…]: Booted during outage -- counters PRESERVED from NVS (… Ah), tracking re-anchored`. Correct here: mains absent and discharging at boot (F01). |
| ☐ | ≈ 19.5 s | UART/NET | `[W][ups:…]: on_press suppressed — already in an outage (start=…); counters preserved` |

**Pass:** no trigger on either channel for any of a–d. MODEM_EN never below 2 V, and GPIO5
never above 1 V.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T4. Shed, latch and release (items 15 and 16; F02, F04; the Q2 override)

**Build:** B.

**Rig:**
- Supply A set for Battery Voltage ≈ 12.50 V.
- Supply B at 13.60 V.
- Modem load on, and the **survival blocker on**.
- **Scope:** CH1 GPIO5, CH2 MODEM_EN, 2 s/div roll.

☐ 1. Boot, or Restart, with supply B on. HA: Mains Present ON after 10 s.

☐ 2. **Start the outage.** Supply B to 0 V. Total Outages becomes ________ (+1).

| ☐ | When | Where | Expected line or state |
|---|---|---|---|
| ☐ | ≤ 1 s | NET | `[I][ups.mains:…]: PSU sense 0.00 V < 7.0 V, no INA260 load step in the last 600 s (glitch, decay < step debounce, or decay > 600 s)`. Supply A was already carrying the load, so there is no step to time. |
| ☐ | 10 polls | HA | Mains Present OFF; On Battery ON 10 s later |

☐ 3. **Above the threshold.** Supply A to Battery Voltage ≈ 11.95 V and wait 30 s. Expect
**no** `MODEM SHED`.

☐ 4. **A short dip.** Supply A to ≈ 11.70 V for 5 s, then back to 11.95 V. Expect **no**
`MODEM SHED`: fewer than 10 consecutive valid reads.

☐ 5. **The shed.** Supply A to ≈ 11.70 V and hold it there.

| ☐ | When | Where | Expected line or state |
|---|---|---|---|
| ☐ | about 10 s | NET | `[W][ups.shed:…]: MODEM SHED #… \| V=11.7… V <= 11.80 V on 10 valid reads, PSU sense 0.00 V \| latched until mains returns` |
| ☐ | same | SCOPE | CH1 HIGH. CH2 ≤ 0.2 V (the Q1 saturation check, design doc 4.4): ________ V. The modem load goes off. |
| ☐ | same | HA | Modem Shed ON; Modem Shed Count +1; MODEM_OFF Readback Fault OFF; Shed Path Stale Reads 0 |

☐ 6. **The ineffective-shed alarm.** Wait 60 s. HA Modem Shed Ineffective turns **ON**.
- That is expected here: the 0.53 A blocker looks like a modem that did not turn off. This
  is F04's positive test.
- There is no `SURVIVAL SLEEP ENTRY`.

☐ 7. **The latch holds.** Supply A to 12.60 V. Expect CH1 to stay HIGH, and no
`MODEM RESTORED`.

☐ 8. **Release on mains.** Supply B to 13.60 V.
- **Q2:** CH2 rises at once, before the firmware acts. Delay ________ ms.
- **Firmware:** CH1 falls about 10 s later. Delay ________ s.

| ☐ | When | Where | Expected line or state |
|---|---|---|---|
| ☐ | 10 polls | NET | `[W][ups.shed:…]: MODEM RESTORED \| mains present, PSU sense 13.6… V (debounced)` |
| ☐ | same | HA | Modem Shed OFF; Modem Shed Ineffective OFF; Mains Present ON |
| ☐ | +60 s | NET | `[I][ups:…]: OUTAGE END #… \| … min \| … Ah \| … Wh \| Start V: … V \| Min V: … V \| Peak chrg: … A` |

☐ 9. **Optional: stale-read negative test (F02, Build B only).**
- ☐ a. Supply B at 13.60 V (mains present). Supply A to Battery Voltage ≈ 11.70 V.
- ☐ b. Press HA "BENCH INA260 Power-Down". Expect NET
  `[W][bench:…]: INA260 config written to 0x6120 (power-down): ok`.
- ☐ c. Supply A to 12.60 V. Battery Voltage must stay frozen at ≈ 11.70 V.
- ☐ d. Supply B to 0 V. About 10 s later expect NET
  `[W][ups.shed:…]: Shed read STALE: INA260 CVRF clear, no conversion since the last poll | V=11.7… | count 1 | read rejected`.
  - It repeats at counts 61, 121, ….
  - Shed Path Stale Reads climbs by 1 per second.
  - There is **no** `MODEM SHED` within 60 s. V4.0 would have shed on the frozen 11.70 V.
  - INA260 Data Fresh stays ON: the platform publishes the frozen registers, so the shed path
    is the only detector.
- ☐ e. HA "Restart". The platform resets the chip, Battery Voltage reads ≈ 12.6 V, and no
  shed follows.

**Pass:**
- steps 3 and 4 do not shed;
- step 5 sheds on the 10th valid read, with CH2 ≤ 0.2 V;
- step 6 alarms; step 7 holds;
- in step 8, Q2 overrides at once and the firmware releases after 10 polls;
- Readback Fault never ON, and Stale Reads 0 through steps 1–8;
- step 9 (if run) does not shed.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T5. GPIO5 hold through deep sleep and the ROM boot (open item 7)

**Build:** B.

**Rig:**
- Supply A set for Battery Voltage ≈ 11.70 V.
- Supply B at 0 V.
- Modem load on; **blocker off**.
- **Scope:** CH1 GPIO5 and CH2 MODEM_EN in roll mode at ≥ 50 s/div. A second scope, or a
  second run, should trigger on CH2 rising: any modem turn-on is a failure.

☐ 1. Boot, or continue from T4 with the blocker removed. Wait for `MODEM SHED`, about 19 s
after mains absent.

☐ 2. **Survival entry.** The modem load drops, and the battery current falls to the board's
own draw. About 30–35 s later:

| ☐ | Where | Expected line |
|---|---|---|
| ☐ | UART/NET | `[W][ups.survival:…]: SURVIVAL SLEEP ENTRY (modem shed) \| V=1…V I=-0.0…A \| snapshot: … Ah / … Wh / min … V \| timer-wake` |
| ☐ | UART/NET | `[I][ups.survival:…]: INA260 powered down (~2 µA) for survival sleep` |
| ☐ | UART | `[I][deep_sleep:…]: Beginning sleep` |
| ☐ | UART | `[I][deep_sleep:…]: Sleeping for 120000000us` |

☐ 3. **Let 5 wakes pass** (about 10 min). Each wake should print, on the UART only and in this
order:

| Order | Expected line |
|---|---|
| 1 | ROM: `rst:0x5` (deep-sleep reset) [S: rom/rtc.h; text format I] |
| 2 | `[I][ups.survival:…]: Boot wake cause = 4 (timer-wake)` |
| 3 | `[I][ups.survival:…]: Wake #N \| V1=1…V \| PSU=0.00V (mains absent)`. N runs 0, 1, 2, … |
| 4 | `[I][ups.survival:…]: V=1…V < 13.0V, mains absent — scheduling re-sleep (cycle N+1)` |
| 5 | `[I][ups.survival:…]: Re-entering survival sleep \| INA260 powered down (~2 µA) \| timer-wake 120s` |
| 6 | `[I][main:…]: UPS Monitor Rev 4 V4.1 boot complete -- …` |
| 7 | `[I][deep_sleep:…]: Beginning sleep`, then `[I][deep_sleep:…]: Sleeping for 120000000us` |

Tick as each wake completes: Wake 1 ☐  2 ☐  3 ☐  4 ☐  5 ☐

**Must not appear:**
`[W][ups.shed:…]: MODEM_OFF read LOW on a survival wake — latch lost or pad unreadable (count …)`

☐ 4. **Scope.** CH1 HIGH and CH2 ≤ 0.2 V the whole time, including through each ROM boot.
The CH2-rising trigger never fires.

☐ 5. **Awake window per wake,** from UART time stamps or SDA activity: ________ ms. Build B
inflates this.

☐ 6. **Exit.** Supply B to 13.60 V. CH2 rises at once (Q2). At the next wake, on the UART:

| ☐ | Expected line |
|---|---|
| ☐ | `[I][ups.survival:…]: Boot wake cause = 4 (timer-wake)` |
| ☐ | `[I][ups.survival:…]: Wake #N \| V1=1…V \| PSU=13.6…V (mains present)` |
| ☐ | `[I][ups:…]: OUTAGE END #… (survival) \| … min total (incl. N slept cycles) \| … Ah \| … Wh \| Start V: … V \| Min V: … V` |
| ☐ | `[I][ups.survival:…]: SURVIVAL EXIT (mains on PSU sense) \| V1=…V V2=…V \| PSU 13.6…V / 13.6…V \| I=…A \| recovery — normal boot, modem released` |
| ☐ | `[I][ups.recharge:…]: Recharge-step Ri not captured for this outage: …` |
| ☐ | `[I][ups.watchdog:…]: INA usable (… V) — normal/survival logic in control; run_duration watchdog disarmed` |
| ☐ | `[I][main:…]: UPS Monitor Rev 4 V4.1 boot complete -- …` |

CH1 falls LOW at that wake.

☐ 7. **Entities, in HA after it reconnects:**
- Last Survival Cycles ________.
- Survival Exit Reason = Recovery.
- Shed Hold Lost Count unchanged: before ______, after ______.
- Survival First / Min / Last Wake Voltage: ______ / ______ / ______ V.
- Survival Exit Test Current ______ A. It reads about the board's draw: supply A cannot take
  charge.

**Reading the result:**

| CH1 on the scope | Shed Hold Lost Count | Meaning | Action |
|---|---|---|---|
| HIGH throughout | unchanged | The hold works, and the pad reads back | **Pass** |
| HIGH throughout | +1 per wake | The held pad does not read back | Fix the -150 readback (item 7, second half) |
| Falls during a sleep or a ROM boot | +1 per wake | The hold is lost | Item 7 fails; decide F14 |
| LOW | unchanged | Not possible by the circuit | Check the probes |

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T6. Survival exit on mains, and the section 8 commissioning test (item 17)

**Build:** B.

**Rig:**
- HDR and #5382 on the bus, with the HDR's PSU_SENSE lead. Supply B disconnected.
- Supply A set for Battery Voltage ≈ 11.70 V once the HDR is off.
- Modem load on; blocker off.
- Scope as in T5.

The five steps are design doc section 8's commissioning test.

☐ 1. **"Force a shed on battery."** Switch the HDR's AC off.
- Expect `PSU sense … V < 7.0 V, … s after the INA260 load step …`.
- After the decay, 10 polls and 10 reads: `MODEM SHED #…`.
- The onset line logs a bench R near 1–2 Ω, which is meaningless here. Close-out (§5) erases
  it.

☐ 2. **"Let survival sleep start."** Expect `SURVIVAL SLEEP ENTRY (modem shed) …`, then
≥ 1 wake with the re-sleep lines of T5 step 3.

☐ 3. **"Restore mains."** Switch the HDR's AC on.
- CH2 rises within ms (Q2). CH1 stays HIGH (held) until the next wake.
- At that wake, the T5 exit lines, with `PSU=13.5…V (mains present)`.
- CH1 then falls.

☐ 4. **"Wait two wake periods."** Supply A to 12.80 V: it stands in for the recharged pack,
since a bench supply cannot take charge. Wait 240 s from step 3.

☐ 5. **"Cut mains again."** Switch the HDR's AC off, and watch for 2 min.

| ☐ | Where | Expected line or state |
|---|---|---|
| ☐ | SCOPE | CH1 stays LOW; CH2 stays high: **the modem stays on** |
| ☐ | NET | `[I][ups.mains:…]: PSU sense … V < 7.0 V, … s after the INA260 load step (HDR decay, open item 6)` |
| ☐ | HA | Mains Present OFF; On Battery ON; **no** `MODEM SHED` (the bus at 12.8 V is above 11.80 V) |
| ☐ | HA | Survival Exit Reason = Recovery; Shed Hold Lost Count unchanged |

**Pass (section 8):** the modem stays on at step 5, which proves the hold was released.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T7. PSU_SENSE wire off (items 18 and 25; exit reason 5, F06; F18)

**Build:** B.

**Part A, on mains.**

**Rig:** HDR and #5382 on the bus; supply A at Battery Voltage ≈ 12.80 V; modem load on.

☐ A1. HDR on for 2 min. Mains Present ON.

☐ A2. Pull the PSU_SENSE lead at TB2 pad 4, leaving the HDR on.

| ☐ | When | Where | Expected line or state |
|---|---|---|---|
| ☐ | ≤ 1 s | NET | `[I][ups.mains:…]: PSU sense 0.00 V < 7.0 V, no INA260 load step in the last 600 s (glitch, decay < step debounce, or decay > 600 s)` |
| ☐ | 10 s | HA | Mains Present OFF |
| ☐ | about 20 s | HA | On Battery ON. This is known and misleading (F18). |
| ☐ | 60 s | HA | PSU Sense Lost **ON** (bus above 13.15 V, \|I\| < 0.20 A) |
| ☐ | throughout | HA/SCOPE | **No** `MODEM SHED`; no `SURVIVAL SLEEP ENTRY`; CH2 high, modem on |

☐ A3. Refit the lead.
- Mains Present ON after 10 s; PSU Sense Lost OFF.
- On Battery OFF 60 s later, with an `OUTAGE END #… | …` line for an outage that was never
  counted (F18, known).

**Part B, exit reason 5.**

**Rig:** as T6.

☐ B1. HDR AC off. Expect `MODEM SHED`, then `SURVIVAL SLEEP ENTRY`, as in T6 steps 1–2.

☐ B2. Pull the PSU_SENSE lead, then switch the HDR's AC on.
- The bus goes to 13.58 V.
- CH2 stays **LOW**: Q2 has no input, and GPIO5 is held HIGH. That is correct: the firmware
  has to find out for itself.

☐ B3. At the next wake (≤ 120 s), on the UART:

| ☐ | Expected line |
|---|---|
| ☐ | `[I][ups.survival:…]: Wake #N \| V1=13.5…V \| PSU=0.00V (mains absent)` |
| ☐ | `[I][ups.survival:…]: SURVIVAL EXIT (bus voltage only, PSU sense absent) \| V1=13.5…V V2=13.5…V \| PSU 0.00V / 0.00V \| I=…A \| recovery — normal boot, modem released` |

- CH1 falls and CH2 rises: the modem is on.
- HA: Survival Exit Reason = "Recovery, PSU sense absent". Survival Exit Test Current
  ________ A.

☐ B4. 60 s later, PSU Sense Lost turns ON. There is no new shed: the bus is at float.

☐ B5. Refit the lead.

> **Note.** On this rig supply A cannot take charge, so the exit-test current reads near 0 A,
> not the amps of a real recharge. The value that decides `survival_exit5_require_charge`
> must come from a real pack (T11 step 6).

**Pass:**
- Part A: no shed, and the alert at 60 s.
- Part B: exit reason 5 at the first wake after AC returns, with the modem on.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T8. Q2's band, and an ineffective shed (F04; design doc 8.1 deviation 4)

**Build:** B.

**Rig:**
- Supply A set for Battery Voltage ≈ 11.70 V.
- Supply B at 13.60 V to start.
- Modem load on; blocker off.
- Scope: CH1 GPIO5, CH2 MODEM_EN.

☐ 1. **Into the band.** Supply B from 13.60 V to **5.00 V**. That is above Q2's threshold but
below `mains_present_v`, so the firmware reads "absent" while Q2 still holds the modem on.

| ☐ | When | Where | Expected line or state |
|---|---|---|---|
| ☐ | ≤ 1 s | NET | `[I][ups.mains:…]: PSU sense 5.0… V < 7.0 V, no INA260 load step in the last 600 s (glitch, decay < step debounce, or decay > 600 s)` |
| ☐ | about 20 s | NET | `[W][ups.shed:…]: MODEM SHED #… \| V=11.7… V <= 11.80 V on 10 valid reads, PSU sense 5.0… V \| latched until mains returns` |
| ☐ | same | SCOPE | CH1 HIGH, but CH2 **stays high**: the modem stays on (Q2's override) |
| ☐ | +60 s | HA | Modem Shed Ineffective **ON**; no `SURVIVAL SLEEP ENTRY`; MODEM_OFF Readback Fault OFF (the pad reads HIGH, as commanded) |

☐ 2. **Q2's release threshold.** Lower supply B in 0.1 V steps, holding each for 5 s, until
CH2 falls (the modem turns off).
- V_Q2 = ________ V. Design: 3.05–3.33 V [D: design doc 4.4].
- Deviation 4's band is V_Q2 to 7.0 V.

☐ 3. **Back out.** The modem is now off, so `SURVIVAL SLEEP ENTRY` follows about 30 s later.
Supply B to 13.60 V. At the next wake, exit reason 1, as in T5 step 6.

**Pass:**
- the ineffective shed raises Modem Shed Ineffective within 60–65 s;
- V_Q2 is recorded, and is below `mains_present_v`.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T9. A mid-outage reboot keeps the outage (F01)

**Build:** B.

**Rig:**
- Supply A set for Battery Voltage ≈ **13.30 V**. That is above 13.15 V: the case V4.0 got
  wrong.
- Supply B at 13.60 V.
- Modem load on.

☐ 1. **Start the outage.** Supply B to 0 V. After about 20 s, On Battery ON. Total Outages
= N = ________.

☐ 2. **Let charge accumulate.** Wait 60 s. Ah Delivered (This Outage) = ________ Ah. Expect
about 0.02 Ah [D: 1.1 A × 80 s ÷ 3600 = 0.024].

☐ 3. **Reboot.** HA "Restart".

| ☐ | When after boot | Where | Expected line or state |
|---|---|---|---|
| ☐ | ≈ 9.5 s | UART (NET only if it reconnects in time [I]) | `[W][ups:…]: Booted during outage -- counters PRESERVED from NVS (0.0… Ah), tracking re-anchored` |
| ☐ | ≈ 19.5 s | UART/NET | `[W][ups:…]: on_press suppressed — already in an outage (start=…); counters preserved` |
| ☐ | after | HA | Total Outages **still N**; Ah Delivered (This Outage) carries on from step 2 (**not** 0) |

☐ 4. **End the outage.** Supply B to 13.60 V. About 70 s later:
`[I][ups:…]: OUTAGE END #N | … min | … Ah | … Wh | Start V: … V | Min V: … V | Peak chrg: … A`.
The duration counts from the re-anchor, which is an inherited limit.

**Pass:** both lines appear; Total Outages is unchanged; the Ah is not reset.

On V4.0 this would fail: neither line, Total Outages N+1, and the Ah back to 0.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T10. Reset during survival (F03)

**Build:** B.

**Rig:** as T5, in survival sleep.

☐ 1. Between two wakes, press the XIAO's RESET button.

| ☐ | When after reset | Where | Expected line or state |
|---|---|---|---|
| ☐ | power-up | UART | ROM: `rst:0x1` [I] |
| ☐ | < 1 s | UART | `[I][ups.survival:…]: Boot wake cause = 0 (cold/reset)` |
| ☐ | < 1 s | UART | `[W][ups.survival:…]: SURVIVAL EXIT (RESET DURING SURVIVAL, wake cause 0) \| modem on; the shed must be re-earned` |
| ☐ | < 1 s | UART | `[I][ups.watchdog:…]: INA usable (11.7… V) — normal/survival logic in control; run_duration watchdog disarmed` |
| ☐ | < 1 s | SCOPE | CH1 LOW from the reset; CH2 high: the modem is on |
| ☐ | ≈ 9.5 s | UART/NET | `[W][ups:…]: Booted during outage -- counters PRESERVED from NVS (… Ah), tracking re-anchored` |
| ☐ | ≈ 19 s | UART/NET | `[W][ups.shed:…]: MODEM SHED #… \| V=11.7… V <= 11.80 V on 10 valid reads, PSU sense 0.00 V \| latched until mains returns` |
| ☐ | ≈ 50–55 s | UART/NET | `[W][ups.survival:…]: SURVIVAL SLEEP ENTRY (modem shed) \| …` |
| ☐ | between | HA | Survival Exit Reason = "Reset during survival" |

Record:
- reset to `MODEM SHED`: ________ s (expect ≈ 19 s);
- reset to `SURVIVAL SLEEP ENTRY`: ________ s (expect 50–55 s) [D: review §3.2].

**Pass:** the modem is on from the reset until the re-earned shed, and the reset boot does not
re-sleep by itself.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## T11. First discharge of the real pack (item 14; the F06 gate; item 19)

**Build:** P (production), or B.

**Rig:** the real system: the Cyclenbatt pack, the HDR at 13.6 V, and the XB7 as both the load
and the AP. HA records at 5 s.

> **Note.** The XB7's AP dies at the shed. Everything after the shed is read from the
> NVS-backed entities once it recovers.

☐ 1. **Float.** Leave it on float for ≥ 24 h [I: assumed full]. Battery Voltage ________ V,
Battery Current ________ A.

☐ 2. **Start.** Switch the HDR's AC off. Start time ________.

☐ 3. **Run to the shed** at 11.80 V. From HA history afterwards, record:
- time to shed: ________ min;
- the last "Ah Delivered (This Outage)": ________ Ah;
- the last "Wh Delivered (This Outage)": ________ Wh;
- the V curve's knee and cliff, by time and voltage: ________;
- the deepest 5 s block dips in the last 10 min (the XB7's peaks; these set
  `shed_valid_reads_n`): ________ V;
- Battery Current 10 Hz SD near the shed: ________ A.

☐ 4. **Survival.** Leave it in survival sleep for ≥ 1 h (≥ 30 wakes).

☐ 5. **Recover.** Switch AC on. Once the XB7's AP is back, 3–5 min later
[S: design doc 1.4], record:
- Survival First / Min / Last Wake Voltage: ______ / ______ / ______ V. All must be below
  13.0 V, or deviation 1 occurs.
- Survival Exit Reason ________. Survival Exit Test Current ________ A (amps positive =
  charging).
- Last Survival Cycles ________. Last Outage Duration ________ min.
- Last Recharge Peak Current ________ A, against the 5.0 A label (item 19).
- PSU Decay To Threshold ________ s.

☐ 6. *Optional, at the next convenient outage:* repeat to the shed, and pull the PSU_SENSE
lead before AC returns (as T7 part B).
- Survival Exit Test Current ________ A.
- If it reads ≥ +0.20 A, `survival_exit5_require_charge` may be set to `"true"`.

**Pass:** every row of §5's table has a measured value or an owner decision.

**PASS ☐  FAIL ☐**   Notes: ______________________________________________

---

## 5. Close-out

☐ 1. **Update the placeholders** in the YAML. Tag each new value [M], with the test it came
from.

| Substitution | V4.1 value | Measured | From test | New value |
|---|---|---|---|---|
| `psu_divider_ratio` | 6.556 | | T1 | |
| `mains_present_v` | 7.0 | V_Q2 = | T8, T2 | |
| `mains_debounce_polls` | 10 | t(7.0 V) = | T2 | |
| `plausibility_alert_delay` | 60s | | T2 | |
| `shed_voltage` | 11.80 | | T11 | |
| `shed_valid_reads_n` | 10 | XB7 dips | T11 | |
| `shed_plausible_v_min` / `_max` | 5.0 / 16.0 | owner's choice | — | |
| `psu_not_feeding_i_a` | −0.50 | modem draw | T11 | |
| `survival_exit_v` | 13.0 | rest V | T11 | |
| `shed_require_cvrf` | true | stale reads | T4 | |
| `survival_exit5_require_charge` | false | exit-test I | T11 | |
| `validated_capacity_ah` | 4.18 | Ah at shed | T11 | |
| `settling/plateau/knee_min_v` | 13.00 / 12.65 / 12.40 | V curve | T11 | |
| `knee/cliff_slope_threshold` | −3.0 / −10.0 | slope | T11 | |
| `survival_entry_current_lo` / `_hi` | −0.30 / 0.20 | post-shed I | T5, T11 | |

☐ 2. **Flash Build P** by OTA. In the HA device info, confirm project version 4.1 (or the new
one).

☐ 3. **Clear the bench counts.**
- Total Outages, Modem Shed Count, Shed Hold Lost Count, the lifetime Ah/Wh and the onset/Ri
  entities still hold bench values.
- To clear them: take the XIAO out of its socket, run `esptool.py erase_flash`, then flash
  Build P over USB.
- Or keep the counts. That is the owner's call.

☐ 4. **Record the results** in the design doc: item 7 (T5), item 17 (T6), item 28 (T1/T3), and
section 8.1.

Signed: ____________________   Date: ____________

---

## Appendix A: Build B, the bench-only edits

Apply these to a **copy** of `ups-monitor-rev4.yaml`. They compiled on ESPHome 2026.10.2 with
0 errors (2026-11-15). Never flash Build B into service.

```yaml
logger:
  level: INFO
  hardware_uart: UART0       # BENCH BUILD ONLY: GPIO21 TX at 115200
  baud_rate: 115200
```

Add under `button:`, after the Restart button:

```yaml
  # BENCH BUILD ONLY — never ship. Freezes the INA260's registers (power-down),
  # which the shed path must reject as stale. Restart restores the chip.
  - platform: template
    name: "BENCH INA260 Power-Down"
    entity_category: diagnostic
    on_press:
      - lambda: |-
          uint8_t pd[3] = {0x00, 0x61, 0x20};
          bool ok = id(ina_raw).write(pd, 3) == i2c::ERROR_OK;
          ESP_LOGW("bench", "INA260 config written to 0x6120 (power-down): %s", ok ? "ok" : "I2C error");
```

---

## Appendix B: log line reference (V4.1)

These are the firmware's own lines, with the substitutions resolved. `…` is a value.
"Seen" says where a line can be observed: UART, NET, or both.

| L | Tag | Line | Seen | Test |
|---|---|---|---|---|
| I | ups.survival | `Boot wake cause = … (timer-wake \| cold/reset)`. 0 = reset, 4 = timer [S: esp_sleep.h] | UART | T1, T3, T5, T10 |
| I | ups.watchdog | `INA usable (… V) — normal/survival logic in control; run_duration watchdog disarmed` | UART | T1, T5, T10 |
| W | ups.watchdog | `INA UNUSABLE (raw=0x… V=…) — awaiting WiFi; run_duration will sleep the device if no AP confirms …` | UART | fault only |
| I | ups.watchdog | `Normal operation confirmed by WiFi association — run_duration watchdog disarmed` | UART | T1 |
| I | main | `UPS Monitor Rev 4 V4.1 boot complete -- INA260 @ 0x40 …` | UART | every boot |
| W | ups | `Booted during outage -- counters PRESERVED from NVS (… Ah), tracking re-anchored` | UART, NET | T3, T9, T10 |
| W | ups | `on_press suppressed — already in an outage (start=…); counters preserved` | UART, NET | T3, T9 |
| I | ups.mains | `PSU sense … V < 7.0 V, … s after the INA260 load step (HDR decay, open item 6)` | NET | T2, T6 |
| I | ups.mains | `PSU sense … V < 7.0 V, no INA260 load step in the last 600 s (glitch, decay < step debounce, or decay > 600 s)` | NET | T4, T7, T8 |
| W | ups.shed | `MODEM SHED #… \| V=… V <= 11.80 V on 10 valid reads, PSU sense … V \| latched until mains returns` | NET | T4, T5, T8, T10 |
| W | ups.shed | `MODEM RESTORED \| mains present, PSU sense … V (debounced)` | NET | T4 |
| W | ups.shed | `Shed read STALE: INA260 CVRF clear, no conversion since the last poll \| V=… \| count …` | NET | T4 step 9 |
| E | ups.shed | `MODEM_OFF readback mismatch: commanded …, pad reads … — re-running pad setup` | NET | must not appear |
| W | ups.shed | `MODEM_OFF read LOW on a survival wake — latch lost or pad unreadable (count …)` | UART | T5: must not appear |
| W | ups.survival | `SURVIVAL SLEEP ENTRY (modem shed) \| V=…V I=…A \| snapshot: … Ah / … Wh / min … V \| timer-wake` | UART, NET | T5, T6, T10 |
| I | ups.survival | `INA260 powered down (~2 µA) for survival sleep` | UART, NET | T5 |
| I | ups.survival | `Wake #… \| V1=…V \| PSU=…V (mains absent \| mains present)` | UART | T5, T6, T7 |
| I | ups.survival | `V=…V < 13.0V, mains absent — scheduling re-sleep (cycle …)` | UART | T5 |
| I | ups.survival | `Re-entering survival sleep \| INA260 powered down (~2 µA) \| timer-wake 120s` | UART | T5 |
| I | ups.survival | `SURVIVAL EXIT (mains on PSU sense \| bus voltage only, PSU sense absent) \| V1=…V V2=…V \| PSU …V / …V \| I=…A \| recovery — normal boot, modem released` | UART | T5, T6, T7 |
| W | ups.survival | `SURVIVAL EXIT (RESET DURING SURVIVAL, wake cause …) \| modem on; the shed must be re-earned` | UART | T10 |
| W | ups.survival | `SURVIVAL EXIT (FAIL-SAFE) \| raw=0x… V=… — booting normally` | UART | fault only |
| W | ups.survival | `SURVIVAL EXIT (MAX CYCLES …) \| V=… — booting normally` | UART | 15-day backstop |
| W | ups.survival | `Exit re-read failed: V1=… V2=… PSU … / … I=… — re-sleeping` | UART | glitch only |
| W | ups.survival | `Reason-5 exit refused: bus … / … V >= 13.0 V but I=… A is not charging (resting pack?)` | UART | gate on only |
| I | ups | `OUTAGE END #… (survival) \| … min total (incl. … slept cycles) \| … Ah \| … Wh \| Start V: … V \| Min V: … V` | UART | T5 |
| I | ups | `OUTAGE END #… \| … min \| … Ah \| … Wh \| Start V: … V \| Min V: … V \| Peak chrg: … A` | NET | T2, T4, T9 |
| I | ups | `AC return detected \| I=… A \| uptime … s` | NET | T11 |
| I | ups.recharge | `Recharge-step Ri not captured for this outage: no discharge->charge step is observable after survival sleep …` | UART | T5 |
| I | ups.onset | `ONSET Ri \| Vf=… Vl=… I=… -> R=… mOhm \| T=…F \| q=…` | NET | T2, T11 |
| I | ups.recharge | `RECHARGE Ri \| Vd=… Vc=… Id=… Ic=… dI=… -> R=… mOhm \| T=…F` | NET | T11 |
| I | ups | `Float confirmed: … V (PSU drift ref)` | NET | after 10 min of float |
| I | deep_sleep | `Scheduling in 60000 ms` / `Beginning sleep` / `Sleeping for 120000000us` [S: deep_sleep_component.cpp] | UART | T1, T5 |
| W | main | `INA260 ALERT held LOW >200ms on GPIO3 -- unexpected (no alert configured); possible INA260/I2C fault` | NET | must not appear |
| W | bench | `INA260 config written to 0x6120 (power-down): ok` (Build B only) | NET | T4 step 9 |

## Appendix C: ESP32-C3 ROM reset codes

Codes are from ESP-IDF 5.5.6 `rom/rtc.h` [S]. The ROM prints them on UART0 as `rst:0x…`
before the app starts; the exact text around the code is [I].

| Code | Reason | When you see it here |
|---|---|---|
| 0x1 | Power-on | Supply A power cycle; the XIAO RESET button [I] |
| 0x3 / 0xc | Software reset (system / CPU) | HA Restart, OTA [I] |
| 0x5 | Deep-sleep wake | Every survival or watchdog timer wake |
| 0x7 / 0x9 | Watchdog | Must not appear |
| 0xf | Brown-out | Must not appear |
