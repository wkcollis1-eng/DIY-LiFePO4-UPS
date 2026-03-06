# DIY UPS — Supplemental Engineering Analysis

**DIY LiFePO4 UPS for Home Assistant Green & Xfinity XB7 Modem**
March 2026

This document provides supplemental engineering analysis derived from the component specifications and design parameters in the project repository. All values are sourced from the current repo documentation.

---

## Contents

- [Appendix A — Thermal Analysis & Enclosure Heat Budget](#appendix-a--thermal-analysis--enclosure-heat-budget)
- [Appendix B — Runtime Analysis](#appendix-b--runtime-analysis)
- [Appendix C — Failure Modes & Effects Analysis (FMEA)](#appendix-c--failure-modes--effects-analysis-fmea)

---

## Appendix A — Thermal Analysis & Enclosure Heat Budget

Heat dissipation at typical ~13.68W combined load (HA Green 0.73W + XB7 12.14W measured + Shelly 0.50W + BP-65 0.018W). PSU efficiency per project documentation: ~87% at approximately 22% of rated 54W load.

### A.1 Component Heat Dissipation

| Component | Parameter | Value | Heat Dissipated |
|-----------|-----------|-------|-----------------|
| Mean Well HDR-60-12 | Efficiency @ ~22% load | 87% | **~2.0 W** |
| | AC wall draw | 15.39 W | *(dominant source — ~90% of total)* |
| Pololu Ideal Diode | Vf × typical current | 0.005V × 1.029A | 0.005 W |
| Victron BP-65 | MOSFET drop + quiescent | 0.003V drop + 1.5mA | 0.02 W |
| Fuse holders (×3 in path) | ~5mΩ each @ 1.029A | 0.015Ω × 1.06 | 0.02 W |
| Wiring (~4 segments 16AWG round trip) | ~40mΩ total | 0.040Ω × 1.06 | 0.04 W |
| **TOTAL** | | | **~2.1 W continuous** |

Wire resistance (~40mΩ round trip) is consistent with the stated device voltage envelope of 11.74–13.26V, which implies 0.041V drop at 1.029A typical. The Victron BP-65 MOSFET design eliminates the ~0.73W of continuous relay coil dissipation that a mechanical relay alternative would have added.

### A.2 Enclosure Thermal Model

Enclosure: LeMotech IP65 ABS, 9.6″×7.6″×4.5″. Passive convection, no fans. Installation: second-floor bedroom, climate-controlled, 63–75°F year-round.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Enclosure surface area | 2,104 cm² (0.21 m²) | All 6 faces |
| Natural convection coefficient (ABS, still air) | ~6 W/m²·K | Conservative estimate |
| Estimated thermal resistance | ~0.79 °C/W | 1/(h × A) |
| ΔT above ambient @ 2.1W | **~1.7 °C** | ΔT = Q × R_th |

### A.3 Internal Temperature Projections

| Condition | Ambient | Est. Internal | Status |
|-----------|---------|---------------|--------|
| Typical winter | 63°F / 17°C | ~19°C | Optimal |
| Typical summer | 75°F / 24°C | ~26°C | Optimal |
| DS18B20 alert threshold | — | 40°C | 14°C headroom vs max ambient |
| LiFePO4 max continuous | — | 45°C | 19°C headroom vs max ambient |

**Conclusion:** The climate-controlled bedroom installation provides substantial margin to all battery thermal limits year-round. At ~2.1W total internal dissipation (reduced from prior estimates due to lower measured load and higher PSU efficiency), enclosure rise above ambient is only ~1.7°C. No active cooling is warranted or beneficial.

---

## Appendix B — Runtime Analysis

The repo README specifies ~8.2 hours runtime at typical combined load. This section documents the calculation basis and confirms consistency with the stated capacity parameters.

### B.1 Usable Energy Budget

| Parameter | Value | Source |
|-----------|-------|--------|
| Nominal capacity | 10 Ah | Cyclenbatt 12V 10Ah datasheet |
| Usable capacity (defined voltage range) | 9 Ah | 13.3V → 11.8V per specifications |
| Average discharge voltage | 12.5 V | (13.3V + 11.8V) ÷ 2; LiFePO4 flat plateau |
| Usable energy | **112.5 Wh** | 9 Ah × 12.5 V |
| Typical system load | ~13.68 W | HA Green 0.73W + XB7 12.14W (measured) + Shelly 0.50W + BP-65 0.018W |
| Runtime @ 13.68W | 8.2 h | 112.5 Wh ÷ 13.68W |
| **Stated runtime** | **~8.2 h** | Consistent with measured load |

### B.2 Runtime Sensitivity

| Scenario | Runtime | Notes |
|----------|---------|-------|
| Specification (new battery, 13.68W) | **~8.2 h** | Theoretical from 9Ah × 12.5V |
| Peak load only (1.582A, ~18.67W) | ~6.0 h | 112.5 Wh ÷ 18.67W; unrealistic for sustained operation |
| End-of-life estimate (~10 yr, 80% capacity) | ~6.6 h | 80% of 112.5 Wh ÷ 13.68W |

### B.3 Key Runtime Milestones

The following timeline assumes the measured typical load of 13.68W (~1.03A at 13.3V):

| Time Elapsed | Battery Voltage | Voltage at Devices | System State |
|--------------|-----------------|-------------------|--------------|
| 0.0 hrs | 13.30V | 13.26V | AC Failure: Seamless switchover (<1ms) |
| 0.5 – 7.5 hrs | 13.2V – 12.8V | 13.16V – 12.76V | Nominal Backup: Flat LiFePO4 plateau period |
| ~7.9 hrs | 12.20V | 12.16V | Soft Alert: HA Green initiates graceful shutdown |
| ~8.2 hrs | 11.80V | 11.74V | LVD Cutoff: Victron BP-65 disconnects all loads |

> Note: The HA Green graceful shutdown at 12.2V provides ~15–20 minutes of warning before LVD cutoff. After shutdown, only the XB7 modem remains powered, reducing load and extending the remaining runtime slightly.

### B.4 Protection Chain — Voltage Thresholds

The system uses hardware-only over-discharge protection. No automated software shutdown is implemented. The Shelly Plus Uni provides voltage and temperature monitoring to Home Assistant dashboards only.

| Protection Layer | Threshold | Action |
|-----------------|-----------|--------|
| **Victron BP-65 LVD (Primary)** | **11.8V** | MOSFET opens after 90-second hold-off. Loads disconnect cleanly. Reconnects at 12.8V after AC restores and battery recovers. |
| **Battery BMS UVP (Backup)** | **10.0V** | Fires only if BP-65 fails to open. Hard cutoff — abrupt shutdown of loads. No hardware damage; minor HA data loss possible. Battery cells protected from further discharge. |
| Shelly Plus Uni (Monitoring) | N/A | Voltage and temperature data to HA dashboard only. No automated protective action. Primary shutdown trigger at 12.2V alerts HA for graceful shutdown. |

The 90-second BP-65 hold-off at 11.8V adds only ~0.02V of additional battery voltage drop at typical current before disconnect — analytically negligible and does not materially affect device voltage at cutoff.

---

## Appendix C — Failure Modes & Effects Analysis (FMEA)

**RPN = Severity × Occurrence × Detection**

Scale 1–10 for each factor. For Occurrence and Detection, lower is better. For Severity, higher indicates greater potential harm. Review threshold: RPN ≥ 70.

### C.1 Rating Criteria

| Severity | Definition | Occurrence | Definition | Detection | Definition |
|----------|------------|------------|------------|-----------|------------|
| 1–2 | Negligible / minor | 1–2 | Remote (<1 in 10 yr) | 1–2 | Certain (Shelly ADC / visual) |
| 3–4 | Function loss; recoverable data risk | 3–4 | Low (1 in 5–10 yr) | 3–4 | High probability |
| 5–6 | Battery damage / extended outage | 5–6 | Moderate (1 in 2–5 yr) | 5–6 | Moderate probability |
| 7–8 | Equipment damage or fire risk | 7–8 | Frequent (~yearly) | 7–8 | Low probability |
| 9–10 | Injury / fire | 9–10 | Systemic | 9–10 | Undetectable |

### C.2 FMEA Results

| Component | Failure Mode | S | O | D | RPN | Controls / Mitigation |
|-----------|-------------|---|---|---|-----|-----------------------|
| PSU HDR-60-12 | Output voltage drifts high | 6 | 2 | 2 | 24 | PSU OVP 13.8–16.2V limits exposure; BMS secondary OVP at 14.4–14.6V; Shelly ADC continuous monitoring alerts HA. |
| PSU HDR-60-12 | Catastrophic OV (OVP fails) | 8 | 1 | 3 | 24 | BMS secondary OVP 14.4–14.6V is backstop. PSU OVP + BMS dual-layer is primary safeguard for battery integrity. |
| PSU HDR-60-12 | Output fails low or off | 3 | 2 | 1 | 6 | System transfers to battery seamlessly (<1ms). Shelly ADC reports voltage change to HA. Runtime clock starts. |
| Pololu Ideal Diode | MOSFET fails shorted | 5 | 2 | 4 | 40 | Battery current exposure limited by BMS (10A). 12–13V differential; no sustained overvoltage on PSU output stage. |
| Pololu Ideal Diode | MOSFET fails open | 4 | 2 | 2 | 16 | Battery cannot recharge. Shelly ADC detects: voltage stagnates at discharge rate rather than recovering to 13.3V. |
| Victron BP-65 | Fails to open (stuck closed) | 4 | 2 | 5 | 40 | Battery discharges to BMS UVP at 10.0V. Abrupt load cutoff — no hardware damage; minor HA data loss possible. BMS protects cells from further discharge. Severity 4: consequence bounded to recoverable data loss only. |
| Victron BP-65 | Fails to close (stuck open) | 3 | 2 | 2 | 12 | Loads remain offline after AC restoration. Detected immediately: HA Green offline, XB7 offline. Voltage present on BP-65 IN terminal confirms fault. |
| Battery BMS | Fails closed (no overcurrent trip) | 6 | 2 | 4 | 48 | Short circuit protection absent; F2 (10A fast-blow) provides hard mechanical backup. BMS failure rate very low. |
| Battery BMS | Fails open (no discharge delivery) | 5 | 1 | 2 | 10 | No backup power on any outage. Detected immediately on first outage event; no silent failure mode. |
| Battery | Capacity loss >20% (aging) | 4 | 3 | 3 | 36 | Shelly ADC SoC trend in HA tracks degradation. LiFePO4 rated 5,000+ cycles >> expected residential usage rate. |
| F1 (10A — PSU output) | Fails open | 4 | 2 | 2 | 16 | PSU circuit opens; battery-only mode; no recharge path. Shelly ADC detects voltage stagnation. Replace F1 to restore. |
| F2 (10A — Battery +) | Open before first use or nuisance open | 6 | 2 | 2 | 24 | No battery backup. Procedure: install F2 first; verify continuity before any other connection. Fuse visible for inspection. |
| F3 (2A — HA Green) | Fails open | 3 | 2 | 1 | 6 | HA Green loses power. Detected immediately. XB7 modem continues operating on F4 branch unaffected. |
| F4 (5A — XB7 Modem) | Fails open | 2 | 2 | 1 | 4 | XB7 modem loses power. Detected immediately. HA Green continues on F3 branch unaffected. |
| Shelly Plus Uni | Loss of monitoring (WiFi or hardware fault) | 2 | 3 | 2 | 12 | Monitoring-only device. HA dashboards go stale; alerts disabled. BP-65 and BMS hardware protection remain fully active and independent. |
| Shelly Plus Uni ADC | Voltage calibration error / drift | 2 | 2 | 3 | 12 | Incorrect SoC readings in HA. No protective consequence — Shelly has no shutdown authority. Verify calibration at commissioning against known reference. |
| Wiring / Terminals | High-resistance crimp or joint | 4 | 3 | 5 | 60 | Localized heating; increased voltage drop. Verify with multimeter at commissioning; IR thermal check at 1 month; annual visual inspection. |
| Wiring / Terminals | Terminal short circuit (pre-F2) | 8 | 1 | 4 | 32 | High instantaneous current to BMS limit (10A). F2 provides backup. IP65 ABS enclosure provides containment. F2-first installation procedure mitigates risk. |
| DS18B20 | Sensor failure | 2 | 2 | 2 | 8 | Battery temperature monitoring disabled; 40°C alert non-functional. Climate-controlled environment provides substantial inherent margin. Alert absence visible in HA dashboard. |

### C.3 Highest-RPN Items

No failure modes exceed the RPN 70 review threshold. The three highest items are:

| RPN | Item | Notes |
|-----|------|-------|
| 60 | Wiring / Terminals — High-resistance joint | Detection score of 5 drives the RPN. Addressed by multimeter verification at commissioning plus periodic inspection. Not a design flaw — applies to any field-assembled wiring. |
| 48 | Battery BMS — Fails closed (no OC protection) | F2 (10A fast-blow) provides hard backup. Acceptable residual risk. |
| 40 | Victron BP-65 — Fails to open / Ideal Diode MOSFET fails shorted | BP-65: BMS UVP at 10V provides hard backstop; consequence bounded to recoverable HA data loss only, no hardware damage. Diode: BMS current limit bounds exposure. Both acceptable. |

### C.4 System-Level Conclusion

No single credible failure mode produces hardware damage, injury, or fire risk in this design. The protection stack is appropriately layered:

- **Overcharge:** PSU OVP (13.8V) → BMS OVP (14.4–14.6V)
- **Over-discharge:** BP-65 LVD (11.8V, primary) → BMS UVP (10.0V, backup)
- **Overcurrent / short:** Branch fuses F3/F4 → F2 → BMS current limit (10A)
- **Monitoring:** Shelly Plus Uni (voltage + temperature to HA) — passive, no shutdown authority

The Shelly Plus Uni's monitoring-only role is architecturally correct: the system does not depend on WiFi connectivity or software automation for any protective function. All hardware-layer protections operate independently. This is the appropriate separation of concerns for a residential UPS application.

The BP-65 worst-case scenario — fails closed, battery discharges to BMS UVP at 10V — results in an abrupt device shutdown equivalent in consequence to a hard power cut. HA Green may lose some automation state; XB7 performs a cold restart and reconnects normally. No lasting harm to hardware. With regular HA backups configured, even the data loss consequence is negligible.
