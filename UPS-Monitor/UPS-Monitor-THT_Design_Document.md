# UPS-Monitor-THT — Design Document

**Project:** Through-Hole UPS Monitor Board
**Designer:** William Collis
**Revision:** V1.0 (Released to Fab)
**Date:** May 14, 2026
**Status:** Ready for OSH Park submission
**File:** `UPS-Monitor-THT.kicad_pcb` (KiCad 10.0.2)

---

## 1. Purpose and Scope

The UPS-Monitor-THT board provides instrumentation for a 12 V LiFePO4 uninterruptible power supply system, monitoring battery voltage, load current, and ambient temperature, with data reported to Home Assistant via an ESP32-C3 microcontroller over Wi-Fi. The board replaces the existing Shelly Plus Uni voltmeter installation and is intended as the production monitoring solution for Bill's DIY UPS at 13.4 V nominal, ~80 mA typical load.

**Secondary use case:** the same board may host an INA228 breakout (with external DROK 200 A shunt) to monitor a 12 V / 500 Ah LiFePO4 battery bank serving a 2000 W inverter. The INA260 and INA228 Adafruit breakouts share pin-compatible 8-pin headers, allowing dual-use without PCB modification.

---

## 2. Mechanical Specifications

| Parameter | Value |
|---|---|
| Board outline | 46.0 × 78.0 mm |
| Layer count | 2 (top + bottom copper) |
| Substrate | FR4, 1.6 mm thickness |
| Copper weight | 1 oz |
| Surface finish | ENIG (immersion gold) |
| Solder mask | Purple (OSH Park standard) |
| Silkscreen | White |
| Mounting holes | 4× M3 (3.2 mm drill) in corners |
| Fabricator | OSH Park (2-layer Prototype Service) |

**Mounting hole positions:**
- H1: (4, 9)
- H2: (42, 9)
- H3: (42, 79)
- H4: (4, 79)

**Cost estimate:** ~$28 USD delivered (3 boards, ENIG, ~12 day lead time)

---

## 3. Electrical Specifications

### 3.1 Power Input
| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| Input voltage (TB1) | 11.0 V | 13.4 V | 14.6 V | LiFePO4 discharge to absorption range |
| Input current (typ) | — | 80 mA | 250 mA | At nominal voltage; peak during ESP32-C3 Wi-Fi TX |
| Pololu input range | 4.0 V | — | 36.0 V | Per Pololu D24V7F3 datasheet |
| Input protection | — | 1 A SB | — | Würth 696108003002 5×20 mm slow-blow fuse |

### 3.2 Power Output Rails
| Rail | Voltage | Source | Max load |
|---|---|---|---|
| BATT_RAW | = V_battery | TB1.2 (post-fuse) | Routed to INA260/U2 VBus tap |
| VIN | = V_battery | Post-fuse → C4/C5 → Pololu input | ~250 mA continuous through Pololu |
| +3V3 | 3.3 V ±2% | Pololu D24V7F3 output | 600 mA rated; ~80 mA actual load |

### 3.3 Signal Levels
| Signal | Type | Logic Level | Drive |
|---|---|---|---|
| SDA | I²C bidirectional | 3.3 V CMOS | Pulled up by Adafruit breakout (10 kΩ to 3.3 V) |
| SCL | I²C clock | 3.3 V CMOS | Pulled up by Adafruit breakout (10 kΩ to 3.3 V) |
| ALERT | Open-drain | 3.3 V CMOS | Pulled up to 3.3 V by R2 (10 kΩ external) + ESP32-C3 internal (~45 kΩ parallel) |
| GPIO10_DQ | 1-Wire | 3.3 V CMOS | DS18B20 sensor module has integral 4.7 kΩ pull-up |

### 3.4 Trace Width and Current Capacity (1 oz Cu, IPC-2152)
| Net | Width | Current Capacity (10 °C rise) | Actual Worst Case | Margin |
|---|---|---|---|---|
| BATT_RAW | 1.5 mm | ~5.5 A | 250 mA peak | 22× |
| VIN | 1.5 mm | ~5.5 A | 250 mA peak | 22× |
| +3V3 | 1.5 mm | ~5.5 A | ~100 mA | 55× |
| Signal traces | 0.25 mm | ~1.5 A | <10 mA each | 150× |
| Width override remnants | 1.0 mm | ~4 A | 0.78 mm total in 2 transition segments | 16× |

