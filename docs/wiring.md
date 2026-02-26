# Wiring Reference

All wiring is 16AWG. See [voltage-drop-analysis.md](voltage-drop-analysis.md) for resistance and drop calculations.

---

## Fuse Locations and Ratings

| Fuse | Rating | Location | Purpose |
|---|---|---|---|
| F1 | 10A fast-blow | PSU output | Protects PSU output circuit |
| F2 | 10A fast-blow | Battery positive | **INSTALL FIRST** — protects battery circuit |
| F3 | 2A fast-blow | BP-65 OUT → HA Green | Protects HA Green load circuit |
| F4 | 5A fast-blow | BP-65 OUT → XB7 Modem | Protects Xfinity Modem load circuit |

> Install F2 before connecting the battery to any other part of the circuit. This is the primary short-circuit protection for the battery.

---

## Component Mounting

| Component | Mounting Method |
|---|---|
| Mean Well LRS-100-12 PSU | Velcro to enclosure base, stabilize to wall |
| Victron BatteryProtect BP-65 | Velcro to enclosure base |
| Pololu Ideal Diode | Float — secure with wire ties |
| Shelly Plus Uni | Float — secure with wire ties |
| Lever Nuts | Float — secure with wire ties |
| Wiring | Cable clips as needed for strain relief |

---

## Wiring Connections — From/To Reference

### AC Input → PSU

| From | To | Notes |
|---|---|---|
| Power Cord — Black (Hot) | PSU Pin 1 AC/L | |
| Power Cord — White (Neutral) | PSU Pin 2 AC/N | |
| Power Cord — Green (Ground) | PSU Pin 3 Ground | Safety ground — required |

### PSU → Ideal Diode

| From | To | Notes |
|---|---|---|
| PSU Pin 4/5 DC Output V− | Ideal Diode GND (V−) | |
| PSU Pin 6/7 DC Output V+ | Ideal Diode VIN (V+) | Via F1 (10A) |

### Ideal Diode → Terminal Block

| From | To | Notes |
|---|---|---|
| Ideal Diode GND (V−) | Input 2 (−) | Terminal Block has 2 inputs |
| Ideal Diode VOUT (V+) | Input 2 (+) | Terminal Block has 2 inputs |

### Battery → Terminal Block

| From | To | Notes |
|---|---|---|
| Battery (V−) | Input 1 (−) | Terminal Block has 2 inputs |
| Battery (V+) | Input 1 (+) | Via F2 (10A) |

### Terminal Block → Victron BatteryProtect BP-65

| From | To | Notes |
|---|---|---|
| Terminal Block + | BP-65 IN terminal | |
| Terminal Block − | BP-65 GND terminal | Use included 1.5mm² wire |

### Victron BP-65 OUT → Loads

| From | To | Notes |
|---|---|---|
| BP-65 OUT terminal | Lever Nut (+) — F3 input (2A) | HA Green load circuit |
| F3 output | HA Green barrel plug (center +) | 5.5mm × 2.1mm, center-positive |
| BP-65 OUT terminal | Lever Nut (+) — F4 input (5A) | Xfinity Modem load circuit |
| F4 output | XB7 Modem barrel plug (center +) | 5.5mm × 2.1mm, center-positive |
| Terminal Block − | Lever Nut − HA Green barrel plug (sleeve) | Common return |
| Terminal Block − | Lever Nut − XB7 Modem barrel plug (sleeve) | Common return |

### Shelly Plus Uni Monitoring

| From | To | Notes |
|---|---|---|
| Battery + (Terminal Block) | Shelly Pin 1 (V+) | Module power in (+) |
| Battery − (Terminal Block) | Shelly Pin 2 (GND) | Module power in (−) |
| Battery + (Terminal Block) | Shelly Pin 3 (Analog In) | Bridge to Pin 1 — battery voltage sense; primary shutdown trigger at 12.2V |
| DS18B20 Yellow/White (Data) | Shelly Pin 5 (Data) | 1-Wire temperature data |
| DS18B20 Black (GND) | Shelly Pin 6 (Sens. GND) | Temperature sensor ground |
| DS18B20 Red (VCC) | Shelly Pin 7 (3.3V Out) | Temperature sensor power |

---

## Enclosure Layout

See [README](../README.md) for the assembly drawing image.

The enclosure is a LeMotech IP65 ABS junction box (9.6″×7.6″×4.5″ interior). Key layout decisions:

- PSU occupies the left side; battery occupies the center. Physical separation provides AC/DC segregation and reduces EMI coupling.
- Cable glands (1/2" NPT) on the bottom face: AC input on the left, DC output barrel jacks on the right.
- Victron BP-65 mounts on the right side wall. Terminal block sits between battery and BP-65.
- Shelly and ideal diode float above the battery, secured with wire ties.
- All 16AWG runs are kept to approximately 6" segments to hold voltage drop within the analyzed 88mV budget.
