# DIY LiFePO4 UPS: Technical Report
## 18 V Boost Subsystem — Post-Installation Review, August 31, 2026

**Data through:** 2026-09-01 01:05 UTC · **Version:** 2026-08-31-r2 · **Report series:** UPS-RPT
**Revision r2:** V1.17 flashed 19:26 EDT and validated against a 54-minute outage test the same night. That test **falsified the phase-duration projection in r1** (§2) and exposed a further defect in the Apparent Ri capture (§5.3). Both are recorded rather than replaced.
**Repository:** https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS
**Subsystem under review:** `UPS-Monitor/boost-subsystem-design.md` (BOOST-DS-r1), as built — **EN/FET not installed**

Every numeric claim carries its basis inline: **[M]** measured, **[D]** derived arithmetic on [M] with the formula shown, **[I]** inferred and carrying its falsifier, **[S]** spec. Anything not [M] that gates a pass/fail is named as such.

---

## Abstract

The Pololu U3V70A boost went on the 12 V bus on 2026-08-29 at ~16:50 ET, taking the ASRock N100DC-ITX HA host off its own AC brick and onto the UPS. Two days of InfluxDB telemetry and one 14.7-minute outage test say the integration is electrically sound: the DC bus load rose 1.80× to 26.80 W, every threshold held, no false on-battery occurred in 26,413 samples, and the pack's own internal resistance is unchanged.

What did not survive the change is the instrumentation around it. Five figures were calibrated against a 14.9 W load that no longer exists, and two instruments have stopped producing usable readings — one of which, `binary_sensor.ups_monitor_battery_fully_charged`, turns out never to have fired **once** in the entire InfluxDB record and had silently killed the PSU-drift reference chain behind it. A third, the onset-Ri capture, has a latch defect that predates the boost and would publish ~616 mΩ against a true ~100 mΩ if a real outage ever ran to LVD.

The one open item that matters operationally is not electrical. With no EN shed fitted, the 18 V rail survives `hassio.host_shutdown`, so the host sits in soft-off with DC still applied and never sees the power-cycle its BIOS is waiting for. Unattended recovery is therefore guaranteed only for outages deep enough to reach the BP-65 LVD.

---

## 1. Test Summary

Comparison windows: a clean seven-day pre-boost window (2026-08-22 → 08-28) against everything since 2026-08-30 04:00 UTC. The changeover itself is unambiguous in the record — the N100's own Kasa plug fell to zero at 2026-08-29 19:40 UTC and the UPS outlet stepped from ~16.8 W to ~30 W at 20:50 UTC.

### 1.1 Steady state, on AC

| Quantity | Before | After | Δ | n |
| :--- | ---: | ---: | ---: | ---: |
| AC at the UPS outlet | 16.832 W | 30.554 W | **+13.722 W** (t = 1077) | 91,940 / 20,794 |
| N100 on its own brick | 12.508 W | 0 W | — | 107,480 |
| **Net cost of the extra conversion stage** | | **+1.21 W** at the wall | +9.7 % | [D] |
| Bus float voltage, mean | 13.2325 V | 13.1970 V | **−35.5 mV** (t = −2390) | 109,931 / 26,413 |
| Bus float voltage, minimum | 13.2230 V | 13.1733 V | −49.7 mV | same |
| Margin to the 13.15 V on-battery trip | 73.0 mV | **23.3 mV** | −68 % | 0 breaches |
| Float-current noise, σ | 6.03 mA | 23.50 mA | ×3.9 | 120,147 / 27,112 |

All [M], from 1-Hz-class Kasa and 5 s INA260 series. The wall-power penalty of routing the host through the PSU and boost rather than its OEM brick is **+1.21 W = $3.08/yr** [D: 13.722 − 12.508, at $0.29/kWh].

Regressing bus voltage on outlet power inside the post-boost window: **−0.993 mV/W** [M] (se 0.035, t = −28.1, r² = 0.259, n = 2,255 one-minute bins, fitted over 29.5–40.5 W). Extrapolating that slope says the bus would not reach 13.15 V until roughly 78 W of AC input [D] — but that is a 2.6× extrapolation of an 11 W lever arm and should be treated as a bound, not a prediction. The direct observation is stronger and needs no model: **zero of 26,413 post-boost samples fell below 13.16 V.**