---

## 4. Bill of Materials

| Ref | Qty | Description | MFR | MFR P/N | Notes |
|---|---|---|---|---|---|
| U1 | 1 | XIAO ESP32-C3 module (socketed) | Seeed | XIAO ESP32-C3 | Plug-in via 2×7 pin sockets |
| U2 | 1 | Power monitor breakout (socketed) | Adafruit | 4226 (INA260) or 5832 (INA228) | 8-pin SIP header |
| U3 | 1 | 3.3 V step-down regulator (socketed) | Pololu | D24V7F3 | 3-pin SIP header, 600 mA |
| F1 | 1 | 1 A slow-blow fuse holder, 5×20 mm | Würth | 696108003002 | Through-hole, PCB-mount |
| TB1 | 1 | 2-pos terminal block, 2.54 mm pitch | TE Connectivity | 282834-2 | BATT+ (pin 2), GND (pin 1) |
| TB2 | 1 | 3-pos terminal block, 2.54 mm pitch | TE Connectivity | 282834-3 | +3V3 (pin 1), DQ (pin 2), GND (pin 3) |
| C1 | 1 | 10 µF ceramic, 50 V, radial | Generic | C_Disc_D5.0 | U3 bulk output decoupling |
| C2 | 1 | 0.1 µF ceramic, 50 V, radial | Generic | C_Disc_D3.8 | U2 +3V3 decoupling |
| C3 | 1 | 0.1 µF ceramic, 50 V, radial | Generic | C_Disc_D3.8 | U1 +3V3 decoupling |
| C4 | 1 | 47 µF aluminum electrolytic, 50 V | Generic | D6.3×11 radial | Pololu input bulk |
| C5 | 1 | 0.1 µF ceramic, 50 V, radial | Generic | C_Disc_D3.8 | Pololu input HF bypass |
| R1 | 1 | 1 kΩ ¼ W carbon film, axial | Stackpole | CF14JT1K00 | LED current limit |
| R2 | 1 | 10 kΩ ¼ W carbon film, axial | Stackpole | CF14JT10K0 | ALERT pull-up |
| LED | 1 | Green LED, 3 mm THT | Generic | Green diffused | Power indicator (cathode=GND, anode=R1) |
| H1–H4 | 4 | M3 mounting hardware | — | — | M3×8 mm screws + standoffs |

**Variant note for battery-bank deployment:** Replace U2 with Adafruit INA228 breakout (PID 5832). Desolder the breakout's onboard 15 mΩ shunt resistor. Wire external DROK 200 A / 75 mV shunt's sense leads to the breakout's terminal block. Solder the VBUS jumper closed on the breakout for high-side measurement.

---

## 5. Schematic / Net List

### 5.1 Net Summary
| Net | Pads | Total Routed Length | Function |
|---|---|---|---|
| BATT_RAW | 2 | 11.91 mm | Post-fuse battery rail; tap for INA260 VBus |
| VIN | 5 | 29.08 mm | Pololu regulator input bus |
| +3V3 | 9 | 84.19 mm | Regulator output to all ICs |
| GND | 11 | (copper pour) | Single-point return |
| SDA | 2 | 47.18 mm | I²C data, U2.4 ↔ U1.GPIO6 |
| SCL | 2 | 54.94 mm | I²C clock, U2.3 ↔ U1.GPIO7 |
| GPIO20_ALERT | 3 | 38.94 mm | INA260 ALERT, U2.5 ↔ R2 ↔ U1.GPIO20 |
| GPIO10_DQ | 2 | 52.28 mm | 1-Wire to TB2.2 ↔ U1.GPIO10 |
| LED_R1 | 2 | 8.64 mm | LED cathode to R1, R1 to +3V3 |

### 5.2 Pin-to-Function Map

**U1 — XIAO ESP32-C3:**
| Pin | Net | Function |
|---|---|---|
| 3V3 | +3V3 | Logic supply |
| GND | GND | Ground reference |
| GPIO6 (SDA, D4) | SDA | I²C data to U2 |
| GPIO7 (SCL, D5) | SCL | I²C clock to U2 |
| GPIO20 (D7_RX) | GPIO20_ALERT | INA260 ALERT interrupt |
| GPIO10 (D10) | GPIO10_DQ | DS18B20 1-Wire |
| 5V, D0–D3, D6, D8, D9 | NC | Unused on this board |

