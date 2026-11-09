# UPS Monitor Rev 4: design document

**Status (2026-11-08):** layout in progress, not fabricated, no Rev 4 firmware yet.
**Master file:** `UPS-Monitor-Rev 4.kicad_pcb` (not yet in this repository). The board is the
master; the schematic was
synced from it on 2026-11-08 and is checked against it with KiCad's schematic-parity DRC.

Figures carry the repository's provenance tags: **[M]** measured, **[S]** specification or prior
document, **[D]** derived by the arithmetic shown, **[I]** inferred and not yet tested (with the
observation that would falsify it). An [M] with no other source was read from the board file
saved 2026-11-08 19:43, using KiCad 10's Python API.

---

## 1. What the board does, and the moment it has to survive

The board sits on the DIY LiFePO4 UPS's 12 V battery bus.
- It measures pack voltage, current and power with an INA260, and temperature with a DS18B20.
  It reports both to Home Assistant through ESPHome on a XIAO ESP32-C3.
- **New in Rev 4:** it powers the cable modem from its own 12 V regulator (U4). That
  replaces the Victron BP-65 low-voltage disconnect [S: schematic note]. It also reads whether
  mains is present.

**The unattended moment:** a long overnight outage with nobody home. "Working" at that moment
means all of the following:
- The modem stays powered while the battery has margin.
- The modem is shed only on battery, and only when the firmware asks.
- No failure of the monitor itself (crash, reset, brown-out, XIAO unplugged) can turn the
  modem off.
- When mains returns, the modem comes back on whatever the firmware is doing.

The enable network in section 4.4 is built so that every one of those holds in hardware.

## 2. Block diagram

```
BUS + (battery) ── F1 ── VIN ─┬─ U3 Pololu D24V7F3 ── +3V3 ── XIAO, INA260 logic, DS18B20, R1
                              └─ U4 Pololu S13V25F12 (EN) ── +12V_MODEM ── MODEM terminal
                                         ▲
GPIO5 MODEM_OFF ── R2/R3 ── Q1 ──────────┘  (Q1 pulls EN low = modem OFF)
                             ▲
PSU_SENSE ─┬─ R4/R5 ── Q2 ───┘  (Q2 clamps Q1's base while mains is present)
           └─ R7/R6, C7 ── GPIO4 (ADC)
INA260 (U2) ── I2C GPIO6/7, Alert GPIO3 (R1 pull-up)      DS18B20 (TB2) ── GPIO10
```

## 3. Interfaces

| Ref | Part | Pin 1 | Pin 2 | Pin 3 |
|---|---|---|---|---|
| BUS | Phoenix MKDS 3.81 mm, 2-pole | GND | BATT_RAW (battery +, to F1) | |
| MODEM | Phoenix MKDS 3.81 mm, 2-pole | GND | +12V_MODEM (U4 output) | |
| PSU_SENSE | Phoenix MKDS 3.81 mm, 2-pole | GND | PSU_SENSE | |
| TB2 | TE 282834-3, 2.54 mm, 3-pole | +3V3 | GND | DQ (GPIO10) |

**Test points** (2.0 mm pads with 1.0 mm drill): VIN, GND, 3V3, MODEM_EN and +12V MODEM [M].

**PSU_SENSE wiring.** It is wired to the Mean Well HDR-60-12 output, upstream of the Pololu #5382
ideal diode, so it reads about 0 V with mains off (owner, 2026-11-08). The commissioning backfeed
test measured 0.10 V there [M: commissioning test, as recorded 2026-11-08].

**TB2 pin order is a wiring hazard.** Rev 4 runs 3V3 / GND / DQ [M]. The deployed board's JST-XH
ran GND / DQ / 3V3 [M: `UPS-Monitor-THT.kicad_pcb` in the repo]. The DS18B20's own order is
GND / DQ / VDD. Rev 4's "GND" silk label sits 1.46 mm from pad 2 and 1.08 mm from pad 3 (DQ)
[M], so it points nearer the wrong pad. Check the pins with a meter before the sensor goes on
(see section 9).

## 4. Circuit blocks