### 1.2 On battery — 2026-08-29 outage test

AC cut at 23:46:03 UTC (`switch.ups_outlet` off), restored 23:59:57 UTC. `on_battery` ON 23:46:17 → OFF 00:00:57, i.e. 14.7 min.

| Metric | May 2026 baseline | 2026-08-29 | Ratio |
| :--- | ---: | ---: | ---: |
| Steady discharge power | 14.9 W | **26.80 W** | ×1.80 |
| Steady discharge current | 1.18 A | **2.089 A** | ×1.77 |
| Peak observed | ~1.29 A | 2.533 A / 32.48 W | ×1.96 |
| Loaded bus voltage | — | 12.839 V (min 12.791) | — |
| Energy delivered | — | 6.114 Wh / 0.4745 Ah | 11.4 % of pack |
| Onset step resistance | — | 188.9 mΩ (see §5.2) | — |
| Apparent Ri (settled step) | — | 122.0 mΩ (see §5.2) | — |

Steady figures over 23:46:30–23:59:30, n = 156 five-second samples, sd 1.58 W [M].

**Requirement R4 (never exceed the 10 A BMS rating) is comfortable:** steady draw is 21 % of the rating, peak 25 %.

---

## 2. The Shutdown Ladder — projected, then measured

Every phase duration in the firmware comments, the automation headers and the dashboard was measured at 1.18 A. Scaling by the measured energy rate:

| Phase | Band | At 14.9 W [M] | At 25.0 W [D] |
| :--- | :---: | ---: | ---: |
| Settling | > 13.00 V | 5 min | 3 min |
| Plateau | 12.65 – 13.00 V | 142 min | 85 min |
| Knee | 12.40 – 12.65 V | 49 min | 29 min |
| **Cliff — shutdown fires here** | 11.80 – 12.40 V | **17 min** | **10 min** |
| **Total to BP-65 LVD** | 13.23 → 11.80 V | **213 min** | **128 min** |

[D: 53.3 Wh ÷ 25.01 W outage mean = 128 min; phases scaled ×0.601].

### 2.1 That table was wrong, and the 2026-09-01 test says by how much

**FALSIFIED the same night.** A 54-minute outage test (00:05:47 → 00:58:07 UTC,
12.97 → 12.565 V, 1.833 Ah / 23.369 Wh = 43.85 % of capacity) measured the
plateau at **~43 min against the ~85 projected — 2.0× out.**

| Phase | Band | @ 14.9 W May [M] | @ 25.0 W projected [D] | @ 26.9 W measured |
| :--- | :---: | ---: | ---: | ---: |
| Settling | > 13.00 V | 5 min | 3 min | **none** — starts loaded at 12.97 V [M] |
| Plateau | 12.65 – 13.00 V | 142 min | 85 min | **~43 min [M]** |
| Knee | 12.40 – 12.65 V | 49 min | 29 min | ~20 min [D] |
| Cliff | 11.80 – 12.40 V | 17 min | 10 min | **not measured** |
| Graceful shutdown fires | ~12.45 V | ~155 min | ~117 min | **~60–70 min [D]** |

**Why the scaling failed, which is the part worth keeping.** r1 flagged that the
linear energy scaling "does not model the extra IR sag at 2.089 A" and published
the numbers anyway. On the flat LFP plateau that sag is not a correction, it is
the dominant term: the terminal voltage reaches 12.65 V at **~35 % depth now
against ~69 % in May** [M]. Energy scales with load; voltage thresholds do not.

The energy figure survived — 53.3 Wh ÷ 25.97 W measured = **123 min** against
the 128 projected — and is irrelevant to the ladder, which trips on volts.

Knee is 11 minutes measured then extrapolated at −8.5 mV/min; everything below
**12.565 V is unmeasured at this load**.

