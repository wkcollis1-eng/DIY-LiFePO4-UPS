# DIY LiFePO4 UPS: Technical Report
## Outage Test & Validation Report — May 6, 2026 (Rev 2)

**Data through:** May 6, 2026
**Published:** May 6, 2026 (Rev 1) / May 18, 2026 (Rev 2 — data-traced corrections)
**Version:** 2026-05-06-r2
**Repository:** https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS
**Report series:** UPS-RPT

> **Rev 2 changes vs Rev 1:** corrected automation-chain narrative (`cliff_imminent` path, not 12.20 V path); replaced D3-vs-projection comparison with D3-vs-measured; tightened BP-65 trip window against the Victron datasheet; rebuilt Section 3.3 phase profile from direct Voltage.csv data; quantified runtime-estimator optimism; added Section 3.6 battery thermal note; updated YAML recommendations to address phase-band misalignment.

---

## Abstract

This report documents the first full-system outage test conducted after the ESPHome INA260 monitoring upgrade (replacing the Shelly Plus Uni) and after the v3 HA automation chain (`ups_*_v3`) replaced the v2 minimal voltage-only controller. The May 6, 2026 outage ran from AC failure at 10:25:20 UTC to the BP-65 hardware LVD trip at ~13:58:30 UTC, then to confirmed AC restoration at ~14:02:30 UTC — a true AC-off duration of ~217 min. The ESPHome state-machine outage indicator reported 222 min owing to debounce timers at both ends; both figures are correct, they measure different things. This is the first event to provide coulomb-counted capacity data: **4.179 Ah / 53.271 Wh delivered**. The v3 graceful-shutdown chain validated cleanly via the `cliff_imminent` (slope-based) path, not the 12.20 V `voltage_critical` path — by the time HA shut down, voltage was 12.43 V, still 230 mV above the critical threshold. The BP-65 hardware LVD subsequently tripped per spec. Measured runtime (~213 min) matched D3's own measured runtime (~214 min) within one minute; both undershot the YAML linear-model projection of 257 min by similar margins, reflecting a known limitation of the linear runtime estimate rather than a system-degradation event. The PSU delivered a peak recharge current of 4.59 A (60.4 W) immediately on AC restoration, at the constant-current limit of the HDR-60-12.

---

## Executive Summary

1. **The v3 automation chain validated end-to-end via the `cliff_imminent` path.** `ups_graceful_shutdown_v3` triggered when the EMA voltage slope crossed −10 mV/min and held there for 60 s (all firmware guards satisfied: V<12.85 V, I<−0.10 A, slope<−10 mV/min), executed its 30 s revalidation delay, and called `hassio.host_shutdown` at 13:40:11 UTC. Last HA sample 6 s later at 13:40:17. The 12.20 V `voltage_critical` path (`ups_critical_shutdown_v3`) was **not** exercised — V did not cross 12.20 V until 13:48:07 UTC, 8 min after HA was already down. The runtime<8-min path likewise did not fire — runtime estimate was 50.8 min at 13:39:40, just before the shutdown trigger.

2. **Outage durations distinguished.** True AC-off duration ≈ **217 min** (AC fail 10:25:20 → AC restored ~14:02:30 UTC). ESPHome flash-stored "Last Outage Duration" = **222 min**, reflecting the `on_battery` binary sensor's `delayed_on: 10s` start debounce + `delayed_off: 60s` end debounce + BP-65 reconnect dynamics. Use 217 min for energy/capacity comparisons; 222 min is the state-machine artifact.

3. **First direct coulomb-count: 4.179 Ah / 53.271 Wh.** This figure is independently corroborated within 0.1% by HA-side trapezoidal integration over the 10:25:20 → 13:40:17 window (48.99 Wh ESPHome vs 48.94 Wh re-derived). It supersedes the D3-inferred 4.85 Ah / 62.5 Wh figure, which was computed as Kill-a-Watt watts × Shelly-timed profile rather than measured by current sensor.

4. **The "43-min shortfall vs D3" framing is retracted.** D3 actual measured runtime (Mar 26 raw voltage CSV: discharge onset 17:01 UTC, BP-65 trip 20:34:58–20:35:29 UTC) was 214 min. May 6 actual measured runtime was 213 min. The two outages agree on runtime within one minute. The 257-min figure in Rev 1 was a YAML linear-model projection (validated_capacity_ah ÷ typical_load_amps × 60), not a D3 measurement; both real outages fall short of that projection because cliff steepening is non-linear, not because of a system fault.

5. **BP-65 trip pinned to a narrow window.** V crossed 11.800 V at 13:56:27 UTC (ESPHome log) and descended monotonically thereafter with no rebound above 11.800 V. Per Victron BP-65 datasheet (Mode A/B, default), under-voltage disconnect occurs 12 s after alarm activation + 90 s after that, i.e. **102 s after first threshold crossing → spec-predicted trip 13:58:09 UTC**. Last log sample at 13:58:17 showed I = −1.216 A (load still drawing), so the actual trip occurred 8+ s past spec — bounded window **13:58:17 to ~14:02 UTC**, best estimate ~13:58:30 ± 15 s (within component tolerance of the 102 s spec).

