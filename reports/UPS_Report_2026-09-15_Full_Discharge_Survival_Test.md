# DIY LiFePO4 UPS: Technical Report
## Full Discharge to BP-65 LVD, First Survival-Mode Validation, Recharge — and a 42 % Capacity Shortfall

**Data through:** 2026-09-15 15:52 UTC (11:52 local) · **Version:** 2026-09-15-r3 · **Report series:** UPS-RPT
**Repository:** https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS
**Firmware under test:** `ups-monitor.yaml`, ESPHome 2026.8.2, project version 1.19, ESP32-C3
**Supersedes:** 2026-09-15-r1 (uncommitted draft). Every r1 finding this revision corrects is recorded at the site where the error was made rather than silently replaced, per R13.
**r3 (2026-09-16):** corrects four r2 errors found by querying the full InfluxDB history rather than the test-window exports: two open items that were never defects (`Last Onset Step Resistance` and `total_outages` both updated during this test, §8.2, §9.1); a fully-charged detector r2 said had never fired, which was ON before both load-matched runs (§4.5); and a publish-skew mechanism that is re-drawn every boot, not fixed (§7.2, §10.3). Each is recorded at its site, the superseded text struck through rather than removed. r3 also records firmware **V1.20** (deployed 2026-09-16), which closes Open Items 19–21 (§11).

Every numeric claim carries its basis inline: **[M]** measured, **[D]** derived arithmetic on [M] with the formula shown, **[I]** inferred and carrying its falsifier, **[S]** spec or prior document with its identifier. Ratios carry n and a test, or they are not written (R17). Any figure whose sampling cadence is slower than the quantity it describes is named as a bound on the instrument, not a property of the world (R18).

**Time base:** all times local (EDT, UTC−4) unless suffixed `Z`. The raw InfluxDB exports are in UTC; the ESPHome and ad hoc monitor logs are in local time.

---

## Abstract

A deliberate outage test (`switch.ups_outlet` OFF at 09:16:58) ran the pack through its full documented ladder — Settling (absent at this current, §3.1), Plateau, Knee, Cliff — to the Victron BP-65 hardware LVD, the first time this system has been run to a genuine hardware cutoff rather than stopped early. Survival sleep, never previously exercised, ran 5 confirmed cycles and exited cleanly. The system recovered without intervention.

**The finding that matters is not the ladder; it is the capacity.** The pack delivered **2.5331 Ah / 31.821 Wh** [M, firmware coulomb counter, cross-validated against an independent HA-side integration to +0.95 %, §4.1]. Against the 2026-08-31/09-01 test — **same load, same voltage span, fourteen days earlier** — this pack delivered **−42.4 % Ah and −42.5 % Wh** [D, §4.3]. Against the 2026-05-06 LVD run it is −39.4 % Ah / −40.3 % Wh. Every mechanical explanation available to this dataset — rate effect at the LVD endpoint (≤0.04 Ah), Peukert (would require an exponent of 2.40 against 1.01–1.05 for LiFePO4), float-ceiling droop (≤0.11 Ah), temperature (both runs inside the LFP flat zone) — accounts for **under 10 % of the LVD-to-LVD gap, and for none of the load-matched gap**. The residual is a property of the pack, not of the test. §4.5 ranks the candidate mechanisms. The pack is sealed — no balance taps, no BMS telemetry — so per-cell voltages are unavailable at any price, and §4.6 gives three non-invasive substitutes instead. One of them has already been run, on data that was in this repository the whole time, and it argues against uniform capacity fade and for a non-uniform pack.

Two secondary results are load-bearing for how this system is specified. First, **the recharge is PSU-current-limited, not pack-limited**: the Mean Well HDR-60-12 is a **54 W / 4.5 A** supply [S, datasheet; confirmed by owner 2026-09-15], and the firmware's captured peak of **4.4465 A** is **98.8 %** of its rated current. Charge power into the battery branch alone reached **~50.9 W** [M] — 94 % of the whole supply's nameplate — before any share for the XB7, host or monitor. A Kasa AC-side measurement (§7.4) closes the power-flow loop against the DC-side INA260 and shows the supply operating within rating everywhere it has coverage. Second, **the raw InfluxDB export covers only the first 37.5 minutes of a ~90-minute discharge** and contains three bit-identical stale samples on recorder restart (§10); anyone re-deriving these figures needs both facts before opening the files.

A third result concerns the shutdown trigger itself. Replaying the firmware against **both** this outage and the 2026-09-01 test shows its slope term carries noise of sd 18.7–24.0 mV/min against a −10 mV/min threshold, crossing that threshold 21 and 12 times respectively, and that **every graceful-shutdown attempt in the record has aborted at least once before succeeding** (§6.1). The cause is arithmetic — `delayed_on: 60s` against a 60 s slope update is one extra sample of confirmation — and §6.1.1 gives the one-line change the data supports.

On the timing question this test was run to answer: from the moment the host went down to the moment BP-65 tripped was **~52.8 minutes** [M], entirely unsupervised. That margin is real, but §6 sets out why it cannot be converted into a threshold change from this test alone — and §4 adds a second reason, which is that the margin was measured on a pack whose usable capacity is changing month to month.

---

## 1. Test Summary

| Event | Local | UTC | V | I | Source |
| :--- | :--- | :--- | ---: | ---: | :--- |
| Last clean float sample | 09:16:55.6 | 13:16:55.6 | 13.2047 | +0.017 A | InfluxDB |
| `switch.ups_outlet` OFF (test start) | 09:16:58 | 13:16:58 | — | — | HA |
| First loaded sample | 09:17:00.6 | 13:17:00.6 | 13.0340 | −1.8725 A | InfluxDB |
| `on_battery` ON | 09:17:10 | 13:17:10 | 12.9548 | −1.94 A | firmware |
| Poller baseline | 09:34:14 | 13:34:14 | 12.692 | −2.066 A | `ha_poller_log` |
| Phase Plateau → Knee | 09:41:48 | 13:41:48 | 12.649 | — | firmware |
| `cliff_imminent` 1st trigger (aborted in the 30 s revalidation window) | 09:44:47 | 13:44:47 | ~12.66 | — | HA |
| `cliff_imminent` 2nd trigger (held) | 09:53:51 | 13:53:51 | 12.532 | −2.03 A | HA |
| **InfluxDB last write — HA recorder stops** | **09:54:30.6** | **13:54:30.6** | 12.5302 | −1.9647 A | InfluxDB |
| HA API begins refusing connections | 09:54:53 | 13:54:53 | — | — | poller |
| ICMP first DOWN (one false recovery follows at 09:55:41) | 09:55:37 | 13:55:37 | — | — | net_watch |
| ICMP sustained DOWN | 09:55:52 | 13:55:52 | — | — | net_watch |
| ESPHome continuous log capture begins | 10:04:58 | 14:04:58 | — | — | ESPHome |
| Direct ESP32 API monitor connects | 10:06:31 | 14:06:31 | 12.5673 | −1.4330 A | direct API |
| Corrected net_watch restarts; confirms HA down | 10:09:30 | 14:09:30 | — | — | net_watch |
| Phase Knee → Cliff | 10:32:50 | 14:32:50 | 12.399 | −1.41 A | firmware |
| Voltage Warning (12.40 V) | 10:33:26 | 14:33:26 | 12.385 | — | firmware |
| Voltage Critical (12.20 V) | 10:38:56 | 14:38:56 | 12.199 | — | firmware |
| LVD Imminent (internal flag) | 10:44:06 | 14:44:06 | 11.897 | — | firmware |
| Last sample **≥** 11.800 V | 10:45:31 | 14:45:31 | 11.802 | — | direct API |
| First sample **<** 11.800 V | 10:45:36 | 14:45:36 | 11.791 | −1.46 A | direct API |
| Last telemetry of any kind | 10:47:07.7 | 14:47:07.7 | 11.675 | −1.4622 A | ESPHome |
| **BP-65 LVD trip** — XB7 ICMP down | **10:47:18** | **14:47:18** | — | — | net_watch |
| ESP32 ICMP down | 10:47:20 | 14:47:20 | — | — | net_watch |
| Survival mode: 5 sleep/wake cycles (§5) | 10:47:18 – 11:00:09 | — | 11.9275 → 11.9762 | ~0 A | firmware NVS |
| **AC restored (bounded, not observed)** | **~10:57:2x – 10:59:2x** | — | — | — | [I], §7.1 |
| XB7 + HA host ICMP return | 10:59:49 | 14:59:49 | — | — | net_watch |
| First ESP32 reading after wake | 11:00:09.98 | 15:00:09.98 | 13.047 | — | ESPHome |
| **Charge current first observed** | **11:00:13.67** | **15:00:13.67** | 13.047 | **+3.8975 A** (published P 54.627 W is skew-corrupted — use V×I = **50.86 W**, §7.2) | ESPHome |
| Phase → Charging | 11:00:19 | 15:00:19 | 13.049 | +3.8516 A | firmware |
| Xfinity Modem Online | 11:00:24 | 15:00:24 | — | — | firmware |
| ESP32 boot confirmed successful | 11:00:47.9 | 15:00:47.9 | — | — | `safe_mode:154` |
| HA API returns 200 | 11:01:19 | 15:01:19 | — | — | poller |
| InfluxDB stale-restore sample (§10.2) | 11:01:24.73 | 15:01:24.73 | *12.5302* | *−1.9647 A* | **artifact** |
| InfluxDB first true post-recovery sample | 11:01:25.27 | 15:01:25.27 | 13.0753 | +3.1862 A | InfluxDB |
| `on_battery` clears (V re-crosses 13.15 V) | 11:39:39 | 15:39:39 | 13.1555 | +1.13 A | firmware |
| `Last Recharge Peak Current` populates | 11:39:52 | 15:39:52 | — | 4.4465 A | firmware |
| Report data cutoff | 11:52:03 | 15:52:03 | 13.160 | +0.792 A | direct API |

**Outage duration.** `on_battery` ON → OFF = **2 h 22 m 29 s** [M]. This is a flag duration, not an AC-off duration: recovery occurred ~39 minutes earlier and the flag correctly stayed ON until bulk-charge current lifted the bus back over its own 13.15 V threshold (§9.1). **Discharge duration** (onset → LVD trip) = **1 h 30 m 08 s** [M, 09:17:10 → 10:47:18]. Use the second figure for all capacity and runtime work.

**On the phase log.** The ESPHome capture contains 240 `ups.phase` lines [M]; the handler re-logs the current phase periodically rather than only on transition, so a `Phase -> Cliff` line at 10:47:05 is a re-log, not a second transition. Transition times in this table are the first occurrence of each phase string.

---

## 2. What This Report Establishes, and What It Does Not

Stated up front so no reader has to reconstruct it from the body (R11).

**Established [M]:**
- Charge and energy delivered to a hardware LVD trip, on two independent integration paths agreeing to +0.95 %.
- A capacity shortfall against two prior runs, one of which is load- and span-matched.
- The BP-65 trip delay, bounded to 90–109 s against a documented ~102 s.
- Survival-mode cycle count, wake voltages and exit path, from NVS.
- Peak *observed* charge current and charge power, and their relation to the PSU nameplate.
- The unsupervised interval between host-down and LVD, on a non-ping anchor.
- That the shutdown trigger's slope term is noise-dominated, and that every shutdown attempt in the record aborted at least once before succeeding — both at n = 2 (§6.1).

**Not established:**
- **Why** capacity fell. §4.5 gives ranked candidates and §4.6 narrows them; none is confirmed. The decisive test is Open Item 14a, a matched-load repeat.
- The true peak recharge current. AC return was observed by nothing (§7.1); 4.4465 A is a **lower bound**.
- Pack state of charge at test start. ~~No instrument on this system confirms a completed charge (§4.5) — "started full" is [I], not [M], and always has been.~~ **r3:** the fully-charged detector was ON for 3 h 51 m before this test's cut, and ON before the 08-31 comparison run too [M] — both began at the same float equilibrium. That is not a state-of-charge measurement, and the May reference predates the detector (§4.5 candidate 3).
- The margin at undiminished load. This outage's load fell mid-discharge because the shutdown fired (§6).
- ~~Root cause for `Last Onset Step Resistance` (Open Item 13) or `total_outages` (Open Item 9b).~~ **r3: neither was a defect** — both updated during this test (§8.2, §9.1).
- Whether the HDR-60-12 exceeded its nameplate or the load share was lower than modelled (§7.2, Open Item 17).