**Two limits, stated rather than buried.** This is a linear energy scaling. It does not model the extra IR sag at 2.089 A, which makes the terminal voltage cross each threshold at a *higher* state of charge than before — conservative for the thresholds, unfavourable for the cliff. Delivered Ah at 2.089 A is expected lower by [D: 0.23 V extra IR sag ÷ ~1.8 V/Ah cliff slope = ~0.13 Ah, 3 % of 4.18 Ah], which is **not measured**. Second, the 08-29 test reached 11.4 % depth; **nothing below 12.79 V has been measured at the new load at all.**

The operational consequence was one line of notification text: *"Cliff entry threshold reached (12.40V). ~17 min to BP-65 LVD."* That is what the phone shows at 2 a.m. It is now roughly 10 minutes. Corrected 2026-08-31 (§6).

One claim was retired rather than rescaled: the "~15 min HA shutdown" budget those comment blocks cited was never a measurement. The May 6 test had the host down 6 s after the service call (`hassio.host_shutdown` 13:40:11, last HA sample 13:40:17) [M].

---

## 3. The Unattended-Recovery Gap

**This is the finding with operational consequence, and it is not electrical.**

Three facts, all now established:

1. BIOS *Restore on AC/Power Loss* is set to **Power On** [M, owner-confirmed 2026-08-31].
2. The boost has no EN control fitted, and takes its input from the **BP-65 load output** [M, owner-confirmed].
3. Therefore the 18 V rail is live whenever the 12 V bus is live [D, topology].

`hassio.host_shutdown` leaves the N100DC in S5 soft-off with DC still applied. The BIOS setting acts on a power-cycle *at the jack*; the boost keeps regulating, so no such edge occurs. **Recovery requires a rail collapse, and the only thing that collapses it is the BP-65 LVD at 11.80 V.**

| Outage shape | Outcome |
| :--- | :--- |
| Runs to LVD | Rail dies. AC returns, BP-65 reconnects at 12.8 V / 30 s, boost soft-starts, board sees fresh DC, boots. **Works.** |
| **AC returns after the graceful shutdown but before LVD** | Rail never dropped. Host sits in S5. **HA is down until someone presses the button.** |

**Window width — revised upward by the 2026-09-01 test, and this makes the gap
worse.** r1 put it at ~17 minutes, reasoning that shutdown fires near the end of
the discharge. §2.1 shows it does not: the ladder trips at ~60–70 min, when only
**[D: 43.85 % measured at 54 min, so ~45–50 % at 60–70 min] of the pack has been used**. After shutdown the load falls to ~15 W and
the terminal voltage recovers (less IR drop), so the pack re-enters territory that
took ~46 min to cross at 1.18 A in May. The window is therefore on the order of
**45+ minutes** [D], not 17.

That is the opposite of reassuring: the interval in which AC can return and leave
the host in S5 is roughly three times wider than r1 claimed, and it sits in the
part of an outage where grid restoration is most likely. How often that happens is
not something 17 logged outages — mostly deliberate tests — can answer, but the
exposure is larger than stated. Only the deep test settles the number.

**Fitting the EN/FET closes it.** A latched EN-low shed *is* the power-cycle edge the BIOS is waiting for, and re-enable on confirmed AC return produces exactly one clean boot. This is a second, independent argument for the EN work; `boost-subsystem-design.md` argues for it on BMS grounds (DR-1) only. Until it is fitted, the honest statement is: **unattended recovery is guaranteed only for outages deep enough to reach LVD.**

### 3.1 What the topology answer closed

The boost sitting behind the BP-65 rather than on the raw bus closes the worst credible failure: the LVD still sheds it alongside the XB7, so the pack stays protected below 11.80 V. Survival-sleep entry is intact and in fact easier to satisfy than designed — the post-trip load collapse is now 2.089 A → ~0.04 A instead of 1.18 A → ~0.04 A, landing further inside the −0.30/+0.20 A entry window. DR-1 also holds by construction on the reconnect path even with no EN: the bus can only climb to the 12.8 V reconnect threshold with the PSU live, so every LVD recovery is an AC-present soft-start by definition.

---

## 4. Instruments That Stopped Meaning What They Said

### 4.1 "Fully Charged" has never once been on

`binary_sensor.ups_monitor_battery_fully_charged` fires on `V > float_voltage − 0.05` = **13.25 V** with `|I| < 0.10 A`, held 600 s. The PSU has never floated that high.

