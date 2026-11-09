# UPS Monitor Rev 4: design document

**Status (2026-11-09):** layout in progress, not fabricated, no Rev 4 firmware yet.
**Document revision:** 2 (2026-11-09). Section 1 now records the system the board serves: a UPS
dedicated to the Xfinity XB7 modem. See the revision history at the end.
**Master file:** `UPS-Monitor-Rev 4.kicad_pcb` (not yet in this repository). The board is the
master; the schematic was
synced from it on 2026-11-08 and is checked against it with KiCad's schematic-parity DRC.

Figures carry the repository's provenance tags: **[M]** measured, **[S]** specification or prior
document, **[D]** derived by the arithmetic shown, **[I]** inferred and not yet tested (with the
observation that would falsify it). An [M] with no other source was read from the board file
saved 2026-11-08 19:43, using KiCad 10's Python API.

---

## 1. The system, the board, and the moment it has to survive

### 1.1 Scope

This UPS has one load: the Xfinity XB7 cable modem, at 12 V DC (owner, 2026-11-09).
- **Not on this system:** the N100DC host and its 18 V Pololu U3V70A boost (owner,
  2026-11-09). BOOST-DS-r1, its EN shed (DR-1/OP-2) and the README's unattended-recovery gap
  do not apply to it.
- **Removed:** the Victron BP-65. The firmware shed through Q1 (section 4.4) is now the only
  low-voltage disconnect above the battery's own BMS (section 1.6).
- **PSU:** a Mean Well HDR-60-12, trimmed to 13.6 V (owner, 2026-11-09; section 1.5).
- **Battery:** a new Cyclenbatt 12 V 10 Ah LiFePO4 pack (owner, 2026-11-09; section 1.6). No
  capacity, resistance or discharge-phase figure measured on the previous pack applies to it.

The board sits on the UPS's 12 V bus.
- It measures the battery branch's voltage, current and power with an INA260, and temperature
  with a DS18B20. It reports both to Home Assistant through ESPHome on a XIAO ESP32-C3.
- **New in Rev 4:** it powers the modem from its own 12 V regulator (U4), in place of the
  BP-65 [S: schematic note]. It also reads whether the PSU's output is present.

### 1.2 The unattended moment

A long overnight outage with nobody home. "Working" at that moment means all of the following:
- The modem stays powered while the battery has margin.
- The modem is shed only on battery, and only when the firmware asks.
- No failure of the monitor itself (crash, reset, brown-out, XIAO unplugged) can turn the
  modem off.
- When mains returns, the modem comes back on whatever the firmware is doing.

The enable network in section 4.4 is built so that every one of those holds in hardware.

### 1.3 Topology

```
120 VAC ─► HDR-60-12, 13.6 V ─┬─► Pololu #5382 ideal diode ─► 12 V bus (Wago)
                              │                                │
                              └─► PSU_SENSE (board)            ├─► INA260 VIN+ ─ shunt ─ VIN− ─► Cyclenbatt 10 Ah
                                                               │
                                                               └─► BUS (board) ─► F1 ─┬─► U3 3.3 V ─► monitor
                                                                                      └─► U4 12 V ─► MODEM ─► XB7
```

- **Mains present:** the PSU holds the bus at its set point less the #5382's drop
  (section 1.5). The pack floats, and the PSU carries the board and the modem.
- **Mains lost:** the #5382 blocks, and the pack carries the board and the modem through the
  INA260. U4 holds the modem at 12 V while the bus falls (section 1.4).
- **BUS lands on the bus side of the INA260 (VIN+), not on Battery+.** All of the system's
  load now passes through BUS: 0.98 to 1.28 A at float (section 1.7).
  - If BUS were on Battery+, that current would bypass the shunt on battery. The INA260 would
    read about 0 A while the pack discharged.
  - On mains it would read the load as about 1 A of charge that the pack is not taking [D].
  - The board's net name for BUS pin 2, BATT_RAW, invites that wiring (open item 10).
