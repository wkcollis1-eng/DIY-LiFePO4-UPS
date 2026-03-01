# DIY UPS — Supplemental Engineering Analysis

**DIY LiFePO4 UPS for Home Assistant Green & Xfinity XB7 Modem**  
February 2026

This document provides supplemental engineering analysis derived from the component specifications and design parameters in the project repository. All values are sourced from the current repo documentation.

---

## Contents

- [Appendix A — Thermal Analysis & Enclosure Heat Budget](#appendix-a--thermal-analysis--enclosure-heat-budget)
- [Appendix B — Runtime Analysis](#appendix-b--runtime-analysis)
- [Appendix C — Failure Modes & Effects Analysis (FMEA)](#appendix-c--failure-modes--effects-analysis-fmea)

---

## Appendix A — Thermal Analysis & Enclosure Heat Budget

Heat dissipation at typical ~17–18W combined load (HA Green ~3W + XB7 ~14W + Shelly ~1W). PSU efficiency per project documentation: ~81% at approximately 18% of rated 102W load.

### A.1 Component Heat Dissipation

| Component | Parameter | Value | Heat Dissipated |
|-----------|-----------|-------|-----------------|
| Mean Well LRS-100-12 | Efficiency @ ~18% load | 81% | **~4.2 W** |
| | AC wall draw | 22.2 W | *(dominant source — 93% of total)* |
| Pololu Ideal Diode | Vf × typical current | 0.04V × 1.5A | 0.06 W |
| Victron BP-65 | MOSFET drop + quiescent | 0.006V drop + 1.5mA | 0.03 W |
| Fuse holders (×3 in path) | ~5mΩ each @ 1.5A | 0.015Ω × 2.25 | 0.03 W |
| Wiring (~6–8 ft 16AWG round trip) | ~75mΩ total | 0.075Ω × 2.25 | 0.17 W |
| **TOTAL** | | | **~4.5 W continuous** |

Wire resistance (~75mΩ round trip) is consistent with the stated device voltage envelope of 11.71–13.16V, which implies 0.09–0.14V drop at 1.5A typical. The Victron BP-65 MOSFET design eliminates the ~0.73W of continuous relay coil dissipation that a mechanical relay alternative would have added.

### A.2 Enclosure Thermal Model

Enclosure: LeMotech IP65 ABS, 9.6″×7.6″×4.5″. Passive convection, no fans. Installation: second-floor bedroom, climate-controlled, 63–75°F year-round.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Enclosure surface area | 2,104 cm² (0.21 m²) | All 6 faces |
| Natural convection coefficient (ABS, still air) | ~6 W/m²·K | Conservative estimate |
| Estimated thermal resistance | ~0.79 °C/W | 1/(h × A) |
| ΔT above ambient @ 4.5W | **~3.5–4.0 °C** | ΔT = Q × R_th |

### A.3 Internal Temperature Projections

| Condition | Ambient | Est. Internal | Status |
|-----------|---------|---------------|--------|
| Typical winter | 63°F / 17°C | ~21°C | ✅ Optimal |
| Typical summer | 75°F / 24°C | ~28°C | ✅ Optimal |
| DS18B20 alert threshold | — | 40°C | 17°C headroom vs max ambient |
| LiFePO4 max continuous | — | 45°C | 22°C headroom vs max ambient |

**Conclusion:** The climate-controlled bedroom installation provides substantial margin to all battery thermal limits year-round. At 4.5W total internal dissipation, enclosure rise above ambient is only 3.5–4°C. No active cooling is warranted or beneficial.

---

## Appendix B — Runtime Analysis

The repo README specifies ~6.3 hours runtime at typical combined load. This section documents the calculation basis and confirms consistency with the stated capacity parameters.

### B.1 Usable Energy Budget

| Parameter | Value | Source |
|-----------|-------|--------|
| Nominal capacity | 10 Ah | Cyclenbatt 12V 10Ah datasheet |
| Usable capacity (defined voltage range) | 9 Ah | 13.3V → 11.5V per specifications |
| Average discharge voltage | 12.4 V | (13.3V + 11.5V) ÷ 2; LiFePO4 flat plateau |
| Usable energy | **111.6 Wh** | 9 Ah × 12.4 V |
| Typical system load | ~17–18 W | HA Green ~3W + XB7 ~14W + Shelly ~1W |
| Runtime @ 18W | 6.2 h | 111.6 Wh ÷ 18W |
| Runtime @ 17W | 6.6 h | 111.6 Wh ÷ 17W |
| **Stated runtime** | **~6.3 h** | Consistent with ~17.7W effective load |

The 6.3-hour figure corresponds to 111.6 Wh ÷ 17.7W effective load, bracketed by the 17W and 18W calculations. No additional derating is applied, which is appropriate for a new battery in a climate-controlled environment.

### B.2 Runtime Sensitivity

| Scenario | Runtime | Notes |
|----------|---------|-------|
| Specification (new battery, ~17.7W) | **~6.3 h** | Theoretical from 9Ah × 12.4V |
| Peak load only (4A, ~48W worst case) | ~2.3 h | 111.6 Wh ÷ 48W; unrealistic for sustained operation |
| End-of-life estimate (~10 yr, 80% capacity) | ~5.0 h | 80% of 111.6 Wh ÷ 17.7W |

### B.3 Protection Chain — Voltage Thresholds

The system uses hardware-only over-discharge protection. No automated software shutdown is implemented. The Shelly Plus Uni provides voltage and temperature monitoring to Home Assistant dashboards only.

| Protection Layer | Threshold | Action |
|-----------------|-----------|--------|
| **Victron BP-65 LVD (Primary)** | **11.8V** | MOSFET opens after 90-second hold-off. Loads disconnect cleanly. Reconnects at 12.8V after AC restores and battery recovers. |
| **Battery BMS UVP (Backup)** | **10.0V** | Fires only if BP-65 fails to open. Hard cutoff — abrupt shutdown of loads. No hardware damage; minor HA data loss possible. Battery cells protected from further discharge. |
| Shelly Plus Uni (Monitoring) | N/A | Voltage and temperature data to HA dashboard only. No automated protective action. |

The 90-second BP-65 hold-off at 11.8V adds only ~0.02V of additional battery voltage drop at 2A before disconnect — analytically negligible and does not materially affect device voltage at cutoff.

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
| PSU LRS-100-12 | Output voltage drifts high | 6 | 2 | 2 | 24 | PSU OVP 13.8–16.2V limits exposure; BMS secondary OVP at 14.4V; Shelly ADC continuous monitoring alerts HA. |
| PSU LRS-100-12 | Catastrophic OV (OVP fails) | 8 | 1 | 3 | 24 | BMS secondary OVP 14.4–14.6V is backstop. PSU OVP + BMS dual-layer is primary safeguard for battery integrity. |
| PSU LRS-100-12 | Output fails low or off | 3 | 2 | 1 | 6 | System transfers to battery seamlessly (<1ms). Shelly ADC reports voltage change to HA. Runtime clock starts. |
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

- **Overcharge:** PSU OVP (13.8V) → BMS OVP (14.4V)
- **Over-discharge:** BP-65 LVD (11.8V, primary) → BMS UVP (10.0V, backup)
- **Overcurrent / short:** Branch fuses F3/F4 → F2 → BMS current limit (10A)
- **Monitoring:** Shelly Plus Uni (voltage + temperature to HA) — passive, no shutdown authority

The Shelly Plus Uni's monitoring-only role is architecturally correct: the system does not depend on WiFi connectivity or software automation for any protective function. All hardware-layer protections operate independently. This is the appropriate separation of concerns for a residential UPS application.

The BP-65 worst-case scenario — fails closed, battery discharges to BMS UVP at 10V — results in an abrupt device shutdown equivalent in consequence to a hard power cut. HA Green may lose some automation state; XB7 performs a cold restart and reconnects normally. No lasting harm to hardware. With regular HA backups configured, even the data loss consequence is negligible.