---

## 3. Discharge Curve — Full Ladder to LVD

The 2026-08-31 report §2.1 had measured only Plateau at the post-boost load and explicitly flagged Knee as extrapolated and Cliff as "not measured". This test closes that.

| Phase | Band | Interval timed | Duration | Avg. current |
| :--- | :---: | :--- | ---: | ---: |
| Settling | 13.00 – 13.15 V | — | **absent, < 5 s** [M] | ~1.9 A |
| Plateau | 12.65 – 13.00 V | 09:17:10 → 09:41:48 | 24 m 38 s | ~2.05 A [M] |
| Knee, HA running | 12.65 → ~12.61 V | 09:41:48 → 09:55:52 | 14 m 04 s | ~2.0 A [M] |
| Knee, HA down | ~12.61 → 12.40 V | 09:55:52 → 10:32:50 | 36 m 58 s | **~1.40 A** [M] |
| Cliff | 12.40 → 11.675 V | 10:32:50 → 10:47:18 | **14 m 28 s** [M] | 1.375 → 1.476 A |
| **Onset → LVD trip** | 12.955 → 11.675 V | 09:17:10 → 10:47:18 | **1 h 30 m 08 s** | 1.686 A mean [D] |

> **Correction to r1 (R13).** The r1 phase table labelled the Cliff band "12.40 – 11.80 V" but quoted 14 m 30 s, which is the interval to the **LVD trip** — 104 s past the 11.80 V crossing the label names. The band as labelled took 12 m 46 s [M]. The same construction inflated the r1 "Knee start to LVD" row. Both rows above now name the interval actually timed. A band and an interval are different quantities, and a phase table must not silently swap them.

**Two load regimes in one outage.** The graceful shutdown fired in mid-Knee, so this discharge ran at a *falling* load: ~2.05 A while HA was up, ~1.40 A for the remaining ~51 minutes. This is a materially different shape from the 05-06 run (constant ~1.18 A) and the 08-31/09-01 run (constant ~2.09 A). No phase duration from this test transfers to a constant-load scenario.

### 3.1 Settling — retrieved from InfluxDB, and there wasn't one

| Time (UTC) | V | I | Note |
| :--- | ---: | ---: | :--- |
| 13:16:55.57 | 13.2047 | +0.017 A | last clean float sample |
| 13:16:58 | — | — | `switch.ups_outlet` OFF |
| 13:17:00.64 | 13.0340 | −1.8725 A (13:17:01.88) | already below both the 13.15 V trip and the 13.00 V Settling floor |
| 13:17:05.57 | 12.9657 | −1.8930 A | |
| 13:17:10.64 | 12.9548 | −1.9367 A | `on_battery` ON |

At ~1.9 A onset, V fell from float through both the 13.15 V trip and the 13.00 V Settling/Plateau boundary **inside one 5 s InfluxDB sampling interval**. By the time `on_battery` registered, V was already 195 mV into Plateau.

**R18 bounds the claim.** The instrument samples at 5 s; the transition completed in under 5 s. This dataset establishes that Settling is *shorter than 5 s at this current* — it does not establish that Settling does not exist. Reporting "no Settling phase" as a property of the pack would be reporting the sampler's blind spot. The 08-31/09-01 tests saw the same thing at higher current; this test shows it also at lower current, which says the collapse is not purely a function of load magnitude across the range tested so far. Resolving it needs a faster capture than any instrument on this system provides.

### 3.2 Cliff current rise — constant-power is the best-supported model, and is not proven

r1 asserted the rising Cliff current was "consistent with the XB7's own switching supply drawing roughly constant power". Tested against the 14 Cliff-phase heartbeats [M]:

| Quantity | Result |
| :--- | :--- |
| V across Cliff | 12.391 → 11.730 (−661 mV, −5.34 %) |
| I across Cliff | 1.375 → 1.476 A (mean 1.4435, sd 0.0473, CV 3.27 %) |
| P across Cliff | 16.973 → 16.899 W (mean 17.444, sd 0.547, CV 3.13 %) |
| Fit dP/dV | +0.313 W/V, R² = 0.015, **t = +0.43**, n = 14 — indistinguishable from flat |
| Fit dI/dV | −0.0997 A/V, R² = 0.202, **t = −1.74**, n = 14, 95 % CI **[−0.225, +0.025]** |

Model predictions at the observed operating point: constant power gives dI/dV = −P/V² = **−0.119 A/V**; constant resistance gives +1/R = **+0.119 A/V**; constant current gives 0.

**Verdict.** The confidence interval **excludes constant resistance**, contains constant power (the point estimate sits essentially on it), and **cannot exclude constant current** at n = 14. Constant-power is the best-supported model and constant-resistance is ruled out, but this test does not establish the mechanism. r1 stated the mechanism without n or a test, which R17 does not permit.

---

## 4. Capacity — the principal finding

### 4.1 What was delivered, and how well it is known

| Quantity | This outage | Basis |
| :--- | ---: | :--- |
| Charge delivered | **2.5331 Ah** | [M] firmware coulomb counter, NVS |
| Energy delivered | **31.821 Wh** | [M] same |
| Mean discharge current | 1.686 A | [D] 2.5331 Ah ÷ 1.5022 h |
| Pack nameplate | 10 Ah | [S] Cyclenbatt 10 Ah LiFePO4 |
| Fraction of nameplate | **25.3 %** | [D] |

**The counter is trustworthy, and this is the first time that has been demonstrated rather than assumed.** Three independent checks:

1. **Two-path cross-check.** At 09:34:14 the HA poller captured the firmware's own counter at **0.5789 Ah** while HA's recorder was independently writing current to InfluxDB. Trapezoidal integration of the InfluxDB series over 09:17:00 → 09:34:14 (n = 206 samples) gives **0.5844 Ah** — a difference of **+5.5 mAh, +0.95 %** [D]. Two storage paths, two clocks, one sensor.
2. **Integrator arithmetic.** Over 10:06:36 → 10:46:28 (n = 41 heartbeats) the counter advanced 0.9409 Ah against 0.9410 Ah by trapezoid on its own published current — **+0.010 %**; Wh **−0.120 %** [D].
3. **The unobserved window closes.** No instrument covered 09:54:31 → 10:06:36 (§10.1). By difference against the counter, that 12.1-minute window must hold 0.2876 Ah → an implied mean of **1.428 A** [D]. The independently measured post-shutdown load is ~1.40 A. A 12-minute hole that nobody watched reconciles to the load measured on either side of it.

> **Correction to r1 (R13).** The r1 Abstract tagged this figure "[M, firmware-published and independently cross-checked]" while r1 §2.2 stated the agreement was "rather than an independent confirmation of either figure." The Abstract outranked its own section, which the project's verdict-vocabulary rule forbids. The cross-check above is the one r1 should have run; the data for it was already sitting in `ha_poller_log.txt`.

**Limit (R18).** All three checks share one sensor. They establish that the INA260's output is transported, integrated and stored correctly; they say nothing about its absolute accuracy. An absolute check needs a second current reference, which this system does not have.

### 4.2 The reference figure is a measurement, not a rating

The live dashboard carries 4.18 Ah / 53.3 Wh as "rated capacity". It is neither rated nor current: it is the **2026-05-06 coulomb count** [S, `UPS_Report_2026-05-06.md` §3.2], dated May on the dashboard. Every "% of capacity" figure this project has published since — including r1's headline "60.6 % of rated capacity" — is a ratio against one four-month-old measurement of the same pack.

That framing hid the finding. Restated against fixed references:

| Run | Ah delivered | % of 10 Ah nameplate | Load | Endpoint |
| :--- | ---: | ---: | ---: | :--- |
| 2026-05-06 | 4.179 | 41.8 % | ~1.18 A | BP-65 LVD |
| 2026-08-31/09-01 | 1.833 | 18.3 % | ~2.09 A | stopped at 12.565 V |
| **2026-09-15** | **2.5331** | **25.3 %** | 1.69 A mean | BP-65 LVD |

The May report's own §4.3 already establishes why none of these approaches the nameplate: the 13.3 V float ceiling leaves ~3.5 Ah permanently inaccessible at the top, and recovering it would need a 14.4 V absorption charger. That is architectural and documented. **It is not what changed between May and September.**

### 4.3 The load-matched, span-matched comparison

The 08-31/09-01 test ran fourteen days before this one, at essentially the same current, over a voltage span this test also traverses. That is the cleanest available comparison: no rate correction is required, because there is no material rate difference to correct.

| | 2026-08-31/09-01 | 2026-09-15 | Δ |
| :--- | ---: | ---: | ---: |
| Voltage span | 12.97 → 12.565 V | 13.034 → 12.546 V | matched |
| Mean current | 2.089 A | **2.043 A** [M] | −2.2 % |
| Elapsed | 54 min | **31.0 min** [M] | **−42.6 %** |
| Charge delivered | 1.833 Ah | **1.0559 Ah** [M, n = 371] | **−42.4 %** |
| Energy delivered | 23.369 Wh | **13.4394 Wh** [M] | **−42.5 %** |

**Ah and Wh agree to a tenth of a point.** That matters: a voltage-measurement fault would move Wh without moving Ah. Their agreement, combined with §4.1's two-path check, places the shortfall in the pack rather than in the instrument.

**Provenance: now [M], not [S] — Open Item 15 closed.** The 08-31/09-01 figures have been re-derived from the raw InfluxDB series for this revision: **1.8316 Ah / 23.316 Wh**, against the 08-31 report's 1.833 Ah / 23.369 Wh — **−0.1 % Ah, −0.2 % Wh**. The 2026-08-29 test re-derives the same way (**0.4731 Ah** against that report's 0.4745 Ah, **−0.3 %**). Both endpoints of this comparison are therefore measured, and the prior report's arithmetic is independently confirmed.

> **Warning for anyone re-running these queries — see §10.5.** The InfluxDB measurements `A`, `V` and `W` are **shared across every entity carrying that unit**: 19 entities in `A`, 24 in `V`, including the separate 500 Ah `battery_bank_monitor_*` pack and `ups_outlet_current`. An unfiltered query returns a mixture of them. Every figure above filters `entity_id`.

Against the LVD-to-LVD comparison with May: **−39.4 % Ah, −40.3 % Wh** over 4.3 months.

### 4.4 What does not explain it

Each candidate quantified against the ~1.65 Ah (LVD-to-LVD) and ~0.78 Ah (span-matched) gaps.

| Mechanism | Magnitude | Verdict |
| :--- | ---: | :--- |
| **Rate effect at the LVD endpoint.** The LVD terminates at a fixed *loaded* 11.80 V, so higher current terminates at higher OCV. ΔI vs May at the Cliff = 0.28 A; Ri spans 93–260 mΩ across every method available (§8.3) → ΔV = 26–73 mV; local cliff slope **2.02 V/Ah** [M] | **0.013 – 0.036 Ah** | ≤ 2.2 % of the LVD gap |
| **Peukert.** Solving 4.179 / 2.5331 = (1.686 / 1.177)^(k−1) | requires **k = 2.40** [D] | LiFePO4 is 1.01–1.05; lead-acid ~1.25. Excluded |
| **Float-ceiling droop.** Pre-outage float 13.2047 V [M] vs 13.1970 V post-boost mean [M, 08-31 §1] — no material change. Charge-side slope near the ceiling ≈ 3.2 Ah/V [D, from 05-06 §4.3: 3.5 Ah between 13.3 V and 14.4 V] | **≤ 0.11 Ah** | ≤ 6.7 % |
| **Temperature.** 77.3–78.2 °F this run [M]; 75.7–81.5 °F in May [M, 05-06 §3.6] | ~0 | Both inside the LFP flat-response zone (±2 % from ~10–35 °C) |
| **Instrumentation change.** INA260 has been the sensor since before the May run [S, 05-06 §1]; the boost draws from the BP-65 load output, inside the measured path [M, owner-confirmed, 08-31 §3] | 0 | Measurement path unchanged |
| **Combined** | **≤ 0.16 Ah** | **≤ 9.7 % of the LVD gap; ~0 % of the load-matched gap** |