- **Today's tap looks bus-side.** At the 2026-11-05/06 equilibrium, with the board then in
  service, the INA260 read a median of +0.7 mA (n = 17,606) [M: Top-Off design §10.2, rev 0.20].
  A tap on Battery+ would have shown that board's ~35 mA as a standing +35 mA [D].
  - This stays [I] until the wiring is traced. The enclosure wiring was replaced between
    2026-10-31 and 11-04 (owner) and is not drawn in this repository.
  - `docs/wiring.md` is the March 2026 build.

### 1.4 The modem: Xfinity XB7

| Item | Value | Basis |
|---|---|---|
| Input | 12 V DC nominal. Comcast publishes no DC input range. The ±10 % (10.8 to 13.2 V) used in `docs/` comes from IEC 62368-1 design practice | [S: `docs/specifications.md`; I] |
| Connector | 5.5 x 2.1 mm barrel, centre-positive | [S: `docs/wiring.md`] |
| OEM adapter | NBC56B120460VU, 12.0 V / 4.6 A, DoE Level VI (at least 88 %) | [S: adapter label, per `docs/specifications.md`] |
| Power, spot figure | 12.2 W DC, the figure the reports have used since April 2026 | [S: 04-05 and 05-06 reports] |
| Power, from the wall | 12.9 W DC typical and 17.9 W DC peak | [D: 14.7 W and 20.3 W AC on the OEM adapter [M: Kill-a-Watt, `docs/specifications.md`] x 0.88] |
| Power, on battery | Up to about 14.4 W: May 2026's 14.9 W, less about 0.5 W for the monitor, if all of the 2.2 W the 08-31 report could not attribute is the XB7 | [M: 14.9 W / 1.18 A, 05-06 report; D: 14.9 − 0.5; I: 08-31 report, open item 6] |
| Lowest input on record | About 11.71 to 11.74 V at its terminals, computed at the BP-65's 11.80 V disconnect for 2.0 and 1.2 A | [S: `docs/voltage-drop-analysis.md`]. Trips seen at 11.77 V, and after 11.675 V of telemetry [M: README] |
| Switchover | No interruption seen at the XB7 in the 2026-08-29, 09-01 or 09-15 outages. 5 s telemetry cannot resolve under 1 ms | [M: README] |
| Restart | About 3 to 5 min from power to a working Wi-Fi AP | [S: survival-sleep design v12, which gives ~3–4 min and ~4–5 min in two places] |
| Network role | It is the gateway whose Wi-Fi the monitor uses. While the modem is shed, the monitor has no network and reports nothing | [S: firmware header, item ⑦; 09-15 report §5] |

**What Rev 4 changes for the modem:**
- U4 holds the modem's input at 12 V ±4 %, which is 11.52 to 12.48 V [S: Pololu #4984; D]. It
  does so at any bus voltage from 2.8 to 22 V [S]. The XB7 no longer sees the bus.
- The low edge of that band is 0.19 V under the lowest input on record [D: 11.71 − 11.52], and
  inside the inferred ±10 % [D]. Measure U4's output at TP +12V MODEM at first power
  (open item 13).
- Behind U4 the XB7 is a constant-power load on the bus. Its bus current rises as the pack
  falls (section 1.7).

### 1.5 The PSU: Mean Well HDR-60-12 at 13.6 V

| Item | Value | Basis |
|---|---|---|
| Rating | 12 V, 4.5 A, 54 W | [S: HDR-60-SPEC, file dated 2026-10-09] |
| Adjust range | 10.8 to 13.8 V. `docs/design-rationale.md` and `docs/component-selection.md` give 10.2 to 13.8 V | [S] |
| Set point | 13.6 V (owner, 2026-11-09). Whether the trimmer is lacquered at this setting is not recorded | — |
| Tolerance | ±1.0 %, including set-up, line and load regulation; ±0.03 %/°C | [S] |
| Ripple and noise | 120 mVp-p max | [S] |
| Over-voltage protection | 14.2 to 16.2 V. "Shut down o/p voltage, re-power on to recover." `docs/bom.md` and `docs/specifications.md` give 13.8 to 16.2 V, from a source revision they do not record | [S] |
| Overload | 105 to 160 % of rated power, constant-current limiting, hiccup below 50 % output voltage; recovers automatically | [S] |
| Efficiency | 88 % typical (230 VAC, rated load) | [S] |
| Hold-up | 12 ms typical at 115 VAC, full load | [S] |
| Set-up / rise | 500 ms / 50 ms at 115 VAC, full load | [S] |

