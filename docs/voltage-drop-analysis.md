# Voltage Drop Analysis

Detailed wiring resistance and voltage drop calculations for the two current paths in the system.

---

## Assumptions

- Wire: 16AWG copper, 4.016 mΩ/ft per conductor at 20°C
- Segment length: 6 inches = 0.5 ft
- Round-trip resistance per segment: 4.016 mΩ (accounts for both positive and negative conductors: 2 × (4.016 mΩ/ft × 0.5 ft) = 4.016 mΩ)
- Design current: 2A (conservative worst-case)
- Actual typical current: 1.2A (derived from Kill-a-Watt measurement at 88% XB7 adapter efficiency)
- Contact resistances: 2 mΩ per crimp terminal, 5 mΩ per ATM fuse, 1 mΩ per Wago lever nut traversal, 3 mΩ BP-65 MOSFET Rds(on), 5 mΩ ideal diode MOSFET (charging path)
- Battery avg voltage: 12.5V during discharge (midpoint of 13.3–11.8V; LiFePO4 flat plateau)

---

## Path 1: Battery → Devices

Current path: Battery → F2 → Wago tap → BP-65 IN → BP-65 → BP-65 OUT → Wago F3 or F4 → F3 or F4 → Device (6 wire segments)

| Component/Type | Qty | Resistance per Item (mΩ) | Total Resistance (mΩ) | Notes |
|---|---|---|---|---|
| Wire Segments (round-trip) | 6 | 4.016 | 24.096 | 6 × 4.016 mΩ |
| Battery Spade Crimps | 2 | 2 | 4 | Female spade connectors at battery +/− |
| BP-65 Ring Terminals | 2 | 2 | 4 | Ring terminals at IN bottom ring and OUT ring |
| ATM Fuses (F2 + F3 or F4) | 2 | 5 | 10 | F2 on battery side; F3 or F4 on load branch |
| Wago Lever Nuts | 2 | 1 | 2 | Wago tap (positive) and Wago F3/F4 (positive); conservative |
| Victron BP-65 MOSFET Rds(on) | — | 3 | 3 | Fixed 3 mΩ (typical; not datasheet-published) |
| **Total Resistance** | | | **47.10 mΩ** | |

> Note: Ground return path includes two additional Wago traversals (Wago GND #2 and GND #1). At 1 mΩ each this adds 2 mΩ and is within rounding at either current level.

**Voltage drop and device terminal voltage:**

| Current | Voltage Drop | Battery — Full Charge | Device Terminal | Battery — LVD | Device Terminal |
|---|---|---|---|---|---|
| 2.0A (design, worst-case) | 0.094V | 13.20V | 13.11V | 11.80V | 11.71V |
| 1.2A (actual typical) | 0.057V | 13.20V | 13.14V | 11.80V | 11.74V |

> At LVD cutoff, the 11.71V minimum (2A worst-case) is within the ±10% tolerance envelope for 12V devices (10.8V–13.2V) inferred per IEC 62368-1 / UL 62368-1 design practice.

---

## Path 2: PSU → Battery (Charging)

Current path: PSU → F1 → Ideal Diode → BP-65 IN stud → Wago tap → F2 → Battery (6 wire segments)

| Component/Type | Qty | Resistance per Item (mΩ) | Total Resistance (mΩ) | Notes |
|---|---|---|---|---|
| Wire Segments (round-trip) | 6 | 4.016 | 24.096 | 6 × 4.016 mΩ |
| Ideal Diode Screw Terminals | 2 | 1 | 2 | VIN+ and VOUT+ screw terminals |
| Battery Spade Crimps | 2 | 2 | 4 | Female spade connectors at battery +/− |
| ATM Fuses (F1 + F2) | 2 | 5 | 10 | F1 on PSU side; F2 on battery side |
| Wago Lever Nut | 1 | 1 | 1 | Wago tap in charging return path |
| BP-65 Ring Terminals | 2 | 2 | 4 | Top ring (PSU path in) and bottom ring (battery path through) at IN stud |
| Ideal Diode MOSFET | — | 5 | 5 | Fixed 5 mΩ |
| **Total Resistance** | | | **50.10 mΩ** | |

**Battery terminal voltage at float:**

| Current | Voltage Drop | Battery Terminal Voltage |
|---|---|---|
| 2.0A (design, worst-case) | 0.100V | 13.20V |
| 1.2A (actual typical) | 0.060V | 13.24V |

> At true float equilibrium the charging current is very low (milliamps, not amps). The 1.2A figure reflects bulk charge, not float. At true float the battery terminal voltage approaches the PSU setpoint of 13.3V.

---

## Resulting Voltage Ranges

| Point in Circuit | 2A Design (worst-case) | 1.2A Actual Typical |
|---|---|---|
| PSU output setpoint | 13.3V | 13.3V |
| Battery terminals — float equilibrium | 13.20V | 13.24V |
| Battery terminals — LVD cutoff | 11.80V | 11.80V |
| Device terminals — full charge | 13.11V | 13.14V |
| Device terminals — LVD cutoff | 11.71V | 11.74V |

The 11.71–13.11V worst-case device terminal envelope is within the ±10% tolerance inferred for 12V DC input rails per IEC 62368-1 / UL 62368-1 design practice. See [specifications.md](specifications.md) for the caveat on manufacturer-published tolerances.

---

## Runtime Calculation

Usable energy: 9Ah × 12.5V average = **112.5 Wh**

Runtime = 112.5 Wh ÷ load W

At 14.5W DC typical load: 112.5 ÷ 14.5 = **~7.8 hours**

> DC load derived from Kill-a-Watt AC measurement (16.0W avg, 2.538 kWh / 158.8 hr) with OEM adapter losses removed: XB7 at 88% efficiency (DoE Level VI, model NBC56B120460VU) = 12.9W DC; HA Green at 85% assumed efficiency = ~1.1W DC; Shelly ~0.5W; BP-65 ~0.018W. Total ~14.5W DC. Runtime using raw AC wall figures (16.0W) would be ~7.0 hours.