**U2 — INA260/INA228 breakout:**
| Pin | Net | Function |
|---|---|---|
| 1 | +3V3 | Logic supply |
| 2 | GND | Ground reference |
| 3 | SCL | I²C clock |
| 4 | SDA | I²C data |
| 5 | GPIO20_ALERT | Open-drain alert output |
| 6, 7, 8 | NC | (INA260: A0, A1, VBus — unused; INA228: IN+, IN-, VBus — accessed via breakout terminal block) |

**U3 — Pololu D24V7F3:**
| Pin | Net | Function |
|---|---|---|
| 1 | +3V3 | Vout (3.3 V regulated, 600 mA max) |
| 2 | GND | Ground |
| 3 | VIN | Input (4–36 V) |

**TB1 — Battery Input:**
| Pin | Net | Function |
|---|---|---|
| 1 | GND | Battery negative |
| 2 | BATT_RAW | Battery positive (+12 V nominal) |

**TB2 — DS18B20 Sensor:**
| Pin | Net | Function | Wire color |
|---|---|---|---|
| 1 | +3V3 | Sensor power | Red |
| 2 | GPIO10_DQ | 1-Wire data | Yellow |
| 3 | GND | Sensor ground | Black |

### 5.3 Key Topology Decisions

**VIN power path (through-pad topology):**
```
F1.2 → trace → C4.1 (47 µF bulk) → trace → C5.2 (0.1 µF HF bypass) → trace → U3.3 (Vin)
```
Current flows *through* both capacitors on its way to the regulator, ensuring both caps see the input current path rather than hanging as stubs. C4-to-C5 spacing 4.72 mm; C5-to-U3.Vin spacing 4.68 mm — within ideal range for clean two-cap input filtering up to ~7 MHz.

**ALERT pull-up topology:**
```
+3V3 ─┬── (rest of +3V3 net)
      │
     R2 (10 kΩ)
      │
      ├── ALERT trace ── U1.GPIO20
      │
      └── ALERT trace ── U2.5 (INA260 ALERT, open-drain)
```
R2 taps the +3V3 rail near U2 (cleanest local +3V3 reference) and connects to the ALERT trace near U2.5 to keep most of the trace at low impedance during open-drain pull events.

**Decoupling cap GND return paths:**
Every decoupling capacitor (C1, C2, C3, C4, C5) has a dedicated GND stitching via within 2.1 mm of its GND pad, keeping bypass loop inductance under ~7 nH and self-resonance above 6 MHz.

---

## 6. Layout Specifications

### 6.1 Board Layer Stack
| Layer | Function |
|---|---|
| F.Cu | All signal and power routing + GND pour |
| B.Cu | Solid GND pour (no signal/power traces) |
| F.SilkS | Component labels, polarity markers, pin function labels, board title |
| B.SilkS | Full BOM descriptions + board metadata (see §6.6) |
| Edge.Cuts | Board outline rectangle |

### 6.2 Design Rules
| Rule | Value | OSH Park Min | Margin |
|---|---|---|---|
| Minimum clearance | 0.3 mm | 0.152 mm (6 mil) | 97% |
| Default track width | 0.25 mm | 0.152 mm (6 mil) | 63% |
| Power track width | 1.5 mm | — | 22× current capacity |
| Via pad size | 0.7 mm | — | — |
| Via drill | 0.3 mm | 0.254 mm (10 mil) | 18% |
| Annular ring | 0.20 mm (7.9 mil) | 0.127 mm (5 mil) | 58% |
| Trace-to-edge | 4.25 mm min | 0.381 mm (15 mil) | 11× |

### 6.3 Copper Pour Coverage
Total copper area (including pads, traces, and pour):
| Layer | Net | Copper Area | Polygons | Notes |
|---|---|---|---|---|
| F.Cu | GND | 3189.77 mm² (~89% of board area) | 2 islands | Carved by signal/power traces |
| B.Cu | GND | 3443.19 mm² (~96% of board area) | 1 contiguous | Solid GND reference plane |