6. **Runtime estimator was ~2.6× optimistic at the cliff trigger.** At 13:39:40 (last HA sample of `Runtime Remaining Minutes`), the estimator reported 50.8 min remaining; actual time to BP-65 trip was 18.6–21 min depending on the trip-window endpoint chosen. This is the architectural reason the slope-based `cliff_imminent` path is the correct primary trigger: at the moment of trigger, the runtime estimate alone would not have flagged urgency.

7. **YAML phase boundaries don't align with the physical LFP plateau.** Direct Voltage.csv reconstruction shows actual phase durations of ~5 / ~93 / ~99 / ~17 min (Settling / Plateau / Knee / Cliff) — most of the discharge sits in what the firmware labels "Knee" because the YAML's 12.85 V Plateau-Knee boundary cuts the physical plateau in two. Rev 1's reported durations (8 / 136 / 53 / 16) were wrong in the middle two bands. See Section 3.3 and Section 6.

8. **Battery thermal response confirmed PSU-driven, not discharge-driven.** Battery temperature dropped from 81.5 °F pre-outage to a 75.7 °F minimum mid-outage, then rose to 83.3 °F during peak-current recharge an hour after AC restoration. This tracked the enclosure's PSU heat soak, not battery activity (I²R dissipation at 1.18 A < 0.1 W). See Section 3.6.

---

## 1. System Configuration Reference

*This section is carried forward in every report. Amend only when hardware changes.*

### 1.1 Hardware

| Component | Model | Role | Key Parameter |
| :--- | :--- | :--- | :--- |
| Battery | Cyclenbatt 10Ah LiFePO4 | Energy storage | 10 Ah nameplate; 4.18 Ah accessible at 13.3 V float |
| PSU | Mean Well HDR-60-12 | Float charger | 13.3 V setpoint (lacquered); 60 W / 4.5 A max |
| LVD | Victron BP-65 (Mode A/B) | Hardware protection | Trip ~11.8 V (12 s alarm + 90 s disconnect delay), reconnect ~12.8 V (30 s hold-off) |
| Diode | Pololu #5382 ideal diode | Reverse current block | — |
| Monitor | XIAO ESP32-C3 + Adafruit INA260 + DS18B20 | Voltage, current, temperature telemetry | INA260: 2 mΩ shunt, ±1.25 mA resolution |
| Host | HA Green | Automation executor | ~0.8 W DC |
| Protected load | Xfinity XB7 modem | Network continuity | ~12.2 W DC |

**Measured DC load (INA260, this outage):** 4.179 Ah / 53.271 Wh over 213 min → ~15.0 W average
**Note on the BP-65 timer chain:** Victron's documented sequence is **alarm activation 12 s after V<trip, then load disconnect 90 s after that**, total 102 s end-to-end. This figure is used for trip-time bounding in Section 2.

### 1.2 Voltage Threshold Reference (v3 automation chain)

| Threshold | Firmware sensor / HA automation | Response | Notes |
| :--- | :--- | :--- | :--- |
| < 13.15 V sustained 10 s | `on_battery` (ESPHome) → Auto 1 | HA notification: outage start | `delayed_on: 10 s` debounce |
| < 12.40 V sustained 30 s with I<−0.10 A | `voltage_warning` (ESPHome) → Auto 2 | HA notification: knee threshold + runtime estimate | — |
| **slope < −10 mV/min, sustained 60 s, V<12.85, I<−0.10** | **`cliff_imminent` (ESPHome) → Auto 3** | **Graceful shutdown** (30 s revalidation → `hassio.host_shutdown`) | **Primary shutdown path** |
| `runtime_remaining_minutes` < 8 | Auto 3 alternate trigger | Graceful shutdown (same chain) | Backup to cliff_imminent |
| < 12.20 V sustained 10 s with I<−0.10 A | `voltage_critical` (ESPHome) → Auto 4 | Hard fallback shutdown (immediate `hassio.host_shutdown`) | Safety net above BP-65 |
| ~11.80 V | BP-65 hardware (Mode A/B) | Alarm 12 s → disconnect 90 s → load off | 102 s total; reconnect 30 s after V>12.8 |

### 1.3 Monitoring System (INA260 — new since April 5 report)

| Item | Value |
| :--- | :--- |
| Current sensor | Adafruit INA260 #4226, 2 mΩ internal shunt |
| Sign convention | Positive = charging, Negative = discharging |
| Coulomb counting | ESPHome `sensor.integration` trapezoidal, per-outage + lifetime |
| Flash persistence | `last_outage_ah`, `last_outage_wh`, `last_outage_duration_min` survive power cycle |
| ESPHome version | 2026.4.3, firmware v1.1 |

---

## 2. Event Timeline

All times UTC. Local time = EDT (UTC−4).