**The 08-31 report predicted this and is falsified by it.** Its §2 stated: *"Delivered Ah at 2.089 A is expected lower by ~0.13 Ah, 3 % of 4.18 Ah, which is not measured."* Measured now: −42.4 % at matched load. That prediction used a cliff slope of ~1.8 V/Ah; this test independently measures **2.02 V/Ah** [M], so the prediction's arithmetic was sound and its *premise* — that only the rate effect had changed — was wrong. Recorded here because this is where the falsifying measurement was made.

### 4.5 What might explain it — ranked, each with its falsifier

None of these is confirmed. All are **[I]**; per R15 none may justify a config or hardware change until the separating measurement exists.

1. **Cell imbalance or a single degraded cell (leading, and now supported by §4.6).** One cell reaching its knee early drags the 4S pack voltage to the 11.80 V LVD while three cells retain charge. This single mechanism explains all three observations at once: low delivered Ah; a pack-level end-of-discharge OCV of 11.9275 V [M] that *looks* like a balanced pack at ~2.98 V/cell but is equally consistent with one cell at ~2.35 V and three at ~3.19 V; and a charge that terminates early because the BMS stops on the highest cell — which is exactly what "I ≈ 0 A at 13.2047 V float" looks like from outside the pack.
   *Falsifier:* per-cell voltages at end of discharge — **not available on this pack.** The cells are sealed with no accessible balance taps or BMS telemetry [M, owner-confirmed 2026-09-15], so the direct test cannot be run without destroying the enclosure. §4.6 gives the non-invasive substitutes, one of which has already been run.
2. **Real capacity fade or a developing cell fault.** A 42 % loss in fourteen days and roughly two cycles is not calendar or cycle aging for LiFePO4 (rated >2000 cycles); it would indicate a cell defect in progress.
   *Falsifier:* a coulomb-counted charge to termination. If the pack accepts ~2.5 Ah and then tapers to zero, its usable window really is ~2.5 Ah.
3. **Incomplete charge at test start.** The pack is assumed to begin at its 13.3 V float ceiling (~65 % SOC [S, 05-06 §4.3]). **Nothing on this system measures that.** `binary_sensor.ups_monitor_battery_fully_charged` fires on V > 13.25 V with |I| < 0.10 A held 600 s, and has **never fired once in the entire InfluxDB record**, because the PSU has never floated that high [M, 08-31 §4.1]. "Started full" has therefore been [I] on every test this project has ever run, including the May reference.
   *Falsifier:* same as 2 — a coulomb-counted charge to termination, compared against the discharge count.
   > **Correction (r3, R13).** "Never fired once" was already false when r2 was written. V1.17, flashed 2026-08-31 19:26 EDT, lowered the detector's threshold from 13.25 V to the 13.15 V `on_battery` threshold, and it first fired at **19:37:30** that evening — its 600 s confirmation after that boot [M, InfluxDB `binary_sensor.ups_monitor_battery_fully_charged`, 350 points since 2026-07-12]. It was **ON immediately before both load-matched runs**: 08-31 19:37:30 → 20:05:50, one second before that test's onset, and 09-15 **05:25:31 → 09:17:00**, 3 h 51 m continuous, ending at this test's cut [M]. The 08-31 report §4.1 was right when written; r2 cited it without re-checking. *What this establishes:* both runs began with the PSU holding the bus above 13.15 V and battery current under 0.10 A for at least ten minutes — the same float equilibrium. *What it does not:* state of charge (this report's own basis puts the float ceiling near ~65 % SOC [S, 05-06 §4.3]), or anything about the May reference, which predates the detector. So candidate 3 in its simple form — the pack had not been recharged after 09-01 — is excluded [M]. What remains is that float equilibrium is not full, which applies to both runs equally and can explain a difference between them only if the equilibrium state itself moved — a property of the pack, not of the test.
4. ~~**The 08-31/09-01 reference figure is wrong.**~~ **Excluded.** Both endpoints have now been re-derived from the raw series and agree with the 08-31 report to −0.1 % Ah (§4.3). This candidate is closed, and with it Open Item 15.

**Charge-return evidence is suggestive but incomplete.** From the first true post-recovery sample to report cutoff (43.5 min), the pack accepted **1.1297 Ah** [M, trapz on InfluxDB, n = 519] against 2.5331 Ah removed. This *excludes* the highest-current part of bulk, which occurred before InfluxDB resumed (§10.1) and before the ESP32 woke (§7.1), so it is a lower bound and **44.6 % is not a meaningful completion figure**. At cutoff the bus was 13.160 V with 0.792 A still flowing and falling — charging was ongoing. Watching one recharge through to termination would discriminate candidates 2 and 3, and costs nothing but patience. Open Item 16.

### 4.6 Discriminating the mechanisms without opening the pack

The pack is sealed: no balance taps, no BMS telemetry [M, owner-confirmed 2026-09-15]. Per-cell voltages are therefore unavailable at any price short of destroying the enclosure, and the direct falsifier for §4.5 candidate 1 cannot be run. This section gives three substitutes that need only pack-terminal measurements. **The first has already been run, on data that was in this repository the whole time.**

**Test A — normalised OCV-vs-charge overlay. Run; result below.**

`data/Voltage.csv`, `data/Current.csv` and `data/Ah Delivered.csv` hold the complete 2026-05-06 discharge at 5 s cadence (n = 2,346 in-window, Ah counter reaching 4.1789). Building pack OCV (= V_loaded + |I| × Ri) against charge removed, and normalising each run against **its own** total delivered charge, separates the two mechanisms cleanly:

- **Uniform capacity fade** — every cell equally degraded — predicts the normalised curves **overlay**. Same voltage at the same *percentage* depth, just less absolute Ah.
- **One weak cell** predicts the September curve sits **below** May's at every depth, because the weak cell is lower than its siblings throughout, and predicts the gap **widens** as that cell approaches its knee.

| Depth (each run vs its own total) | May OCV | Sept OCV | Δ |
| ---: | ---: | ---: | ---: |
| 5 % | 13.084 V | 12.988 V | **−0.096 V** |
| 10 % | 13.071 V | 12.955 V | −0.116 V |
| 20 % | 13.065 V | 12.901 V | −0.164 V |
| 30 % | 13.040 V | 12.838 V | −0.201 V |
| 40 % | 12.991 V | 12.787 V | −0.204 V |
| 50 % | 12.940 V | 12.719 V | **−0.221 V** |
| 60 % | 12.862 V | 12.701 V | −0.161 V |
| 80 % | 12.684 V | 12.621 V | −0.064 V |
| 90 % | 12.591 V | 12.429 V | −0.161 V |
| 95 % | 12.543 V | 12.142 V | **−0.402 V** |

At matched **absolute** charge the gap widens monotonically: −134 mV at 0.25 Ah, −266 mV at 1.00 Ah, −327 mV at 2.00 Ah, −924 mV at 2.50 Ah.

**The result is robust to the Ri correction.** Because Δ = (V_sept − V_may) + (I_sept − I_may) × Ri and ΔI ≈ 0.77 A, the sensitivity is +0.77 V per ohm. Sweeping Ri across the entire measured family (§8.3):

| Ri used | Δ at 20 % | 30 % | 40 % | 50 % | 60 % |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 93 mΩ | −0.164 | −0.201 | −0.204 | −0.221 | −0.161 |
| 146 mΩ | −0.123 | −0.160 | −0.163 | −0.180 | −0.120 |
| 173 mΩ | −0.102 | −0.139 | −0.142 | −0.159 | −0.099 |
| 260 mΩ | −0.035 | −0.072 | −0.075 | −0.092 | −0.032 |

**September sits below May at matched depth for every Ri in the family, including the 260 mΩ upper outlier** — which is itself almost certainly too high, since the survival-wake step bounds ohmic Ri at ≤172.7 mΩ *including* two minutes of relaxation (§5). Uniform fade predicts 0.000 in every cell of that table.

**Reading, stated with its limit.** This is evidence *against* uniform capacity fade and *for* a non-uniform pack — one cell, or one cell group, sitting lower than its siblings. It is not proof, and it has one substantial confound: **the curve is anchored at "charge removed = 0", which assumes both runs started from the same state.** Nothing on this system verifies that (§4.5 candidate 3, Open Item 18). A September run that simply began at a lower SoC would shift the whole curve down and produce the same table. Tests B and C close exactly that confound. **r3:** for the 08-31 → 09-15 pair, the fully-charged detector now shows both began at the same float equilibrium [M, §4.5 candidate 3 correction]. Test A compares against **May**, which predates the detector, so for this overlay the confound stands as written.

**Test B — coulomb-count one recharge to termination (Open Item 16).** Leave the system on AC after the next outage and log until charge current stops falling. Charge accepted ≈ charge delivered (~2.5 Ah), then taper to near zero, means the pack's usable window really is ~2.5 Ah. Charge accepted materially *exceeding* the discharge count means the pack had not started full, and the reference comparisons in §4.3 are measuring starting SoC rather than capacity. Non-invasive, needs only patience, and it is the single most informative test available.

**Test C — repeat the discharge at May's current (Open Item 14a).** Shut the N100 host down *before* cutting AC, so the load is XB7 + monitor only (~1.2–1.4 A) rather than 2.089 A. That matches May's load within a few percent and removes every rate, IR and two-regime confound at once — the comparison becomes same pack, same load, same 11.80 V endpoint, same instrument. **If it still delivers ~2.5 Ah against May's 4.179 Ah, the loss is confirmed and no correction can be argued away.** This replaces the per-cell measurement as the decisive test.

### 4.7 Consequence for the design claim

The system's runtime claim rests on delivered capacity. At the post-boost load of 2.089 A the 08-31 projection was ~128 min to LVD [D, 08-31 §2]. **Measured here: 90.1 min** [M] — and that was with the load *falling* to 1.40 A for the last 51 minutes. Had the load held at 2.089 A throughout, the same 2.5331 Ah would have supported **~73 min** [D, 2.5331 Ah ÷ 2.089 A × 60] — a **43 % shortfall against projection**.

That is the operational meaning of §4. The graceful-shutdown ladder still fired correctly and the hardware backstop still held, but the time budget the ladder is tuned against has shrunk by about two-fifths, and **no instrument on this system would have reported it.** §6's margin finding must be read against that.

---

## 5. Survival Mode — First Validation

Survival sleep has existed in firmware since V1.6–V1.11 and had never been exercised by a real outage. Every prior outage either stayed above the trip point or was ended deliberately before LVD.

| Metric | Value | Source |
| :--- | ---: | :--- |
| Sleep/wake cycles completed | **5** | `Last Survival Cycles` [M, NVS] |
| Survival First Wake Voltage | 11.9275 V | [M] |
| Survival Min Wake Voltage | 11.9275 V (= first) | [M] |
| Survival Last Wake Voltage | 11.9762 V | [M] |
| Exit reason | `Recovery` | [M], with the caveat below |
| Blackout span, observed | ~12 m 51 s (10:47:18 → 11:00:09) | [M] |
| Per-cycle budget | 120 s sleep + up to 60 s awake | [S, `survival_sleep_interval_s`, `survival_run_duration`; live and public repo byte-identical] |

**Behaviour was as designed.** Min-wake never fell below first-wake — the pack rested unloaded throughout — and last-wake rose 48.7 mV above first-wake, consistent with LiFePO4 OCV relaxation once discharge stress is removed. Five cycles at a ~154 s observed mean against a ~180 s ceiling is consistent with wake windows shorter than the 60 s maximum.