- Highest bus voltage in the **entire** InfluxDB record: **13.2705 V** [M, 2026-08-29 19:34 UTC — during the boost install, with the load off].
- Normal ceiling was 13.2348 V; it is now 13.2017 V.
- 98 writes of that binary sensor across all history, **max 0, min 0** [M]. Off since the series began 2026-05-31.

13.30 V is the HDR-60 **nameplate** [S]; the measured float is 13.197–13.232 V [M]. The threshold was derived from spec, and the spec was never met.

**Blast radius.** The `on_press` handler is the only writer of `last_float_voltage`, the PSU-drift reference. So `sensor.ups_monitor_last_float_voltage` reads *unknown*, which fails the availability guard on `sensor.ups_apparent_internal_resistance`, which in turn leaves `sensor.ups_ir_temperature_compensated` *unknown*. Three entities dead behind one threshold that could never be crossed.

The current half of the gate was checked separately and is **not** implicated: the longest continuous run under 0.10 A in the post-boost record is 31,987 s [M], against a 600 s requirement.

### 4.2 The coulomb counter started integrating noise

`discharge_current` rectifies — it returns `|I|` when `I < −50 mA` and zero otherwise. Rectifying a symmetric noise tail integrates one way.

| | Pre-boost | Post-boost |
| :--- | ---: | ---: |
| Float-current σ | 6.03 mA | 23.50 mA |
| Deadband in σ | 8.3 σ | **2.1 σ** |
| Samples breaching −50 mA | 6 / 120,147 (0.005 %) | 764 / 27,112 (2.818 %) |
| Ah drift on AC, no outage | 0.212 mAh/day (21 clean days) | **43.3 mAh/day** (39.9 h, n = 1,501 writes) |

Two-proportion z = 58 on the breach rates [M]. The mechanism closes independently: 2.8 % of samples at a mean breach of ~57 mA reproduces the observed drift [D].

**Not affected:** runtime remaining, the shutdown ladder, `last_outage_ah/wh`, and every alarm. `ah_delivered_outage.reset()` runs in the on-battery `on_press`, so the phantom is wiped at outage start and never enters `(capacity − ah_used) ÷ |I|`.

**Affected:** the lifetime counters, which have no reset and are the only cycle-count proxy for a pack whose replacement decision will rest on cycles plus Ri. The phantom equals the entire 08-29 outage in **11 days** and the whole 7.787 Ah lifetime total in **about six months** [D]. In Wh it is worse — 209 Wh/yr of phantom against 99.9 Wh accumulated in three months.

**Urgency is narrow and real:** the counter was ~0.95 % contaminated when this was found. Fixed now, no reset is needed and the history stays good. Left a month, it is ~17 % contaminated and `button.ups_monitor_reset_lifetime_counters` becomes the only clean option.

### 4.3 The onset-Ri capture re-fires all outage long

The 100 ms detector arms on `I < −0.5 A` for two consecutive polls. `onset_capture` clears its own `g_onset_capturing` guard after a 2 s delay — and the condition is still true, because the outage is still happening. It re-captures roughly every 2.4 s for the whole event: **~3,200 times in a full 128-minute discharge** [D] where one was intended, each overwriting `g_onset_r` with (stale float V) − (present loaded V) ÷ I.

Observed 2026-08-29: `last_onset_step_resistance` published **165.1 → 181.7 → 188.3 → 188.9 mΩ** at successive 60 s intervals across one 14.7-minute test [M]. A latched onset step would not move.

**The error grows with depth and nothing rejects it.** Unlike `apparent_ri`, this sensor has no plausibility band. Run to LVD — the only outage anyone would consult it after — the surviving sample is (13.20 − 11.80) ÷ 2.27 A = **~616 mΩ** [D], six times the pack's ohmic value, published without complaint.