**Why 13.6 V is now possible.** The 13.3 V float was a ceiling set by the XB7 on the bus.
- It kept the modem's terminals at 13.11 to 13.14 V at most [S: `docs/voltage-drop-analysis.md`],
  at the cost of holding the previous pack near 65 % SOC [S: README, Operating Modes item 1;
  05-06 report §4.3].
- Behind U4 the modem sees 11.52 to 12.48 V whatever the bus does. The bus limit on this board
  is now U4's 22 V input maximum [S], not the modem [D].

**At the bus:**
- The bus floats at 13.571 to 13.587 V [D: 13.6 V less the #5382's regulated 13 to 29 mV, per
  the 2026-10-29 correction in `docs/component-selection.md`].
- That is 0.8 V under the bottom of the label's 14.4 to 14.6 V charge range [D: 14.4 − 13.6].
- It is 0.71 V under the lowest BMS cut seen on the bench pack (section 1.6) [D: 14.310 − 13.6].

**Margin to the PSU's own OVP**, by the method of Top-Off §4.1:
- Worst-case output: 13.6 + 0.136 (1 %) + 0.102 (25 °C x 0.03 %/°C) + 0.060 (half of 120 mVp-p)
  = 13.898 V [D, for an assumed 25 °C rise].
- Against the 14.2 V floor on the 2026-10-09 datasheet: 0.302 V of margin [D].
- Against the 13.8 V floor in the repository's earlier figures: the set point is 0.2 V under
  it, and the worst case is 0.098 V over it [D].
- **The OVP latches.** A trip would leave the PSU off with mains present [S].
  - The pack would carry the modem, and PSU_SENSE would read about 0 V.
  - The board would treat that as an outage and shed at 11.8 V.
  - Nothing would recover until AC is cycled at the PSU [D].
  - Which range the installed unit has is open item 11.

**Recharge:**
- After an outage the pack gets the PSU's output less the load: 3.22 to 3.52 A at rated
  current [D: 4.5 A − 0.98 to 1.28 A].
- On 2026-09-15 the PSU ran briefly into its overload band: 77.66 W, 143.8 % of nameplate
  [D: 09-15 report §7.4]. It was a transient of minutes [S: Top-Off §4.1].
- At the Rev 4 load, the same 77.66 W at an assumed 13.0 V bus would put 4.64 to 4.95 A into
  the pack [D: 77.66 W ÷ 13.0 V = 5.97 A, less 1.02 to 1.34 A of load].
- That is just under the 5.0 A that the bench pack's "max charge .5c" label allows [S: Top-Off
  §11.1; D: 0.5 x 10 Ah].

### 1.6 The battery: a new Cyclenbatt 12 V 10 Ah LiFePO4

| Item | Value | Basis |
|---|---|---|
| Identity | New Cyclenbatt 12 V 10 Ah LiFePO4. Whether it is the "second, new Cyclenbatt 12.8 V 10 Ah" pack used on the top-off bench from 2026-10-28 is not recorded (open item 12) | Owner, 2026-11-09; [S: Top-Off §11.1] |
| Build | 4S LiFePO4, sealed: no balance taps, no BMS telemetry | [S: README, for the previous pack of this model; I for this one] |
| Label | The bench pack reads "12.8 V 10 Ah" and "max charge .5c 14.6v max". The previous pack's label gives a 14.4 to 14.6 V charge voltage and charging only above 32 °F, with no upper charge temperature | [S: Top-Off §11.1; §3, RQ-9 to RQ-11] |
| BMS | 10 A discharge rating; under-voltage cutoff 10.0 V. The over-voltage cutoff is not documented | [S: `docs/component-selection.md`; `docs/specifications.md` and its 2026-10-16 correction] |
| BMS cuts seen | On the bench pack, three cuts on charge at VBUS 14.310 to 14.315 V and 0.95 to 1.30 A (2026-10-28) | [M: Top-Off §11.1] |
| Capacity | Nameplate 10 Ah. Not measured on this pack (section 1.8, open item 14) | [S] |
| Float | 13.6 V set point, 13.571 to 13.587 V at the bus (section 1.5). The SOC that holds is not measured | [D; I] |
| Temperature | DS18B20 on TB2 (section 4.6) | — |