**Caveat on `Exit Reason` (R18).** This field read `Recovery` **before** the test as well [M, ESPHome log 10:05:46, alongside `Last Survival Cycles` = 0 and all three wake voltages `nan`]. A value equal to the expected value is not evidence of a fresh write. Cycle count (0 → 5) and all three wake voltages (`nan` → populated) demonstrably did update, so the survival block ran; whether `Exit Reason` was rewritten or left stale cannot be distinguished from its value alone, and is not resolved here.

**Nothing is observable during survival mode, confirmed by two independent observers.** This session's direct-API monitor and the owner's separate continuous `esphome logs` capture show the same blackout to within seconds. This is structural rather than a coverage gap: survival-mode entry is the same event that takes the XB7 down, since both sit behind the BP-65 output. **No network observer can see this window without a second, independently powered receiver.** The NVS summary fields are the complete record, and they are intact.

**It also yields one genuinely new measurement.** First-wake voltage is an unloaded reading taken ~2 minutes after a known loaded reading at a known current — the only clean load-step this system produces. (11.9275 − 11.675) ÷ 1.4622 A = **172.7 mΩ** [D]. Because ~2 minutes of relaxation is included, this is an **upper bound** on ohmic Ri, not a step resistance. It sets the upper limit of the Ri range used in §4.4.

---

## 6. Shutdown-to-LVD Margin

| Interval | Duration | Basis |
| :--- | ---: | :--- |
| First (aborted) `cliff_imminent` → LVD | 1 h 2 m 31 s | 09:44:47 → 10:47:18 [M] |
| Second (held) `cliff_imminent` → LVD | 53 m 27 s | 09:53:51 → 10:47:18 [M] |
| **HA recorder stops → LVD** | **52 m 47 s** | 09:54:30.6 → 10:47:18 [M] |
| ICMP sustained-down → LVD | 51 m 26 s | 09:55:52 → 10:47:18 [M] |

**The anchor changed from r1 and is now non-ping.** InfluxDB's last write at 09:54:30.6 is an independent witness of HA going down, 75 s earlier than r1's ping-derived estimate. Three witnesses form a coherent three-stage shutdown — recorder stops 09:54:30.6, API refuses 09:54:53, ICMP ceases 09:55:52 — which is what an orderly HA core shutdown followed by an OS halt looks like.

> **Correction to r1 (R13).** r1 gave "HA host confirmed fully down (ICMP + TCP) ~09:55:45" and derived ~51 m 35 s. That timestamp came from the **uncorrected** reachability tool, which was still emitting false recoveries for another eleven minutes (§9.2); the corrected tool's first confirmation is 10:09:30. The margin figure was approximately right for the wrong reason, and is now anchored on evidence that does not depend on the buggy tool at all.

**At the post-shutdown load of ~1.40 A, the system ran ~52.8 minutes on the BP-65 hardware LVD as its only protection.** The trigger that fired — `cliff_imminent` — tripped at V ≈ 12.53–12.61 V, well inside Knee. Its condition is a composite of slope, dwell and a voltage *gate*; §6.1 shows the slope term is noise-dominated and the firing time effectively stochastic, so the trigger point should not be read as a measurement of pack state.

**Four reasons this is not yet a threshold recommendation:**

1. **n = 1**, and the first test ever to reach LVD on this hardware.
2. **The load dropped because the shutdown itself fired.** The margin was measured at the *reduced* load. Delaying the trigger changes the very quantity that produced the margin; a later trigger consumes capacity faster for as long as it stays armed. These are not independent variables.
3. **The trigger that fired is the noisiest of the three paths.** `cliff_imminent` bounced at least twice before holding (09:44:47 aborted, 09:53:51 held), driven by ordinary load-current IR sag — the same burst phenomenon that defeats the Apparent-Ri gate (§8.1) and that broke this session's own slope tool (§9.2). The `voltage_warning` (12.40 V) and runtime paths did not fire first here, but either could in a different load shape.
4. **§4 supersedes the arithmetic.** The margin is a time interval on a pack whose usable capacity fell 42 % in fourteen days. A threshold tuned to this margin is tuned to a moving quantity. **Capacity must be characterised and stabilised before any threshold moves.** This is now the gating dependency on Open Item 10, which it was not in r1.

**A false-alarm cost is already demonstrated.** The aborted trigger sent "Host shutting down in 30 s" to a phone ~62 minutes before LVD. Moving the trigger later without first addressing slope-bounce sensitivity would produce more of these.

---

### 6.1 The trigger is noise-dominated — replicated at n = 2

r1, and the first draft of this revision, described the shutdown trigger as "slope < −10 mV/min sustained 60 s while V < 12.65 V" and left it there. Reading `ups-monitor.yaml` and then replaying it against **two** runs shows that shorthand hides the actual behaviour.

**The condition, as deployed:**

```
cliff_imminent:  i <= -0.10 A            (confirmed discharging)
             AND v <  12.65 V            (plateau_min_v -- a GATE, not the trigger)
             AND slope_ema < -10.0 mV/min
             delayed_on: 60s, delayed_off: 30s

slope:  sampled every 60 s
        raw = (V_now - V_60s_ago) * 1000
        ema = 0.35*raw + 0.65*ema_prev
```

**The voltage is a gate, and it was not what was binding.** On 2026-09-15 the gate opened at 09:41:48 and the trigger did not hold until 09:53:51 — twelve minutes later. Whatever sets the firing time, it is not the voltage threshold.

**What sets it is slope noise.** Using the firmware's **own published** `voltage_slope` (InfluxDB measurement `mV/min`, entity `ups_monitor_voltage_slope`), over each run's discharge window:

| Run | n | sd | range | crossings of −10 mV/min |
| :--- | ---: | ---: | ---: | ---: |
| 2026-09-01 | 52 | 18.7 mV/min | −94.4 … +3.9 | **21** in 52 min |
| 2026-09-15 | 37 | 24.0 mV/min | −115.3 … −1.2 | **12** in 37 min |

**The noise standard deviation is roughly twice the threshold value on both runs.** The lambda's comment budgets for INA260 LSB noise of ±1.25 mV/min; observed noise is ~15–20× that, it is load-driven rather than ADC-driven, and that comment predates the boost putting the N100 on the bus.

**Consequence, confirmed on both runs** — from the `automation.ups_graceful_shutdown_cliff_or_8_min_runtime` trace records:

```
2026-09-01   fired 00:55:32Z -> aborted 00:56:02Z (30 s)  -> fired again 00:57:32Z
2026-09-15   fired 13:44:47Z -> aborted 13:45:18Z (30 s)  -> fired again 13:53:47Z (held)
```

**Every graceful-shutdown attempt in the record has aborted at least once before succeeding — 2 for 2.** This is not an anomaly of one outage; it is how the trigger behaves. And 2026-09-01 reached a floor of only 12.565 V, never entering the Cliff band at all, so all 21 of its threshold crossings and both of its shutdown attempts occurred in the **knee**. They were false alarms on a pack nowhere near a cliff.

**Root cause is arithmetic.** `delayed_on: 60s` against a 60 s slope update period is **exactly one extra sample of confirmation**. The comment says it "prevents 1-sample spikes", and that is literally all it does — a two-sample excursion passes straight through, and 2026-09-15 had one.

**The fix the data supports.** Firmware-published slope inside the gated region (V < 12.65 V):

```
09-01:  -10  -1  -6  -15  -5  -7  -20  +1  -13  -3
09-15:   -3  -4 -13  -1  -2 -14  -5  -6  -17  -5 -10  -7  -7  -5  -7  -8  -8 -10 -12
```

| Threshold | 09-01 longest consecutive run below | 09-15 longest |
| ---: | ---: | ---: |
| −10 mV/min | **1 sample** | **2 samples** |
| −15 mV/min | 1 | 1 |
| −20 mV/min | 1 | 0 |

**Every knee excursion is one or two samples. Never three.** The change this implies is Open Item 19.

### 6.1.1 Recommended change — the shutdown dwell

**Change `cliff_imminent`'s confirmation dwell from one extra sample to three. Leave the slope threshold alone.**

```yaml
  - platform: template
    name: "Cliff Imminent"
    ...
    filters:
-     - delayed_on:  60s     # 1 min sustained slope - prevents 1-sample spikes
+     - delayed_on: 180s     # 3 consecutive 60 s slope samples. 60 s against a
+                            # 60 s update period was ONE extra sample, which a
+                            # 2-sample burst walks through: measured 2026-09-01
+                            # and 2026-09-15, every knee excursion below
+                            # -10 mV/min was 1-2 samples, never 3 (report SS6.1).
      - delayed_off: 30s
```

| | now | recommended |
| :--- | :--- | :--- |
| Slope threshold | −10.0 mV/min | **unchanged** |
| Voltage gate | V < 12.65 V | **unchanged** |
| Current guard | I ≤ −0.10 A | **unchanged** |
| `delayed_on` | 60 s = 1 extra sample | **180 s = 3 consecutive samples** |
| `delayed_off` | 30 s | **unchanged** |

**Why this and not a threshold move.** The threshold is not what is wrong — the confirmation depth is. Raising the threshold to −20 mV/min would also have suppressed the knee triggers, but it would equally suppress a *slow* genuine cliff at light load, which is the case the trigger exists for. Requiring persistence discriminates on the axis that actually separates signal from noise here: real cliff slopes are sustained across many consecutive samples, burst artefacts are not.

**Expected effect on timing.** On 2026-09-15 this suppresses both knee triggers and moves the first assert into the Cliff, which began 10:32:50 — roughly 10:36 with a 3-sample hold, against the 09:53:51 that actually fired. At the load that outage actually ran (1.40 A post-shutdown) that leaves ~11 min to LVD. At a sustained 2.089 A the Cliff is traversed faster: the same ~0.34 Ah at 2.089 A is ~10 min, leaving roughly **7 minutes** after a 3-minute hold — still ~3.5× the measured ~2-minute shutdown, but tighter, and this figure is [D] extrapolated, not measured.

**The change is not unprotected.** `voltage_critical` (V < 12.20 V sustained 10 s, I < −0.10 A) calls `hassio.host_shutdown` **immediately, with no 30 s revalidation** [S, 05-06 §2]. That is precisely the backstop a delayed primary trigger needs, and it has never yet been exercised — on 2026-09-15 it asserted at 10:38:56, 8 m 22 s before LVD, but HA was already down and no automation ran. Delaying `cliff_imminent` is what finally gives that path a job.

**`knee_approaching` has the same defect and is left alone deliberately.** Its `delayed_on: 120s` is two samples, and its −3.0 mV/min threshold sits far inside a noise band of sd 18–24 mV/min, so it is close to a coin flip — which is what the 2026-09-15 direct log shows (on 10:12:48, off 10:14:18, on 10:20:48). It drives a phone notification only (Auto 2), so its failure mode is nuisance rather than risk. Fixing it is not urgent and should not be bundled with a change to the shutdown path.

**What is still untested.** That the EMA converges fast enough for a 3-sample hold to fire promptly in a real cliff rests on reconstruction plus the lambda's own comment, not on a measurement (see the limit below). Ship this behind the 14a repeat, not ahead of it. **V1.20 (2026-09-16): shipped ahead of 14a by owner decision**, so 14a now observes it rather than gating it — through the direct API logger, since 14a shuts the host down first and HA will not record the cliff.

*Limit (R11/R18).* The Cliff-phase slopes quoted elsewhere in this report (−27 to −80 mV/min, sustained across ~14 consecutive samples) are **reconstructed from ESP32 heartbeats**, because HA was down and InfluxDB has no coverage during the cliff. That a 3-sample hold would still fire promptly in a genuine cliff therefore rests on that reconstruction plus the lambda's own claim that the EMA converges within 3–4 intervals on a sustained slope — **[S], not [M]**. Verifying it needs a run that reaches the Cliff with HA still recording, which is Open Item 14a.