**Not affected:** survival sleep (the detect lambda's first line is `if (id(survival_mode_active)) return;`), and V1.16's `apparent_ri`, which is correctly latched — after evaluating it sets `ri_rest_v = NAN` and can only re-arm once `|I| ≤ 0.20 A` returns, which cannot happen mid-outage.

---

## 5. Reading the Resistance Numbers

### 5.1 The pack is fine

The one number that says something about the cells is the **recharge step: 102.9 mΩ** against a 96.6 mΩ May baseline at a warmer 84.6 °F [M]. Nothing in this review is battery degradation.

### 5.2 Why the other two moved, and why neither is comparable

| Instrument | Value | Conditions |
| :--- | ---: | :--- |
| Apparent Ri (settled step, 45 s) | 122.0 mΩ | 2026-08-29 23:46, at 2.089 A |
| Apparent Ri, previous sample | 140.5 mΩ | 2026-08-29 20:53, at ~1.1 A |
| Onset step resistance | 188.9 mΩ | same event, corrupted by §4.3 |
| Recharge step resistance | 102.9 mΩ | same event, clean |
| May 2026 baseline | 96.6 mΩ | at 1.18 A, 78 °F |

Apparent Ri **fell** from 140.5 to 122.0 mΩ when the load nearly doubled. That is expected and is not a battery improvement: the method uses the PSU-held float voltage as the rest reference, and that fixed float-above-OCV offset divides by a larger current. **Comparing either figure to the 96.6 mΩ baseline taken at 1.18 A is comparing two different instruments.**

One genuine upside: the bigger step improves the onset instrument once §4.3 is fixed. Step-resistance resolution from the INA260's ±14 mV goes from ±16.8 mΩ at 1.18 A to **±9.5 mΩ** at 2.089 A [D] — a 1.8× sharper reading of the same quantity.

---

### 5.3 Apparent Ri has a publish-timing race, and r1 vouched for it

r1 called `apparent_ri` "the good instrument… correctly latched". The latching is
correct — confirmed 2026-09-01, one sample per rest→load event. **Its reference is
not.**

The settled-step lambda reads `ina260_voltage.state` and `ina260_current.state` —
two **independently published** 5 s averages. At an AC cut the voltage state
updates first, so the `|I| ≤ 0.20 A` "at rest" branch stays true for up to one
publish interval while the bus is already collapsing, and that sample becomes the
rest reference.

Measured on the 2026-09-01 switchover:

| | Value |
| :--- | ---: |
| Last clean float sample, 00:05:45 | 13.1970 V |
| Sample published 00:05:50, straddling the cut | **13.0510 V** |
| Current state at that tick (published 00:05:46) | −0.0075 A — still "at rest" |
| `rest_v` actually latched | 13.0510 V |
| Apparent Ri published | **67.31 mΩ** |
| Same sample with the true float | 141.94 mΩ |

Replaying the raw published series through the lambda reproduces **67.31 mΩ**
against the firmware's 67.3143692 — to 0.005 mΩ. The mechanism is proven, not
inferred. The same race explains the 08-29 sample of 122.0 mΩ, which implies a
`rest_v` of 13.133, also below float.

**So the published series 140.5 → 122.0 → 67.3 mΩ is not pack behaviour. It is
where the 5 s boundaries happened to fall.** The onset capture never had this bug,
because it reads both registers raw inside one 100 ms poll — which is exactly why
its 97.59 mΩ agrees with the recharge step (100.35) and the May baseline (96.6)
while `apparent_ri` disagreed with all three. Fixed in V1.18 (§6.6).

With the fix, the same event gives onset 97.59 mΩ and settled-step 141.91 mΩ — a
ratio of 1.45, which is the polarization growth over 45 s that the two-method
bracket exists to measure. The two instruments finally say something together.

---

## 6. Changes Made, 2026-08-31

### 6.1 Firmware — `ups-monitor-v1-17.yaml` (written and gated, **not flashed**)

153 diff lines, **7 of them code**. Nothing in the shutdown ladder, survival sleep or the watchdogs touched; eight safety-critical substitutions asserted unchanged.

| Change | From | To | Closes |
| :--- | ---: | ---: | :--- |
| Rectifier deadband → substitution | −0.05 A (2.1 σ) | −0.20 A (8.5 σ) | §4.2 |
| Once-per-event latch on `onset_capture` | re-fires ~2.4 s | one sample | §4.3 |
| `onset_float_i_max` — the "at rest" window | 0.05 A | 0.20 A | quality flag |
| `battery_fully_charged` voltage gate | 13.25 V (nameplate) | `on_battery_threshold_v` | §4.1 |

The deadband is now a named substitution rather than a literal in two lambdas, sized in σ of the measured noise so the next load change has somewhere obvious to be re-sized. −0.20 A costs nothing real: an outage draws 1.9–2.5 A and the post-LVD ESP-only load is ~40 mA, already below the old threshold.

`onset_float_i_max` 0.05 → 0.20 aligns the onset quality gate with the window V1.16's settled-step capture already uses for the same judgement. There were **two definitions of "at rest" in one firmware**, two hundred lines apart, and the boost is what made the disagreement matter.

**R4 impact scan first:** 4 `-0.05f` code sites, **2 in scope**. The other two are outage-validity guards gated on `v < on_battery_threshold_v`, where float noise cannot reach. A blanket replace would have hit them.

### 6.2 Validation performed

| Gate | Method | Result |
| :--- | :--- | :--- |
| Parse + substitutions | YAML load; every `${…}` resolved; substituted C++ literals regex-checked | **PASS (parse-clean)** |
| Structural (R3/R4) | 7 code lines changed; 8 safety-critical substitutions asserted unchanged | **PASS** |
| Lambda compile | `riscv32-esp-elf-g++ 14.2.0 -Wall -Wextra -Wfloat-conversion` — the real ESP32-C3 toolchain | **0 errors, 0 warnings** |
| Behaviour (R2, both directions) | replay of the measured InfluxDB traces through V1.16 vs V1.17 logic | **SUITE PASSED** |
| **Real compile → `src/main.cpp.o`** | ESPHome Builder add-on, on the HA host | **OPEN** |

**R2 replay results** — driven by the measured record, not synthetic input:

| Assertion | V1.16 | V1.17 |
| :--- | ---: | ---: |
| *Direction 1 — fires on the data exhibiting the fault* | | |
| Phantom drift, post-boost float trace (38.6 h, n = 27,783) | 44.17 mAh/day | **0.000 mAh/day** |
| Onset captures across the 08-29 outage | 83 | **1** |
| Longest span able to latch `fully_charged` (needs 600 s) | 0 s | **31,987 s** |
| *Direction 2 — silent where things were already right* | | |
| Real outage charge, 08-29 | 0.480667 Ah | 0.480269 Ah (−0.083 %) |
| Pre-boost float drift | 0.073 mAh/day | 0.000 mAh/day |
| Recharge-step capture still arms and fires | 1 | 1 |
| Latch re-arms — outage, float, second outage | — | 2 captures |
| `fully_charged` true at any discharging sample (166) | 0 | 0 |

**Fidelity, stated rather than implied.** The rectifier and the fully-charged gate read the 5 s throttled averages InfluxDB stores, so replaying that series is exact. The onset detector reads registers raw at 100 ms — a series that never leaves the ESP — so the latch test proves *control flow*, and the ~3,200-captures-per-outage figure stays arithmetic. Two rounds of this suite failed on test bugs before it passed: intersecting the V and I series discarded 92 % of the record (they are written on state change, at different instants), and a window that opened mid-outage meant the latch correctly never armed.

### 6.3 Home Assistant configuration

- **`sensor.ups_apparent_internal_resistance` and `sensor.ups_ir_temperature_compensated` retired.** A second copy of a quantity the firmware computes three ways from live current, divided by a hardcoded `typical_i = 1.18 A` against a measured 1.956 A. A tombstone comment records why at the site.
- **UPS notification text corrected** — three automations, five user-visible lines. "~17 min to BP-65 LVD" → "~10 min", "~10 min" → "~6 min", "HA Green" → "Host".
- **Comment blocks corrected, not deleted** — validated phase durations, cliff-to-LVD margin, and the 30 s stability-delay justification now carry both loads with the May figures kept.
- **Dashboard** — regenerated from the deployed `.storage` artifact, not retyped: 6 of 31 cards changed, 25 verified byte-identical. Axes widened (both were clipping the measured peaks), superseded baselines greyed rather than overwritten, phase table gains a measured-load column tagged [D].

### 6.4 The Grafana UPS dashboard had been showing a permanent false alarm

Found while sweeping for anything else still describing the old load.
`grafana/dashboards/ups.json` carried thresholds that could not discriminate on a
12 V bus, and Grafana's model (base colour applies below the first numeric step;
otherwise the LAST step whose value <= the reading wins) made three of them read
as alarms at all times:

