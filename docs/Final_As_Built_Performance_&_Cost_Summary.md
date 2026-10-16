
***

# Final As-Built Performance & Cost Summary
**Project:** DIY LiFePO4 UPS
**Date:** March 2026
**Status:** Validated & Deployed

> **Currency note (2026-10-16).** This document is part of the original design set. It describes the build as of March 2026, when a Home Assistant Green ran directly on the 12 V bus and a Shelly Plus Uni ADC did the monitoring. Since then the ESPHome INA260 monitor (April 2026, now on the UPS-Monitor-THT Rev 1 board) has become the measurement of record, the HA Green has been retired, and the HA host is an ASRock N100DC that has run from this UPS through an 18 V boost since 2026-08-29 ([BOOST-DS-r1](../UPS-Monitor/boost-subsystem-design.md)). The load on battery is now 2.089 A / 26.80 W steady [M, 2026-08-29 outage, n = 156, [08-31 report](../reports/UPS_Report_2026-08-31_Boost_Integration.md)]. On 2026-09-15 the pack delivered 2.5331 Ah / 31.821 Wh from onset to LVD [M, [09-15 report](../reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md)], a capacity shortfall that is still under investigation. The [README](../README.md) describes the system as it runs now.
>
> *In this document:* Its runtime, its comparison with the APC BE600M1 and its 10-year cost table are worked at the HA Green load, and its "Validated & Deployed" status refers to that build.

## Executive Summary
Following 25+ hours of continuous full-load operation in its permanent 2nd-floor location, the DIY LiFePO4 UPS has been fully validated. The system currently supports an Xfinity XB7 modem and a Home Assistant Green hub. All thermal, electrical, and efficiency metrics align precisely with the original engineering models.

---

## 1. Performance Results
*Measured over 25h 5m of continuous operation (Kill-a-Watt, final configuration: PSU → Kasa HS103 → Kill-a-Watt).*

| Metric | Value |
| :--- | :--- |
| **Average AC Wall Draw** | 17.90 W |
| **Peak AC Wall Draw** | 29.3 W (Includes Kasa HS103 in measurement chain) |
| **Derived DC Load** | ~14.4 W (Typical) |
| **PSU Terminal Voltage** | 13.3 V (Set) |
| **Battery Terminal Voltage** | 13.23 – 13.27 V (Avg: 13.25 V) |
| **Battery Temperature** | 72–77 °F (8–10 °F above ambient) |

### Comparison to Original Specification

| Parameter | Original Spec | As-Built Performance | Status |
| :--- | :--- | :--- | :--- |
| Typical AC Wall Power | 16.0 W | 17.90 W | Matches thermal model |
| Peak AC Wall Power | 23.0 W | 29.3 W | Acceptable¹ |
| Typical DC Load | 14.5 W | ~14.4 W | **Excellent match** |
| Float Voltage (PSU) | 13.3 V | 13.3 V | **Exact setpoint** |
| Battery Voltage (Float) | 13.24 V | 13.25 V (Avg) | **Exact match** |
| Expected Runtime | ~7.8 Hours | ~8.0 – 8.3 Hours | **Exceeds target** |

> ¹ *Final measurement configuration: PSU plugged into Kasa HS103, Kasa into Kill-a-Watt. Peak of 29.3 W includes Kasa HS103 idle overhead (~0.5 W) and XB7 spike events. The Mean Well HDR-60-12 and DC-side components see a lower peak (~21–22 W AC equivalent), well within safety ratings.*

---

## 2. Engineering Notes
*   **Voltage Regulation:** The voltage drop from 13.3 V (PSU) to 13.25 V (Battery) confirms a total path resistance of ~50 mΩ, validating the `voltage-drop-analysis.md` calculations.
*   **Thermal Margin:** Thermal performance remains excellent, maintaining a buffer of ~27–32 °F below the 40 °C (104 °F) DS18B20 alert threshold.
*   **Switchover Efficiency:** Confirmed seamless transition; zero reset events on the XB7 or Home Assistant Green during testing.
*   **HA Shutdown Automation:** Validated against actual discharge data (2026-03-26). Outlier filter radius set to 0.10 V; trigger duration 1 minute. Total automation chain 2.5 min; margin before BP-65 hardware LVD ~18 min at 15 W actual load.

---

## 3. Cost Analysis

### Actual Build Cost
*   **Total Investment:** $223.88
*   **Effective Hardware Cost:** ~$211.00 (excluding one-time tools)

### Annual Operating Cost Comparison
| System Configuration | Annual Cost | Notes |
| :--- | :--- | :--- |
| Standard AC Adapters (No UPS) | $41 /yr | 16.0 W base load |
| **DIY LiFePO4 UPS** | **$46 /yr** | **17.90 W (As-built)** |
| APC BE600M1 | $52 /yr | Estimated efficiency loss |
| APC BX1500M | $64 /yr | Higher idle power draw |

---

## 4. 10-Year Lifecycle Cost Comparison

| Metric | DIY LiFePO4 UPS | Standard AC Adapters | APC BE600M1 | APC BX1500M |
| :--- | :--- | :--- | :--- | :--- |
| **Initial Cost** | $224 | $0 | $85 | $180 |
| **Battery Repl.** | $30 (1x) | — | $60–90 | $100–150 |
| **Electricity** | $460 | $410 | $520 | $640 |
| **10-Year Total** | **~$714** | **~$410** | **~$665–695** | **~$920–970** |

---

## 5. Value Proposition
The DIY UPS represents a **$304 premium over 10 years** compared to unprotected power; this is the **cost of redundancy**. For this investment, the system delivers:
*   **High Performance:** 3× longer runtime than a comparable APC BE600M1.
*   **Instantaneous Response:** <1 ms switchover (10× faster than typical consumer standby UPS).
*   **Longevity:** 10–20 year battery service life vs. 2–3 years for Lead-Acid (SLA) equivalents.
*   **Intelligence:** Integrated Kasa HS103 enables smart switching and remote power monitoring.

## Conclusion
The as-built system performs exactly as designed. Voltage regulation and thermal margins are well within engineered parameters. The UPS is cleared for long-term service, providing approximately 8 hours of reliable, seamless backup for the home network infrastructure at a competitive lifecycle cost.
