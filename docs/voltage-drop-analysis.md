# Voltage Drop Analysis

Detailed wiring resistance and voltage drop calculations for the two current paths in the system.

---

## Assumptions

- Wire: 16AWG copper, 4.016 mΩ/ft per conductor at 20°C
- Segment length: 6 inches = 0.5 ft
- Round-trip resistance per segment: 4.016 mΩ (accounts for both positive and negative conductors: 2 × (4.016 mΩ/ft × 0.5 ft) = 4.016 mΩ)
- Current: 2A (conservative steady-state load)
- Contact resistances: conservative values (2 mΩ per crimp terminal or butt splice, 5 mΩ per ATM fuse, 1 mΩ per screw terminal block clamp)

---

## Path 1: Battery → Devices

Current path: Battery → F2 → Terminal Block → BP-65 → F3 or F4 → Butt Splice → Device (4 wire segments)

| Component/Type | Qty | Resistance per Item (mΩ) | Total Resistance (mΩ) | Notes |
|---|---|---|---|---|
| Wire Segments (round-trip) | 4 | 4.02 | 16.06 | 4 × 4.016 mΩ |
| Battery Spade Crimps | 2 | 2 | 4 | Female spade connectors at battery +/− |
| BP-65 Ring Terminals | 3 | 2 | 6 | Ring terminals at IN, GND, OUT (stacked rings at OUT) |
| Butt Splice | 1 | 2 | 2 | BP-65 OUT to barrel plug positive |
| ATM Fuses (F2 + F3 or F4) | 2 | 5 | 10 | One path assumes F2 and one load fuse |
| Terminal Block Clamps | 2 | 1 | 2 | Bare wire contacts |
| Victron BP-65 MOSFET Rds(on) | — | 3 | 3 | Fixed 3 mΩ (typical; not datasheet-published) |
| **Total Resistance** | | | **43.06 mΩ** | |
| **Voltage Drop at 2A** | | | **0.086V** | V = 2A × 0.04306Ω |

**Device terminal voltage range:**

| Condition | Battery Voltage | Device Terminal Voltage |
|---|---|---|
| Full charge | 13.25V | 13.16V |
| LVD cutoff | 11.80V | 11.71V |

---

## Path 2: PSU → Battery (Charging)

Current path: PSU → Ideal Diode → F1 → Terminal Block → Battery (2 wire segments)

| Component/Type | Qty | Resistance per Item (mΩ) | Total Resistance (mΩ) | Notes |
|---|---|---|---|---|
| Wire Segments (round-trip) | 2 | 4.02 | 8.03 | 2 × 4.016 mΩ |
| Screw Terminal Blocks | 2 | 1 | 2 | Ideal diode screw terminals (no crimps at PSU) |
| Battery Spade Crimps | 2 | 2 | 4 | Female spade connectors at battery +/− |
| ATM Fuse (F1) | 1 | 5 | 5 | |
| Terminal Block | 1 | 1 | 1 | Bare wire contact |
| Ideal Diode MOSFET | — | 5 | 5 | Fixed 5 mΩ |
| **Total Resistance** | | | **25.03 mΩ** | |
| **Voltage Drop at 2A** | | | **0.050V** | V = 2A × 0.02503Ω |

**Battery terminal voltage at full charge:**

PSU setpoint (13.3V) − charging path drop (0.050V) = **13.250V ≈ 13.25V**

---

## Resulting Voltage Ranges

| Point in Circuit | Low | High |
|---|---|---|
| PSU output setpoint | 13.3V | 13.3V |
| Battery terminals | 11.80V (LVD cutoff) | 13.25V (float equilibrium) |
| Device terminals | 11.71V | 13.16V |

The 11.71–13.16V device terminal envelope is within the ±10% tolerance inferred for 12V DC input rails per IEC 62368-1 / UL 62368-1 design practice. See [specifications.md](specifications.md) for the caveat on manufacturer-published tolerances.