### 6.4 Via Stitching
- **Count:** 85 vias, all on GND net
- **Geometry:** 0.7 mm pad, 0.3 mm drill, 0.20 mm annular ring
- **Spacing:** mean 5.46 mm, min 3.50 mm, max 8.32 mm
- **Worst gap:** 6.36 mm from any point to nearest via
- **Density:** 1 via per ~36 mm² of board area
- **RF performance:** at 2.4 GHz Wi-Fi (λ ≈ 59 mm in FR4), average spacing of 5.46 mm equals λ/11 — exceeds RF best-practice λ/10

### 6.5 Silkscreen Content

**Front silkscreen (F.SilkS):** Component reference designators (R1, R2, C1–C5, U1–U3, F1, LED, TB1, TB2), pin function labels on socketed ICs and terminal blocks (Vout/GND/Vin on U3; SCL/SDA/ALT on U2 right column; 3V3/GND/5V/DQ on U1 east row; ALERT/SCL/SDA on U1 west row), polarity markers (+/− on C4 and LED, + on TB1.2), terminal block descriptions ("TB1 BATTERY", "TB2 DS18B20", + and GND on terminal pins), component descriptions ("Pololu D24V7F3", "Adafruit INA260", "F1 — 5 x 20mm 1A Slow Blow").

**Back silkscreen (B.SilkS):** This board carries an unusually thorough BOM-on-board documentation strategy — full component descriptions printed on the back so the BOM is permanently associated with the physical board, no separate datasheet needed:

| Position (mm) | Content |
|---|---|
| (23.5, 79.0) | `"UPS-Monitor-THT.kicad_pcb"` / `Rev 0` / `May 14, 2026` / `OSH PARK - Fabricator` |
| (23.5, 72.5) | `W. Collis` *(currently shows 'B. Collis' — verify before fab)* |
| (23.0, 51.0) | `Board Size:` / `46mm x 78mm` / `1 13/16" x 3 1/16"` |
| (23.0, 14.0) | `C1 — CAP CER 10UF 10% 25V X7R RADIAL` |
| (24.5, 18.0) | `C4 — CAP ALUM 47UF 20% 50V RADIAL` |
| (28.0, 20.0) | `R1 — 1K OHM 5% 1/4W AXIAL` |
| (39.5, 16.0) | `C2, C3, C5 — CAP CER 0.1UF 50V X7R RADIAL` |
| (39.5, 22.0) | `R2 — RES 10K OHM 5% 1/4W AXIAL` |

### 6.6 Component Placement

| Component | Position (mm) | Orientation |
|---|---|---|
| U1 (XIAO socket) | (17.35, 9.27) | Horizontal pin rows N/S |
| U2 (INA260 socket) | (37.36, 49.00) | Vertical pin row (180° rotated) |
| U3 (Pololu socket) | (21.46, 57.00) | Horizontal (90° rotated) |
| F1 (fuse) | (23.50, 78.00) | Horizontal, lower edge |
| TB1 (Battery) | (7.50, 65.50) | West edge, wire entry west |
| TB2 (DS18B20) | (7.50, 54.00) | West edge, wire entry west |
| C1 (10 µF bulk) | (21.50, 53.00) | Center between U3 and U2 |
| C2 (U2 decoupling) | (33.50, 46.50) | Adjacent to U2 |
| C3 (U1 decoupling) | (30.00, 28.00) | Just south of U1 |
| C4 (47 µF bulk) | (34.50, 57.00) | East side, between C5 and east edge |
| C5 (HF bypass) | (30.50, 54.50) | Between C4 and U3 in VIN path |
| R1 (LED current limit) | (7.50, 32.38) | West side |
| R2 (ALERT pull-up) | (32.00, 32.38) | Between U1 and U2 area |
| LED | (8.50, 21.73) | NW corner |

### 6.7 Drill Statistics

Total holes: **137** (85 vias + 48 PTH pads + 4 NPTH mounting)

| Count | Diameter | Type | Use |
|---|---|---|---|
| 85 | 0.30 mm | PTH via | GND stitching |
| 25 | 1.02 mm | PTH pad | Pin sockets for U1 (×14), U2 (×8), U3 (×3) |
| 14 | 0.80 mm | PTH pad | Ceramic capacitor leads (C1, C2, C3, C5) + axial resistor leads (R1, R2) |
| 5 | 1.10 mm | PTH pad | Terminal block leads (TB1 ×2, TB2 ×3) |
| 4 | 3.20 mm | NPTH | M3 mounting holes |
| 2 | 1.50 mm | PTH pad | Fuse holder F1 leads |
| 2 | 0.90 mm | PTH pad | LED leads + C4 electrolytic leads |