| Panel | Steps | What it displayed |
| :--- | :--- | :--- |
| Battery Voltage (stat + timeseries) | red(base) / yellow 46 V / green 52 V | 13.2 V < 46, so base applied: **red 100 % of 30,006 float samples** [M] |
| Battery Power | green(base) / yellow -200 W / red -400 W — descending, malformed | -26.8 W matches both, last wins: **red 100 % of 30,882 samples** [M] |
| Voltage Slope | red(base) / green 0 mV/min | float slope is ~-1.8 mV/min: **red 43.4 % of the time** [M] |

The 46/52 V pair is a 48 V-system default that was never retuned; it did not come
from `battery_bank.json`, which has sensible 12.0/12.4 V steps. Nothing was wrong
with the data or the queries — the colour was simply decoupled from the readings,
which is the INFO HYGIENE failure in another surface: an alarm that is always on
is an alarm nobody reads.

**Retuned to the thresholds the system already acts on**, not to new numbers:
the firmware substitutions (11.80 / 12.20 / 12.40 / 12.65 / 13.15 V; knee slope
-3, cliff slope -10 mV/min), with the colours ported from the HA gauge card so
the two surfaces agree. Power uses the measured load: -33 W (below the -32.48 W
peak) and **-3.0 W** for the discharge boundary rather than 0 W — float power noise
is sd 0.3075 W with an observed min of -2.405 W [M, n=30,879], so a boundary at 0
flickers 43 % of the time at rest. -3.0 W is [D: 3.0 / 0.3075 = 9.8] sigma of that noise and the real
discharge is [D: 26.80 W / 3.0 W = 8.9] beyond it. The first attempt used 0 W and the two-direction replay
caught it.