### 4.1 Input and fuse
BUS + reaches F1, a Würth 696108003002 holder for 5x20 mm fuse-links, and leaves as VIN.
- Track widths are 2.0 mm on BATT_RAW, 1.6 to 2.1 mm on VIN and 1.8 mm on +12V_MODEM [M].
- F1 now carries U4 (the modem) as well as U3. The schematic note puts that at about 1.1 to
  1.2 A at 12 to 11.8 V [S: schematic note, D: 13.4 W bus load / V].
- The fuse is 2 to 2.5 A (owner, 2026-11-08). A time-lag, DC-rated link is advised (schematic note).
- Bulk decoupling on VIN: C4 47 µF 50 V aluminium electrolytic, plus C5 and C6 0.1 µF X7R.
  C6 sits at U4.

### 4.2 3.3 V supply
U3 is a Pololu D24V7F3 step-down module in a 1x3 socket: pin 1 +3V3, pin 2 GND, pin 3 VIN.
- +3V3 feeds the XIAO's 3V3 pin (pad 12), the INA260's VCC, the DS18B20 and R1.
- The XIAO's 5V pin (pad 14) is not connected [M].
- Decoupling: C1 10 µF X5R, C2 and C3 0.1 µF.

### 4.3 Modem 12 V (U4)
U4 is a Pololu #4984 S13V25F12, a 12 V ±4 % step-up/step-down regulator [S: Pololu #4984 page].
- It is mounted on the **bottom** side and uses only the module's 0.1 in row, in the order
  EN, VIN, GND, GND, VOUT [S: Pololu product picture + STEP hole positions, per schematic note].
  **Confirm that order on the module in hand before soldering.**