All drill diameters ≥ 0.254 mm OSH Park minimum.

---

## 7. Operating Parameters

### 7.1 Power Budget
| Component | Current Draw | Notes |
|---|---|---|
| ESP32-C3 (U1) | 30–80 mA typ, 250 mA peak | Peaks during Wi-Fi TX bursts |
| INA260/INA228 (U2) | 0.3 mA | Per datasheet |
| Pololu D24V7F3 quiescent | 0.3 mA | At no-load |
| DS18B20 sensor (via TB2) | 1.5 mA active, 1 µA idle | Brief reads at temperature sample |
| LED + R1 | 1.3 mA | At Vf ≈ 2 V, 3.3 V rail |
| **Total typical (3.3 V side)** | **~35 mA** | |
| **Total peak (3.3 V side)** | **~80 mA** | During Wi-Fi TX |

At 13.4 V battery with Pololu efficiency ~88% (typ): **~10 mA from battery typical, ~22 mA peak**

### 7.2 Thermal
- Pololu D24V7F3 thermal rise at 80 mA: negligible (<5 °C above ambient)
- Largest dissipator: R1 at 4.3 mW (LED current). Imperceptible.
- Operating temperature range (worst component): −40 °C to +85 °C (limited by INA260 commercial grade)

### 7.3 Electrical Performance
- INA260 (V1 use case): bus voltage 0.5% accuracy, current ±0.15% at full-scale 15 A, ±1.25 mV LSB on shunt
- INA228 (V2 battery bank use case): 20-bit ADC, ~0.83 mA LSB through 0.375 mΩ DROK shunt at ±163.84 mV range
- Update rate: configurable 50 µs to 4.12 ms per conversion (firmware-controlled)
- I²C bus speed: 100 kHz standard / 400 kHz fast (firmware-selectable)
- Wi-Fi connectivity: 2.4 GHz 802.11 b/g/n via ESP32-C3 onboard antenna

### 7.4 Reliability Factors
- Connectorized ICs (U1, U2, U3): all in sockets for easy replacement
- Single-point fuse protection: F1 protects entire downstream circuit
- Polarity protection: not implemented (relies on silk markers + user care at install)
- ESD protection: relies on chip-internal protection (typically ±2 kV HBM)
- Surge protection: not implemented (battery wire is short, no inductive loads)

---

## 8. Firmware Interface

### 8.1 ESP32-C3 Pin Assignments
```c
#define PIN_SDA      6      // I²C data, GPIO6 (D4)
#define PIN_SCL      7      // I²C clock, GPIO7 (D5)
#define PIN_DQ       10     // DS18B20 1-Wire, GPIO10 (D10)
#define PIN_ALERT    20     // INA260 alert input, GPIO20 (D7_RX)
```

### 8.2 I²C Configuration
- INA260 / INA228 address: 0x40 (default)
- DS18B20: 1-Wire bus on PIN_DQ, no I²C

### 8.3 ALERT Pin Configuration
- Input mode: `INPUT` (R2 external pull-up provides idle-high state; do NOT enable `INPUT_PULLUP` — internal pull-up adds 45 kΩ parallel which is unnecessary)
- Interrupt edge: `FALLING` (INA260 asserts ALERT low on threshold trigger)
- Idle voltage: 3.3 V (pulled high by R2 = 10 kΩ)
- Asserted voltage: ~0 V (INA260 sinks via internal open-drain)

### 8.4 Library Requirements
- For V1 (INA260): `Adafruit_INA260` Arduino library
- For V2 (INA228): `Adafruit_INA228` or `RobTillaart/INA228` library
- DS18B20: `OneWire` + `DallasTemperature` libraries
- Wi-Fi/MQTT: standard `WiFi.h` + `PubSubClient` (or ESPHome native config)

### 8.5 Calibration (INA228 V2 use case only)
```cpp
ina228.setShunt(0.000375, 200.0);  // 0.375 mΩ DROK, max 200 A
ina228.setAdcRange(0);              // ±163.84 mV (full range for 200 A)
```

---

