# Voltage Drop Analysis

Detailed wiring resistance and voltage drop calculations for the two current paths in the system.

---

## Assumptions

- Wire: 16AWG copper, 4.016 mΩ/ft per conductor at 20°C
- Segment length: 6 inches = 0.5 ft
- Round-trip resistance per segment: 4.016 mΩ (positive + negative)
- Current: Context-specific (typical 1.029A, peak 1.582A)
- Contact resistances: 2 mΩ per crimp, 5 mΩ per ATM fuse, 1 mΩ per terminal block, 3 mΩ BP-65 MOSFET, 5 mΩ ideal diode (charging path)
- AC-DC efficiency: 82.5% (midpoint typical for switching adapters at partial load; confirmed via Mean Well datasheets showing 80–85% at low % load)
- Battery avg voltage: 12.5V during discharge (midpoint of 13.3–11.8V)
- No significant self-discharge or other parasitics beyond listed

---

## Path 1: Battery → Devices

Current path: Battery → F2 → Terminal Block → BP-65 → F3 or F4 → Device (4 wire segments)

| Component/Type | Qty | Resistance per Item (mΩ) | Total Resistance (mΩ) | Calculation Notes |
|---|---|---|---|---|
| Wire Segments (round-trip) | 4 | 4.016 | 16.064 | 4 × 4.016 mΩ |
| Crimp Ring/Spade Terminals | 4 | 2 | 8 | 4 × 2 mΩ |
| ATM Fuses (F2 + F3/F4) | 2 | 5 | 10 | 2 × 5 mΩ |
| Terminal Block Clamps | 2 | 1 | 2 | 2 × 1 mΩ |
| Butt Splice | 1 | 1 | 1 | 1 × 1 mΩ |
| Victron BP-65 MOSFET | — | 3 | 3 | Fixed 3 mΩ |
| **Total Resistance** | | | **40.064 ≈ 0.040 Ω** | Sum |

**Voltage drop at typical (1.029A):** 1.029A × 0.040 Ω = **0.041V**

**Voltage drop at peak (1.582A):** 1.582A × 0.040 Ω = **0.063V**

**Device terminal voltage range:**

| Condition | Battery Voltage | Voltage Drop | Device Terminal Voltage |
|---|---|---|---|
| Normal (AC On) | 13.30V | 0.041V | 13.26V |
| Backup Start | 13.30V | 0.041V | 13.26V |
| Backup End (LVD) | 11.80V | 0.069V (Peak) | 11.73V |

---

## Path 2: PSU → Battery (Charging)

Current path: PSU → Crimp → Ideal Diode → F1 → Terminal Block → Battery (2 wire segments)

| Component/Type | Qty | Resistance per Item (mΩ) | Total Resistance (mΩ) | Calculation Notes |
|---|---|---|---|---|
| Wire Segments (round-trip) | 2 | 4.016 | 8.032 | 2 × 4.016 mΩ |
| Crimp Terminals | 2 | 2 | 4 | 2 × 2 mΩ |
| ATM Fuse (F1) | 1 | 5 | 5 | 1 × 5 mΩ |
| Terminal Block | 1 | 1 | 1 | 1 × 1 mΩ |
| Ideal Diode MOSFET | — | 5 | 5 | Fixed 5 mΩ |
| **Total Resistance** | | | **23.032 ≈ 0.023 Ω** | Sum |

**Voltage drop at 1A (recovery):** 1A × 0.023 Ω = **0.023V** (negligible at float ~0A)

---

## Resulting Voltage Ranges

| Point in Circuit | Low | High |
|---|---|---|
| PSU Float Setpoint | 13.3V | 13.3V |
| Battery Voltage Range | 11.80V (LVD cutoff) | 13.3V (float equilibrium) |
| Device Voltage Range | 11.73V | 13.26V |

The 11.73–13.26V device terminal envelope is within the ±10% tolerance inferred for 12V DC input rails per IEC 62368-1 / UL 62368-1 design practice. See [specifications.md](specifications.md) for the caveat on manufacturer-published tolerances.

---

## Runtime Calculation

Usable Wh = 9Ah × 12.5V = 112.5 Wh

Runtime = 112.5Wh / load W

At 13.68W typical load: 112.5 / 13.68 = **8.2 hours**
