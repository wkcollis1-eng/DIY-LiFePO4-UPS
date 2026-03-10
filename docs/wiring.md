# Wiring Reference

All power wiring is 16AWG unless noted. See [voltage-drop-analysis.md](voltage-drop-analysis.md) for resistance and drop calculations.

---

## Fuse Locations and Ratings

| Fuse | Rating | Location | Purpose |
|---|---|---|---|
| F1 | 7.5A fast-blow | PSU output | Protects PSU output circuit; selective coordination with PSU internal 8A fuse |
| F2 | 10A fast-blow | Battery positive | **INSTALL FIRST** — protects battery circuit |
| F3 | 2A fast-blow | BP-65 OUT → HA Green | Protects HA Green load circuit |
| F4 | 5A fast-blow | BP-65 OUT → XB7 Modem | Protects Xfinity Modem load circuit |

> Install F2 before connecting the battery to any other part of the circuit. This is the primary short-circuit protection for the battery.

---

## Component Mounting

| Component | Mounting Method |
|---|---|
| Mean Well HDR-60-12 PSU | Flat on enclosure floor, trimmer facing up |
| Victron BatteryProtect BP-65 | Left wall of enclosure |
| Pololu Ideal Diode | Float — secure with wire ties |
| Shelly Plus Uni | Float — secure with wire ties |
| Wago lever nuts | Float — secure with wire ties or cable clips |
| DS18B20 sensor | Kapton tape against battery case midpoint |

---

## BP-65 Terminal Stud Assembly

Both the IN and OUT M6 studs accept two stacked M8 ring terminals using a copper washer sandwich. Assembly order (bottom to top):

1. M6 copper washer — seats on stud, centers lower ring
2. M8 ring terminal (first source or load)
3. M6 copper washer — separates rings, prevents rotation
4. M8 ring terminal (second source or load)
5. M6 copper washer — tops the stack
6. Lock washer
7. M6 nut — torque 4–5 N·m

Apply NO-OX-ID or equivalent contact grease to washer faces before assembly.

| Stud | Bottom Ring | Top Ring |
|---|---|---|
| BP-65 IN | Battery+ via F2 | PSU+ via F1 + ideal diode |
| BP-65 OUT | XB7 branch via F4 | HA Green branch via F3 |

---

## Wiring Connections — From/To Reference

### AC Input → PSU

| From | To | Notes |
|---|---|---|
| Power Cord — Black (Hot) | PSU L terminal | |
| Power Cord — White (Neutral) | PSU N terminal | |
| Power Cord — Green (Ground) | PSU Ground terminal | Safety ground — required |

### PSU → BP-65 IN

| From | To | Notes |
|---|---|---|
| PSU V+ | F1 input | 16AWG |
| F1 output | Ideal Diode VIN+ | 16AWG |
| Ideal Diode VOUT+ | BP-65 IN stud (top ring) | 16AWG; M8 ring, copper washer sandwich |
| PSU V− | Wago GND #1 port 2 | 16AWG |

### Battery → BP-65 IN

| From | To | Notes |
|---|---|---|
| Battery+ (spade) | F2 input | 16AWG; **install F2 first** |
| F2 output | Wago tap (221-415) port 1 | 16AWG |
| Wago tap port 2 | BP-65 IN stud (bottom ring) | 16AWG; M8 ring, copper washer sandwich |

### BP-65 OUT → Loads

| From | To | Notes |
|---|---|---|
| BP-65 OUT stud (top ring) | Wago F3 (221-415) port 1 | 16AWG; M8 ring, copper washer sandwich |
| Wago F3 port 2 | F3 input (2A) | 16AWG |
| F3 output | HA Green barrel plug+ (center) | 5.5mm × 2.1mm, center-positive |
| BP-65 OUT stud (bottom ring) | Wago F4 (221-415) port 1 | 16AWG; M8 ring, copper washer sandwich |
| Wago F4 port 2 | F4 input (5A) | 16AWG |
| F4 output | XB7 barrel plug+ (center) | 5.5mm × 2.1mm, center-positive |

