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

Heat dissipation at typical 14.5W DC combined load (XB7 12.9W + HA Green 1.1W + Shelly 0.5W + BP-65 0.018W). PSU efficiency per project documentation: ~81% at approximately 26% of rated 54W load (14.5W DC ÷ 0.81 = ~17.9W AC wall draw).

### A.1 Component Heat Dissipation

| Component | Parameter | Value | Heat Dissipated |
|-----------|-----------|-------|-----------------|
| Mean Well HDR-60-12 | Efficiency @ ~26% load | ~81% | **~3.4 W** |
| | AC wall draw | ~17.9W | *(dominant source — ~95% of total)* |
| Pololu Ideal Diode | Vf × typical current | 0.005V × 1.2A | 0.006 W |
| Victron BP-65 | MOSFET drop + quiescent | 0.003V drop + 1.5mA | 0.02 W |
| Fuse holders (×3 in path) | ~5mΩ each @ 1.2A | 0.015Ω × 1.44 | 0.02 W |
| Wiring (~47mΩ total path resistance) | 0.047Ω × 1.44 | — | 0.07 W |
| **TOTAL** | | | **~3.5 W continuous** |

> Wire resistance (~47mΩ round trip) is consistent with the stated device voltage envelope of 11.71–13.11V, which implies 0.057V drop at 1.2A typical.

### A.2 Enclosure Thermal Model

Enclosure: LeMotech ABS, 9.6″×7.6″×4.5″. Passive convection, no fans. Six ¼″ ventilation holes drilled: 3 low on the PSU wall (intake), 3 high on the BP-65 wall (exhaust), creating a thermal chimney geometry. Installation: second-floor bedroom, climate-controlled, 63–75°F year-round.

> **Note on IP65 rating:** The drilled holes compromise the original IP65 water-jet resistance rating. The enclosure should be considered IP4X (splash-resistant from above; not jet-proof from sides) post-modification. For an indoor floor installation this is a non-issue practically.

#### Wall Conduction Path

| Parameter | Value | Notes |
|-----------|-------|-------|
| Enclosure surface area | 2,104 cm² (0.21 m²) | All 6 faces |
| Natural convection coefficient (ABS, still air) | ~6 W/m²·K | Conservative estimate |
| Estimated thermal resistance | ~0.79 °C/W | 1/(h × A) |
| ΔT above ambient @ 3.5W | **~2.8 °C** | ΔT = Q × R_th |

#### Chimney Airflow Through Holes

| Parameter | Value | Notes |
|-----------|-------|-------|
| Hole geometry | 6 × ¼″ diameter | 3 intake (low/PSU side), 3 exhaust (high/BP-65 side) |
| Total open area | 0.295 in² (1.90 cm²) | 6 × π × (0.125″)² |
| Effective flow area (Cd = 0.6) | 1.14 cm² | Sharp-edged holes, conservative discharge coefficient |
| Chimney height | ~4″ (0.10 m) | Vertical separation intake to exhaust |
| Chimney velocity at ΔT = 2.8°C | ~0.14 m/s | v = √(2gh·ΔT/T) |
| Convective heat removal via holes | **~0.05 W** | ρ·cp·A_eff·v·ΔT |
| Chimney contribution to total cooling | **~1.5%** | Wall conduction handles remaining 98.5% |

**Engineering finding:** At 3.5W total heat load the ¼″ holes are thermally ineffective. The ABS wall surface area (0.21 m²) provides adequate conduction-convection at only 2.8°C above ambient. To create meaningful chimney airflow at these heat levels would require significantly larger openings. The holes' practical benefits are pressure equalization during thermal cycling (reduces gasket stress over time) and marginal moisture exchange — not meaningful thermal improvement.

### A.3 Internal Temperature Projections

| Condition | Ambient | Est. Internal | Status |
|-----------|---------|---------------|--------|
| Typical winter | 63°F / 17°C | ~20°C | Optimal |
| Typical summer | 75°F / 24°C | ~27°C | Optimal |
| DS18B20 alert threshold | — | 40°C | 13°C headroom vs max ambient |
| LiFePO4 max continuous | — | 45°C | 18°C headroom vs max ambient |

**Conclusion:** The climate-controlled bedroom installation provides substantial margin to all battery thermal limits year-round. At ~3.5W total internal dissipation, enclosure rise above ambient is only ~2.8°C — essentially unchanged by the ventilation holes at this heat level. No active cooling is warranted or beneficial. The DS18B20 temperature sensor on the battery will confirm actual internal temperatures during initial operation.

---

## Appendix B — Runtime Analysis

### B.1 Usable Energy Budget

| Parameter | Value | Source |
|-----------|-------|--------|
| Nominal capacity | 10 Ah | Cyclenbatt 12V 10Ah datasheet |
| Usable capacity (defined voltage range) | 9 Ah | 13.20V → 11.8V per specifications |
| Average discharge voltage | 12.5 V | (13.3V + 11.8V) ÷ 2; LiFePO4 flat plateau |
| Usable energy | **112.5 Wh** | 9 Ah × 12.5 V |
| Typical DC system load | ~14.5 W | XB7 12.9W + HA Green 1.1W + Shelly 0.5W + BP-65 0.018W |
| Runtime @ 14.5W DC | **~7.8 h** | 112.5 Wh ÷ 14.5W |