## 9. Manufacturing Notes

### 9.1 Pre-Submission Checklist (completed)
- [x] All routed nets electrically continuous (DRC: 0 unconnected pads)
- [x] Trace widths sized for current (power 1.5 mm, signal 0.25 mm)
- [x] Via geometry meets OSH Park spec with margin (0.7/0.3 mm)
- [x] Edge clearance > 4 mm everywhere
- [x] Decoupling caps have local GND vias (≤ 2.1 mm each)
- [x] Polarity markers on all polar components (C4, LED, TB1)
- [x] Pin function labels on terminal blocks (TB1, TB2)
- [x] Pin function labels on socketed IC pin rows
- [x] Board title, author, fab name, date on F.Silk and B.Silk
- [x] Full BOM descriptions printed on B.Silk for permanent reference
- [x] Through-pad input filter topology (F1 → C4 → C5 → U3)

### 9.1.1 Outstanding Items Before Submission
- [ ] **Verify author name on B.Silk** at (23.5, 72.5) — currently reads "B. Collis"; confirm this is intentional or update to "W. Collis"

### 9.2 DRC Status
**19 violations, all `Local override; warning` — none affect manufactured board:**
- 13× `lib_footprint_mismatch` — version-drift advisories on standard library footprints (U1, U2, U3, R1, R2, C1, C2, C3, C4, C5, LED, TB1, TB2)
- 1× `lib_footprint_issues` — UPS_Custom library (Würth fuse holder) not in default search path
- 3× `silk_overlap` — U2/C1 silk text proximity (cosmetic)
- 2× `silk_over_copper` — U2 silk outline clipped at C3 pads (standard fab behavior — silk masks at pad openings)

### 9.3 Submission to OSH Park
1. Export Gerbers using KiCad GUI File → Plot (NOT kicad-cli — silently skips zone fills)
2. Verify ZONE_FILLER ran before export (look for substantial F.Cu / B.Cu polygon coverage)
3. Upload Gerbers zip to OSH Park
4. **Verify in OSH Park web preview before paying**: check each layer renders correctly, especially silk text legibility
5. Standard 2-Layer Proto Service: 3 boards for ~$28, ~12 day lead time, ENIG finish included

### 9.4 Assembly Notes
- Hand-solder all THT components
- Recommended order: passives (R1, R2, C1-C5), LED, fuse holder F1, terminal blocks TB1/TB2, then SIP sockets for U1/U2/U3
- **Critical orientation checks before powering:**
  - C4 electrolytic: '−' stripe aligned with silk '−' marking
  - LED: cathode (flat side, shorter lead) on '−' pad
  - U1 XIAO module: verify "ESP32-C3" labeling before insertion (not S3 or RP2040)
  - U2 INA260/INA228: pin 1 matches silk pin-1 indicator
  - U3 Pololu: Vin/GND/Vout labeling matches silk (verify with meter before applying 12 V)
- Power-up test sequence: connect 12 V, verify LED illuminates, measure +3V3 at U1 socket
- Operating verification: USB-flash ESP32-C3 firmware once; thereafter OTA updates only

### 9.5 Critical Safety Note
**VBUS on the INA260 breakout connects to BATT_RAW. Never connect USB to the XIAO while the board is powered from 12 V battery.** USB +5 V would back-feed into the +3V3 net or compete with the Pololu output. Firmware flashing should occur only with TB1 disconnected. After initial USB flash, all firmware updates should use OTA.

---

## 10. Validation Plan (Post-Fabrication)

### 10.1 Initial Power-Up
1. Visually inspect all solder joints under magnification
2. Continuity check between TB1+ and TB1− (should be open, not shorted)
3. Continuity check between +3V3 and GND with U3 socket empty (open)
4. Connect 12 V from bench supply (current limited to 500 mA) to TB1
5. Verify F1 doesn't blow
6. Measure +3V3 at U3.1 (should read 3.30 V ±0.07 V)
7. Insert U1 (XIAO), U2 (INA260), U3 (Pololu) in their sockets
8. Verify LED illuminates
9. Measure battery current: should be 10–25 mA at 12 V input