> **Correction, recorded rather than replaced (R13).** An earlier analysis in this session proposed computing the slope on IR-compensated voltage (`V + I·Ri`) as the fix, citing a 2.5× noise reduction. That figure came from a single hand-picked 24-minute window of one run. Re-measured inside the gated region where the trigger actually operates, on both runs:
>
> | Run | sd @ Ri = 0 | sd @ 95 mΩ | improvement | crossings @ 0 | crossings @ 95 mΩ |
> | :--- | ---: | ---: | ---: | ---: | ---: |
> | 2026-09-01 | 11.34 | 5.66 | 2.0× | 0 | **1** |
> | 2026-09-15 | 21.38 | 16.86 | **1.3×** | 6 | **8** |
>
> **IR compensation makes the crossing count worse on both runs.** In the gated region the current is already comparatively steady, so the IR term is near-constant and its derivative small; the residual noise is not IR sag. The proposal does not survive n = 2 and is withdrawn. It was generated and refuted inside a single session, which is the whole argument for testing a proposed fix against a second run before it reaches firmware.

---

## 7. Recharge

### 7.1 AC return was not observed, and the bound matters

No instrument recorded AC restoration. What bounds it:

- The ESP32 wakes on a **120 s** quantum. Its wake at ~10:57:2x did not detect recovery; the wake at 11:00:09 did. → AC-on ∈ (10:57:2x, 11:00:09).
- XB7 and HA host ICMP returned at **10:59:49** [M], which requires BP-65 reconnect plus host boot before it — and BP-65 reconnects **30 s after V > 12.8 V** [S, README Mode 6].
- Combining: **AC restored ≈ 10:57:2x – 10:59:2x**, best estimate ~10:58 [I]. *Falsifier:* any independently powered AC-side logger, which this system does not have.

**Consequence.** Charging had been running for roughly **60–160 s** before the ESP32's first charge reading. The highest-current part of bulk was seen by nothing. Every "peak" figure below is a **lower bound**.

> **Correction to r1 (R13).** r1 treated 11:00:14 as the recovery time and derived a "~12 m 54 s survival duration". That timestamp is quantised to the sleep interval; it is an upper bound on the blackout, not a measurement of AC return. r1 also called 4.4465 A "True peak recharge current for this event". It is a lower bound.

### 7.2 The recharge is PSU-limited — r1 concluded the opposite

**The Mean Well HDR-60-12 is a 54 W / 4.5 A supply** [S, Mean Well HDR-60 datasheet; confirmed by owner 2026-09-15; `docs/bom.md` "4.5A/54W"; `docs/component-selection.md` "4.5A rated capacity"].

> **Correction to r1 (R13), the most consequential in this revision.** r1 read the nameplate as "54 A", computed the observed 3.952 A as "7.3 % of that rating", and concluded *"this recharge was never PSU-limited; whatever set the taper shape is the pack/charge-controller side, not the supply."* The 54 is watts. The conclusion inverts. r1 tagged the figure `[S, owner]` without confirming the document covers the identifier — precisely the failure R16 exists to prevent. A 54 A DIN-rail supply is also not a physically plausible object, which should have stopped the number before any sourcing question arose.

Measured against the correct nameplate:

| Time | I (battery branch) | % of 4.5 A | P, V×I [corrected] | % of 54 W |
| :--- | ---: | ---: | ---: | ---: |
| 11:00:13.67 | +3.8975 A | 86.6 % | **50.86 W** | **94.2 %** |
| 11:00:18.68 | +3.8516 A | 85.6 % | 50.04 W | 92.7 % |
| 11:00:33.67 | +3.9520 A | 87.8 % | 51.68 W | 95.7 % |
| firmware peak (11:39:52) | **4.4465 A** | **98.8 %** | ~58 W [D, × 13.05 V] | ~107 % |

> **Correction to an earlier draft of this revision (R13).** That draft quoted the 11:00:13 sample as **54.627 W = 101.2 % of nameplate** and built Open Item 17 on it. The figure does not survive checking. `Battery Power` is a template computing `V × I` from the two published channels (`ups-monitor.yaml:1613`), each carrying its own `throttle_average: 5s`, and the template runs on a third independent 5 s tick — so the three clocks free-run against each other with a consistent ~1.29 s V-vs-I offset (§10.3). Across 215 charging samples, published power agrees with a nearest-timestamp `V × I` to **mean +0.29 %, sd 1.41 %**; 13 disagree by more than 3 %; and **11:00:13 is the single worst sample in the entire recharge at +7.41 %**, because the system was four seconds into a CC transient with V moving fast, where a 1.29 s pairing error does maximum damage. The sample implies `P/I = 14.016 V`, which is not physically possible with the PSU floating at 13.3 V and BMS OVP at 14.4–14.6 V. The defensible figure is **V × I = 50.86 W, 94.2 % of nameplate**. The headline was built on the least trustworthy point in the series.

> **Correction to that correction (r3, R13).** The figure is still wrong and 50.86 W still stands, but the mechanism above is not what happened. The offset is not a consistent 1.29 s: ESPHome starts each filter's interval at a random offset re-drawn every boot (§10.3). 11:00:13 falls in the boot that began at the **10:59:47 survival wake**, where current published **1.30 s *before*** voltage and `Battery Power` fired in the same scheduler pass just ahead of the current filter. In all 68 samples of that boot where the two candidate pairings differ, published power used the **previous** current window [M, ESPHome log]. So 54.627 W is 13.047 V (published 3.7 s earlier) × an implied **4.187 A** [D: 54.627 / 13.047] — the current window from ~5 s before, published before the log connected and so not itself observed. The +7.4 % error is current falling between windows (4.187 → 3.8975 A), not voltage moving fast: V went 13.047 → 13.049 V. The "215 samples, sd 1.41 %" figure above compares published power with a nearest-timestamp V × I, and both are skewed estimates — it bounds their disagreement, not the error.

**These are the battery branch alone.** The XB7, the host via the boost, the ESP32 and the BP-65 all draw from the same supply and are not included in any of these figures. §7.4 measures that load share independently on the AC side. The recharge was at the HDR-60-12's constant-current limit from the moment BP-65 reconnected — exactly as README Mode 6 specifies ("PSU immediately enters CC mode at 4.5A") and as the 2026-05-06 run measured directly (4.59 A, "at the constant-current limit of the HDR-60-12" [S, 05-06 §1]).

**The overage is a transient, not a steady state — tested against the BP-65 reconnect hypothesis.**

The owner's proposed mechanism (2026-09-15) is that the BP-65's reconnect hold-off keeps the modem and host disconnected for a period after AC returns, so the PSU charges the battery *alone* with no load share — which would account for the high charge power at the first reading — and that the signature would be *"a rapid downfall once the modem/HA PC was powered on."* The 5 s ESPHome trace tests that directly.

Values below are **as published**; the P column at 11:00:13 carries the skew artifact corrected in §7.2 (V×I = 50.86 W). The current column, which is what this test turns on, is unaffected.

| Time | I (battery) | P as published | ΔI | Event |
| :--- | ---: | ---: | ---: | :--- |
| 11:00:13 | 3.8975 | 54.627 | — | first reading after wake |
| 11:00:18 | 3.8516 | 50.257 | −0.046 | |
| 11:00:23 | **2.9447** | 38.257 | **−0.907** | |
| 11:00:24 | | | | `Xfinity Modem Online` → ON |
| 11:00:28 | 3.7192 | 48.358 | **+0.774** | |
| 11:00:33 | 3.9520 | 51.488 | +0.233 | **higher than before the dip** |
| 11:00:43 → 11:07:58 | 3.780 → 1.904 | 49.5 → 25.0 | monotonic | smooth CC→CV taper, V 13.07 → 13.14 |

**There is no sustained downfall.** Exactly one transient appears — a −0.907 A dip at 11:00:23, one second before the modem-online flag, with V dipping 13.049 → 12.991 alongside it — and battery current recovers *above* its pre-dip value within 10 s. A BP-65 closure admitting ~2 A of load would drop battery current by ~2 A and hold it there at constant terminal voltage. That step is absent from the record. The dip's size and shape read as load inrush, not as a contactor closing.

**The hold-off window was nevertheless real — it simply closed before any instrument was awake.** XB7 and HA-host ICMP both returned at **10:59:49** [M], twenty-four seconds before the first charge reading, and neither can answer a ping unpowered. So by 11:00:13 the loads were already connected, and 54.627 W was measured *with* them live. **The owner's mechanism is therefore the correct explanation for the true peak — which occurred inside that unobserved window and was seen by nothing (§7.1) — but not for the 54.627 W reading.**

**Total-output arithmetic, using the measured post-boost load of 2.089 A / 26.80 W [M, 08-31 §2]:**

| Time | Battery branch | + loads | Total | % of 54 W |
| :--- | ---: | ---: | ---: | ---: |
| 11:00:13 | ~~54.63 W~~ 50.86 W | 26.80 W | ~~81.43 W~~ 77.66 W | ~~150.8 %~~ **143.8 %** |
| 11:00:33 | 51.49 W | 26.80 W | 78.29 W | 145.0 % |
| 11:01:18 | 41.81 W | 26.80 W | 68.61 W | 127.1 % |
| 11:03:18 | 33.18 W | 26.80 W | 59.98 W | 111.1 % |
| 11:05:53 | 26.05 W | 26.80 W | 52.85 W | 97.9 % |
| 11:07:58 | 25.02 W | 26.80 W | 51.82 W | **96.0 %** |

*r3 (R13): the 11:00:13 row used the skew-corrupted published 54.63 W that §7.2 had already corrected; recomputed with V × I = 50.86 W [D: (50.86 + 26.80) / 54 = 143.8 %]. The other rows are as published, which agrees with V × I to sd 1.41 % across the recharge.*

**The supply settles inside its nameplate within about 90 seconds and stays there.** The overage is confined to the first minute or so of bulk. That is the shape of a short-duration peak-load region, not of a supply running chronically over-rated — and it is benign.

**What remains open, much narrowed.** With the corrected 50.86 W, the battery branch sits *within* nameplate at every sample the INA260 covers, and §7.4 shows the supply within rating everywhere the Kasa covers. What is still unmeasured is the true peak: the firmware's 4.4465 A max-tracker implies ~58 W (~107 %), and a PSU pinned at its 4.5 A CC limit implies ~58.7 W into the battery alone — both single instantaneous samples, both in the window no instrument observed (§7.1). That is consistent with a short-duration peak region, and inconsistent with chronic overload. **The Mean Well HDR-60 peak-load rating and its permitted duration have deliberately not been quoted here** — doing so without reading the datasheet for this identifier would repeat the R16 failure that produced r1's "54 A" error. **Open Item 17.**

### 7.4 AC-side cross-check — the Kasa closes the power-flow loop

`sensor.ups_outlet_current_consumption` is the Kasa smart plug feeding the HDR-60-12, i.e. the **AC** side of the supply. It is also the device `switch.ups_outlet` toggles, so it is what was switched off to start this test.

**It does not capture AC restoration.** Its record has a single gap, **09:16:58 → 11:08:07 (111.1 min)** [M] — opening exactly at test start and closing about eight minutes *after* the ESP32 woke, because the plug sits behind the XB7 on WiFi and could not be polled until both the gateway and HA were back. §7.1's bound on AC return stands unchanged; nothing observed it.

**What it does establish, on two counts:**

| Window | Kasa AC | Basis |
| :--- | ---: | :--- |
| Pre-test float, loads running | **29.99 W** mean (n = 695, min 28.8, max 37.7) | [M] |
| Post-recovery, charging + loads | 42.45 W mean (n = 996, max **63.2**, only 8 samples ≥ 60 W) | [M] |

1. **The load figure is independently confirmed.** 29.99 W AC at the documented 87 % efficiency [S, `docs/component-selection.md`] is **26.1 W DC** — against the 26.80 W post-boost load measured on the DC side in the 08-31 report. Two instruments on opposite sides of the PSU, agreeing to **3 %**.

2. **The power-flow loop closes.** Over 11:08–11:13, the one window both instruments cover:

```
battery (INA260, DC)          +23.84 W   [M, n=60]
loads   (Kasa baseline, DC)    26.1  W   [D]
                              --------
total DC                       49.9  W
-> AC at 87 % efficiency       57.4  W   predicted
Kasa observed                  56.2 - 59.4 W   [M]
```

**The supply is within its 54 W rating at every moment the Kasa covers**, and its maximum ever recorded — 63.2 W AC ≈ 55 W DC — sits essentially at nameplate. The 63 W excursions occur at 11:10:09 and 11:10:34, ten minutes after recovery, when battery current had already tapered to ~1.8 A; they are load bursts, not charge current.

### 7.3 Taper

| Time | Elapsed | V | I | Note |
| :--- | ---: | ---: | ---: | :--- |
| 11:00:19 | +0 | 13.049 | +3.8516 | Charging phase begins, CC |
| 11:01:19 | 1 m | 13.083 | +3.1959 | |
| 11:03:20 | 3 m | 13.119 | +2.4700 | |
| 11:05:54 | 5.6 m | 13.138 | +1.9830 | V effectively at plateau |
| 11:19:57 | 19.6 m | 13.140 | +1.6110 | |
| 11:39:39 | 39.3 m | 13.155 | +1.1300 | `on_battery` clears |
| 11:52:03 | 51.7 m | 13.160 | +0.7922 | report cutoff, still charging |

Terminal voltage reached its plateau within ~6 minutes while current tapered roughly monotonically — CC handing over to CV. The observed ceiling of 13.14–13.16 V against the 13.3 V nameplate float is consistent with ideal-diode drop plus wiring at these currents, and with the post-boost float figures in the 08-31 report.

---

## 8. Instrument Findings — read from the firmware source

~~Four Ri-family sensors held pre-test values through the test. Reading `ups-monitor.yaml` directly resolves two, narrows one, and leaves one open.~~ **r3 (R13):** three of the four held their values. `Last Onset Step Resistance` did not — it updated at 09:17:48, and the value r2 took for "pre-test" was this test's own capture (§8.2).

| Sensor | Pre-test | After | Status |
| :--- | ---: | :--- | :--- |
| `Apparent Ri` (settled-step) | 67.314 mΩ | unchanged | **Mechanism identified — r1's mechanism was wrong (§8.1)** |
| `Last Onset Step Resistance` | ~~108.744 mΩ~~ **97.586 mΩ** (08-31) | ~~unchanged~~ **108.744 mΩ at 09:17:48** | ~~Open, narrowed~~ **Worked — not a defect (r3, §8.2)** |
| `Last Recharge Step Resistance` | 100.347 mΩ | unchanged | **Confirmed**: arming flag wiped by survival deep sleep. **r3: correct behaviour, not a defect** — see below |
| `Last Recharge Peak Current` | 2.847 A | **4.4465 A** | **Not a defect** — correctly gated on `on_battery`'s `on_release` |

`Last Recharge Peak Current` is not a fault: `last_recharge_peak_a` is written only in `on_battery`'s `on_release` handler, so it could not populate until 11:39:39. It did, 13 s later. The underlying `recharge_peak_a` max-tracker had been running correctly throughout — and because it samples on its own 5 s schedule it caught 4.4465 A, an instant the throttled publish stream missed.

`Last Recharge Step Resistance` is confirmed: the detector requires `g_onset_was_discharging`, declared `restore_value: no`, which each of the five survival-mode deep sleeps reset to false. The reference pair `g_last_loaded_v` / `g_last_loaded_i` is also `restore_value: no` and was wiped identically, so even an armed detector would have rejected for want of a valid discharge reference. **This interaction had never been exercised because survival mode never had been.**

> **Correction (r3, R13) — the mechanism is right; calling it a defect was not.** After a survival sleep there is no discharge→charge step to measure. The BP-65 had cut the load at the trip, so the pack sat at rest (~40 mA of ESP draw) through every sleep, and charging had been running for up to one 120 s wake interval before the boot that would look for the step (§7.1). Persisting `g_onset_was_discharging` across the sleep would pair a pre-trip loaded sample with a charging sample 13+ minutes later — the relaxation-contaminated ~256 mΩ in §8.3. A mid-outage reboot *without* survival sleep re-arms by itself, because the detector sets the flag while I < −0.5 A. The firmware keeps the prior value; the only defect was that it did so silently. V1.20 logs it at survival recovery.

### 8.1 `Apparent Ri` — a bursty load, not a ramp

r1 attributed the ±15 % current-stability gate failure to the onset current "still ramping" 45 s in. The data does not support that.

Over the dwell window (20 samples, arm at −1.8725 A), deviation from `trig_i`:

```
 -0.00  +1.09  +3.43 [+24.77]  +4.15  +7.04  +5.77  +7.16 [+21.52] [+18.89]
+12.59  +2.88  +3.99  +14.83  +3.18 +11.47  +6.65  +6.26 [+20.21]  +8.83
```

| Test | Result |
| :--- | :--- |
| Consecutive differences | **10 up / 9 down** — a monotonic ramp would be near-unanimous in one sign |
| Dispersion | mean 2.0454 A, sd 0.1363, **CV 6.66 %**, peak-to-peak 22.7 % of mean |
| Samples inside the ±15 % band | **16 of 20 (80 %)** |

This is a **bursty load with stationary noise**, and the 45 s mark landed on one of the ~20 % of samples that are burst excursions. r1's own §6.2 had already diagnosed this exact phenomenon in the slope tool and did not connect the two.

**This changes the fix.** r1's diagnosis implies "lengthen the dwell"; that would not help, because the noise does not decay. The likely remedy is to **compare a median or windowed mean of current against `trig_i`, rather than a single instantaneous sample**. On this data that would convert an ~80 %-reliable capture into a reliable one.

> **Do not ship that change on this evidence alone (R7).** The recommendation rests on **one window of one run** — the same evidential footing as the IR-compensated-slope proposal that §6.1 had to withdraw once it was tested against a second run. Re-test it against 2026-09-01 and against whatever 14a produces, before it reaches firmware. Open Item 20.

> **Re-tested and shipped (V1.20, 2026-09-16).** The V1.19 gate was replayed at 1 s ticks over the InfluxDB V/I series for every rest→load onset since 2026-08-10, at ten tick phases each [M, n = 4 onsets]. It reproduces this test (arm −1.8725 A, reject at −18.9 %, would have published 148.1 mΩ) and the 08-31 value V1.18 documented (141.9 mΩ), and it also rejects 08-29 16:08 on an inrush sample ahead of a steady ~0.82 A load. A windowed gate — mean current over 5–20 s after arming against 30–45 s, Ri from the 30–45 s means — publishes all four (deviations −1.7 / −1.4 / +3.3 / −1.6 %), and on this test's data still rejects an injected ±25 % load change and aborts on a return to rest. For 09-15 the result was reproduced by compiling the firmware's verbatim lambda text in a host harness (147.2–148.7 mΩ across phases). Every reject now logs. Still to observe: that it publishes on 14a's onset — pre-registered in the home-assistant-config CHANGELOG prediction ledger.

**Separately and correctly identified in r1, retained:** both the success branch (`ESP_LOGI`) and the rejection branch (`ESP_LOGW … "out of band"`) sit *inside* the `if (… && stable)` block, so when `stable` is false **nothing is logged and nothing is published**. A silent drop with no log line is a defect in its own right, independent of what triggers it.

**On the reconstructed value.** r1 reconstructed Apparent Ri ≈ 146 mΩ using the firmware's formula at the 45 s mark. That sample is one of the burst excursions — the reconstruction inherits the very artifact that caused the failure. It is carried in §8.3's range but is not a preferred estimate.

### 8.2 `Last Onset Step Resistance` — open, but narrowed

`g_onset_r` is `restore_value: yes` and would have survived every reboot. It stayed bit-identical through ~1.5 hours of continuous uptime between onset (09:17:10) and the first deep sleep (10:47:18) — a window with no reboot to explain it.

**New narrowing from the prior report.** The 08-31 report §4.3 documents that this capture **re-fires roughly every 2.4 s for an entire outage** (~3,200 times in a 128-minute discharge), each overwriting `g_onset_r`, and observed the value moving 165.1 → 181.7 → 188.3 → 188.9 mΩ across one 14.7-minute test [M]. The pre-test value here is 108.744 mΩ — neither the August value nor the May baseline — so **the sensor did update at some point between 2026-08-31 and 2026-09-15**, during the 08-31/09-01 test. It is not permanently dead. Something about *this* onset differed.

The candidate mechanism remains the silent no-op path: if every raw I²C read during the ~100 ms capture window fails the `vraw != 0x0000 && vraw != 0xFFFF` guard, `g_cap_n` stays 0 and the evaluation block is skipped with neither a success nor a rejection log. **There is no log coverage of 09:17:10** — the owner's capture begins at 10:04:58 — so this remains [I] and Open Item 13.

> **Resolved (r3, R13): not a defect.** The sensor updated **during this test**. InfluxDB records **97.586 mΩ (2026-08-31 20:06:30) → 108.744 mΩ at 09-15 09:17:48**, 38 s after the cut [M — in the `mOhm` measurement, where V1.19 moved new points from `mΩ`], with `Last Onset Float Voltage` 13.20375 V, `Last Onset Loaded Voltage` 12.98300 V and `Last Onset Current` 2.030 A published alongside: (13.20375 − 12.98300) / 2.030 × 1000 = **108.74 mΩ** [D], the capture's own inputs. `Onset Capture Quality Good` stayed on. r2 read 108.744 as "pre-test" because every instrument it used started *after* the onset — the HA poller at 09:34:14, the ESPHome capture at 10:04:58, the direct API monitor at 10:06:31 — and the value never changed again. The narrowing above therefore narrowed toward a defect that did not exist, and the silent-I²C-failure mechanism was never needed. Open Item 13 closed.

### 8.3 Ri estimates are not comparable to each other

| Estimate | Method | Note |
| ---: | :--- | :--- |
| 67.3 mΩ | firmware `Apparent Ri`, stale | never updated this test |
| 90.2 – 91.2 mΩ | onset step, V@13:17:00 pairing | |
| 97.5 mΩ | poller live step 09:35:14 (−1.974 → −2.489 A) | [M] |
| 126.3 – 127.6 mΩ | onset step, V@13:17:05 pairing | **same data, different pairing** |
| 146.3 mΩ | settled-step reconstruction at 45 s | lands on a burst sample (§8.1) |
| 172.7 mΩ | survival first-wake load step (§5) | upper bound, includes ~2 min relaxation |
| **75 – 95 mΩ** | **slope-noise minimisation (§6.1 method)** | **Window-dependent: 75 / 85 / 95 / 95 mΩ across four windows. Uses no step, no rest baseline and no V/I pairing, so it is immune to the 1.24 s publish skew (§10.3) — but it is not the single clean value (110 mΩ) an earlier draft of this session reported, and the spread is real.** |
| ~256 mΩ | recharge-step, firmware formula | spans a 13-min blackout with full relaxation |
| 260 mΩ | 2026-03 commissioning, OCV recovery | [S] |

**The onset figure swings 90 → 128 mΩ on pairing choice alone**, because V and I publish **1.24 s apart** on a 5 s grid [M] while the load is stepping. That is R18 exactly: the spread is a property of the sampler, not the pack. r1 quoted 91 mΩ as "a rough bound" without stating how rough.

**No two methods agree within 30 %.** The 08-31 report §5.2 already warned that comparing figures across methods "is comparing two different instruments"; r1's suggestion that these are "consistent with Ri rising as the pack ages" is not supportable and contradicts that warning. **Any Ri trend claim requires one method held fixed across runs.** None of these figures is evidence about §4, in either direction.

---

## 9. Behaviour Initially Read as Defects

### 9.1 `on_battery` stayed ON through 39 minutes of charging — correct