Verified by replaying the real series through Grafana's own threshold algorithm:
voltage red 100 % -> on-AC colour 100 % at float and a distinct colour during the
08-29 outage; power red 100 % -> green 100 % at float, orange 100 % on battery;
slope 43.4 % red -> 99.8 % normal at float, and during the outage it separates
cliff (57 %) from knee (21 %) from normal (21 %). R3: 5 of 11 panels changed, each
differing **only** in its thresholds block, every query untouched.

Unlike the HA dashboard, this file **is** loaded — it is provisioned from
`/config/grafana/dashboards`, so it takes effect on Grafana's next poll.

### 6.5 The ordering dependency this creates

Fixing `battery_fully_charged` makes it fire for the first time in the system's life, which writes `last_float_voltage` — the availability guard holding the orphaned Ri template dead. Left in place, it would have **come alive publishing 198.1 mΩ where the truth is 119.5** [D: (13.197 − 12.9633) ÷ 1.18 vs ÷ 1.956], against a 96.6 mΩ dashboard baseline. Retiring it (§6.3) is therefore a **prerequisite to the flash**, not housekeeping. A dead wrong number is harmless; a live one that looks like battery degradation is not.

---

### 6.6 Firmware — `ups-monitor-v1-18.yaml` (written and gated, **not flashed**)

73 diff lines, 3 of them code.

| Change | Closes |
| :--- | :--- |
| `apparent_ri` rest baseline rejects a candidate more than 20 mV from the held value (~8σ of float noise), self-healing after 5 consecutive rejections | §5.3 |
| Header phase durations replaced with the 2026-09-01 measurement, and the reason the scaling failed | §2.1 |

Validated: `riscv32-esp-elf-g++ -Wall -Wextra -Wfloat-conversion` → 0 errors,
0 warnings. R2 replay of the real switchover → V1.17 latches 13.0510 V and
publishes 67.31 mΩ (matching the firmware), V1.18 latches 13.1970 V and publishes
141.91 mΩ. Direction 2: across 25 min of ordinary float, 1,491 samples adopted,
**0 rejected** — the gate does not interfere at rest. `src/main.cpp.o` remains
open.

---

## 7. Open Items