- EN is active-low, with a 475 kΩ internal pull-up to VIN and a 1.0 to 1.2 V threshold
  [S: Pololu #4984 page].

### 4.4 Modem-enable logic (Q1, Q2)
Q1 and Q2 are 2N3904 transistors, formed-lead TO-92 (Diotec, 2.54 mm).
- **Q1** pulls U4's EN low, which turns the modem off. GPIO5 (MODEM_OFF) drives its base
  through R2 100k, and R3 100k holds the base to GND.
- **Q2** shorts Q1's base to GND whenever PSU_SENSE is up. PSU_SENSE drives Q2's base through
  R4 100k, and R5 22k holds that base to GND.

| GPIO5 (MODEM_OFF) | Mains (PSU_SENSE) | Q2 | Q1 | Modem |
|---|---|---|---|---|
| high-Z (ESP off, reset, crashed, unplugged) | any | any | off (R3) | **ON** |
| low | any | any | off | **ON** |
| high | present (over about 3.0 to 3.3 V) | on | off (base clamped) | **ON** |
| high | absent | off (R5) | on | **OFF** |

**Design figures.** These are worked at an assumed PSU output of 13.8 V. The HDR-60-12 set
point is not recorded on the board.
- **Mains override threshold:** about 3.0 to 3.3 V [D: VBE 0.55 to 0.6 V [I] x 122/22].
- **GPIO5 at reset:** high-Z with no pull [S: ESP32-C3 datasheet v2.4, Table 2-1]. R3 is
  what keeps the modem on through boot.
- **Q1 drive:** base current about 21 µA [D: (1.65 − 0.6) V / 50 kΩ]. It sinks the EN pull-up,
  at most about 29 µA [D: 13.8 V / 475 kΩ], so forced β is about 1.4 [D].
- **Q2 drive:** base current about 105 µA [D: (2.49 − 0.6) V / 18.0 kΩ]. It sinks R2's
  33 µA [D: 3.3 V / 100 kΩ], so forced β is about 0.3 [D].
- **Saturation check:** both transistors are deep in saturation [I]. That is falsified if the
  MODEM_EN test point reads above about 0.2 V with GPIO5 high and mains absent.

### 4.5 Mains readback (PSU_ADC)
R7 100k runs from PSU_SENSE to PSU_ADC, R6 18k from PSU_ADC to GND, and C7 0.1 µF from PSU_ADC
to GND. PSU_ADC goes to XIAO pad 3 (D2 = GPIO4, ADC1).
- **Scale:** the pin sees 18/118 = 0.1525 of PSU_SENSE, which is 2.10 V at 13.8 V [D].
- **Range:** ADC1 at its 12 dB setting reads 0 to 2500 mV with a calibrated total error of
  ±35 mV [S: ESP32-C3 datasheet v2.4, Table 5-6, p. 56]. That covers up to 16.4 V at the
  terminal [D: 2.5 V x 118/18].
- **Uncalibrated accuracy at 13.8 V:** about ±1.2 V from the 5 % carbon-film resistors the
  board lists now [D: (100/118) x 10 % x 13.8 V], or ±0.23 V with the 1 % parts chosen in
  section 6 [D: (100/118) x 2 % x 13.8 V]. Add ±0.23 V from the ADC [D: 35 mV x 118/18].
  That is fine as a mains-present signal but rough as a voltage.
- **Calibrated accuracy:** a one-point calibration against a DMM at the terminal removes both
  errors at the set point. The residual should be tens of mV [I]. That is falsified if a day's
  readings drift more than about 0.1 V from DMM spot checks.
- **Source impedance:** 15.25 kΩ [D: 100k ‖ 18k]. With C7 that is a 1.5 ms time constant [D].
  100 nF is also the datasheet's own test condition for its linearity figures [S: Table 5-5].
- **If the PSU_SENSE wire comes off:** R5 holds Q2 off (no override) and the ADC reads 0 V.
- **Load on the PSU:** about 0.23 mA for both dividers together [D: 13.8/122k + 13.8/118k].

### 4.6 Monitoring (INA260, DS18B20)
**INA260 (U2)** is an Adafruit breakout in a 1x8 socket: 1 VCC (+3V3), 2 GND, 3 SCL, 4 SDA,
5 Alert.
- Pins 6 to 8 (VBus, Vin+, Vin−) are not connected on this PCB [M]. The measured current runs
  through the breakout's own terminal block, as on the deployed board (schematic note).
- The breakout carries the I2C pull-ups [S: firmware header].
- R1 10k pulls Alert up to +3V3. On the deployed board this resistor is called R2, so the
  firmware comment needs updating.

**DS18B20** connects on TB2 to GPIO10. **There is no 1-Wire pull-up on this board** [M], and the
deployed board had none either [M]. The pull-up is in the sensor lead (owner, 2026-11-08); its
value is not recorded. **A replacement sensor must bring its own pull-up** (typically 4.7k from DQ
to VDD), or nothing will read on GPIO10.

### 4.7 XIAO ESP32-C3 pin map
The XIAO sits on female and male headers, about 10 mm above the board (owner).

| Pad | XIAO | GPIO | Net |
|---|---|---|---|
| 2 | D1 | GPIO3 | Alert (INA260) |
| 3 | D2 | GPIO4 (ADC1) | PSU_ADC |
| 4 | D3 | GPIO5 | MODEM_OFF |
| 5 | D4 | GPIO6 | SDA |
| 6 | D5 | GPIO7 | SCL |
| 11 | D10 | GPIO10 | DQ (1-Wire) |
| 12 / 13 | 3V3 / GND | | +3V3 / GND |
| 1, 7-10, 14 | D0, D6-D9, 5V | | not connected |

The strapping pins (GPIO2/8/9) and UART pins (GPIO20/21) are deliberately unused (schematic
note). The underside pads 15 to 23 cannot be reached through the sockets.

**Footprint check against Rev 1.** Rev 1's custom XIAO footprint names its pads by function.
The pad it calls "GPIO3" sits fourth from D0, which is the D3 position (GPIO5). So Rev 1's
ALERT reaches GPIO5 while the firmware reads GPIO3 [M: pad positions in
`UPS-Monitor-THT.kicad_pcb`; this is the CHANGELOG's Pending item]. Rev 4's footprint numbers
pads 1 to 14 in Seeed's order. The two rows pair D0/5V, D1/GND, D2/3V3, D3/D10, D4/D9, D5/D8
and D6/D7, and run counter-clockwise seen from the top, as on the module [M: pad positions,
2026-11-08]. Rev 4 therefore puts Alert on GPIO3, where the firmware already reads it.

## 5. Failure modes

| Event | Result | Basis |
|---|---|---|
| ESP crashes, resets, browns out or is unplugged | Modem stays ON | 4.4 truth table |
| Firmware asserts MODEM_OFF while mains is present | Modem stays ON | Q2 override |
| PSU_SENSE wire comes off with mains present | No override, and the ADC reads "mains absent". The firmware sheds only if the battery is also ≤ 11.8 V, which it should not be while mains is charging it [I]. | Falsified by a float voltage at or below 11.8 V |
| Mains lost | Q2 keeps the override until the HDR output decays below about 3 V, so MODEM_OFF works only after that decay | **Decay time unmeasured** (open item 6) |
| ESP deep-sleeps after shedding the modem | GPIO5 may float, and R3 then turns the modem back ON unless the pin is held | **Untested** (open item 7) |
| F1 blows, or U4 fails | Modem off. Nothing on the board bypasses F1 or U4. | Design trade: the modem now depends on F1, U4 and this board |
| Pack hits BMS cutoff, then recovers | Everything restarts, and U4's EN pull-up brings the modem back without firmware | 4.3 |

## 6. Mechanical and assembly

**Board:**
- Outline 38.10 x 53.85 mm, 2 layers, 1.60 mm thick, GND pour on both layers [M].
- Fabricator per back silk: OSH Park.
- **The back-silk "Board Size: 38.25mm x 58.75mm" text is stale** [M: outline 53.85 mm long].

**Mounting holes:** three M3 holes, H1, H2 and H4.
- H1 sits under the INA260 and gets a standoff to support its overhang (owner).
- H2 sits under the XIAO and is board-only ("Not in schematic").
- In the 3D view, the Würth 15 mm standoffs hang below the board. A standoff supporting the
  INA260 would sit on top, about 10 mm tall if the INA260 uses the same header stack as the
  XIAO [I].

**Under the XIAO** (about 10 mm clearance) [M: overlap with U1's fab outline]:
- R1 to R3.
- C3 and C7: body 3.6 mm [S: distributor listings for K104K10X7RF53L2].
- H2's screw head.
- Only pad 1 of Q1 and of Q2.

**Height limit:** vertical resistors are kept under 8 mm (owner).
- Digi-Key's pre-formed "radial bend" parts do not fit. Stackpole Panasert forming is 5.08 mm
  pitch, up to 12.50 mm tall [S: Stackpole RNF/RNMF datasheet, 3/30/2023, p. 7], against these
  2.54 mm pads (0.80 mm drill) [M].
- **Chosen (owner, 2026-11-08):** plain-lead Stackpole RNMF14 mini metal film, formed upright
  by hand, for R1 to R7. Its body is 3.30 x 1.78 mm [S: same datasheet, p. 2], about 5.8 mm
  tall standing [D: 3.30 + 2.50 bend allowance]. It also gives 1 % / ±50 ppm on the R6/R7
  divider [S: p. 1]. The existing 2.54 mm footprints stay. The board's part fields will be
  updated to match; until then they list 5 % carbon film.

**Assembly order:**
1. Fit H2's screw before the XIAO. The XIAO has to come out to reach it again.
2. Solder the parts that go under the modules before their sockets.
3. Fit U4 on the bottom side.

## 7. Verification status (2026-11-08)

| Check | Result |
|---|---|
| DRC, 19:43 board | 100 violations, 43 errors, 0 unconnected [M] |
| DRC errors by type | 34 PTH inside courtyard, 6 NPTH inside courtyard, 3 courtyard overlaps; no clearance or copper errors [M]. This fits parts deliberately placed under the socketed modules, but each one has not been reviewed [I]. |
| DRC warnings by type | 18 silk over copper, 15 silk-to-edge, 13 library-footprint mismatch, 7 silk overlap, 3 co-located holes (screw models over H1/H2/H4), 1 text height [M] |
| Schematic ERC | 0 [M, 18:48] |
| Netlist, schematic vs 18:10 board | "differences: 0" [M] |
| Schematic parity vs 19:43 board | 8: five REF** screw models (board side), plus C7's value and Q1/Q2's Description changed on the board since the sync [M] |
| Fabricated / assembled / powered | **No** |
| U4 pin order on the actual module | **Not checked** |
| Rev 4 firmware | **Not written** |

## 8. Firmware requirements for Rev 4

- **GPIO5 (MODEM_OFF):** output, LOW at boot and on restore (modem on). Drive HIGH only when
  battery ≤ 11.8 V **and** mains is absent [S: schematic note]. Decide and test how it behaves
  through deep sleep (open item 7).
- **GPIO4 (PSU_ADC):** ADC at 12 dB attenuation, averaged.
  - Multiply by 118/18 = 6.556 nominal [D], then replace that with DMM ÷ reading.
  - The mains-present threshold must sit between the 0.10 V backfeed [M] and the PSU set point.
  - To time the HDR decay, sample faster than the decay itself. A slow poll gives only a bound.
- **Unchanged from the deployed firmware:**
  - INA260 on I2C GPIO6/7, at the address set by the module's A0 jumper (0x40 on this build)
    [S: firmware header].
  - Alert on GPIO3, now pulled up by R1. Do not carry over any GPIO5 Alert workaround for
    Rev 1's routing (section 4.7): GPIO5 is MODEM_OFF on this board.
  - DS18B20 on GPIO10.
- Run the ESP firmware validation gate (compile, not just config-valid) before flashing.

## 9. Open items

1. **TB2:** the silk "GND" label sits nearer pad 3 (DQ) than pad 2, and the pin order differs
   from the deployed board. Fix the silk, or meter the pins before connecting the sensor.
2. ~~**1-Wire pull-up:** where is the deployed DS18B20's pull-up?~~ **RESOLVED 2026-11-08:** it
   is in the sensor lead (owner). No board change. See section 4.6 about replacement sensors.
3. **Back silk:** the "Board Size" text is stale (58.75 mm vs 53.85 mm).
4. **REF\*\* screw models:** give them unique references and tick "Not in schematic" to clear
   5 parity items.
5. **Schematic:** it trails the board by C7's Value and Q1/Q2's Description.
   **BOM CSV** (16:09) predates R6, R7 and C7 and lists R1 as horizontal; regenerate it from
   the board.
6. **HDR-60-12 decay:** how long the output takes to fall after AC loss is unmeasured. It sets
   the delay before a shed takes effect.
7. **GPIO5 through deep sleep:** if the pin is not held, the modem turns back on during survival
   sleep.
8. **U4:** confirm the 0.1 in row pin order on the module in hand.
9. **Resistors:** RNMF14 chosen (section 6); the board's part fields and BOM still to be
   updated. **INA260 standoff:** check whether a breakout mounting hole lines up with H1.

## Sources

- [ESP32-C3 Series Datasheet v2.4 (Espressif)](https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf): Table 2-1; §5.5, Tables 5-5 and 5-6, p. 56.
- [Seeed XIAO ESP32C3 wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/): pin map.
- [Pololu #4984 S13V25F12](https://www.pololu.com/product/4984): output, EN pull-up and threshold.
- [Stackpole RNF/RNMF datasheet](https://www.seielect.com/catalog/SEI-RNF_RNMF.pdf), rev 3/30/2023: pp. 1, 2, 7.
- [element14: K104K10X7RF53L2](https://nz.element14.com/vishay/k104k10x7rf53l2/cap-0-1-f-50v-10-x7r/dp/2860096): body height.
- Schematic notes in `UPS-Monitor-Rev 4.kicad_sch` (not yet in this repository).
- Deployed firmware header: [`ups-monitor.yaml`](../UPS-Monitor/ups-monitor.yaml).
- Deployed board: [`UPS-Monitor-THT.kicad_pcb`](../UPS-Monitor/UPS-Monitor-THT.kicad_pcb).
- Pending item on Rev 1's ALERT routing: [CHANGELOG.md](../CHANGELOG.md).