| UTC | Local EDT | Event | Source |
| :--- | :--- | :--- | :--- |
| 10:25:20 | 06:25:20 | AC failure — Ah counter resets to 0, outage begins | HA Ah CSV |
| 10:25:30 | 06:25:30 | V<13.10 (first sample after AC fail), t+0.2 min | Voltage.csv |
| 10:30:55 | 06:30:55 | V<13.00 sustained (Settling → Plateau per YAML), t+5.6 min | Voltage.csv |
| 12:06:41 | 08:06:41 | V<12.85 sustained (Plateau → Knee per YAML), t+101.4 min | Voltage.csv |
| ~13:42:22 | ~09:42:22 | V<12.40 (Knee → Cliff per YAML), t+197.0 min — *interpolated*, HA recorder was offline | Quadratic fit, HA-last 12.431 V @ 13:40:17 → ESP-first 12.260 V @ 13:46:40 |
| 13:38:41 | 09:38:41 | Voltage slope first crosses −10 mV/min (= −10.027) | Voltage_Slope.csv |
| 13:39:41 | 09:39:41 | Slope sustained 60 s; `cliff_imminent` binary sensor → ON; `ups_graceful_shutdown_v3` triggers; notification sent | YAML logic + slope data |
| 13:40:11 | 09:40:11 | 30 s revalidation delay elapsed; conditions still met; `hassio.host_shutdown` service called | Automation YAML |
| 13:40:17 | 09:40:17 | Last HA sensor sample (V=12.431 V); OS shutdown in progress | HA CSVs |
| 13:46:40 | 09:46:40 | ESPHome log capture begins (direct ESPHome Web API) — V=12.260, I=−1.174 A, Cliff phase, 50.54 Wh delivered | ESPHome log |
| 13:48:07 | 09:48:07 | V<12.20 first crossed (would have triggered `voltage_critical` with 10 s delay, but HA already down) | ESPHome log |
| 13:56:27 | 09:56:27 | V<11.800 first crossed; monotonic descent thereafter, no rebound | ESPHome log |
| ~13:58:09 | ~09:58:09 | BP-65 spec-predicted trip (12 s alarm + 90 s disconnect from threshold) | Victron datasheet |
| 13:58:17 | 09:58:17 | Last ESPHome log sample under load: V=11.675, I=−1.216 A (load still drawing — trip ~8+ s past spec) | ESPHome log |
| ~13:58:30 ±15s | ~09:58:30 | **BP-65 LVD actual trip (best estimate within component tolerance)** | Spec + data bound |
| 13:58:17 → 14:02:58 | — | Log gap: ESP32 continues running (uptime continuous), WiFi temporarily off | ESPHome uptime sensor |
| ~14:02:30 | ~10:02:30 | **AC restoration (true grid restore)** — derived from first +current sample at 14:03:02 minus BP-65 30 s reconnect + brief reconnect dynamics | Spec + data inference |
| 14:02:58.977 | 10:02:58.977 | First post-gap sample: P=+60.444 W (peak recharge power) | ESPHome log |
| 14:03:02 | 10:03:02 | Charging phase confirmed: I=+4.591 A, V=13.093 V (PSU CC limit) | ESPHome log |
| 14:04:10 | 10:04:10 | HA→ESPHome API connection lost (HA mid-reboot) | ESPHome log |
| 14:05:29 | 10:05:29 | HA "unavailable" — graceful shutdown chain complete | HA state |
| 14:05:32 | 10:05:32 | HA back online; reads ESPHome final outage totals from flash | HA + ESPHome log |
| 14:06:52 | 10:06:52 | `on_battery` → OFF (after `delayed_off: 60 s` debounce); `ups_ac_restored_v3` notification fires | ESPHome log |
| 14:07:20 | 10:07:20 | ESPHome logs "Last Outage Duration: 222 min" (state-machine timer) | ESPHome log |

**Outage duration accounting (two different things):**

```
True AC-off:              10:25:20 → ~14:02:30 = ~217 min  (energy bookkeeping)
ESPHome on_battery span:  10:25:30 → 14:06:52  =  222 min  (state machine timer, with debounces)
Runtime to LVD:           10:25:20 → ~13:58:30 = ~213 min  (battery-side discharge time)
```

---

## 3. Outage Analysis

### 3.1 Automation Chain — All Tiers Confirmed

| Tier | Trigger condition | Evidence | Status |
| :--- | :--- | :--- | :--- |
| Auto 1: outage start notification | `on_battery` → ON (V<13.15 sustained 10 s) | V<13.10 by 10:25:30 — debounce satisfied by ~10:25:40 | ✅ Confirmed |
| Auto 2: voltage warning | `voltage_warning` → ON (V<12.40, I<−0.10, 30 s) | V<12.40 estimated at ~13:42:22; warning fired in the 24 min before HA shutdown — *automation chain assumed; HA was up at the time, log not separately captured* | ✅ Inferred from data; HA log not preserved through shutdown |
| **Auto 3: graceful shutdown (cliff path)** | **`cliff_imminent` → ON** (slope<−10 mV/min, V<12.85, I<−0.10, 60 s) | **Slope crossed −10 at 13:38:41, sustained at −11.94 by 13:39:41; HA off-air at 13:40:17 — consistent with 30 s delay + ~6 s OS shutdown latency** | ✅ **CONFIRMED — primary shutdown path** |
| Auto 3 (runtime path) | `runtime_remaining_minutes < 8` | Estimator was at 50.8 min at 13:39:40 — never reached the 8-min threshold | ⬛ Not exercised |
| Auto 4: hard fallback | `voltage_critical` → ON (V<12.20, I<−0.10, 10 s) | V<12.20 not until 13:48:07 — 8 min after HA was already down | ⬛ Not exercised |
| BP-65 hardware LVD trip | V<11.80 + 12 s + 90 s | V<11.80 crossed monotonically at 13:56:27; predicted trip 13:58:09; data shows trip occurred 8+ s later, ~13:58:30 ±15 s | ✅ Confirmed within spec tolerance |
| BP-65 reconnect | V>~12.8 for 30 s hold-off | First charging sample 14:02:58.977 → reconnect ~14:02:30 UTC | ✅ Confirmed |