> DC load derived from Kill-a-Watt AC measurement (16.0W avg, confirmed over 158.8 hours) with OEM adapter losses removed. XB7 at 88% efficiency (DoE Level VI confirmed, model NBC56B120460VU). HA Green at 85% assumed (not characterized). Runtime using raw AC wall figure (16.0W) would be ~7.0 hours.

### B.2 Runtime Sensitivity

| Scenario | Runtime | Notes |
|----------|---------|-------|
| Nominal (new battery, 14.5W DC) | **~7.8 h** | 112.5 Wh ÷ 14.5W |
| Peak load only (~20.2W DC) | ~5.6 h | 112.5 Wh ÷ 20.2W; unrealistic for sustained operation |
| Battery at 80% capacity (calendar aging) | ~6.2 h | 80% of 112.5 Wh ÷ 14.5W |
| Battery at 50% capacity (~24 yr @ 2%/yr) | ~3.9 h | 50% of 112.5 Wh ÷ 14.5W; still covers most residential outages |

### B.3 Battery Longevity

LiFePO4 calendar aging at conservative float (13.3V = 3.325V/cell) and moderate temperature (63–75°F / 17–24°C) is the primary degradation mechanism for this design. Cycle-induced aging is negligible given rare residential outages.

| Scenario | Annual Capacity Loss | Years to 80% | Years to 50% |
|----------|---------------------|--------------|--------------|
| Optimistic (1%/yr) | 1% | ~20 years | ~49 years |
| Conservative (2%/yr) | 2% | ~10 years | ~24 years |
| Realistic estimate | 1–2%/yr | **15–20 years** | — |

At 2% annual loss, 50% capacity is reached in ~24 years, yielding ~3.9h runtime — still adequate for the majority of residential outage durations. The practical end-of-life threshold for this application is when runtime can no longer cover a typical worst-case outage, not a fixed percentage of original capacity.

### B.4 Key Runtime Milestones

The following timeline assumes the measured typical load of ~14.5W DC (~1.2A at 12.5V average):

| Time Elapsed | Battery Voltage | Voltage at Devices | System State |
|--------------|-----------------|-------------------|--------------|
| 0.0 hrs | 13.20V | 13.14V | AC Failure: Seamless switchover (<1ms) |
| 0.5 – 7.5 hrs | 13.2V – 12.8V | 13.14V – 12.74V | Nominal Backup: Flat LiFePO4 plateau period |
| ~7.5 hrs | 12.20V | 12.14V | Soft Alert: HA Green initiates graceful shutdown |
| ~7.8 hrs | 11.80V | 11.74V | LVD Cutoff: Victron BP-65 disconnects all loads |

> Note: The HA Green graceful shutdown at 12.2V provides ~15–20 minutes of warning before LVD cutoff. After shutdown, only the XB7 modem remains powered, reducing load and extending remaining runtime slightly.

### B.5 Protection Chain — Voltage Thresholds

| Protection Layer | Threshold | Action |
|-----------------|-----------|--------|
| **Victron BP-65 LVD (Primary)** | **11.8V** | MOSFET opens after 90-second hold-off. Loads disconnect cleanly. Reconnects at 12.8V after AC restores and battery recovers. |
| **Battery BMS UVP (Backup)** | **10.0V** | Fires only if BP-65 fails to open. Hard cutoff — no hardware damage; minor HA data loss possible. Battery cells protected from further discharge. |
| Shelly Plus Uni (Monitoring) | N/A | Voltage and temperature data to HA dashboard only. No automated protective action. Graceful shutdown trigger at 12.2V alerts HA. |

The 90-second BP-65 hold-off at 11.8V adds only ~0.02V of additional battery voltage drop at typical current before disconnect — analytically negligible.

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
| Victron BP-65 | Fails to open (stuck closed) | 4 | 2 | 5 | 40 | Battery discharges to BMS UVP at 10.0V. Abrupt load cutoff — no hardware damage; minor HA data loss possible. BMS protects cells from further discharge. |
| Victron BP-65 | Fails to close (stuck open) | 3 | 2 | 2 | 12 | Loads remain offline after AC restoration. Detected immediately: HA Green offline, XB7 offline. Voltage present on BP-65 IN confirms fault. |
| Battery BMS | Fails closed (no overcurrent trip) | 6 | 2 | 4 | 48 | Short circuit protection absent; F2 (10A fast-blow) provides hard mechanical backup. BMS failure rate very low. |
| Battery BMS | Fails open (no discharge delivery) | 5 | 1 | 2 | 10 | No backup power on any outage. Detected immediately on first outage event; no silent failure mode. |
| Battery | Capacity loss >20% (aging) | 4 | 3 | 3 | 36 | Shelly ADC SoC trend in HA tracks degradation. LiFePO4 rated 5,000+ cycles >> expected residential usage rate. Calendar aging at 1–2%/yr means 10–20 years before significant capacity loss at 13.3V float, 63–75°F. |
| F1 (7.5A — PSU output) | Fails open | 4 | 2 | 2 | 16 | PSU circuit opens; battery-only mode; no recharge path. Shelly ADC detects voltage stagnation. Replace F1 to restore. |
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