### 10.2 Functional Verification
1. Flash ESP32-C3 via USB with test firmware
2. Verify I²C device discovery returns INA260 at 0x40
3. Read INA260 bus voltage: should match battery voltage ±0.5%
4. Read INA260 current: at no-load, should read 5–25 mA (own consumption)
5. Apply known load to BATT_RAW (e.g., 1 A through external resistor) and verify INA260 reads within ±1% of true value
6. Connect DS18B20 to TB2, verify 1-Wire bus discovers sensor
7. Trigger INA260 ALERT (set low threshold below current draw), verify ESP32-C3 ISR fires and ALERT pin goes low

### 10.3 EOL Calibration
Document INA260 calibration coefficients against a reference meter for the actual deployment current range.

---

## 11. Design History and Lessons Learned

### 11.1 Revision History
- **V1.0** (May 14, 2026): Released to OSH Park. Power traces 1.5 mm, 85 GND stitching vias, R2 ALERT pull-up, C5 HF bypass, fully through-pad VIN topology. Min clearance tightened to 0.3 mm. BOM-on-board silk added to B.Silk.
- **V0.3** (May 13): Added R2, C5; bumped via pads from 0.6 to 0.7 mm
- **V0.2** (May 12): Fixed SDL→SDA silk typo, R1 value field (680R→1k)
- **V0.1** (May 11): Initial layout, INA260 single-shunt topology

### 11.2 V2 Improvements (Planned)
For a future revision dedicated to the battery bank application:
- P-channel MOSFET reverse-polarity protection on TB1 input
- Dedicated terminal block (3 or 4 positions) for shunt-sense wires routed as Kelvin differential pair away from switching nets
- 100 Ω series + 0.1 µF low-pass filters on DQ and sense lines (inverter EMI rejection)
- Optional TVS (P6KE18CA) across BATT_RAW for transient protection
- Diagonal +3V3 routing through repositioned R1 (cosmetic tidiness)
- Test points for BATT_RAW, VIN, +3V3, GND for debug probing
- Board name + revision + date on visible silk corner

### 11.3 Key Design Decisions Documented
- **2-pin TB1 (vs design intent's 3-pin):** dual-GND on TB1 would save <0.65 mV at peak 250 mA load (below INA260 LSB of 1.25 mV). INA260 measures differentially, so common-mode ground shifts don't affect current accuracy. 2-pin is electrically adequate.
- **No TVS on V1:** short battery wire (<30 cm), quiet LiFePO4 source, no inductive loads sharing the bus. TVS skipped for V1; recommended for V2 if deployed in inverter-bank context.
- **VIN through-pad topology over stub topology:** forces current through C4 and C5 sequentially rather than past them. Lower effective bypass loop inductance for HF noise from Pololu switching at ~700 kHz.
- **R2 placement near U2:** keeps high-impedance ALERT trace section between R2 and U1 short, minimizing crosstalk pickup. R2 sources +3V3 from cleanest local rail (near C2 decoupling).
- **0.7 mm vias over 0.6 mm:** doubles annular ring margin against OSH Park's worst-case tolerance stack (±2.5 mil position, ±2.5 mil drill diameter). Zero clearance cost on this layout.
- **Pour split into 2 islands on F.Cu, 1 on B.Cu:** F.Cu pour gets carved by signal routing into 2 regions (large + small); B.Cu pour is unobstructed since no traces on bottom layer. Stitching vias bridge the two F.Cu islands through the B.Cu plane.

---

## 12. References and Datasheets

| Document | Source |
|---|---|
| Seeed XIAO ESP32-C3 wiki | https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/ |
| Adafruit INA260 breakout (PID 4226) | https://www.adafruit.com/product/4226 |
| Adafruit INA228 breakout (PID 5832) | https://www.adafruit.com/product/5832 |
| Pololu D24V7F3 datasheet | https://www.pololu.com/product/2842 |
| INA260 datasheet | Texas Instruments SBOS763 |
| INA228 datasheet | Texas Instruments SBOS951 |
| DS18B20 datasheet | Maxim Integrated DS18B20 |
| Würth fuse holder 696108003002 | Würth Elektronik catalog |
| OSH Park 2-layer specs | https://docs.oshpark.com/services/two-layer/ |

---

## 13. License and Attribution

Designed by William Collis (GitHub: wkcollis1-eng). Hardware design released under CERN-OHL-S (or equivalent permissive open-source hardware license at designer's discretion). Reuse and modification encouraged with attribution.

---

*End of design document.*