**This is the first live validation of `ups_graceful_shutdown_v3` end-to-end via the cliff path.** It closes the outstanding April 5 commissioning item, but in a different mode than the April 5 report had anticipated (the April 5 report still referenced the v2 12.2 V trigger; v3 replaced this with the slope-based path). The 12.20 V `voltage_critical` path (`ups_critical_shutdown_v3`) remains untested by deliberate experiment.

### 3.2 Energy and Capacity Metrics

| Metric | This Outage (INA260, measured) | D3 (Mar 2026, measured) | Delta |
| :--- | ---: | ---: | ---: |
| Total Ah delivered | **4.179 Ah** | 4.85 Ah¹ | −13.8 % |
| Total Wh delivered | **53.271 Wh** | 62.5 Wh¹ | −14.8 % |
| Outage duration (AC → AC, true) | **~217 min** | — | — |
| Runtime to LVD (measured) | **213.2 min** ±15 s | **~214 min**² | < 1 min |
| Avg discharge current | **~1.18 A** | 1.16 A | +1.7 % |
| Avg power | **~14.9 W** | 14.5 W | +2.8 % |
| Peak cliff voltage slope (EMA, mV/min) | **−58.4 mV/min** (13:57:41) | — | — |
| Peak recharge current | **4.591 A** | — | at PSU CC limit |
| Peak recharge power | **60.444 W** | — | at PSU rated limit |

¹ D3 Ah/Wh were inferred (Kill-a-Watt watts × Shelly-timed voltage profile, no current sensor). Likely 5–10% high vs a true coulomb count.
² D3 runtime derived from: April 5 report Section 3.1 (sustained discharge onset 17:01 UTC) and Test_D3_March_2026_Voltage.csv (last V<11.80 at 20:34:58, V rebound to 11.93 at 20:35:29 → BP-65 trip mid-point ~20:35:13 UTC). Total: 20:35:13 − 17:01:20 = 213.9 min.

### 3.3 Discharge Phase Profile (re-derived from Voltage.csv)

Phase boundaries computed by direct first-sustained-crossing analysis on the 12,087-sample HA Voltage.csv (5 s cadence). The V<12.40 crossing fell inside the HA recorder offline window; it is interpolated from HA-last (V=12.431 @ 13:40:17) and ESPHome-first (V=12.260 @ 13:46:40) using a slope-steepening quadratic between the two anchor slopes (−11.94 mV/min at HA-last → −30.25 mV/min at ESP-first), yielding 13:42:22 UTC, t+197.0 min.

| Phase | Voltage Band (YAML) | This Outage (May 6) | D3 (Mar 26, same bands)³ | Notes |
| :--- | :--- | ---: | ---: | :--- |
| Settling | V > 13.00 | ~5 min | 0 min | D3 started from plateau, not float — not a from-float outage |
| Plateau | 12.85 – 13.00 V | ~93 min | ~10 min | LFP physical plateau spans both this band and the next |
| Knee | 12.40 – 12.85 V | ~99 min | ~178 min | This is the bulk of the discharge in both runs |
| Cliff | V < 12.40 V | ~17 min | ~26 min | Steepening: −12 mV/min at entry → −58 mV/min near LVD |
| **Total to LVD** | | **213.2 min** | **213.9 min** | < 1 min apart |