`binary_sensor.ups_monitor_on_battery` read `on` continuously through reconnect and 39 minutes of Charging. It cleared at 11:39:39 at V = 13.1555 V — just over the documented 13.15 V trip. The bus needed ~39 minutes of tapering bulk current to climb the last ~15 mV from 13.138–13.142 V back above the threshold. This is symmetric, correct behaviour: the threshold that trips the flag on during discharge must be re-crossed on the way back up.

> **Correction to r1 (R13).** An r1 draft called this a stuck firmware flag after ~20 minutes of observation, without checking it against the actual trip voltage. Recorded rather than removed.

**Still open:** `sensor.ups_monitor_total_outages` read 19 before and after, though this is outage #20. The increment fires at *outage start*, before any deep-sleep interaction, so the survival-mode explanation that closed the sibling items does not apply here. Open Item 9b.

> **Resolved (r3, R13): not a defect.** The counter incremented **18 → 19 at 09:17:49** [M, InfluxDB `sensor.ups_monitor_total_outages`], 39 s after the cut — the `on_press` path, exactly as the firmware says. Its own history runs 14 (08-24) → 15, 16, 17 (08-29) → 18 (08-31) → 19 (this test), so this *was* outage #19; the "#20" tally was wrong. As with §8.2, the "before" reading came from an instrument that started after the increment. Open Item 9b closed.

### 9.2 Ad hoc tooling — two defects, recorded at the site

Per R13, applied to throwaway session tooling, because a wrong reading that goes uncorrected in the moment is the failure mode the standard exists to prevent.

1. **A naive dV/dt over a short window produced false swings (−44.9 to −70.3 mV/min)** during ordinary load transients, misreading IR sag from a current step as an accelerating discharge trend. Fixed by subtracting I × R before computing slope and widening the minimum window. *This is the same burst phenomenon as §8.1 and §6(3).*
2. **A ping check misread Windows `ping.exe`'s own "Destination host unreachable" replies — sent by the local machine, not the target — as evidence the target was up**, because it checked only the process return code. Fixed by requiring the literal target IP as replier and rejecting unreachable / TTL-expired text, then verified against both a known-up and a known-down host before being trusted again.

> **Correction to r1 (R13).** r1 said this produced "two false 'back UP' reports". The preserved log shows **three**: 09:55:41, 09:59:04 and 10:06:40 [M, `network_reachability_log.txt`]. The corrected tool restarted at 10:09:26 and produced no further false recoveries.

Neither defect affected firmware, HA config, or any figure in this report; §6 has been re-anchored onto evidence that does not depend on the tool at all.

---

## 10. Data Integrity — read this before opening the raw files

### 10.1 The InfluxDB export covers 37.5 of ~90 discharge minutes

| Series | Gap start | Gap end | Duration |
| :--- | :--- | :--- | ---: |
| V | 13:54:30.6Z | 15:01:24.7Z | 4014.1 s (66.90 min) |
| A | 13:54:31.9Z | 15:01:24.7Z | 4012.8 s |
| W | 13:54:30.1Z | 15:01:24.7Z | 4014.6 s |

The gap opens when **HA's recorder dies at the graceful shutdown**, 53 minutes before LVD — not at the LVD trip. `raw_V/A/W.json` therefore cover the discharge only from 13:17 to 13:54:31Z. **Every Knee-HA-down and Cliff figure in this report comes from the direct-API and ESPHome captures, not from InfluxDB.**

> **Correction to r1 (R13).** r1 §5 and the dataset README both stated the gap ran "from the LVD trip", and r1's Appendix claimed these files cover "the full discharge ladder". Neither is true. r1's causal explanation — "HA's recorder needed roughly a minute after reconnect to resume writing" — explains ~70 s of a 4,014 s gap; the other 65 minutes are simply HA being off.

### 10.2 Three bit-identical stale samples on recorder restart

The first value after the gap in each series is **byte-for-byte equal** to the last value before it:

```
V  13:54:30.641901Z = 12.5302495956421   ->  15:01:24.728230Z = 12.5302495956421
A  13:54:31.898975Z = -1.96474993228912  ->  15:01:24.728682Z = -1.96474993228912
W  13:54:30.147715Z = -25.3829574584961  ->  15:01:24.728887Z = -25.3829574584961
```

This is HA's recorder writing last-known state on restart. It is **not a measurement**. The first true post-recovery samples are at 15:01:25.27Z (13.0753 V, +3.1862 A). A naive plot or integration of these files yields a −1.96 A *discharge* datapoint 74 seconds after charging began. **Any re-analysis must drop the 15:01:24.73Z row from all three series.**

### 10.3 Publish skew between series

V, A and W are published on independent schedules: A lands consistently **+1.24 to +1.32 s** after V, and W **−0.43 to −0.53 s** before it [M, n = 12 consecutive]. On a 5 s grid that is a fifth of a sample period, and it is the dominant error term in every step-resistance derivation (§8.3). **Pair V with I only where the load is steady, and never across a step.**

**Root cause, from the firmware.** The `ina260` platform runs at `update_interval: 1s`, and each channel carries its own **`throttle_average: 5s`** (`ups-monitor.yaml:1570-1612`). A time-based throttle publishes when *its own* window closes, so the two channels lock into whatever offset they happened to start with and hold it indefinitely — here 1.29 s. `Battery Power` compounds it: it is a template computing `V × I` from the two published `.state` values on a **third** independent `update_interval: 5s` tick (`ups-monitor.yaml:1613-1628`), so it can pair a fresh current with a 1.3 s-old voltage. The chip's own POWER register is internal-only and unused, correctly, because it is unsigned.

> **Correction (r3, R13).** "Hold it indefinitely — here 1.29 s" is true only within one boot. Each `throttle_average` registers its own scheduler interval, and ESPHome starts every interval at a random offset in [0, min(interval / 2, 5 s)) drawn at boot (`scheduler.cpp`, source-verified at ESPHome 2026.8.2). The offset is therefore **re-drawn every boot**: in the ESPHome capture, current landed **+1.294 s after** voltage in the pre-outage boot (n = 506, sd 0.026 s) and **1.30 s before** it after the 10:59:47 survival wake (n = 215) [M]. That wake falls inside this export, so **the recovery portion of `raw_A` / `raw_V` carries the opposite skew from the discharge portion.** `Battery Power` did not "pair a fresh current with a 1.3 s-old voltage": it read whichever `.state` values were latest when its own tick fired, which in the post-wake boot was the previous current window in 68 of 68 discriminating samples (§7.2).

**This skew has now produced three wrong figures in this report's lifetime:** the onset-step resistance swinging 90 → 128 mΩ on pairing choice (§8.3), r1's inverted recharge conclusion, and the 54.627 W / 101 % figure corrected in §7.2. It is a firmware defect, not an analysis hazard to be worked around — **Open Item 21.**

> **Fixed in V1.20 (2026-09-16).** The V and I platform channels are now internal and unfiltered; one accumulator on the raw current publish averages 5 (V, I) pairs and publishes V, I, `Battery Power` and the discharge current/power that feed the Ah/Wh integrals together. Its pairing rests on the `ina260` driver publishing voltage before current and returning early on a failed read (`ina260.cpp` byte-identical at 2026.8.2 and the deployed 2026.9.0). After flashing, one InfluxDB query shows a median V–I arrival gap of **1 ms** on two V1.20 boots against **1,318 ms** on V1.19, and `Battery Power` = V × I of the same block in **40 of 40** points [M]. Data from before 2026-09-16 keeps every caveat in this section.

### 10.4 A defect fixed since 08-31, confirmed by arithmetic

The 08-31 report §4.2 documented a phantom-drift defect adding **43.3 mAh/day** to the lifetime counters with no outage. Checked here:

```
08-31 lifetime total                  7.787 Ah   [S, 08-31 §4.2]
+ 08-31/09-01 test                    1.833 Ah   [S]
+ this outage                         2.533 Ah   [M]
= predicted                          12.153 Ah   [D]
observed 'Ah Delivered (Lifetime)'   12.17  Ah   [M, ESPHome 11:18:43]
residual over ~14 days                0.017 Ah  = 1.2 mAh/day
```

