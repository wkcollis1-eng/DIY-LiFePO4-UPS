# DIY LiFePO4 UPS: Technical Report
## Outage Test & Validation Report — June 18, 2026

**Data through:** June 20, 2026 (recharge tail) · **Version:** 2026-06-18-r1
**Repository:** https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS · **Report series:** UPS-RPT

---

## Abstract

A partial outage on June 18, 2026 ran 183.3 min from AC failure (18:10:10 UTC) to AC restoration at 12.452 V — the pack stopped right at the cliff threshold without forming one. INA260 coulomb counting gives **3.62 Ah / 46.34 Wh delivered**. Compared against the May 6 baseline at a common 12.45 V depth, June delivered ~5.3% less charge to reach the same loaded voltage. This report decomposes that delta. After ruling out a measurement artifact, capacity fade, temperature, sensor drift, and starting-state/float-history differences, the residual is attributed to a measured ~10% higher pack internal resistance in June; no battery-health flag is warranted and the delta sits well under the 10% watch threshold.

---

## 1. Test Summary (measured, INA260, 5 s cadence)

| Metric | Value |
| :--- | :--- |
| Event type | Partial outage — AC restored, **not** taken to LVD |
| Discharge window | 18:10:10 → 21:13:26 UTC (183.3 min) |
| Ah / Wh delivered | 3.62 Ah / 46.34 Wh |
| Avg current / power | 1.186 A / 15.18 W |
| Float (pre-outage) | 13.23 V |
| Onset loaded V / onset IR | 13.105 V / **106.7 mΩ** @ 1.174 A |
| Bottom V | 12.452 V @ 21:13:06 |
| Battery temp | 81.9 °F onset → 79.1 °F min (ambient 73.6–75.7 °F) |
| Peak recharge | 4.48 A / 58.7 W (PSU CC limit) |

**Protection chain:** `cliff_imminent` did **not** arm — the EMA slope touched −10.2 mV/min on a single sample but did not hold the 60 s guard, so no cliff formed and HA stayed online throughout. No protection automation fired. This was a sub-threshold event, not a full validation of the shutdown chain.

---

## 2. Comparison to May 6 Baseline (both coulomb-counted)

| Depth (loaded) | May time | June time | May Ah | June Ah |
| :--- | ---: | ---: | ---: | ---: |
| 12.85 V | 92.8 min | 87.6 min | 1.803 | 1.716 |
| 12.65 V | 147.8 min | 137.9 min | 2.885 | 2.713 |
| 12.50 V | 189.7 min | 179.6 min | 3.719 | 3.546 |
| **12.45 V** | **194.1 min** | **182.9 min** | **3.807** | **3.615** |

- **Delta to 12.45 V: +0.19 Ah / +5.3%** (May delivered more to the same loaded depth).
- **Plateau band 12.65→12.50 V: May 0.834 Ah vs June 0.833 Ah — identical to 0.2 mAh.** The discharge curves run parallel through the plateau → **same bulk capacity**.
- **Onset IR: May 97.1 mΩ vs June 106.7 mΩ (June ~10% higher)** — measured at near-equal temperature (May 79.9 °F, June 81.9 °F); confirmed at the recharge step (June ~114 mΩ).

---

## 3. The 5% Delta — Hypotheses Tested

| Hypothesis | Disposition | Basis |
| :--- | :--- | :--- |
| Artifact of May estimate | **Rejected** | Measured 3.807 Ah / 194.1 min vs prior estimate 3.80 Ah / 193 min — within 0.2% |
| Capacity fade | **Rejected** | Plateau Ah identical (±0.2 mAh); June was a partial run (full capacity never measured); 6-week gap too short |
| Temperature | **Rejected** | June ran 1.5–2.2 °C warmer (which favors June); OCV correction moves the residual <0.02 Ah, and works *against* the observed direction |
| Sensor drift (INA260 / ESP32-C3) | **Rejected** | Shunt 10 ppm/°C → 0.002% over a 2 °C run-to-run gap (~1400× too small); same chip both runs cancels absolute calibration; ESP32 not in the analog path |
| Starting-SoC / float-anchor scatter | **Rejected (this pair)** | 47-day record: both tests preceded by saturated sub-mA float → same starting SoC |
| Float duration / maintenance recency | **Rejected** | June floated steady at +0.75 mA for 13 days pre-test (no decay = fully topped); re-saturation completes in ~4–9 days, so the post-June-1 maintenance left ample time |
| **Internal resistance / overpotential** | **Leading candidate** | June ~10% higher R (onset 97→107 mΩ, recharge-step ~114 mΩ) — same charge delivered at lower terminal voltage, hitting the 12.45 V cutoff sooner |

The onset-IR snapshot quantifiably accounts for ~0.03 Ah of the loaded-voltage gap. The remaining ~0.14 Ah could not be closed with this dataset because May's bottom-of-discharge resistance fell inside the HA-offline gap, so the dynamic overpotential is unmeasured. The residual is within run-to-run reproducibility for this bench setup.

---

## 4. Conclusion

No capacity-health flag. The ~5% loaded-voltage delta — between two fully-floated runs of the **same** pack six weeks apart — is best explained by June's measured ~10% higher internal resistance (a resistance/overpotential effect: the pack holds the same charge but presents lower voltage under load), with the remainder inside normal reproducibility and the whole delta under the 10% watch threshold. The pack is healthy in float: steady sub-mA current, no creeping self-discharge, re-saturates in ~4–9 days.

**Minor note:** float current stepped from ~0.0 mA (pre-maintenance) to a steady ~+0.75 mA (post-maintenance) and held. Negligible for SoC, but a real change in float equilibrium worth a glance at next service.

---

## 5. Recommendations

1. **Capacity trending must use a common absolute anchor.** The 13.3 V float does not pin SoC tightly enough for cross-event comparison. Discharge baseline and comparison tests to the **same LVD endpoint** and compare usable Ah — not "Ah from float."
2. **Add a mid-discharge rest step** (open load 60–120 s at a known Ah) to capture true OCV, separating capacity from resistance with no reconstruction assumptions.
3. **Log float-hours-since-last-disturbance** (and annotate maintenance events) as a per-test covariate.
4. **Capture the recharge step in HA** (avoid the `hassio.host_shutdown` gap) so effective resistance is measurable at the bottom of every run.
5. **Watch across future outages:** onset IR (97 → 107 mΩ) and the post-maintenance float-current step (0.0 → 0.75 mA). Single observations; treat as trend only if they persist.

---

## Appendix: Data Provenance

| Item | Source |
| :--- | :--- |
| June V / I / P / slope / temp | `sensor.ups_monitor_bench_*`, 5 s cadence, continuous (no recorder gap in discharge) |
| Coulomb count | Trapezoidal integration of INA260 current; cross-checks ESPHome counter within ~0.14% |
| Float-state history | 47-day continuous record (May 4 – June 20) |
| May baseline | UPS_Report_2026-05-06 r2 + raw May Voltage/Current/Temp CSVs |