### Ground Returns

All grounds consolidate at two daisy-chained Wago 221-415 five-port connectors connected via pigtail to battery−. A separate Wago Sensor GND handles the sensor ground reference per the Shelly Plus Uni schematic.

| From | To | Notes |
|---|---|---|
| Battery− (spade) | Wago GND #1 port 1 | 16AWG pigtail |
| PSU V− | Wago GND #1 port 2 | 16AWG |
| BP-65 GND terminal | Wago GND #1 port 3 | 18AWG |
| Wago GND #1 port 4 | Wago GND #2 port 1 | 16AWG daisy-chain jumper |
| XB7 barrel plug− (sleeve) | Wago GND #2 port 2 | 18AWG |
| HA Green barrel plug− (sleeve) | Wago GND #2 port 3 | 18AWG |
| Shelly harness VAC2 (black) | Wago GND #2 port 4 | 22AWG; Shelly power ground |
| Wago Sensor GND port 3 (pigtail) | Wago GND #2 port 5 | 22AWG; ties sensor GND to system ground |

### Shelly Plus Uni Monitoring

The Shelly connects via a pre-attached wiring harness. All connections require a Wago to join a harness wire to the corresponding field wire. The Wago tap (221-415) on the battery+ line after F2 provides the Shelly supply and voltage sense — this ensures the Shelly reads true battery voltage independent of PSU state.

| From | To | Notes |
|---|---|---|
| Wago tap (221-415) port 3 | Shelly harness VAC1 (red) | 22AWG; Shelly supply (9–28VDC input) |
| Shelly harness VAC2 (black) | Wago GND #2 port 4 | 22AWG; Shelly power ground |
| Wago tap (221-415) port 4 | Shelly harness ANALOG IN (white) | 22AWG; battery voltage sense; configure for 0–15V range in Shelly web UI |

### DS18B20 Temperature Sensor

The Shelly Plus Uni has a built-in pull-up on the DATA harness wire — no external resistor required. DS18B20 GND routes through the Shelly's GND (green) wire per the schematic, ensuring a common sensor and ADC reference ground.

DS18B20 wire colors: red (VCC), yellow (Data), blue (GND).

| From | To | Notes |
|---|---|---|
| Shelly harness SENSOR VCC (yellow) | Wago DS18B20 VCC (221-415) port 1 | 22AWG |
| DS18B20 VCC (red) | Wago DS18B20 VCC (221-415) port 2 | 22AWG |
| Shelly harness DATA (blue) | Wago DS18B20 Data (221-415) port 1 | 22AWG |
| DS18B20 Data (yellow) | Wago DS18B20 Data (221-415) port 2 | 22AWG |
| Shelly harness GND (green) | Wago Sensor GND (221-415) port 1 | 22AWG; sensor and ADC reference ground |
| DS18B20 GND (blue) | Wago Sensor GND (221-415) port 2 | 22AWG |
| Wago Sensor GND port 3 | Wago GND #2 port 5 | 22AWG pigtail to system ground |

---

## Wago Connector Summary

| Designator | Part | Ports Used | Function |
|---|---|---|---|
| Wago tap | 221-415 (5-port) | 4 of 5 | Battery+ tap — BP-65 IN ring, Shelly VAC1, Shelly ANALOG IN |
| Wago F3 | 221-415 (5-port) | 2 of 5 | BP-65 OUT top ring to F3 fuse |
| Wago F4 | 221-415 (5-port) | 2 of 5 | BP-65 OUT bottom ring to F4 fuse |
| Wago DS18B20 VCC | 221-415 (5-port) | 2 of 5 | Shelly SENSOR VCC (yellow) to DS18B20 red |
| Wago DS18B20 Data | 221-415 (5-port) | 2 of 5 | Shelly DATA (blue) to DS18B20 yellow |
| Wago Sensor GND | 221-415 (5-port) | 3 of 5 | Sensor ground node — Shelly GND (green), DS18B20 GND (blue), pigtail to GND #2 |
| Wago GND #1 | 221-415 (5-port) | 4 of 5 | Ground bus — battery−, PSU−, BP-65 GND, jumper |
| Wago GND #2 | 221-415 (5-port) | 5 of 5 | Ground bus — jumper, XB7−, HA Green−, Shelly VAC2, sensor GND pigtail |