Against 43.3 mAh/day, a **~36× reduction** [D] — consistent with the defect having been fixed in V1.18/V1.19. Not a clean closure (the 7.787 Ah figure's exact timestamp is not pinned, and the 1.833 Ah input is [S]), but the lifetime counters are now usable as a cycle proxy to within a few percent, which they were not in August.

### 10.5 InfluxDB measurements are shared across entities — filter or be wrong

`A`, `V` and `W` are **not** per-device measurements. Home Assistant's InfluxDB integration names the measurement after the *unit*, and tags rows with `entity_id`. This database holds **19 entities in `A`** and **24 in `V`** [M], including:

- `battery_bank_monitor_battery_current` / `_voltage` — the **separate 12 V / 500 Ah pack**, an entirely different battery
- `ups_outlet_current` / `ups_outlet_voltage` — the **AC** side of the outlet
- `ups_monitor_bench_battery_current` / `_voltage` — this pack under its **former entity name**, which is what the May 2026 CSVs carry

An unfiltered query returns all of them interleaved. Doing exactly that, while preparing this revision, produced a "discharge" on 2026-08-02 that never happened, an integration of **659 Wh out of a 53 Wh pack**, and a starting voltage of **119.0 V** — house AC. The error is loud once you look at the numbers and silent if you do not.

Every query must carry both entity names:

```sql
WHERE ("entity_id"='ups_monitor_battery_current'
    OR "entity_id"='ups_monitor_bench_battery_current')
```

The saved JSON exports in `data/2026-09-15_full_discharge_survival_test/` were produced with the filter applied, which is why this trap had not been hit before.

### 10.6 Shallow runs cannot measure capacity

Of the six UPS discharges in the retained record, three never leave the plateau and carry **no** capacity information: 2026-07-21 (floor 12.837 V), 2026-07-28 (12.933 V) and 2026-08-29 (12.791 V). Band comparisons against them are not stable — comparing 2026-08-29 to this outage at matched load gives **−4.4 %** over 12.95→12.90 V and **−73.7 %** over 12.90→12.80 V, from the same two datasets. Adjacent bands in a matched-load May-vs-July comparison likewise give −81.4 %, −41.2 %, **+3.2 %** and −26.2 %.

Near the top of the LiFePO4 curve, charge-per-volt is large enough that a few millivolts of offset moves the answer by tens of percent. **Only runs that leave the plateau — 2026-05-06, 2026-09-01 and 2026-09-15 — can be compared for capacity**, which is why §4.3 uses the one pair that is both load-matched and spans a region with real slope.

---

## 11. Open Items

| # | Item | Status |
| :--- | :--- | :--- |
| 1 | EN/FET not fitted — unattended recovery guaranteed only for outages reaching LVD | **Partially closed.** This outage reached LVD and recovery worked. It does **not** establish the BIOS auto-power-on behaviour claimed in 08-31, because AC restoration was operator-timed rather than passive; that distinction was not isolated. |
| 2 | Full discharge to LVD at the post-boost load | **Closed** — §3, with the caveat that the load fell mid-discharge, so this is not a clean single-load replication. |
| 8 | `on_battery` slow to clear | **Closed, not a defect** — §9.1. |
| 9 | `last_recharge_peak_current` not populating | **Closed, not a defect** — §8. Value is a lower bound (§7.1). |
| 9b | `total_outages` not incremented | ~~Open, unexplained~~ **CLOSED (r3) — not a defect.** Incremented 18 → 19 at 09:17:49 [M]; the "before" read came after it. §9.1. |
| 10 | Repeat full-discharge at constant load to measure the real trigger-to-LVD margin | **Open, and now merged into Item 14a**, which is a constant-load full discharge and satisfies both. A margin measured on a pack losing capacity month to month cannot set a threshold. Characterise capacity first. |
| 11 | Firmware constants cited from the public clone while `H:` was unreachable | **Closed.** `diff` against `H:\esphome\ups-monitor.yaml` is byte-identical, both `version: "1.19"`. |
| 12 | Whether V1.19 contains the V1.18 Apparent-Ri rest-baseline fix | **Closed.** Present and armed correctly. The capture failed a different, downstream gate — §8.1. |
| 13 | `Last Onset Step Resistance` never updated | ~~Open, narrowed — §8.2. Now known to have updated between 08-31 and 09-15, so not permanently dead.~~ **CLOSED (r3) — not a defect.** Updated 97.586 → 108.744 mΩ at 09:17:48, during this test [M]. §8.2. |
| ~~14~~ | ~~Per-cell voltages at end of discharge~~ | **WITHDRAWN — not measurable.** The pack is sealed with no balance taps and no BMS telemetry [M, owner-confirmed 2026-09-15]; the measurement would require destroying the enclosure. Replaced by Items 14a and 16, and partly answered already by §4.6 Test A. |
| **14a** | **Repeat the full discharge at May's current** — shut the N100 host down *before* cutting AC, so the load is XB7 + monitor only (~1.2–1.4 A). Same pack, same load, same 11.80 V endpoint, same instrument as 2026-05-06. | **OPEN — highest priority.** Now the decisive test: ~2.5 Ah against May's 4.179 Ah confirms the loss with no rate, IR or two-regime correction left to argue about. Also satisfies Item 10's constant-load requirement in the same run. |
| ~~15~~ | Re-derive the 08-31/09-01 figures from the raw series | **CLOSED** — §4.3. Re-derived as **1.8316 Ah / 23.316 Wh**, within **−0.1 % / −0.2 %** of the 08-31 report. 2026-08-29 also re-derives to −0.3 %. Both endpoints of the capacity comparison are now [M]. |
| **16** | **Coulomb-count one recharge to termination and compare against the discharge count** | **OPEN — second priority.** Discriminates §4.5 candidates 2 and 3, closes §4.6's one substantial confound (that the curve is anchored on an unverified "started full"), and would give this project its first measured answer to that question. |
| 17 | PSU overage at 11:00:13 | **Largely resolved** — §7.2, §7.4. The 101 %-of-nameplate figure was a publish-skew artifact (Open Item 21); corrected to **94.2 %**, within rating. The Kasa AC-side trace shows the supply within rating everywhere it has coverage, and independently confirms the 26.1 W DC load share to 3 %. **Residual:** the unobserved true peak implies ~58 W (~107 %) for a moment no instrument covered. Closing it needs the Mean Well HDR-60 peak-load rating and duration for this identifier (not quoted here — R16). |
| **21** | **Publish V, I and P from a single synchronised read** — each `ina260` channel currently carries its own free-running `throttle_average: 5s`, and `Battery Power` runs on a third independent tick, giving a ~~fixed~~ ~1.29 s V-vs-I skew (**r3:** re-drawn every boot, §10.3) | ~~OPEN — firmware defect, highest instrument-side priority.~~ **DEPLOYED, V1.20 (2026-09-16); acceptance passed** — V–I gap 1 ms vs 1,318 ms, P = V × I in 40/40 [M] (§10.3). Has produced three wrong published figures (§10.3). Corrupts every step-resistance method (§8.3) and every V×I power sample taken during a transient. |
| **19** | **Change `cliff_imminent` `delayed_on: 60s` → `180s`** (§6.1.1). Threshold, gate and guard unchanged. | ~~OPEN — ready to implement, gated on 14a.~~ **DEPLOYED, V1.20 (2026-09-16), ahead of 14a by owner decision.** Still unmeasured: fire time in a genuine cliff — observe in 14a via the direct API logger. Measured at n = 2: every knee excursion below −10 mV/min lasts 1–2 samples, never 3. Backstopped by `voltage_critical` at 12.20 V, which calls `host_shutdown` with no revalidation. |
| **20** | **Re-test §8.1's median-filter proposal for the Apparent-Ri gate against a second run before shipping it** | ~~OPEN (R7).~~ **DEPLOYED, V1.20 (2026-09-16), after re-test at n = 4 onsets** (windowed means rather than a median; §8.1). Remaining: that it publishes on 14a's onset. It rested on one window of one run — the same footing as the IR-compensated-slope proposal §6.1 had to withdraw after testing at n = 2. |
| 18 | `battery_fully_charged` has never fired — no instrument confirms a completed charge | ~~Open, carried from 08-31 §4.1. Now load-bearing: it is why §4.5 candidate 3 cannot be excluded.~~ **CLOSED (r3) — the premise was stale.** Fires since V1.17 (first ON 2026-08-31 19:37:30) and was ON before both load-matched runs [M]. It confirms float equilibrium, not state of charge; candidate 3 narrowed accordingly (§4.5). |

---

## 12. Conclusion

The system did what it was designed to do. It ran the full documented ladder for the first time, tripped the hardware LVD inside its specified window, ran survival sleep for the first time with no surprises, and recovered unattended. The core safety claim held under a real test rather than a projection.

**What it did not do is hold its capacity.** At matched load over a matched voltage span, this pack delivered 42.4 % less charge than it did fourteen days earlier, with Ah and Wh agreeing to a tenth of a point and the coulomb counter validated against an independent path to under 1 %. Rate effects, Peukert, float droop and temperature together account for under a tenth of the LVD-to-LVD gap and for none of the load-matched gap. The instrument is not the problem; the pack is. ~~And nothing on this system would have reported it — the fully-charged detector has never fired once in the entire record, so "the pack started full" has been an assumption on every test this project has ever run, including the May measurement now serving as the reference.~~ **r3:** the fully-charged detector was ON before both load-matched runs, so the 42.4 % comparison is between two runs that began at the same float equilibrium [M] — which leaves less room, not more, to attribute the shortfall to how the test started. Float equilibrium is not a state-of-charge measurement, and the May reference predates the detector (§4.5).

That reorders the work. The ~52.8-minute unsupervised margin is real and generous, but it is a time measured on a shrinking reservoir, and tuning a threshold to it now would be fitting a constant to a moving target. **Characterise the capacity first** — one discharge repeated at May's load with the host shut down beforehand, and one recharge counted through to termination. Both are cheap, both are non-invasive, and between them they settle what this dataset cannot. The pack is sealed, so the textbook test for imbalance is off the table; §4.6 shows the terminal-only substitute still carries real information, and it points away from uniform fade.

Two things r1 called defects were not: `on_battery` was waiting for the same 13.15 V threshold the dashboard documents, and `Last Recharge Peak Current` was waiting for `on_battery` to clear before copying a value it had tracked correctly throughout. Two that were real got sharper: the recharge-step sensors have a named cause (a `restore_value: no` arming flag, broken specifically by the survival deep sleeps this test was the first to exercise — **r3: correct behaviour, since no step exists after a survival sleep, §8**), and `Apparent Ri` has a named and *reproducible* one — a ±15 % gate compared against a single instantaneous sample of a load whose bursts exceed that band 20 % of the time. That last one has a fix that follows from the diagnosis, which the r1 diagnosis did not. **r3 adds two more to the first list:** `Last Onset Step Resistance` and `total_outages` both worked (§8.2, §9.1) — read after the fact by instruments that started too late to see them change.

And one number in r1 was wrong in a way worth naming plainly: the HDR-60-12 was read as a 54 **amp** supply. It is 54 watts. The recharge was running at its constant-current limit throughout — the firmware's captured peak of 4.4465 A is 98.8 % of the rated current. A figure as implausible as a 54 A DIN-rail supply should not have survived to a conclusion, and the rule that would have caught it — R16, identity before spec — was available and was not applied.

This revision then made a smaller version of the same mistake and caught it the same way. An earlier draft read the first post-recovery sample as 54.627 W, called it 101 % of nameplate, and built an open item on it. Checking rather than quoting showed that sample implies a 14.02 V pack, which cannot happen here: it is the worst publish-skew artifact in the entire recharge, and the defensible figure is 50.86 W — 94 % of nameplate, within rating. What settled it was an instrument nobody had thought to look at, on the other side of the PSU. The Kasa plug's AC trace independently confirms the DC-side load share to 3 % and closes the power-flow loop, and it shows the supply inside its rating everywhere it has coverage.

The general lesson is now on its third instance and has been promoted to a firmware defect rather than a caveat: **V, I and P are published on three free-running clocks**, and every figure that pairs them across a transient is wrong by an amount nobody can bound from the published data alone. That is Open Item 21, and it is the highest instrument-side priority in this report. **It was fixed in V1.20 on 2026-09-16 and passed its acceptance test the same day (§10.3).**

---

## Appendix: Data Provenance

All raw data is under `data/2026-09-15_full_discharge_survival_test/`.

| File | Contents | Coverage limit |
| :--- | :--- | :--- |
| `raw_V.json`, `raw_A.json`, `raw_W.json` | InfluxDB export, 13:16–15:45Z, 5 s class | **Discharge coverage ends 13:54:31Z (§10.1). Drop the 15:01:24.73Z row (§10.2). Series are skewed (§10.3).** |
| `esp32_direct_api_log.txt` / `.py` | Direct ESPHome-API monitor via `aioesphomeapi` to `10.0.0.232:6053` | 93 heartbeats (60 s) + 73 flags (5 s); blackout 10:46:28–11:00:19 |
| `ha_poller_log.txt` / `.py` | HA REST-API monitor | Carries the 09:34:14 firmware-counter anchor used in §4.1 |
| `network_reachability_log.txt` / `.py` | Independent ICMP/TCP probes: XB7, host, ESP32 | Contains the uncorrected tool's three false recoveries (§9.2), preserved deliberately |
| `live_vs_public_repo.diff` | `diff` of `H:\esphome\ups-monitor.yaml` vs `UPS-Monitor/ups-monitor.yaml` | 0 lines; both `version: "1.19"` |

Also used, one level up: `data/logs_ups-monitor-Sept_15_2026_logs.txt` — the owner's independent continuous `esphome logs` capture, 10:04:58–11:18:44, 5 s sensor cadence. **This is the only source for the first post-recovery charge reading (§7.2) and for the pre-test `Survival Exit Reason` value (§5).**

> **Provenance note on that file (R13).** The committed copy is **not byte-identical** to the ESPHome output. This repository's `trailing-whitespace` pre-commit hook stripped a trailing space from **179 of 7,595 lines** at commit time — every one of them ESPHome's own trailing space after a unitless sensor value (`>> 19 ` → `>> 19`, `>> 5 `, `>> 0 `). No timestamp, value, field or line was otherwise altered, and no figure in this report is affected. Recorded because a provenance file that a formatter has touched should say so, rather than let a future reader discover a diff against their own capture and wonder what else moved.

**Credential handling.** `esp32_direct_api_script.py` reads the ESPHome noise PSK from the **`UPS_MONITOR_NOISE_PSK`** environment variable. An earlier draft of that script carried the key inline; it was removed before the first commit and **never entered git history** (`git log --all -S` over the literal returns nothing). This repository is public, and its `.gitleaks.toml` exists because ESPHome credentials were published here for three months in 2026 — the gate was re-run and passes on the corrected file.

Prior reports cited: `UPS_Report_2026-05-06.md` (§1 PSU CC limit, §3.2 capacity, §3.6 thermal, §4.3 capacity budget), `UPS_Report_2026-08-31_Boost_Integration.md` r2 (§1 float voltage, §2 projection and the 09-01 test, §4.1 fully-charged detector, §4.2 phantom drift, §4.3 onset re-fire, §5.2 Ri comparability). Repo docs: `README.md` Mode 6, `docs/bom.md`, `docs/component-selection.md`, `boost-subsystem-design.md`.

| Source | Detail |
| :--- | :--- |
| Home Assistant REST API | `GET /api/states`, `/api/history/period`, 5–20 s ad hoc polling |
| InfluxDB 1.x | `Home Assistant` db, `10.0.0.210:8086`, `ha_ro`. Writes on state change, not on a sample clock |
| ESPHome native API | `aioesphomeapi` → `10.0.0.232:6053`, bypassing HA |
| ICMP/TCP probes | Independent of both; ground truth for LVD trip and recovery timing |
| Firmware source | `H:\esphome\ups-monitor.yaml`, byte-identical to the public clone |

**What this report does not establish** is listed in §2 and is not repeated here.