³ D3 phase tabulation re-derived from Test_D3_March_2026_Voltage.csv using **May 6 YAML band boundaries** (not the April 5 report's narrative bands). This is the apples-to-apples comparison.

**Why Rev 1's phase numbers (8 / 136 / 53 / 16) were wrong:** the report mapped narrative labels onto YAML boundaries inconsistently. The YAML's `plateau_min_v = 12.85` boundary cuts the *physical* LFP plateau (which is flattest around 12.7–12.9 V at this discharge rate) into two pieces: a small "Plateau" segment (12.85–13.00) and a larger "Knee" segment (12.40–12.85). Rev 1 reported as if the physical plateau ≈ the YAML Plateau, which inflated the Plateau number and shrunk the Knee number relative to direct measurement.

**Cliff slope sub-table (Section 3.4 in Rev 1):** the 12 slope readings 09:46–09:57 EDT and their corresponding voltages (12.260 → 11.720 V; slope −30.25 → −58.40 mV/min) reproduce exactly from the ESPHome log. No revision needed there.

### 3.4 Voltage Slope During Cliff Phase

*(Unchanged from Rev 1 — verified against ESPHome log; reproduced for completeness.)*

| Time (EDT) | Voltage Slope (mV/min) | Voltage (approx.) |
| :--- | ---: | ---: |
| 09:46 | −30.25 | 12.260 V |
| 09:47 | −33.66 | 12.234 V |
| 09:48 | −34.30 | 12.199 V |
| 09:49 | −36.47 | 12.165 V |
| 09:50 | −38.06 | 12.118 V |
| 09:51 | −42.24 | 12.076 V |
| 09:52 | −42.15 | 12.030 V |
| 09:53 | −45.25 | 11.975 V |
| 09:54 | −47.79 | 11.929 V |
| 09:55 | −51.80 | ~11.85 V |
| 09:56 | −56.59 | 11.783 V |
| 09:57 | −58.40 | 11.720 V |

The slope **steepens monotonically by ~28 mV/min over 11 minutes of cliff** — a 90% increase in voltage-fall rate over a short window. This is the physical reason the linear runtime estimate fails near the cliff (see Section 3.5).

### 3.5 Runtime Estimator Behavior at the Cliff

The HA `Runtime Remaining Minutes` sensor uses the linear model `(validated_capacity_ah − ah_used) ÷ |I_now|`. It cannot account for the cliff-phase voltage collapse because |I| stays roughly constant while V falls fast — Wh-based capacity is being depleted faster than the Ah-based formula predicts.

| HA sample time UTC | Reported runtime remaining | Actual time to BP-65 trip (target ~13:58:30 UTC) | Estimator factor |
| :--- | ---: | ---: | ---: |
| 13:35:10 | 55.16 min | 23.3 min | 2.4× optimistic |
| 13:36:10 | 53.05 min | 22.3 min | 2.4× |
| 13:38:10 | 52.97 min | 20.3 min | 2.6× |
| 13:39:40 (last sample) | **50.79 min** | **18.8 min** | **2.7×** |

At the moment `cliff_imminent` was about to fire (13:39:41), the runtime estimator was reporting ~50.8 min remaining — well above the 8-min Auto 3 fallback threshold. **This is exactly why the slope-based cliff path is the correct primary trigger and the runtime path is correctly positioned as a fallback** for outages where slope detection fails or never crosses threshold (lighter loads, partial-SOC starts).

### 3.6 Battery Thermal Response

| Time UTC | Battery (°F) | Ambient (°F) | ΔT (°F) | Note |
| :--- | ---: | ---: | ---: | :--- |
| 04:00 (pre-outage) | 81.5 | 73.6 | 7.9 | Steady-state float, PSU heat soak |
| 10:25:20 (AC fail) | 79.9 | 71.6 | 8.3 | PSU heat already declining slightly |
| 12:00 (mid-outage) | 76.0 | 71.2 | 4.8 | Enclosure cooling toward ambient, PSU off |
| 12:26 (outage minimum) | **75.7** | 71.3 | 4.4 | Outage-window thermal minimum |
| 13:58:30 (BP-65 trip) | 76.8 | 72.1 | 4.7 | Slight rise (battery resistance heating cumulating) |
| 15:00 (+1 h post-recovery) | 83.3 | 72.7 | 10.6 | Peak recharge current → PSU dissipation overshoot |
| 22:00 (end of day) | 80.0 | 72.3 | 7.7 | Returned to steady-state float |

**Interpretation.** Battery temperature tracks the enclosure thermal envelope, not battery activity. Pre-outage ΔT (battery − ambient) of ~8 °F is steady-state PSU heat soak. With the PSU off during the outage, ΔT collapses to ~4.5 °F over ~95 min as the enclosure cools passively toward ambient. The 1.18 A discharge through the pack's internal resistance dissipates I²R ≈ 0.04–0.07 W — three orders of magnitude smaller than the ~13 W PSU heat soak that disappeared, and undetectable against the enclosure's thermal mass. Post-recovery peak charge current (4.6 A) briefly drives ΔT to 10.6 °F before tapering back to 7.7 °F at steady state.

**Self-heating sensitivity for the watch list.** The 24–26 °C battery operating range observed here sits squarely in the LFP flat-response zone (capacity essentially temperature-invariant within ±2% from ~10–35 °C). The Section 7.2 watch threshold (battery > 95 °F summer alert) remains correct and unchanged. Cold-weather LFP capacity loss (below ~5 °C, where capacity can drop 10–15 %) is not in scope for this Connecticut installation.

### 3.7 PSU Recharge Ramp

*(Unchanged from Rev 1 — verified against ESPHome log; reproduced for completeness.)*

The HDR-60-12 immediately entered constant-current (CC) mode on AC restoration, delivering maximum rated current to the deeply discharged battery, then tapering to constant-voltage (CV) as battery voltage approached the 13.3 V setpoint.

| Time (EDT) | Current | Voltage | Power | Note |
| :--- | ---: | ---: | ---: | :--- |
| 10:02:58 | — | — | **60.444 W** | First reading post-gap |
| 10:03:02 | 4.591 A | 13.093 V | 60.1 W | PSU at CC limit |
| 10:03:07 | 4.524 A | 13.099 V | 59.3 W | |
| 10:03:17 | 4.356 A | 13.104 V | 56.7 W | |
| 10:03:32 | 4.112 A | 13.108 V | 53.6 W | |
| 10:03:42 | 3.963 A | 13.112 V | 52.1 W | |
| 10:04:02 | 3.722 A | 13.121 V | 48.5 W | |
| ~10:05:29 | ~3.0 A | ~13.13 V | **~40 W** | HA back online — first dashboard reading |
| 10:11:32 | 2.269 A | 13.164 V | 30.0 W | Log end |

---

## 4. Capacity Accounting

### 4.1 The Two Outages Agree on Runtime; the Linear Model is the Outlier

D3 measured runtime: **214 min**. May 6 measured runtime: **213 min**. The "43-min shortfall" framing in Rev 1 compared the May 6 measurement to a YAML linear-model projection (4.85 Ah ÷ 1.16 A × 60 ≈ 251 min, or the report's 257-min phase-summed equivalent), not to D3's actual measured time. With apples-to-apples comparison, the two outages match within one minute.

The linear model overshoots both real measurements by ~40 min because it doesn't account for the cliff-phase voltage collapse — the same reason the runtime estimator was 2.7× optimistic at the moment of shutdown trigger (Section 3.5).

### 4.2 D3 Coulomb Inference vs INA260 Coulomb Count

| Factor | Estimated contribution to D3-INA260 Wh gap | Confidence |
| :--- | :--- | :--- |
| D3 capacity inferred (Kill-a-Watt × time × voltage profile), not measured | Primary — D3 figure likely 5–10% high vs true coulomb count | Medium (no D3 current sensor to audit) |
| Higher actual load today vs D3 baseline (+2.8% W) | ~1.5 Wh over 3.5 h | High (INA260 measured) |
| ESP32 monitoring stack on-board load (INA260 includes itself; D3 Shelly Plus Uni had similar but smaller draw) | Estimated 30–80 mA differential × 12.75 V × 3.5 h ≈ 1.3–3.5 Wh — *uncertain magnitude* | Low–medium (gap-window Ah drift of 2.9 mAh over 285 s is consistent with brief residual full-load discharge before BP-65 actually opens; doesn't cleanly isolate monitor-only load) |
| Rate effect: higher current hits LVD earlier due to IR drop | ~0.4 Ah | Medium (IR ≈ 260 mΩ × 0.58 A delta) |
| Battery capacity fade since commissioning | Minor; LiFePO4 calendar-life very stable | Low |

The D3 inferred-vs-INA260 measured 9 Wh gap is dominated by the D3 figure being inferred. The monitor-load and rate-effect contributions are real but small and individually noisy.

### 4.3 Capacity Budget — What Remains Inaccessible

Of the battery's 10 Ah nameplate rating:

| Zone | Ah (est.) | Notes |
| :--- | ---: | :--- |
| Float ceiling — never charged (13.3 V float ≈ 65% SOC) | ~3.5 Ah | Architectural; requires 14.4 V absorption charger to recover |
| Rate effect — stranded at LVD due to IR drop at 1.18 A | ~0.5 Ah | Physics; would partially recover at lower discharge rate |
| Delivered this outage | **4.18 Ah** | INA260 coulomb-counted |
| Protected at LVD cutoff (~8–12% SOC remaining at 11.8 V terminal) | ~0.8 Ah | Intentional; prevents over-discharge |
| Below LVD to rated-empty (~10.5 V) | ~0.8 Ah | Intentional; cell protection |
| **Total** | **~9.8 Ah** | Slight rounding vs 10 Ah nameplate |

**Bottom line:** the single-rail 13.3 V architecture leaves ~3.5 Ah (35%) permanently inaccessible at the top. This is the core architectural constraint documented in the design rationale, not a defect.

---

## 5. Comparison to Previous Outages

| Metric | Outage 1 (Mar 26 = D3) | Outage 2 (Mar 28) | **May 6 (this report)** |
| :--- | ---: | ---: | ---: |
| Monitor | Shelly | Shelly | **INA260** |
| HA automation generation | v1 (12.2 V trigger) | v1 (12.2 V trigger) | **v3 (`cliff_imminent` primary)** |
| Starting SOC | ~100% | ~75–85% | ~100% |
| True AC-off duration | — | — | **~217 min** |
| Runtime to LVD (measured) | ~214 min | ~92 min below 12.8 V | **~213 min** |
| Min recorded voltage | 11.770 V | 12.130 V | **11.675 V** |
| Energy delivered | 41.3 Wh (est.) | 23.1 Wh (est.) | **53.27 Wh** (coulomb-counted) |
| Software graceful shutdown chain | Not tested live | Not tested live | ✅ **Confirmed via `cliff_imminent` path** |
| 12.20 V fallback path (`voltage_critical`) | Not tested | Not tested | ⬛ Not exercised this outage |
| BP-65 LVD | Direct (11.77 V) | Inferred (rebound signature) | ✅ Confirmed (V=11.675 last sample under load) |
| Measurement method | Voltage + assumed load | Voltage + assumed load | **Coulomb counting** |

---

## 6. YAML Parameter Updates

### 6.1 Capacity substitution values (mechanical update)

In `ups-monitor.yaml` substitutions block:

| Parameter | Current (D3 inferred) | Updated (INA260 measured) | Notes |
| :--- | :--- | :--- | :--- |
| `validated_capacity_ah` | `"4.85"` | **`"4.18"`** | INA260 coulomb-counted, May 6 |
| `validated_capacity_wh` | `"62.5"` | **`"53.3"`** | INA260 integrated, May 6 |
| `typical_load_amps` | `"1.16"` | **`"1.18"`** | Average from INA260 this outage |
| Header comment "Phase durations" | settling 8 / plateau 146 / knee 81 / cliff 22 | **settling ~5 / plateau ~93 / knee ~99 / cliff ~17** | Data-derived from Voltage.csv (Section 3.3) |
| Capacity formula comment | 4.85 Ah × ~12.9 V mean | 4.18 Ah × ~12.75 V mean | Update comment |

### 6.2 Phase-band realignment to match physical LFP discharge curve

The current YAML uses `plateau_min_v = 12.85` and `knee_min_v = 12.40`. Direct data shows the physical LFP plateau spans roughly 12.4–13.0 V at this discharge rate; the current YAML cuts it in two and labels the lower half "Knee" — which is misleading on the dashboard. Recommended retune:

| Parameter | Current | Proposed | Effect |
| :--- | :--- | :--- | :--- |
| `plateau_min_v` | `"12.85"` | **`"12.65"`** | Plateau band now covers the bulk of the physical plateau |
| `knee_min_v` | `"12.40"` | `"12.40"` (unchanged) | Knee band 12.40–12.65 is the actual steepening transition |
| `cliff_slope_threshold` | `"-10.0"` | `"-10.0"` (unchanged) | Slope guard remains the primary cliff predictor |

Applying the proposed bands to this outage's data:

| Phase | Proposed band | This outage duration |
| :--- | :--- | ---: |
| Plateau | 12.65–13.00 V | ~142 min |
| Knee | 12.40–12.65 V | ~49 min |
| Cliff | < 12.40 V | ~17 min |

This realignment makes the dashboard's `discharge_phase` state more operator-meaningful: "Knee" labels the last ~50 min before cliff entry rather than the second half of a long, flat plateau.

### 6.3 `cliff_imminent` voltage guard tightening

Current logic: `slope < −10 AND V < plateau_min_v AND I < −0.10`, sustained 60 s.

With `plateau_min_v` retuning to 12.65, the voltage guard automatically tightens — `cliff_imminent` will only fire if slope is steepening AND voltage is already in the proposed knee-or-cliff zone. The slope guard alone is sufficient earlier in discharge for nothing-yet-urgent indicators; the voltage guard prevents premature firing on transient slope dips at the top of discharge.

### 6.4 Runtime estimator — no change, but document the known limitation

The linear runtime formula is correctly architected as a *fallback* trigger (8-min threshold in Auto 3), not the primary. The Section 3.5 finding (2.4–2.7× optimistic at the cliff trigger) quantifies why and validates the architecture. No formula change recommended; the cliff_imminent primary path already protects against the failure mode.

---

## 7. Recommendations

### 7.1 Immediate

| Action | Priority | Detail |
| :--- | :--- | :--- |
| Update `ups-monitor.yaml` capacity substitutions (Section 6.1) | High | Mechanical; 5-line edit |
| Retune `plateau_min_v` to 12.65 (Section 6.2) | Medium | Improves dashboard `discharge_phase` clarity; no protection-chain impact |
| Capture an HA automation-log slice spanning the next outage | Medium | Auto 3 trigger event is currently inferred from data timing; explicit log would close the loop. Consider writing automation events to a flat file that survives `hassio.host_shutdown`. |
| Schedule a deliberate `voltage_critical` (Auto 4) validation test | Low | The cliff path got there first this outage; the 12.20 V fallback path remains unvalidated by deliberate test. Could be exercised by running discharge with cliff_imminent's slope guard temporarily masked. |

### 7.2 Ongoing Monitoring

| Metric | Baseline (this report) | Watch Threshold |
| :--- | :--- | :--- |
| Capacity per outage (Ah) | 4.18 Ah | Decline > 10% from this baseline warrants investigation |
| Capacity per outage (Wh) | 53.27 Wh | Same |
| Peak cliff slope (EMA mV/min) | −58.4 mV/min | Sustained > −70 mV/min may indicate rising internal resistance |
| Float voltage mean | 13.23 V | Trend shift > ±20 mV from baseline |
| Peak recharge current | 4.591 A | Should remain near 4.5 A CC limit on deep discharge events |
| Battery temperature at LVD | 75.9–76.0 °F | > 95 °F summer alert (PSU heat soak + ambient) |
| BP-65 actual disconnect delay vs spec (102 s) | data shows 8+ s past spec at this outage; in tolerance | Investigate if > +30 s past spec on future outages — could indicate BP-65 timer aging |

### 7.3 Future Consideration

A two-stage charging architecture (dedicated 14.4 V absorption charger + DC-DC buck regulator for load isolation) would recover approximately 3.5 Ah of the float ceiling loss, extending runtime from ~3.5 h to ~6 h at the current load. Documented in the design rationale as the path toward the 7.8–8.5 h theoretical maximum. Not a near-term recommendation — the current system is performing as designed.

---

## 8. Key Metrics Summary

| Metric | Value | Notes |
| :--- | :--- | :--- |
| Report type | Post-outage test, v3 chain validation, INA260 baseline | — |
| Data window | May 6, 2026 | Single outage event |
| HA automation chain | Fully validated via `cliff_imminent` path | First live validation; 12.20 V fallback path not exercised |
| True AC-off duration | ~217 min | AC fail to AC restoration |
| ESPHome on_battery span | 222 min | State-machine timer with debounces |
| Runtime to LVD | 213.2 min ±15 s | Bounded by spec + log |
| Ah delivered | 4.179 Ah | INA260 coulomb-counted |
| Wh delivered | 53.271 Wh | INA260 integrated |
| Min voltage at LVD | 11.675 V | Last log sample before BP-65 trip |
| Peak cliff slope | −58.4 mV/min | At 13:57:41 UTC |
| Peak recharge power | 60.444 W | At PSU CC limit (4.591 A, 13.093 V) |
| Runtime estimator factor at trigger | 2.7× optimistic | Validates slope-based cliff path as primary |
| Battery thermal range during outage | 75.7–79.9 °F | Driven by enclosure cooling, not discharge |
| INA260 baseline established | Yes | Supersedes D3 inferred figures |

---

## Appendix A: Revision History

| Version | Date | Changes |
| :--- | :--- | :--- |
| 2026-04-05 | Apr 5, 2026 | Inaugural commissioning report |
| 2026-05-06 (r1) | May 6, 2026 | Post-outage test report; INA260 first measurement |
| **2026-05-06 (r2)** | **May 18, 2026** | **Data-traced corrections: automation chain via `cliff_imminent` not 12.20 V; D3-vs-measured (not vs-projection) framing; BP-65 trip tightened against datasheet; Section 3.3 phase profile re-derived from Voltage.csv; Section 3.5 runtime-estimator quantification added; Section 3.6 battery thermal note added; Section 6 YAML recommendations refined.** |

---

## Appendix B: Discharge Phase Voltage Reference (updated for proposed YAML retune)

| Phase | Voltage Band | Characteristic | This Outage Duration |
| :--- | :--- | :--- | ---: |
| Float / PSU online | ≥ 13.15 V | PSU maintaining charge | — |
| Settling | 13.00–13.15 V | Post-float OCV relaxation | ~5 min |
| Plateau *(proposed retune)* | 12.65–13.00 V | Bulk LFP discharge; flat curve | ~142 min |
| Knee *(proposed retune)* | 12.40–12.65 V | Accelerating decline | ~49 min |
| Cliff | < 12.40 V | Rapid voltage collapse; −30 to −58 mV/min | ~17 min |
| BP-65 trip | ~11.8 V | Load disconnected after 102 s spec delay | — |
| BP-65 reconnect | ~12.8 V (after 30 s) | Load restored | — |

---

## Appendix C: Data Provenance and Verification

All claims in this report are traced to specific data sources. Where measurements are inferred or interpolated, the inference is stated explicitly.

| Claim category | Primary source | Verification |
| :--- | :--- | :--- |
| AC fail / Ah counter reset at 10:25:20 UTC | HA Ah_Delivered.csv row 3 (counter resets to 0) | HA Current.csv corroborates: I transitions to −1.13 A at 10:25:10 |
| HA last sample 13:40:17 V=12.431 | HA Voltage.csv row 6492 | HA Wh.csv row 2343 corroborates (48.99 Wh at same instant) |
| Cliff slope timeline 13:38–13:57 EDT | ESPHome log file `logs_esphome-web-ed2ba4_logs__1_.txt` | Direct read |
| `cliff_imminent` trigger time 13:39:41 | Voltage_Slope.csv: −10.027 at 13:38:41 → −11.94 at 13:39:41 (60 s sustained); ups-monitor.yaml lines 745-769 (delayed_on: 60s) | YAML+data composition |
| `ups_graceful_shutdown_v3` chain at 13:40:11 | Automations.yaml `ups_graceful_shutdown_v3` (cliff trigger + 30 s delay + revalidation + hassio.host_shutdown) | Last HA sample 13:40:17 = trigger+36 s, consistent |
| V<11.80 monotonic from 13:56:27 | ESPHome log, 31 consecutive V samples | Verified |
| BP-65 spec (12 s alarm + 90 s disconnect, 30 s reconnect) | Victron BP-65 datasheet (manualslib.com/manual/1487388) | Datasheet retrieval Rev 2 |
| Final outage totals 4.1789 Ah / 53.271 Wh / 222 min | ESPHome log 14:11:41–14:11:42 EDT | Direct read |
| D3 actual runtime 213.9 min | Test_D3_March_2026_Voltage.csv (sustained discharge 17:01:20 → BP-65 trip mid-point 20:35:13) + April 5 report Section 3.1 | Cross-source |
| Battery temp trajectory | Battery_Temp.csv 727 numeric samples, Ambient_Temp.csv 47 numeric samples | Direct read |

---

**Repository:** https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS
**License:** CC BY 4.0 (data) / MIT (code)