All Wago 221-series: 24–12AWG, 20A, 450V. One conductor per port — do not insert two wires into a single port.

---

## Wire Gauge Reference

| Gauge | Used for | Ampacity (chassis wiring) |
|---|---|---|
| 16AWG | All main power paths | 13A |
| 18AWG | BP-65 GND, device barrel leads | 10A |
| 22AWG | Shelly harness, DS18B20 leads | 3A |

---

## Assembly Sequence

1. Mount all components per enclosure layout.
2. Install F2 on battery positive lead — verify open circuit before proceeding.
3. Build Wago GND bus: wire battery− pigtail to Wago GND #1 port 1; wire PSU V− to port 2; wire BP-65 GND to port 3; jumper GND #1 port 4 to GND #2 port 1.
4. Wire device ground returns: XB7 barrel− to GND #2 port 2; HA Green barrel− to GND #2 port 3.
5. Build BP-65 IN stud assembly: copper washer, battery ring, copper washer, PSU ring, copper washer, lock washer, nut. Torque 4–5 N·m.
6. Wire battery+ → F2 → Wago tap port 1; Wago tap port 2 → BP-65 IN bottom ring.
7. Wire PSU V+ → F1 → ideal diode → BP-65 IN top ring.
8. Build BP-65 OUT stud assembly same as IN stud.
9. Wire F3 branch: BP-65 OUT top ring → Wago F3 → F3 → HA Green barrel+.
10. Wire F4 branch: BP-65 OUT bottom ring → Wago F4 → F4 → XB7 barrel+.
11. Wire Shelly harness: VAC1 (red) from Wago tap port 3; ANALOG IN (white) from Wago tap port 4; VAC2 (black) to Wago GND #2 port 4.
12. Wire DS18B20: VCC (red) via Wago DS18B20 VCC port 2; Data (yellow) via Wago DS18B20 Data port 2; GND (blue) to Wago Sensor GND port 2. Wire Shelly GND (green) to Wago Sensor GND port 1; pigtail Wago Sensor GND port 3 to Wago GND #2 port 5.
13. Secure DS18B20 against battery case midpoint with kapton tape.
14. Verify all connections with multimeter before applying AC power.
15. Follow commissioning.md for first power-up sequence.

---

## Enclosure Layout

See [README](../README.md) for the assembly drawing image.

The enclosure is a LeMotech ABS junction box (9.6″ × 7.6″ × 4.5″ interior), originally IP65-rated. Six ¼″ ventilation holes have been drilled (3 intake low on the PSU wall, 3 exhaust high on the BP-65 wall), reducing the effective rating to approximately IP4X. This is a non-issue for an indoor floor installation. Key layout decisions:

- PSU lies flat on the enclosure floor against one wall, trimmer facing up; battery occupies the center floor with ~¾″ gap between them forming a DC wiring chase.
- BP-65 mounts on the left wall. Both supply sources (PSU and battery) run directly to the BP-65 IN stud — no terminal block in the positive power path.
- Ideal diode floats above the PSU, secured with wire ties.
- Shelly floats above the battery, secured with wire ties. Wago connectors cluster near the Shelly for short harness runs.
- Cable glands (½″ NPT) on the bottom face: AC input on the left, DC output barrel jacks on the right.
- DS18B20 mounts on the battery case midpoint; its leads route to the DS18B20 Wago connectors near the Shelly.
