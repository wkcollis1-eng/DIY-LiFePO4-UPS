<div align="center">

# DIY UPS for Home Assistant Green & Xfinity XB7 Modem

**12V LiFePO4-Based Uninterruptible Power Supply**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Complete-green.svg)](#status)
[![Runtime](https://img.shields.io/badge/Runtime-3.6%20hours-green.svg)](#measured-performance)
[![Switchover](https://img.shields.io/badge/Switchover-%3C1ms-brightgreen.svg)](#key-specifications)

</div>

A 12V LiFePO4-based uninterruptible power supply for keeping a Home Assistant Green and Xfinity XB7 cable modem running during grid outages. Built into an IP65 enclosure with Home Assistant monitoring via ESPHome INA260 current sensor.

> **Honest context:** A $85 APC BE600M1 provides comparable backup capability. This build costs roughly the same over 10 years as that option (based on battery replacements and electricity usage). The engineering rationale — longer battery life, faster switchover, direct HA integration, no DC-DC converter voltage regulation — is documented in [design-rationale.md](docs/design-rationale.md). Build this if those tradeoffs matter to you.

---

## ⚠️ Safety Warning

> [!CAUTION]
> **This project involves lithium batteries and AC mains voltage.** Improper handling can cause fire, electric shock, or equipment damage.

- ✅ **Disconnect AC power** before any work inside the enclosure
- ✅ Use appropriate **fusing** on battery connections
- ✅ Never charge LiFePO4 below **0°C (32°F)**
- ✅ Keep a **Class B or ABC fire extinguisher** accessible
- ✅ Review [docs/safety.md](docs/safety.md) before building

**Disclaimer:** Information provided for educational purposes only. Build at your own risk.

---

## Performance Summary

**Validated Runtime:** **~3.6 hours** to hardware LVD (11.8V) under a sustained **14.9W** load.

> **Monitoring upgrade note:** The Shelly Plus Uni has been replaced by an ESPHome XIAO ESP32-C3 + Adafruit INA260 current sensor. All capacity figures below are now coulomb-counted by INA260 rather than inferred from voltage profiles. The May 2026 figures supersede the March 2026 D3 estimates.

### Key Finding

The UPS delivers a reliable **~3.6 hours** of runtime at typical HA Green + XB7 loads. This is **~42%** of the theoretical maximum runtime at full charge (10 Ah / 1.18A = 8.47h).

This result is **not** due to battery degradation, measurement error, or software issues. It is a direct consequence of the **single-rail 13.3V CV architecture**.

### Why the Runtime is Limited

The system uses a single shared rail for both charging and load. To keep the voltage safe for the connected equipment, charging is capped at 13.3V. This holds the battery at approximately **65% SOC**, preventing proper absorption charging at 14.4V. As a result, approximately **3.5 Ah** (~35%) of the battery's rated 10 Ah capacity is never accessible.

| Capacity zone | Ah | Reason |
| :--- | ---: | :--- |
| Float ceiling — never loaded | ~3.5 Ah | 13.3V float ≈ 65% SOC; requires 14.4V charger to recover |
| Rate/LVD penalty | ~1.3 Ah | IR drop at 1.18A strands charge above LVD threshold |
| **Delivered (INA260 measured)** | **4.18 Ah** | Coulomb-counted, May 6 2026 |
| Protected at LVD cutoff | ~0.8 Ah | Intentional; prevents over-discharge |
| Below LVD to rated-empty | ~0.8 Ah | Intentional; cell protection |

### Discharge Characteristics

- Extremely flat voltage plateau from 13.0V down to 12.85V — delivers the bulk of usable energy
- Knee region (12.40–12.85V) shows accelerating decline; ~53 min at production load
- Cliff begins at **~12.40V**: voltage slope accelerates from −30 mV/min to −58 mV/min
- 12.4V warning provides approximately **15–20 minutes** of action time before hardware LVD

### Conclusion

The system performs exactly as designed. The layered protection (voltage warnings → automated shutdown → BP-65 hardware LVD) is robust and all three tiers are now fully live-validated.

**Current validated specification:** ~3.6h runtime at 14.9W average under the existing single-rail topology, based on INA260 coulomb counting (May 6 2026).

A two-stage charging architecture (dedicated 14.4V charger + DC-DC regulator) would be required to approach the full ~7.1–8.5 hour theoretical runtime.

Reports and data can be found in [docs/](docs/).  
Last validated: **May 2026 (INA260 coulomb counting)**

---

## Commissioning Results

![Commissioning Results](assets/Commissioning_Results_2026_03_26.png)

The chart records a full two-cycle discharge test performed March 25–26, 2026 using a
Netgear R6400 router (~7W DC) as a substitute load, with battery voltage logged via the
Shelly Plus Uni at 5-second intervals.

**Discharge 1 (7.76h):** Voltage held the characteristic LiFePO4 flat plateau from 13.2V
to 13.0V over 7.76 hours — a drop of only 0.2V at light load, confirming textbook cell
behavior. **Recharge (10.1h):** AC restored; PSU returned the battery to float within
minutes, peaking at 13.28V and holding stable through a 10-hour recharge window.
**Discharge 2 (9.36h):** A second full discharge ran the battery to LVD cutoff. The
Victron BP-65 tripped at **11.77V** — within 0.03V of the 11.8V design target —
confirming protection circuit accuracy. Post-LVD OCV rebound to 12.13V confirms healthy
cell chemistry with no permanent capacity loss from the deep discharge.

Key findings:
- Discharge plateau variance under 0.2%/hr
- BP-65 cutoff accuracy ±0.03V
- Internal resistance ~260mΩ at low SoC (derived from OCV recovery)
- Bulk recharge from 12.9V to 13.2V completed in under 12 minutes after AC restoration

---

## System Overview

AC grid powers a Mean Well HDR-60-12 PSU set to 13.3V float, which charges a 12V 10Ah LiFePO4 battery through a MOSFET ideal diode. On grid failure, loads switch directly to battery in under 1ms. A Victron BatteryProtect BP-65 disconnects loads at 11.8V to prevent over-discharge. An ESPHome XIAO ESP32-C3 with Adafruit INA260 current sensor and DS18B20 temperature sensor reports battery voltage, current, power, and accumulated Ah/Wh to Home Assistant.

![System Architecture](assets/System_Overview.png)

---

## Key Specifications

| Parameter | Value |
| :--- | :--- |
| PSU | Mean Well HDR-60-12, 13.3V float |
| Battery | Cyclenbatt 12V 10Ah LiFePO4 |
| Float voltage | 13.3V (set on PSU trimmer, lacquered) |
| LVD cutoff | 11.8V (Victron BP-65, Setting 7) |
| LVD reconnect | 12.8V (30s delay after threshold met) |
| Device voltage envelope | 11.71–13.11V at terminals (2A worst-case) |
| Switchover time | <1ms (MOSFET ideal diode) |
| Typical load | 16.0W AC wall / 14.9W DC at devices + monitor (INA260 measured) |
| Accessible capacity | 4.18 Ah / 53.3 Wh (INA260 coulomb-counted, May 2026) |
| Runtime at typical load | ~3.6 hours to LVD |
| Battery lifespan | 10–20 years (calendar aging at 13.3V float, 63–75°F) |
| Enclosure | LeMotech IP65 ABS, 9.6″×7.6″×4.5″ |
| Monitoring | ESPHome XIAO ESP32-C3 + INA260 + DS18B20 → Home Assistant |
| Total build cost | ~$224 + ~$25 ESPHome monitor board |

---

## Operating Modes

**Mode 1 — AC Present:** PSU outputs 13.3V through ideal diode; battery held at float equilibrium. Loads draw from PSU, not battery.

**Mode 2 — AC Failure:** PSU output drops to 0V. Ideal diode blocks. Battery feeds loads directly, no interruption.

**Mode 3 — Low Battery (~12.4V):** ESPHome Cliff phase alert. HA notification: Critical Warning.

**Mode 4 — Low Battery (~12.2V):** ESPHome detects threshold. Home Assistant initiates graceful HA Green shutdown; modem continues on battery.

**Mode 5 — LVD Cutoff (11.8V):** Victron BP-65 disconnects loads after 90-second hold-off.

**Mode 6 — AC Restoration:** PSU resumes 13.3V, ideal diode switches source, BP-65 reconnects after 30s hold-off. PSU immediately enters CC mode at 4.5A (~60W) bulk recharge, tapering to CV float over approximately 10–15 minutes.

![System Architecture](assets/lifepo4_discharge_curve.png)

---

## Automation Validation Status

| Automation | Threshold | Mar 26 | Mar 28 | May 6 | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Early Warning | < 13.0V for 2 min | ✅ | ✅ | ✅ | **PASS** |
| Critical Warning | < 12.4V | ✅ | ✅ | ✅ | **PASS** |
| Graceful Shutdown | < 12.2V for 1 min | ⚠️ Not tested | ⚠️ Not tested | ✅ **Confirmed** | **PASS** |
| BP-65 hardware LVD | ~11.8V | ✅ Direct (11.77V) | ✅ Inferred | ✅ Confirmed (11.675V) | **PASS** |

All four tiers are now fully live-validated. The graceful shutdown automation was confirmed on May 6, 2026 — the final outstanding commissioning item.

---

## Assembly Layout

![Component Layout](assets/UPS_Layout_with_12_Volt_Regulator.png)

*Elevation (top) and plan (bottom) views of LeMotech junction box. Interior Dimensions in inches.*

## Assembly Pictures

![Assembly Pics](assets/IMG_1907.jpeg)
![Assembly Pics](assets/IMG_1912.jpeg)

---

## Documentation

| File | Contents |
| :--- | :--- |
| [docs/bom.md](docs/bom.md) | Full bill of materials with vendor, price, and notes |
| [docs/wiring.md](docs/wiring.md) | From/To wiring tables, fuse locations, component mounting |
| [docs/specifications.md](docs/specifications.md) | Electrical, performance, and protection spec tables |
| [docs/design-rationale.md](docs/design-rationale.md) | Build-vs-buy analysis, float charging strategy |
| [docs/component-selection.md](docs/component-selection.md) | Per-component selection rationale |
| [docs/cost-analysis.md](docs/cost-analysis.md) | Build cost breakdown and 10-year lifecycle comparison |
| [docs/safety.md](docs/safety.md) | AC and battery safety procedures |
| [docs/voltage-drop-analysis.md](docs/voltage-drop-analysis.md) | Wiring resistance and voltage drop calculations |
| [docs/supplemental-analysis.md](docs/supplemental-analysis.md) | Thermal Analysis & Enclosure Heat Budget, Runtime Analysis, Failure Modes & Effects Analysis (FMEA) |
| [docs/design-specification.md](docs/design-specification.md) | Formal requirements, design decisions, and verification matrix |
| [docs/commissioning.md](docs/commissioning.md) | System commissioning process and results |
| [docs/Final_As_Built_Performance_&_Cost_Summary.md](docs/Final_As_Built_Performance_&_Cost_Summary.md) | Final As-Built Performance & Cost Summary |
| [docs/UPS_Validation_Report.md](docs/UPS_Validation_Report.md) | Final Validation Report with Home Assistant configuration |
| [docs/UPS_Report_2026-04-05.md](docs/UPS_Report_2026-04-05.md) | Inaugural commissioning report (Apr 5, 2026) |
| [docs/UPS_Report_2026-05-06.md](docs/UPS_Report_2026-05-06.md) | Outage test report; INA260 first measurement; 12.2V automation confirmed |

## Datasheets

- [Mean Well HDR-60-12 - Datasheet](https://www.meanwell.com/Upload/PDF/HDR-60/HDR-60-SPEC.PDF)
- [Victron Smart BatteryProtect BP-65 — Datasheet](https://www.victronenergy.com/upload/documents/Datasheet-Smart-Battery-Protect-65-A--100-A--220-A-EN.pdf)
- [Victron Smart BatteryProtect — Manual](https://www.victronenergy.com/upload/documents/Smart_BatteryProtect_12V_24V/114439-Smart_BatteryProtect-pdf-en.pdf)
- [Adafruit INA260 — Guide](https://learn.adafruit.com/adafruit-ina260-current-voltage-power-sensor-breakout)
- [TI INA260 — Datasheet](https://www.ti.com/product/INA260)
- [Seeed Studio XIAO ESP32-C3 — Datasheet](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/)

---

## Related Projects

- [LiFePO₄ Battery Bank Study](https://github.com/wkcollis1-eng/Lifepo4-Battery-Banks) — 500Ah DIY battery bank with 130+ days of monitoring
- [Home Assistant Config](https://github.com/wkcollis1-eng/home-assistant-config) — HVAC monitoring implementation

---

## Status

- [x] Design complete
- [x] Components specified
- [x] Components ordered / received
- [x] Build complete
- [x] XB7 power measurement complete (14.7W avg, 20.3W peak — 1.066 kWh / 72.4 hr standalone)
- [x] Combined system power measurement complete (16.0W avg, 23.0W peak — confirmed across 5 windows, 525 hours total)
- [x] Home Assistant automation documentation
- [x] ESPHome INA260 monitor build complete and deployed (Apr 2026)
- [x] INA260 coulomb counting validated — first direct capacity measurement: 4.18 Ah / 53.3 Wh (May 2026)
- [x] HA graceful shutdown automation live-validated (May 6, 2026)
- [x] All four automation tiers confirmed — system fully commissioned

---

## Notes

- Device input voltage tolerance (±10%) is inferred from IEC 62368-1 design practice; neither Nabu Casa nor Comcast publish explicit DC input voltage ranges for these products.
- The PSU output trimmer is set to 13.3V and lacquered. Drift analysis shows expected aging drift of 3–5 mV/year — negligible relative to the 500mV headroom before OVP.
- No DC-DC converter is used. The direct battery feed strategy is documented in [design-rationale.md](docs/design-rationale.md).
- The INA260 monitor board (XIAO ESP32-C3 + Adafruit INA260 + DS18B20 on SBB400 breadboard) replaced the Shelly Plus Uni in April 2026, adding coulomb counting, phase detection, and runtime estimation. Monitor draws ~30–40 mA from the 12V battery bus via Pololu D24V7F3 3.3V regulator.
- The Shelly Plus Uni ADC-based capacity estimates (D3, March 2026: 4.85 Ah / 62.5 Wh) are superseded by the INA260 coulomb-counted measurement of 4.18 Ah / 53.3 Wh from May 2026. The D3 figure was computed from voltage profile timing × assumed constant load and should no longer be used as the capacity baseline.