| # | Item | Basis |
| :--- | :--- | :--- |
| 1 | **EN/FET not fitted** — unattended recovery guaranteed only for outages reaching LVD (§3) | [D] |
| 2 | Full discharge to LVD at the new load — closes §2's 128 min, the real cliff duration, survival-sleep arming at 2.089 A, and §3 empirically | not measured |
| 3 | `src/main.cpp.o` compile of V1.17 — needs the Builder add-on on the HA host | open |
| 4 | Recharge headroom post-outage. The design brief estimated a stretch of [S: BOOST-DS-r1 §7, 4.5 A → 2.8 A recharge current]; with the host's boot draw inside the same 60 W budget it may be worse — [I: ~25 W host boot + 12.2 W XB7 + 0.5 W monitor leaves ~1.7 A for bulk charge. FALSIFIER: the peak recharge current logged after the next deep outage]. The only post-boost recharge on record followed a 0.47 Ah discharge and peaked at 1.149 A — nowhere near the CC limit | not measured |
| 5 | Design-brief §10 scope gate (V1/V2/V5) — untouched by telemetry. The BP-65's 12.8 V reconnect now soft-starts the boost into a cold N100, which *is* V2 | open |
| 6 | ~2.2 W of the pre-boost 14.9 W bus load unattributed. The HA Green is eliminated (off the bus since the ASRock install); the load was flat across the period it left [M, n = 5 outage tests]. Most likely XB7 variance above its 12.2 W spot figure. One bench minute with the XB7 unplugged settles it | [I] |
| 7 | The onset-Ri series is **not a continuation** — every stored value was produced by the §4.3 path | — |

---

## 8. Conclusion

The load nearly doubled and every threshold held. No false on-battery in 26,413 samples, no BMS pressure, no XB7 disturbance in the record, the modem stayed online through the test, and the pack's own resistance is unchanged. **The integration works.**

What degraded is the instrumentation around it — and on a system whose stated philosophy is that no help is coming, an instrument that reads plausibly while measuring nothing is the failure mode that matters. Three of the four firmware defects trace to a single root cause — float-current noise up [D: σ 23.50 mA / 6.03 mA = 3.9] — and are a token each; the fourth predates the boost entirely and had been silently wrong since the sensor was written.

The item that deserves the next hour of bench time is not on that list. It is the EN/FET, because it is the only one that changes what happens when the power comes back and nobody is home.

---

## Appendix: Data Provenance

| Source | Detail |
| :--- | :--- |
| InfluxDB 1.x | `Home Assistant` database, 10.0.0.210:8086, retention `autogen` (infinite). Series: `A` / `V` / `W` by `entity_id` tag. **Writes occur on state change, not on a sample clock** — an unchanged value writes nothing, and intersecting two series therefore discards most of the record. |
| INA260 | 5 s throttled averages published to HA; ±14 mV / ±2.75 mA at 1.18 A. Raw 100 ms register reads used by the firmware's onset detector never leave the device. |
| Kasa plugs | `ups_outlet_current_consumption` (PSU AC input), `ha_n100_pc_current_consumption` (host brick, 0 W since 2026-08-29 19:40 UTC by design — the brick is unplugged at the jack and the plug is retained as the documented fallback path). |
| Live entity states | `GET /api/states`, 2026-08-31. |
| Deployed dashboard | `.storage/lovelace.lovelace`, view path `new-ups-dashboard`, read directly rather than transcribed. |
| Firmware source | `ups-monitor-v1-16.yaml` at `origin/main` `60afe8d`. The deployed build is dated 2026-07-18, config hash `0xf52e01a0`; the local clone was three commits behind and was pulled for this review. |
| Owner-confirmed physical facts | Boost input on the BP-65 load output; BIOS *Restore on AC/Power Loss* = Power On; HA Green off the bus since the ASRock install; N100 brick unplugged at the jack. Recorded in `open_questions.yaml` (2026-08-31). |

**What this report does not establish.** Nothing below 12.79 V at the new load; no soft-start, overshoot, hiccup or barrel-insertion behaviour; no recharge behaviour after a deep discharge; and no confirmation that the §3 gap behaves as derived — that requires letting the shutdown fire and restoring AC before LVD.