**Protection on this system**, top to bottom:
1. Over-voltage: the PSU's own OVP, 14.2 to 16.2 V, or 13.8 to 16.2 V (open item 11), latching
   [S].
2. Over-voltage: the BMS, cutoff undocumented [S].
3. Under-voltage: the firmware shed at 11.8 V, on battery only (section 8). It is not
   independent of the firmware.
4. Under-voltage: the BMS at 10.0 V [S]. U4 runs down to 2.8 V input [S], so it adds no floor of
   its own.
5. Over-current: F1 for the board and the modem (section 4.1), and the BMS's 10 A [S].

### 1.7 Load and current budget

**Inputs:**
- XB7: 12.2 to 14.4 W typical and 17.9 W peak (section 1.4).
- U4 efficiency: 85 to 95 % [S: Pololu #4984].
- The board's own ~35 mA [S: firmware header], taken as 0.45 W [D: about 35 mA x 12.8 V].

**Power at the bus** = XB7 ÷ efficiency + 0.45 W [D]:
- Typical, low: 12.2 ÷ 0.95 + 0.45 = 13.29 W.
- Typical, high: 14.4 ÷ 0.85 + 0.45 = 17.39 W.
- Peak: 17.9 ÷ 0.85 + 0.45 = 21.51 W.
- The schematic note's 13.4 W is the low end. It implies 94 % efficiency [D: 12.2 ÷ (13.4 − 0.45)].

**Current at the bus** = power ÷ bus voltage [D]:

| Bus voltage | Typical, 13.29 to 17.39 W | Peak, 21.51 W |
|---|---|---|
| 13.58 V, float (from the PSU) | 0.98 to 1.28 A | 1.58 A |
| 12.8 V, mid-discharge | 1.04 to 1.36 A | 1.68 A |
| 11.8 V, the shed threshold | 1.13 to 1.47 A | 1.82 A |
| 10.0 V, the BMS cutoff, if the shed fails | 1.33 to 1.74 A | 2.15 A |

**What the figures bound:**
- **F1** (section 4.1):
  - The highest continuous current is 1.74 A, with a failed shed at the BMS cutoff: 87 % of a
    2 A link, 70 % of a 2.5 A link [D].
  - Down to the shed threshold it is 1.47 A: 74 % of 2 A, 59 % of 2.5 A [D].
  - The 2.15 A peak is a transient that a time-lag link is meant to ride [I].
  - Uncertainty: the rule of thumb of at most about 75 % of rating at 25 °C is general
    fuse-maker guidance, not taken from the chosen link's datasheet. Check that datasheet at the
    enclosure's temperature.
- **U4:**
  - Peak output 1.49 A [D: 17.9 W ÷ 12 V], against the 2.5 A Pololu lists [S].
  - Typical loss 0.64 to 2.54 W [D: 12.2 x (1/0.95 − 1); 14.4 x (1/0.85 − 1)]. Pololu warns
    the module can get hot enough to burn [S].
- **Board copper:** about 3.7 A for a 1.8 mm track at a 10 °C rise, against the 2.15 A peak.
  - [D: IPC-2221 external layers, 0.048 x 10^0.44 x 97.7^0.725, with 97.7 mil² = 70.9 mil x
    1.378 mil.]
  - 1 oz copper is assumed, since the board does not record its copper weight [I].
- **BMS:** the 2.15 A peak against its 10 A rating [S].
- **PSU at float:** 22 to 28 % of its 4.5 A rating [D: 0.98 ÷ 4.5; 1.28 ÷ 4.5].

### 1.8 Runtime: an estimate, not a measurement

**This pack has not been discharged.** Its usable energy between the 13.6 V float and the
11.8 V shed is unknown. The figures below are a bracket from arithmetic, not a prediction.

Runtime = usable Wh ÷ bus power, 13.29 to 17.39 W [D]:
- At the 53.271 Wh the previous pack delivered in May 2026 from a 13.3 V float [M: 05-06
  report]: 3.06 to 4.01 h.
- At the original design's 112.5 Wh (9 Ah x 12.5 V) [S: `docs/specifications.md`]: 6.47 to
  8.46 h.

Neither end is a bound. A new pack should beat the old pack's May figure, and a 13.6 V float
should start it fuller than 13.3 V did, but neither is measured [I]. The falsifier is the first
coulomb-counted discharge of this pack to the shed (open item 14).

## 2. Block diagram

```
BUS+ (Wago bus) ── F1 ── VIN ─┬─ U3 Pololu D24V7F3 ── +3V3 ── XIAO, INA260 logic, DS18B20, R1
                              └─ U4 Pololu S13V25F12 (EN) ── +12V_MODEM ── MODEM terminal ── XB7
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
| BUS | Phoenix MKDS 3.81 mm, 2-pole | GND | BATT_RAW, to F1. Despite the name, it lands on the bus side of the INA260 (section 1.3) | |
| MODEM | Phoenix MKDS 3.81 mm, 2-pole | GND | +12V_MODEM (U4 output), to the XB7's 5.5 x 2.1 mm centre-positive barrel | |
| PSU_SENSE | Phoenix MKDS 3.81 mm, 2-pole | GND | PSU_SENSE | |
| TB2 | TE 282834-3, 2.54 mm, 3-pole | +3V3 | GND | DQ (GPIO10) |

**Test points** (2.0 mm pads with 1.0 mm drill): VIN, GND, 3V3, MODEM_EN and +12V MODEM [M].

**PSU_SENSE wiring.** It is wired to the Mean Well HDR-60-12 output, upstream of the Pololu #5382
ideal diode, so it reads about 0 V with mains off (owner, 2026-11-08). With mains on it reads the
PSU's 13.6 V set point (section 1.5). The commissioning backfeed
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
  A 1.8 mm track carries about 3.7 A at a 10 °C rise (section 1.7).
- F1 now carries U4 (the modem) as well as U3, which is the whole system's load.
  - The schematic note puts that at about 1.1 to 1.2 A at 12 to 11.8 V [S: schematic note, D:
    13.4 W bus load / V].
  - Section 1.7 bounds it at 0.98 to 1.74 A continuous and 2.15 A peak [D].
- The fuse is 2 to 2.5 A (owner, 2026-11-08). A time-lag, DC-rated link is advised (schematic
  note). Section 1.7 gives the margin at each end of that range.
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
- Input 2.8 to 22 V, with reverse-voltage protection to 20 V. Output 12 V ±4 %, 2.5 A in the
  spec table [S: Pololu #4984 page].
- It has soft-start, input under-voltage lockout, output over-voltage protection, over-current
  protection and thermal shutdown, at about 500 kHz [S].
- Quiescent current is 10 to 35 mA enabled at no load. Disabled, it draws 2 to 10 µA per volt
  of VIN, including the EN pull-up [S]. That is 24 to 118 µA at the 11.8 V shed threshold
  [D: 2 x 11.8; 10 x 11.8].
- The module is 22.9 x 22.9 x 9.7 mm, with two M2 holes [S]. A second row of four larger
  3.5 mm-pitch holes carries VIN, GND and VOUT; this board does not use it.
- Its output, loss and current are budgeted in section 1.7. What it does for the XB7 is in
  section 1.4.

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

**Design figures.** These are worked at the PSU's 13.6 V set point at PSU_SENSE (owner,
2026-11-09; section 1.5). Revision 1 of this document used an assumed 13.8 V.
- **Mains override threshold:** about 3.0 to 3.3 V [D: VBE 0.55 to 0.6 V [I] x 122/22].
- **GPIO5 at reset:** high-Z with no pull [S: ESP32-C3 datasheet v2.4, Table 2-1]. R3 is
  what keeps the modem on through boot.
- **Q1 drive:** base current about 21 µA [D: (1.65 − 0.6) V / 50 kΩ]. It sinks U4's EN
  pull-up, which runs from the bus [D: V / 475 kΩ]:
  - 24.8 µA at the 11.8 V shed threshold, where Q1 is meant to be on. Forced β is 1.18 [D].
  - At most 30.4 µA from a freshly topped pack resting at 14.42 V [M: owner's DMM, Top-Off
    §11.1]. Forced β is 1.45 [D].
- **Q2 drive:** its base sees a Thevenin source of 2.45 V and 18.0 kΩ [D: 13.6 x 22/122;
  100k ∥ 22k]. Base current is about 103 µA [D: (2.45 − 0.6) V / 18.0 kΩ]. It sinks R2's
  33 µA [D: 3.3 V / 100 kΩ], so forced β is about 0.32 [D].
- **Saturation check:** both transistors are deep in saturation [I]. That is falsified if the
  MODEM_EN test point reads above about 0.2 V with GPIO5 high and mains absent.

### 4.5 Mains readback (PSU_ADC)
R7 100k runs from PSU_SENSE to PSU_ADC, R6 18k from PSU_ADC to GND, and C7 0.1 µF from PSU_ADC
to GND. PSU_ADC goes to XIAO pad 3 (D2 = GPIO4, ADC1).
- **Scale:** the pin sees 18/118 = 0.1525 of PSU_SENSE, which is 2.07 V at the 13.6 V set
  point [D].
- **Range:** ADC1 at its 12 dB setting reads 0 to 2500 mV with a calibrated total error of
  ±35 mV [S: ESP32-C3 datasheet v2.4, Table 5-6, p. 56]. That covers up to 16.4 V at the
  terminal [D: 2.5 V x 118/18].
  - That spans the PSU's whole OVP band, up to 16.2 V [S: section 1.5].
  - So PSU_ADC can watch the set point's margin to the OVP: 14.2 V reads 2.17 V [D].
- **Uncalibrated accuracy at 13.6 V:** about ±1.15 V from the 5 % carbon-film resistors the
  board lists now [D: (100/118) x 10 % x 13.6 V], or ±0.23 V with the 1 % parts chosen in
  section 6 [D: (100/118) x 2 % x 13.6 V]. Add ±0.23 V from the ADC [D: 35 mV x 118/18].
  That is fine as a mains-present signal but rough as a voltage.
- **Calibrated accuracy:** a one-point calibration against a DMM at the terminal removes both
  errors at the set point. The residual should be tens of mV [I]. That is falsified if a day's
  readings drift more than about 0.1 V from DMM spot checks.
- **Source impedance:** 15.25 kΩ [D: 100k ‖ 18k]. With C7 that is a 1.5 ms time constant [D].
  100 nF is also the datasheet's own test condition for its linearity figures [S: Table 5-5].
- **If the PSU_SENSE wire comes off:** R5 holds Q2 off (no override) and the ADC reads 0 V.
- **Load on the PSU:** about 0.23 mA for both dividers together [D: 13.6/122k + 13.6/118k].
- **Not a wake source.** 2.07 V is under the ESP32-C3's minimum input-high level, 0.75 x 3.3 =
  2.475 V [S: `../UPS-Monitor/esp32-c3_datasheet.pdf` v1.2, Table 14; D].
  - So PSU_ADC cannot wake the chip from deep sleep as a digital input.
  - It does not need to: Q2 restores the modem in hardware when mains returns (section 4.4).

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
| Firmware never sheds on battery (down, or running with no INA260 reading) | Modem stays ON and the pack runs to the BMS's 10.0 V cutoff, where the next row applies. With the BP-65 removed, nothing else sheds it | Sections 1.1 and 1.6; F1 at that point in section 1.7 |
| Pack hits BMS cutoff, then recovers | Everything restarts, and U4's EN pull-up brings the modem back without firmware | 4.3 |
| HDR-60-12 OVP trips | The PSU shuts off with mains present. PSU_SENSE reads about 0 V, so the board sees an outage: the pack carries the modem, and the firmware sheds at 11.8 V. Nothing recovers until AC is cycled at the PSU | OVP latches [S: HDR-60 datasheet]; margin in section 1.5; open item 11 |

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

**U4 on the bottom side:**
- The module is 22.9 x 22.9 x 9.7 mm [S: Pololu #4984], held by its five 0.1 in pins.
- This board's holes are H1, H2 and H4 (M3), so the module's own two M2 holes go unused.
- It dissipates 0.64 to 2.54 W in typical service (section 1.7), facing the enclosure floor.
- Its clearance to the floor below the 15 mm standoffs is not recorded.

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
| System, section 1 (2026-11-09) | PSU set point 13.6 V and the new pack (owner). The installed PSU's OVP range, U4's output and the new pack's capacity are **not checked** (open items 11, 13 and 14) |

## 8. Firmware requirements for Rev 4

- **GPIO5 (MODEM_OFF):** output, LOW at a cold boot and on restore (modem on). Drive HIGH only
  when battery ≤ 11.8 V **and** mains is absent [S: schematic note].
  - **On a timer wake from survival sleep it must stay HIGH.** Survival sleep reboots the ESP
    every 120 s [S: README, Operating Modes item 7]. A firmware that drives GPIO5 LOW at every
    boot would power the modem up at every wake [D].
  - The deployed firmware already reads the wake cause (`ups-monitor.yaml`, line 590).
  - **Deep-sleep hold.** On the ESP32-C3, `gpio_hold_en` alone does not hold a digital pad
    through deep sleep; `gpio_deep_sleep_hold_en` is also needed [S: ESP-IDF GPIO reference,
    ESP32-C3].
  - Whether the held level survives the ROM boot on a timer wake is not documented there. Test
    it (open item 7).
- **GPIO4 (PSU_ADC):** ADC at 12 dB attenuation, averaged.
  - Multiply by 118/18 = 6.556 nominal [D], then replace that with DMM ÷ reading.
  - The mains-present threshold must sit between the 0.10 V backfeed [M] and the 13.6 V set
    point.
  - To time the HDR decay, sample faster than the decay itself. A slow poll gives only a bound.
- **On battery comes from PSU_ADC, not from a bus threshold.**
  - The deployed firmware sets `on_battery` when the bus falls below 13.15 V, 23.3 mV under the
    old 13.2 V float [S: README].
  - At a 13.571 to 13.587 V float that threshold is 0.42 to 0.44 V down [D]. A full pack could
    hold the bus above it for some time on battery [I].
- **Re-derive on this pack.** The discharge-phase thresholds (Plateau ≥ 12.65 V, Knee 12.40 to
  12.65 V, Cliff ≤ 12.40 V), the runtime estimator's capacity and the Ri baselines were set on
  the previous pack, at a 13.3 V float [S: README].
  - The host-shutdown ladder (`cliff_imminent`, `voltage_warning`, `voltage_critical`) has no
    host to shut down on this system (section 1.1).
  - Set the replacements from this pack's first discharge (open item 14).
- **Survival-sleep entry.** The deployed firmware enters on the load collapse at the BP-65's trip
  (on battery, −0.30 A < I < +0.20 A) [S: README].
  - With no BP-65, that collapse is the board's own shed. Entry therefore follows the shed.
  - The board's own draw after a shed, about −35 mA, sits inside that window [D].
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
   the delay before a shed takes effect. On section 1.8's bracket the shed comes 3 to 8.5 h into
   an outage [I], so a decay of seconds or minutes would not matter.
7. **GPIO5 through deep sleep:** if the pin is not held, the modem turns back on during survival
   sleep. Section 8 gives the ESP32-C3's hold calls and the timer-wake boot path to test.
8. **U4:** confirm the 0.1 in row pin order on the module in hand.
9. **Resistors:** RNMF14 chosen (section 6); the board's part fields and BOM still to be
   updated. **INA260 standoff:** check whether a breakout mounting hole lines up with H1.
10. **BUS pin 2's net name:** BATT_RAW invites wiring it to Battery+. That would take the
    modem's ~1 A out of the INA260's view on battery (section 1.3).
    - Rename it BUS+ on the silk and schematic, or mark the terminal.
    - Draw the current enclosure wiring (replaced 2026-10-31 to 11-04, owner), with the BUS
      lead's fuse at the bus end.
11. **HDR-60-12 OVP range on the installed unit:** 14.2 to 16.2 V on the 2026-10-09 datasheet,
    13.8 to 16.2 V in `docs/bom.md` and `docs/specifications.md`.
    - At 13.6 V the worst-case output is 13.898 V (section 1.5), so the 13.8 V floor would leave
      no margin. The OVP latches.
    - Find which applies from the unit's label or datasheet revision.
12. **Which pack:** is the new pack in service the "second, new" Cyclenbatt used on the top-off
    bench from 2026-10-28 (Top-Off §11.1)? If so, its label, its BMS cuts at 14.310 to 14.315 V
    and its bench history apply to it (section 1.6).
13. **U4's output** at TP +12V MODEM at first power, against the XB7's lowest input on record,
    11.71 V (section 1.4).
14. **First discharge of this pack** to the 11.8 V shed, coulomb-counted by the INA260. It sets
    the runtime (section 1.8) and the firmware's phase thresholds (section 8).

## Sources

- [ESP32-C3 Series Datasheet v2.4 (Espressif)](https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf): Table 2-1; §5.5, Tables 5-5 and 5-6, p. 56.
- [Seeed XIAO ESP32C3 wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/): pin map.
- [Pololu #4984 S13V25F12](https://www.pololu.com/product/4984): output, EN pull-up and threshold, input range, reverse-voltage protection, quiescent current, size, efficiency range.
- [Mean Well HDR-60 series datasheet](https://www.meanwell.com/Upload/PDF/HDR-60/HDR-60-SPEC.PDF), file dated 2026-10-09: the HDR-60-12 column.
- [ESP-IDF GPIO reference, ESP32-C3](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32c3/api-reference/peripherals/gpio.html): `gpio_hold_en`, `gpio_deep_sleep_hold_en`.
- ESP32-C3 datasheet v1.2, in the repository: [`esp32-c3_datasheet.pdf`](../UPS-Monitor/esp32-c3_datasheet.pdf), Table 14 (input-high level).
- XB7: [`docs/specifications.md`](../docs/specifications.md), [`docs/wiring.md`](../docs/wiring.md), [`docs/voltage-drop-analysis.md`](../docs/voltage-drop-analysis.md); reports [05-06](../reports/UPS_Report_2026-05-06.md), [08-31](../reports/UPS_Report_2026-08-31_Boost_Integration.md) and [09-15](../reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md); [survival-sleep design v12](../UPS-Monitor/UPS_SurvivalSleep_Design_Summary_v12.md).
- PSU and battery history: [`docs/component-selection.md`](../docs/component-selection.md), [`docs/bom.md`](../docs/bom.md), [README](../README.md), [Top-Off design](../Top-Off-Charger/top-off-charger-design.md) §4.1, §9 to §11.
- [Stackpole RNF/RNMF datasheet](https://www.seielect.com/catalog/SEI-RNF_RNMF.pdf), rev 3/30/2023: pp. 1, 2, 7.
- [element14: K104K10X7RF53L2](https://nz.element14.com/vishay/k104k10x7rf53l2/cap-0-1-f-50v-10-x7r/dp/2860096): body height.
- Schematic notes in `UPS-Monitor-Rev 4.kicad_sch` (not yet in this repository).
- Deployed firmware header: [`ups-monitor.yaml`](../UPS-Monitor/ups-monitor.yaml).
- Deployed board: [`UPS-Monitor-THT.kicad_pcb`](../UPS-Monitor/UPS-Monitor-THT.kicad_pcb).
- Pending item on Rev 1's ALERT routing: [CHANGELOG.md](../CHANGELOG.md).

## Revision history

| Rev | Date | Change |
|---|---|---|
| 1 | 2026-11-08 | First issue |
| 2 | 2026-11-09 | System scope (owner): a UPS dedicated to the XB7, with no host or boost and no BP-65, the HDR-60-12 at 13.6 V, and a new Cyclenbatt pack. Section 1 rewritten, with the topology, the modem, the PSU, the battery, the load budget and a runtime bracket. Sections 4.4 and 4.5 reworked at 13.6 V. Section 4.3 gains U4's ratings. Two failure modes, four firmware requirements and open items 10 to 14 added |
