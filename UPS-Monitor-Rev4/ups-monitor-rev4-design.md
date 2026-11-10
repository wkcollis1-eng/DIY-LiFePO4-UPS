# UPS Monitor Rev 4: design document

**Status (2026-11-10):** layout in progress, not fabricated. Rev 4 firmware V4.0 is written and
compiles; it has never been flashed or bench-tested (section 8.1).
**Document revision:** 7 (2026-11-10): revision 6 brought it into line with the board as saved
2026-11-10 16:06 (3.81 mm terminal), with the owner's decisions on F1, R8 and PSU_SENSE pad 1,
and with the datasheets read that day. Revision 7 adds U4's pin order and three datasheets the
owner supplied. See the revision history at the end.
**Dates and times:** dates from revision 2 on are UTC. Clock times (the board's saves, the
BOM's 16:09) and revision 1's dates are local, EST (UTC−5). Revisions 2 and 3 were written on the
evening of 2026-11-08, local time.
**Master file:** `UPS-Monitor-Rev 4.kicad_pcb` (not yet in this repository). The board is the
master; the schematic was
synced from it on 2026-11-08 and has trailed it since: KiCad's schematic-parity DRC lists 41
differences (section 7). Where the two disagree, this document follows the board.

Figures carry the repository's provenance tags: **[M]** measured, **[S]** specification or prior
document, **[D]** derived by the arithmetic shown, **[I]** inferred and not yet tested (with the
observation that would falsify it). An [M] with no other source was read from the board file
saved 2026-11-10 16:06 (sha256 02d74bea98f1b086…), by parsing the file and running KiCad 10's
`kicad-cli pcb drc`. That save differs from the 15:22 save only at the 3-pole terminal, the two
tracks that reach it and two GND vias [M: object-by-object comparison of the two saves], so text
that names "the 15:22 board" for anything else still holds. Positions are board coordinates in mm.

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
- No loss of function in the monitor (crash, reset, brown-out, XIAO unplugged) can turn the
  modem off. The firmware requirements in section 8 close the cases where the output is wrong.
- When mains returns, the modem comes back on whatever the firmware is doing.

The enable network in section 4.4 makes the second and fourth promises hold in hardware. It
makes the third hold for any failure that leaves GPIO5 floating or low.

Hardware cannot tell a correct HIGH on GPIO5 from a wrong one. A hold that is never released, or
a shed on a bad reading, sheds the modem at the next outage with a full pack (section 5). Only
the firmware and its commissioning test close those cases (section 8, open items 15 to 17).

### 1.3 Topology

```
120 VAC ─► HDR-60-12, 13.6 V ─┬─► Pololu #5382 ideal diode ─► 12 V bus (Wago)
                              │                                │
                              └─► PSU_SENSE (board)            ├─► INA260 VIN+ ─ shunt ─ VIN− ─► Cyclenbatt 10 Ah
                                                               │
                                                               └─► BUS (board) ─► F1 ─┬─► U3 3.3 V ─► monitor
                                                                                      └─► U4 12 V ─► terminal pin 1 (MODEM +) ─► XB7
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
  - The board's net is now named BUS, and its terminal pad carries a "+" on the silk [M]. The
    schematic still calls it BATT_RAW, a name that invites that wiring (open item 10).
- **One GND pole serves both leads.** The terminal block has a single GND pad (section 3), so the
  modem's return lands on the enclosure's GND bus, not on the board (owner's layout, 2026-11-09;
  not yet wired). The board's GND lead then carries only the difference between what enters on
  BUS and what leaves on MODEM: at most about 0.66 A at the 2.15 A input peak, and less on mains
  [D: 2.15 − 1.49, Kirchhoff's current law on the board's three power terminals].
  - **Corrected 2026-11-10 (revision 6).** Revision 5 said here that the GND lead "carries the
    same current as its BUS lead". That was wrong: it counted U4's input current and missed that
    the modem's share returns on the GND bus, not through the board.
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

**The x 0.88 is a floor, not a measurement.** It is DoE Level VI's minimum efficiency, not the
adapter's efficiency at about 13 W out of its 55 W. So the DC figures above may read low.
- At 0.92, for example, the peak would be 18.7 W [D: 20.3 x 0.92].
- The failed-shed peak current at the bus would then be 2.24 A instead of 2.15 A
  [D: (18.7 ÷ 0.85 + 0.45) ÷ 10.0 V].
- The first outage will measure bus power directly.

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
| Overload | 105 to 160 % of rated power. Constant-current limiting from 50 to 100 % of rated output voltage; hiccup below 50 %; recovers automatically (p. 2, read 2026-11-10; open item 20, closed) | [S] |
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
- **That is the bottom of the range, not a bound** (peer review, S1). The 143.8 % shows only
  that the limit is at least that high. The datasheet allows up to 160 % [S]. At 160 % and a
  13.0 V bus:
  - read as current, 1.6 x 4.5 A = 7.20 A, which puts 5.86 to 6.18 A into the pack [D];
  - read as power, 1.6 x 54 W = 86.4 W [D], and 86.4 W ÷ 13.0 V = 6.65 A, which puts 5.31 to
    5.63 A into the pack [D].
- **Both exceed the 5.0 A** that the bench pack's "max charge .5c" label allows
  [S: Top-Off §11.1; D: 0.5 x 10 Ah].
- **Whether the pack draws enough to reach the PSU's limit is not measured** [I]. It depends on
  two things:
  - the headroom over the charge plateau, which the 13.6 V set point raises by 0.3 V;
  - the resistance of the battery branch.
  This is falsified if the first recharge's logged peak into the pack stays at or under 5.0 A
  (open item 19).
- **If the pack does reach the limit,** the PSU spends much of the recharge in its overload band.
  The datasheet lists that band under PROTECTION, not under OUTPUT: "105 ~ 160% rated output
  power", with "Constant current limiting within 50% ~100% rated output voltage" and "Hiccup
  mode when output voltage <50%", each recovering automatically [S: HDR-60-SPEC, 2026-10-09,
  p. 2]. So between 6.8 V and 13.6 V it limits current and keeps running (open item 20, closed).
- **The BMS's charge over-current limit is not documented.** A trip there would drop the load
  suddenly, and the PSU's latching OVP has only 0.302 V of margin [I].
- **The #5382 can carry it.** It is rated 10 A, < 10 mΩ, on an LM74700-Q1 [S: Pololu #5382
  product page, read 2026-11-10], so 7.20 A is 72 % of its rating [D].
- **The PSU-positive fuse is the tight one.** The enclosure fuses PSU positive at 7.5 A and the
  battery lead at 10 A (owner, 2026-11-09).
  - At the 160 % ceiling the PSU's 7.20 A is 96 % of the 7.5 A fuse [D: 7.20 ÷ 7.5]. The
    6.18 A into the pack is 62 % of the 10 A fuse [D: 6.18 ÷ 10].
  - 96 % is above the rule-of-thumb 75 % (section 1.7), and above what the fuse's own sheet
    allows. The owner supplied the sheet for the enclosure's blade fuses (2026-11-10):
    Littelfuse MINI, 32 V. It allows a 7.5 A link 6.4 A of continuous load at 20 °C and 6.0 A
    at 40 °C, and a 10 A link 9.2 A and 8.6 A [S: Littelfuse MINI 32 V datasheet, revised
    2024-09-27, p. 3, derating table, which includes a 20 % margin].
    - The PSU's 7.20 A ceiling is over the 7.5 A link's allowance. Its rated 4.5 A is inside
      it, and so is the 10 A link's 6.18 A [D: against 6.4 A and 9.2 A].
    - It is not a prompt trip. At 110 % of rating, 8.25 A, the sheet's shortest opening time
      is 360 000 s, which is 100 h [S: same, p. 3; D: 1.1 x 7.5]. The sheet does not say what
      hours above the allowance do to the link.
  - The first recharge's logged peak decides whether the PSU gets there (open item 19). The
    PSU's output is the pack's current plus the 0.98 to 1.28 A load (section 1.7).
  - A PSU fuse that opens leaves the PSU running with no path to the bus. Section 5's row for
    that case applies if PSU_SENSE taps on the PSU side of that fuse. Where it taps is not
    recorded. Tapping on the bus side of the fuse turns that case into an ordinary outage
    (section 3).

### 1.6 The battery: a new Cyclenbatt 12 V 10 Ah LiFePO4

| Item | Value | Basis |
|---|---|---|
| Identity | New Cyclenbatt 12 V 10 Ah LiFePO4. Whether it is the "second, new Cyclenbatt 12.8 V 10 Ah" pack used on the top-off bench from 2026-10-28 is not recorded (open item 12) | Owner, 2026-11-09; [S: Top-Off §11.1] |
| Build | 4S LiFePO4, sealed: no balance taps, no BMS telemetry | [S: README, for the previous pack of this model; I for this one] |
| Label | The bench pack reads "12.8 V 10 Ah" and "max charge .5c 14.6v max". The previous pack's label gives a 14.4 to 14.6 V charge voltage and charging only above 32 °F, with no upper charge temperature | [S: Top-Off §11.1; §3, RQ-9 to RQ-11] |
| BMS | 10 A discharge rating; under-voltage cutoff 10.0 V. The over-voltage cutoff is not documented | [S: `docs/component-selection.md`; `docs/specifications.md` and its 2026-10-16 correction, for the previous pack; I for this one until open item 12 closes] |
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
4. Under-voltage: the BMS at 10.0 V [S for the previous pack; I for this one, open item 12]. U4
   runs down to 2.8 V input [S], so it adds no floor of its own.
5. Over-current: F1 for the board and the modem (section 4.1), the 10 A fuse on the battery
   lead (owner, 2026-11-09), and the BMS's 10 A [S for the previous pack; I for this one].

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
    2 A link, 70 % of a 2.5 A link, 55 % of the 3.15 A link now chosen [D: 1.74 ÷ 3.15;
    section 4.1].
  - Down to the shed threshold it is 1.47 A: 74 % of 2 A, 59 % of 2.5 A, 47 % of 3.15 A
    [D: 1.47 ÷ 3.15].
  - The 2.15 A peak is a transient that a time-lag link is meant to ride [I].
  - Uncertainty: the rule of thumb of at most about 75 % of rating at 25 °C is general
    fuse-maker guidance, not taken from the chosen link's datasheet. That sheet's own gate is
    1.5 x rated held for at least 60 min [S: Schurter SPT 5x20, p. 3]. Its derating with
    ambient temperature was not read; check it at the enclosure's temperature.
- **U4:**
  - Peak output 1.49 A [D: 17.9 W ÷ 12 V], against the 2.5 A Pololu lists [S].
  - Typical loss 0.64 to 2.54 W [D: 12.2 x (1/0.95 − 1); 14.4 x (1/0.85 − 1)]. Pololu warns
    the module can get hot enough to burn [S].
- **Board copper:** about 3.7 A at a 10 °C rise for 1.85 mm, the narrowest track on the modem's
  path (section 4.1), against the 2.15 A peak.
  - [D: IPC-2221 external layers, 0.048 x 10^0.44 x 100.4^0.725, with 100.4 mil² = 72.8 mil x
    1.378 mil.]
  - The board's stackup records 35 µm (1 oz) copper on both layers [M]. Revisions 1 to 4 assumed
    it.
- **BMS:** the 2.15 A peak against its 10 A rating [S].
- **PSU at float:** 22 to 28 % of its 4.5 A rating [D: 0.98 ÷ 4.5; 1.28 ÷ 4.5].

### 1.8 Runtime: an estimate, not a measurement

**This pack has not been discharged.** Its usable energy between the 13.6 V float and the
11.8 V shed is unknown. The figures below are a bracket from arithmetic, not a prediction.

Runtime = usable Wh ÷ bus power, 13.29 to 17.39 W [D]:
- At the 53.271 Wh the previous pack delivered in May 2026 from a 13.3 V float [M: 05-06
  report]: 3.06 to 4.01 h.
- At this pack's nameplate, 128 Wh (10 Ah x 12.8 V) [S: label; D]: 7.36 to 9.63 h. Revision 2
  used the original 9 Ah design's 112.5 Wh here [S: `docs/specifications.md`], which gave 6.47 to
  8.46 h.

Neither end is a bound. A new pack should beat the old pack's May figure, and a 13.6 V float
should start it fuller than 13.3 V did, but neither is measured [I]. The falsifier is the first
coulomb-counted discharge of this pack to the shed (open item 14).

## 2. Block diagram

```
BUS+ (Wago bus) ── F1 ── VIN ─┬─ U3 Pololu D24V7F3 ── +3V3 ── XIAO, INA260 logic, DS18B20, R1
                              └─ U4 Pololu S13V25F12 (EN) ── +12V_MODEM ── terminal pin 1 ── XB7
                                         ▲
GPIO5 MODEM_OFF ── R2/R3 ── Q1 ──────────┘  (Q1 pulls EN low = modem OFF)
                             ▲
PSU_SENSE ─┬─ R4/R5 ── Q2 ───┘  (Q2 clamps Q1's base while mains is present)
           └─ R7/R6, C7 ── GPIO4 (ADC)
INA260 (U2) ── I2C GPIO6/7, Alert GPIO3 (R1 pull-up)      DS18B20 (TB2) ── GPIO10 (R8 pull-up, DNP)
```

## 3. Interfaces

| Ref | Part | Pin 1 | Pin 2 | Pin 3 |
|---|---|---|---|---|
| BUS | Phoenix 5442769 (BC-381X9-3 GN), 3.81 mm, 3-pole, on KiCad's MKDS 1/3-3.81 footprint | +12V_MODEM (U4 output), silk "MODEM" and "+": to the 3 A fuse and the XB7's 5.5 x 2.1 mm centre-positive barrel | GND, silk "GND": to the GND bus | BUS, silk "+", to F1. It lands on the bus side of the INA260 (section 1.3) |
| PSU_SENSE | Phoenix 5442756 (BC-381X9-2 GN), 3.81 mm, 2-pole, on KiCad's MKDS 1/2-3.81 footprint | No net, silk "NC" | PSU_SENSE, silk "+" | |
| TB2 | TE 282834-3, 2.54 mm, 3-pole | +3V3, silk "+" | GND, silk "GND" | DQ (GPIO10), silk "DQ" |

**One 3-pole block replaces revision 4's separate BUS and MODEM blocks** [M]. Its only GND pole
is the board's return; the modem's return goes to the GND bus (section 1.3).

**The terminal's footprint now matches the part** (open item 26, closed on the 16:06 board).
- The 15:22 board had a 3.50 mm footprint under a 3.81 mm part. The owner replaced it.
- The pads are now 3.81 mm apart with a 1.1 mm drill; pads 1 and 3 are 2.5 mm, pad 2 is 2.0 mm [M].
- Phoenix's sheet for 5442769 gives [S: Phoenix Contact, BC-381X9-3 GN, item 5442769, catalogue
  PDF of 2023-10-31, pp. 2, 4, 5]: a 3.81 mm pitch, pins 0.5 by 0.9 mm and 3.5 mm long, and a
  1.1 mm hole.
- The pin's diagonal is 1.03 mm [D: √(0.5² + 0.9²)], so it enters the 1.1 mm hole.
- The body is 11.43 mm wide and 7.3 mm deep, with the pin row 3.6 mm from one face [S: same,
  pp. 4, 5]. The footprint's courtyard is 12.51 x 8.40 mm [M], which fits that body.
- The courtyard overhangs the board edge by 0.4 mm and four of the block's silk segments sit
  at the edge [M]. Both are cosmetic: no copper or hole is involved.

**Ratings.** 5442769 is rated 13.5 A and 200 V, for 0.14 to 1.5 mm² or 26 to 16 AWG wire, with
5 mm of strip and 0.22 to 0.25 Nm on the screws [S: same, p. 2]. Revision 5's "10 A, 16 to 30
AWG" came from a distributor listing. The BUS lead pair is 16 AWG (owner, 2026-11-09), the
largest wire the block takes.
- **Hold the block while tightening.** On a 2- or 3-pole block one soldered pin per pole cannot
  take the screw torque by itself [S: same, p. 3, application note].
- 5442756 (the 2-pole PSU_SENSE block) is BC-381X9-2 GN: 13.5 A, 200 V, 3.81 mm pitch, 2
  positions, screw connection, soldered [S: Phoenix Contact, "PCB terminal block - BC-381X9- 2
  GN - 5442756", catalogue print dated 11/10/2014, p. 1; supplied by the owner 2026-11-10].
  - Its footprint is 3.81 mm pitch with 1.1 mm holes and 2.0 mm pads [M], so the pitch matches.
  - That print has no dimensioned drawing: it gives no pin size and no hole diameter. Those
    are still taken from the 3-pole part of the same series [I: falsified by a 5442756 pin
    that does not enter 1.1 mm] (open item 30).

**PSU_SENSE pad 1 connects to nothing, by decision** [M] (owner, 2026-11-10). No ground wire
runs with the sense lead: the PSU's negative already reaches the board through the GND bus and
the board's GND pole, and the two dividers return that way.

**Test points** (2.0 mm pads with 1.0 mm drill): VIN, GND, 3V3, MODEM_EN and +12V MODEM [M].

**PSU_SENSE wiring.** It is wired to the Mean Well HDR-60-12 output, upstream of the Pololu #5382
ideal diode, so it reads about 0 V with mains off (owner, 2026-11-08). With mains on it reads the
PSU's 13.6 V set point (section 1.5). The commissioning backfeed
test measured 0.10 V there [M: commissioning test, as recorded 2026-11-08].

**The PSU_SENSE lead is unfused** (owner, 2026-11-09). **Fuse it at the tap end, at 0.5 A**
(recommended; revision 4 said 0.5 to 1 A; open item 25):
- **The board's sense copper is the thinnest unprotected conductor on it.** The track is 0.30
  to 0.50 mm wide [M]. A 0.30 mm track carries 1.0 A for a 10 °C rise and fuses near 3.1 A
  [D: IPC-2221 and Preece, 35 µm copper], below the 4.73 to 7.20 A the PSU can feed into a short.
  A 0.5 A time-lag link's 1.05 A overload warms it 11 °C; a 1 A link's 2.1 A warms it 54 °C [D].
- **The PSU does not protect a thin sense wire.** It hiccups only when a fault pulls its output
  below 50 %, which is 6.8 V [S: section 1.5; D]. A partial short that holds the output above
  that is fed continuously in the overload band, 4.73 to 7.20 A [D: 1.05 x 4.5; 1.6 x 4.5]. If
  the #5382 fails short, the pack can feed the fault as well.
- **The 7.5 A PSU-positive fuse does not protect it either.** It is rated above the PSU's
  maximum output (section 1.5). And if the tap is on the PSU side of that fuse, the sense wire is
  not in its path at all.
- **It costs no accuracy.** The sense load is about 0.23 mA (section 4.5). Even 10 Ω of fuse
  resistance against the dividers' 118 to 122 kΩ is under 85 ppm [D: 10 ÷ 118k].
- **It fails safe.** A blown sense fuse looks like the wire coming off (section 5). The mirror
  alert in section 8 reports it.
- **Where to tap.** Tap between the 7.5 A fuse and the #5382, still upstream of the diode so the
  pack cannot backfeed it. Then a blown PSU fuse reads as an ordinary outage and the shed logic
  handles it, rather than leaving the PSU running with no path to the bus (section 1.5). Where it
  taps today is not recorded.

**TB2 pin order is a wiring hazard.** Rev 4 runs 3V3 / GND / DQ [M]. The deployed board's JST-XH
ran GND / DQ / 3V3 [M: `UPS-Monitor-THT.kicad_pcb` in the repo]. The DS18B20's own order is
GND / DQ / VDD. Rev 4's "GND" silk label sits 1.46 mm from pad 2 and 1.08 mm from pad 3 (DQ)
[M], so on its own it points nearer the wrong pad. The 15:22 board adds "+" at pad 1 and "DQ"
below pad 3, so the three labels now read in pad order [M]. Still check the pins with a meter
before the sensor goes on
(see section 9).

## 4. Circuit blocks

### 4.1 Input and fuse
BUS + reaches F1, a Würth 696108003002 holder for 5x20 mm fuse-links, and leaves as VIN.
- Track widths along each load path [M]:
  - BUS, terminal pad 3 to F1: 2.5 mm, 7.0 mm long (re-routed on the 16:06 board).
  - VIN, F1 to U4: 1.85 mm at its narrowest, 35.2 mm long.
  - VIN, F1 to U3: 1.6 mm at its narrowest, 18.1 mm long. This branch carries only the
    board's ~35 mA.
  - +12V_MODEM, U4 to terminal pad 1: 2.0 to 2.5 mm, 35.2 mm long (re-routed likewise).
  - The 0.8 mm on VIN and the 1.0 mm on +12V_MODEM are spurs to their test points only.
  - A 1.85 mm track carries about 3.7 A at a 10 °C rise (section 1.7).
  - Section 7 checks every net's width against its load and against the fuse behind it.
- Track resistance [D: track length ÷ width x 0.49 mΩ per square, for 35 µm copper at 20 °C;
  pads, vias, the fuse and its holder are not included]:
  - Terminal to U4's input: 10.3 mΩ [D: 1.38 + 8.87], which drops 22 mV at the 2.15 A peak.
  - U4's output to the terminal: 7.25 mΩ, which drops 11 mV at the 1.49 A peak.
- F1 now carries U4 (the modem) as well as U3, which is the whole system's load.
  - The schematic note puts that at about 1.1 to 1.2 A at 12 to 11.8 V [S: schematic note, D:
    13.4 W bus load / V].
  - Section 1.7 bounds it at 0.98 to 1.74 A continuous and 2.15 A peak [D].
- The owner first gave 2 to 2.5 A (2026-11-08). A time-lag, DC-rated link is advised (schematic
  note). Section 1.7 gives the margin at each end of that range.
- **Revision 3 advised 2.5 A** (peer review, S4; superseded below). A failed shed at the BMS
  cutoff runs a 2 A link at 87 % and a 2.5 A link at 70 % [D: 1.74 ÷ 2.0, 1.74 ÷ 2.5]. Down
  to the shed threshold the figures are 74 % and 59 % [D: 1.47 ÷ 2.0, 1.47 ÷ 2.5]. Only
  2.5 A stays under the 75 % guidance in both cases [D: 70 % and 59 %].
- **The board now names a 3.15 A link.** F1's Description field reads "Use Fuse - 3.15 A 250 V
  300 V Fuse Cartridge, Ceramic 5mm x 20mm, 0001.2509" [M].
  - At 3.15 A the failed-shed case is 55 %, the shed-threshold case 47 % and the 2.15 A peak
    68 % [D: 1.74 ÷ 3.15, 1.47 ÷ 3.15, 2.15 ÷ 3.15]. All three sit under the 75 % guidance.
  - The narrowest track behind F1, 1.6 mm, carries about 3.4 A at a 10 °C rise
    [D: 0.048 x 10^0.44 x 86.8^0.725, with 86.8 mil² = 63.0 mil x 1.378 mil], so a 3.15 A link
    still sits under the copper. That 1.6 mm section is on the branch to U3 only, about 35 mA
    in service [M: path trace on the 16:06 board].
- **F1 is 3.15 A** (owner, 2026-11-10: "unless it causes a safety issue"). **The datasheets
  show none.** This supersedes the 2.5 A advice above (open item 21, closed).
  - **The link.** 0001.2509 is a Schurter SPT 5x20: time-lag T, ceramic, to IEC 60127-2 sheet 5,
    rated 250 VAC and 300 VDC. It breaks 1500 A at 250 VAC (IEC) and 1500 A at 300 VDC (UL)
    [S: Schurter SPT 5x20 datasheet, dated 2026-07-21, pp. 1 to 4, row 0001.2509]. The bus is
    13.6 V DC, far inside that. What the pack can deliver into a short is not recorded here.
  - **Its gates** [S: same, p. 3, 1 to 3.15 A row]: it holds 1.5 x rated for at least 60 min,
    and opens within 30 min at 2.1 x, in 0.75 to 80 s at 2.75 x, in 0.095 to 5 s at 4 x and in
    10 to 150 ms at 10 x. Here those are 4.73, 6.62, 8.66, 12.6 and 31.5 A [D: multiples of 3.15].
  - **The copper behind it survives the worst the link allows.** The 1.85 mm path to U4 rises
    17 °C at 4.73 A held indefinitely and 37 °C at 6.62 A for up to 30 min. The 1.6 mm branch to
    U3 rises 22 °C and 47 °C [D: IPC-2221, external, 35 µm; section 7].
  - **The holder.** 696108003002 is rated 6.3 A at 250 VAC by VDE and 20 A by UL, −30 to
    +120 °C [S: Würth drawing 696 108 003 002, rev D, sheet 1]. Its 22.6 mm pin pitch and 1.5 mm
    hole match the board [M].
  - **One formal mismatch, not new with 3.15 A.** The holder's rated power acceptance is 1.6 W
    (VDE) [S: same]. The link's power at 1.5 x rated is 0.8 W typical and 4.0 W maximum; the
    2.5 A link's is 0.6 W and 2.5 W [S: Schurter, p. 3]. So on the maximum column every SPT link
    of 1 A and above exceeds that holder figure.
    - In service the link dissipates 0.21 W at most at the 2.15 A peak
      [D: 2.15² x 0.140 V ÷ 3.15 A, the maximum voltage drop at rated current].
    - The 4 W case needs 4.73 A or more held for minutes. Nothing downstream is known to draw
      that without tripping U4's own limits (section 4.3) [I: falsified by a fault that holds
      F1 between 4.7 and 6.6 A].
  - **What 3.15 A gives up against 2.5 A:** a fault between 3.75 and 4.73 A, which a 2.5 A link
    opens and a 3.15 A link may hold [D: 1.5 x 2.5; 1.5 x 3.15]. The copper carries it (above).
- **The BUS lead's own fuse must be rated above F1,** so that a fault on the board opens F1 and
  not the lead.
  - The enclosure has three fuses (owner, 2026-11-09):
    - 3 A on the modem lead, between terminal pin 1 and the XB7's barrel jack;
    - 7.5 A on PSU positive;
    - 10 A on the battery lead.
  - **The 3 A fuse is downstream of U4,** so it does not protect the BUS lead and needs no
    coordination with F1. The XB7's 1.49 A peak is 50 % of it [D: 1.49 ÷ 3].
    - The fuse's sheet allows a 3 A link 2.5 A of continuous load at 20 °C and 2.2 A at 60 °C
      [S: Littelfuse MINI 32 V datasheet, p. 3], so 1.49 A is inside it.
    - Its typical cold resistance is 33.75 mΩ, which drops 50 mV at 1.49 A ahead of the XB7
      [S: same, p. 2; D: 1.49 x 0.03375] (open item 13).
    - A short that U4 feeds at its 5.1 A limit is 170 % of the link, which the sheet opens
      within 600 s [S: same, p. 3, the 135 % gate; D: 5.1 ÷ 3].
  - **The BUS lead pair is 16 AWG, about 6 in long, with no fuse of its own** (owner,
    2026-11-09). In Rev 4 that lead
    carries the whole system's load: 0.98 to 1.74 A continuous and 2.15 A peak (section 1.7).
    Rev 1's lead carried only the board's ~35 mA.
    - Its protection is the 10 A battery fuse and the 7.5 A PSU fuse, both upstream of it.
      The US electrical code's small-conductor rule allows 16 AWG copper a 10 A device with
      continuous load up to 8 A [S: NEC 240.4(D)(2), as quoted by secondary sources; the code
      text itself was not read]. That rule is for building wiring and is used here as a
      benchmark only. The lead's 1.74 A continuous is far under it [D].
    - The owner supplied the hook-up wire's sheet (2026-11-10): CnC Tech UL 1569, PVC, rated
      105 °C and 300 V, flame class VW-1. Its 16 AWG is 26 strands of 0.254 mm, 1.25 mm²,
      2.40 mm over the insulation, and 14.6 Ω/km at most [S: CnC Tech, UL 1569 Hook-Up Wire,
      P/N 1569-XX-1-0500-0XX-1-TS, pp. 1, 2]. That is inside the terminal's 1.5 mm² limit.
      - Each 6 in conductor is 2.2 mΩ and dissipates 0.22 W at 10 A [D: 14.6 Ω/km x 0.1524 m;
        10² x 0.0022].
      - The sheet gives no current rating, so the 10 A benchmark above still stands on the
        code's figure alone. The marking on the lead itself was not read.
    - The terminal takes 13.5 A, and the 2.5 mm BUS track rises 57 °C at a sustained 10 A
      [D: IPC-2221], over its 7.0 mm between two large pads. So the lead, the terminal and the
      track ahead of F1 all stand behind the 10 A fuse.
    - Selectivity: the upstream fuses are 10 A and 7.5 A against F1's 3.15 A, and F1's melting
      I²t is 22 A²s [S: Schurter, p. 3]. The owner supplied the enclosure fuses' sheet
      (2026-11-10): Littelfuse MINI blade fuses, 32 V DC, interrupting 1000 A. Typical I²t is
      122 A²s for the 10 A link and 82 A²s for the 7.5 A [S: Littelfuse MINI 32 V datasheet,
      revised 2024-09-27, pp. 1, 2].
      - **In a hard short on the board F1 melts first.** The 10 A link needs 5.5 times F1's
        melting I²t and the 7.5 A link 3.7 times [D: 122 ÷ 22; 82 ÷ 22]. Those are typical
        values, and F1's clearing I²t at 12 V is on neither sheet [I: falsified by a bench
        short on VIN that opens the 10 A link].
      - **Around 13 A the order is not guaranteed.** The 10 A link may open in 0.75 s at
        13.5 A (its 135 % gate, 0.75 to 600 s) [S: Littelfuse, p. 3; D: 1.35 x 10]. F1 may
        take 5 s at 12.6 A (its 4 In gate, 0.095 to 5 s) [S: Schurter, p. 2; D: 4 x 3.15].
      - **The PSU cannot open the 7.5 A link ahead of F1.** Its 7.20 A ceiling is 96 % of
        that link and 2.29 times F1's rating, which F1 opens within 30 min [D: 7.20 ÷ 7.5;
        7.20 ÷ 3.15; S: Schurter, the 2.1 In gate].
      - If the 10 A link does open first, the pack is off the bus while the PSU carries the
        load. The INA260 would then read the PSU-held bus and no pack current, as it does
        with a full pack at float, and the next outage would drop the modem at once
        [I: falsified by a section 8 alert that fires with the battery lead open].
- Bulk decoupling on VIN: C4 47 µF 50 V aluminium electrolytic, plus C5 and C6 0.1 µF X7R.
  C6 sits at U4.

### 4.2 3.3 V supply
U3 is a Pololu D24V7F3 step-down module in a 1x3 socket: pin 1 +3V3, pin 2 GND, pin 3 VIN.
- +3V3 feeds the XIAO's 3V3 pin (pad 12), the INA260's VCC, the DS18B20, R1 and R8.
- The XIAO's 5V pin (pad 14) is not connected [M].
- Decoupling: C1 10 µF X5R, C2 and C3 0.1 µF.
- U3 takes 4 to 36 V in and gives 600 mA continuous at most, with short-circuit and
  over-temperature protection and no reverse-voltage protection [S: Pololu #5592 product page,
  features list, read 2026-11-10]. The page gives no figure for its short-circuit current.
- The +3V3 trunk is 1.5 mm and its branches to TB2, R8 and the test point are 0.30 mm [M]. A
  0.30 mm track rises about 3 °C at U3's 600 mA [D: IPC-2221, external, 35 µm], so U3 limits
  before the copper does.

### 4.3 Modem 12 V (U4)
U4 is a Pololu #4984 S13V25F12, a 12 V ±4 % step-up/step-down regulator [S: Pololu #4984 page].
- It is mounted on the **bottom** side and uses only the module's 0.1 in row, in the order
  EN, VIN, GND, GND, VOUT [S: Pololu product picture + STEP hole positions, per schematic note].
  **EN is next to VIN on the module's row** (owner, 2026-11-10), as on the footprint, whose
  pad 1 is MODEM_EN and pad 2 VIN [M] (open item 8, closed).
- EN is an active-high enable. A 475 kΩ internal pull-up to VIN enables the module by default,
  and driving EN low puts it to sleep. The rising threshold is 1.0 to 1.2 V and the falling
  threshold typically 100 mV lower [S: Pololu #4984 page].
  - **Correction (revision 3):** revisions 1 and 2 called EN "active-low". That was an error in
    revision 1's text, found by the peer review. The circuit was never affected: Q1 pulls EN low
    to turn the modem off, and the 475 kΩ pull-up holds it on, as section 4.4 always described.
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
- **The 2.5 A is the spec table's figure, not the figure at this board's input** (peer review,
  S6). A buck-boost's output limit falls as its input falls. Pololu's maximum-continuous-output
  curve for the 12 V version passes about 2.3 A at 9 V and 2.7 A at 12 V [S: Pololu #4984,
  "Maximum continuous output current" graph, read by eye to about ±0.1 A, 2026-11-10]. That
  gives about 2.4 A at 10.0 V and 2.65 A at 11.8 V [D: linear between those two points], both
  above the 1.49 A peak (open item 23, curve part closed). Its output current limit is 5.1 A
  [S: same page].
- **Its temperature and floor clearance are unchecked.** It hangs from the bottom side and can
  get hot enough to burn (section 1.7). At first power, measure its temperature at the XB7's
  peak load, and check the clearance between the module and whatever the board stands on
  (open item 23).

### 4.4 Modem-enable logic (Q1, Q2)
Q1 and Q2 are 2N3904 transistors, formed-lead TO-92 (Diotec, 2.54 mm).
- Their footprints are in-line TO-92 at 2.54 mm pad pitch. Pad 1 goes to GND (emitter), pad 2
  is the base and pad 3 the collector [M: pad nets]. Check that order against the part's
  marking before soldering.
- Both are turned so that pad 1, the GND end, faces U4's large-hole row (section 6).
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
- **Uncalibrated accuracy at 13.6 V:** about ±0.23 V from the 1 % RNMF14 parts the board now
  lists for R6 and R7 [M; D: (100/118) x 2 % x 13.6 V]. Revision 4's ±1.15 V was for the 5 %
  parts the board listed then. Add ±0.23 V from the ADC [D: 35 mV x 118/18].
  That is fine as a mains-present signal but rough as a voltage.
- **Calibrated accuracy:** a one-point calibration against a DMM at the terminal removes both
  errors at the set point. The residual should be tens of mV [I]. That is falsified if a day's
  readings drift more than about 0.1 V from DMM spot checks.
- **Source impedance:** 15.25 kΩ [D: 100k ‖ 18k]. With C7 that is a 1.5 ms time constant [D].
  100 nF is also the datasheet's own test condition for its linearity figures [S: Table 5-5].
- **If the PSU_SENSE wire comes off:** R5 holds Q2 off (no override) and the ADC reads 0 V.
- **Load on the PSU:** about 0.23 mA for both dividers together [D: 13.6/122k + 13.6/118k].
- **Not a wake source.** 2.07 V is under the ESP32-C3's minimum input-high level,
  0.75 x 3.3 = 2.475 V [S: `../UPS-Monitor/esp32-c3_datasheet.pdf` v1.2, Table 14; D].
  - So PSU_ADC cannot wake the chip from deep sleep as a digital input.
  - It does not need to: Q2 restores the modem in hardware when mains returns (section 4.4).

### 4.6 Monitoring (INA260, DS18B20)
**INA260 (U2)** is an Adafruit breakout in a 1x8 socket: 1 VCC (+3V3), 2 GND, 3 SCL, 4 SDA,
5 Alert.
- Pins 6 to 8 (VBus, Vin+, Vin−) are not connected on this PCB [M]. The measured current runs
  through the breakout's own terminal block, as on the deployed board (schematic note).
- The breakout carries the I2C pull-ups [S: firmware header].
- R1 10k pulls Alert up to +3V3. On the deployed board this resistor is called R2, and firmware
  V4.0's comments still use that name (section 8.1).

**DS18B20** connects on TB2 to GPIO10.
- **R8, 4.7 kΩ from DQ to +3V3, is now on the board** [M]. Revisions 1 to 4 said this board had
  no 1-Wire pull-up, which was true of the saves they described. The deployed board has none
  [M].
- **The sensor in service carries its own pull-up, in its head** (owner, 2026-11-08 and
  2026-11-10); its value is not recorded.
- **R8 is therefore not fitted (DNP)** (owner, 2026-11-10; open item 27, closed). The footprint
  stays on the board. The board file does not yet mark R8 as DNP [M], so mark it before the
  BOM is regenerated (open item 5).
- A replacement sensor with no pull-up of its own needs R8 fitted.
- R8 lies under the edge of the INA260 breakout (section 6).

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

The pad nets in this table were re-read from the 15:22 board [M]. Firmware V4.0 uses the same
six GPIOs [S: `ups-monitor-rev4.yaml`; section 8.1].

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
| PSU_SENSE wire comes off with mains present | No override, and the ADC reads "mains absent". The firmware sheds only if the battery is also ≤ 11.8 V, which it should not be while mains is charging it [I]. Survival sleep could also start: see the survival-sleep row below. A blown PSU_SENSE fuse (section 3) looks the same. Firmware V4.0 raises "PSU Sense Lost" after 60 s in this state, and starts survival sleep only after a latched shed (section 8.1) | Falsified by a float voltage at or below 11.8 V |
| PSU_SENSE lead shorts while unfused | The PSU feeds the fault at up to its 7.20 A ceiling, and hiccups only if the fault pulls its output below 6.8 V. A thin sense wire can overheat | Section 3: fuse at the tap; open item 25 |
| Mains lost | Q2 keeps the override until the HDR output decays below about 3 V, so MODEM_OFF works only after that decay | **Decay time unmeasured** (open item 6) |
| ESP deep-sleeps after shedding the modem | GPIO5 may float, and R3 then turns the modem back ON unless the pin is held. Firmware V4.0 latches the pad HIGH with both hold calls before it sleeps, and counts every wake that finds the pad LOW ("Shed Hold Lost Count", section 8.1) | **Untested on hardware** (open item 7) |
| ESP reboots during a latched shed (crash, watchdog, OTA) | The modem comes back on: V4.0 keeps the latch in RAM only. The firmware sheds again after about 20 s of valid readings at or below 11.8 V [D: 10 mains polls + 10 valid reads, at 1 s each; both placeholders] | Section 8.1; by design, so that no stored state can shed at boot |
| INA260 unreadable or implausible on a survival wake | V4.0 leaves survival sleep and boots normally, with the modem on (exit reason 2). With no valid reading it never sheds again, so a depleted pack runs to the BMS's 10.0 V cutoff | Section 8.1, deviation 2: on any doubt the modem stays on |
| Shed pack rests at or above 13.0 V during survival sleep, with PSU_ADC reading mains absent | V4.0 leaves survival sleep (exit reason 5) and the modem comes back on, on battery. The firmware sheds again at 11.8 V, and the cycle can repeat [I] | Section 8.1, deviation 1. Falsified by a shed pack that rests below 13.0 V (open item 14) |
| A solder tail under U4 touches the module's large-hole row or its underside | Depends on the pair: a Q2 tail on the VIN hole shorts VIN to GND behind F1 and blows it [D] | Section 6: trim flush, Kapton; open item 29 |
| F1 blows, U4 fails, or the 3 A modem-lead fuse opens | Modem off. Nothing on the board bypasses F1 or U4. Recovery is to plug the XB7 into its OEM adapter (NBC56B120460VU) on mains: a one-plug bypass. The adapter is on hand (owner, 2026-11-09); keep it beside the UPS | Design trade: the modem now depends on F1, U4 and this board; open item 22 |
| Firmware never sheds on battery (down, or running with no INA260 reading) | Modem stays ON and the pack runs to the BMS's 10.0 V cutoff, where the next row applies. With the BP-65 removed, nothing else sheds it. With no valid reading this is the intended direction: an invalid reading never sheds (section 8) | Sections 1.1 and 1.6; F1 at that point in section 1.7 |
| Pack hits BMS cutoff, then recovers | Everything restarts, and U4's EN pull-up brings the modem back without firmware | 4.3 |
| HDR-60-12 OVP trips | The PSU shuts off with mains present. PSU_SENSE reads about 0 V, so the board sees an outage: the pack carries the modem, and the firmware sheds at 11.8 V. Nothing recovers until AC is cycled at the PSU | OVP latches [S: HDR-60 datasheet]; margin in section 1.5; open item 11 |
| GPIO5 left HIGH after a shed: the deep-sleep hold never released | Hidden on mains, because Q2 holds the modem on. At the next outage the modem sheds as soon as the HDR output decays, **with a full pack** | Peer review, C1. Section 8: drive LOW, then release the hold, at every mains poll, plus a readback alert; open items 15 to 17 |
| Shed on an invalid reading (NaN, a stale value, or 0 V from a failed read) | Modem off with a full pack, for the rest of the outage once the shed is latched | Peer review, C1. Section 8: the valid-reading rule; open item 15 |
| ESPHome restores GPIO5 HIGH at boot, before `on_boot` runs | On battery, the modem sheds at boot, whatever charge the pack holds | Peer review, C1. Section 8: GPIO5 kept out of the switch and output components; open item 15 |
| PSU running, but its path to the bus open (#5382 open, or a PSU or bus lead off) | PSU_SENSE stays up, so Q2 blocks any shed. The pack carries the modem to the BMS's 10.0 V cutoff with no warning | Peer review, C2. Section 8: plausibility alert; open item 18 |
| No latch: the bus recovers above 11.8 V once the modem's load is gone | The modem cycles off and on as the load comes and goes | Peer review, S2. Section 8: latch the shed; open item 15 |
| Survival sleep entered with mains present (PSU_SENSE wire off, pack at float, near 0 A) | The monitor goes dark between 120 s wakes with mains present. The modem is unaffected | Peer review, S3. Section 8: entry tied to the latched shed, plus the mirror alert; open item 18 |

Firmware V4.0 implements the section 8 measure named in each "Peer review" row (section 8.1).
None of them has run on hardware.

## 6. Mechanical and assembly

**Board:**
- Outline 38.00 x 53.25 mm, measured on the centre line of the Edge.Cuts rectangle [M].
- 2 layers, 1.60 mm thick, 35 µm copper and a GND pour on both layers [M].
- Fabricator per back silk: OSH Park.
- The back-silk "Board Size: 38mm x 53.25mm" text now agrees with the outline [M].

**Mounting holes:** three 3.2 mm holes [M]: H1 at (32.25, 27.50), H2 at (17.50, 44.75) and H4 at
(25.75, 62.25).
- **Hardware is M2.5 nylon,** standoffs and screws (owner, 2026-11-09). An M2.5 screw has
  0.35 mm of play all round in a 3.2 mm hole [D: (3.2 − 2.5) ÷ 2].
- H1 sits under the INA260 and gets a standoff to support its overhang (owner).
  - **That standoff is a rest, not a fastening.** The breakout's two mounting holes are
    17.78 mm from its header row [S: Adafruit INA260 (PID 4226) fabrication print, read
    2026-11-10; D: 0.90 − 0.10 − 0.10 in]. From U2's socket row at y 33.0 that puts them at
    y 15.2, about 9.0 mm beyond the board's edge at y 24.25 [D]. H1 is 5.5 mm from the row [M],
    so it lines up with neither hole (open item 9, this part closed).
- H2 sits under the XIAO, and H4 under U3.
- **Keep the hardware nylon.** +3V3 copper on the front runs 2.00 mm from H2's centre and
  2.50 mm from H4's centre [M]. A metal head or washer wider than 4.0 mm would sit on the
  track at H2 [D: 2 x 2.00]. Only GND copper is near H1 [M].
- **Three "REF\*\*" M3 screw placeholders still sit over the holes.** They cause 9 of the DRC
  errors (section 7). The owner deletes them when the board is finalised (open item 4).
- Revision 4 noted that the 3D view hangs Würth 15 mm standoffs below the board. That was not
  re-read on the 15:22 board.

**U4 on the bottom side:**
- The module is 22.9 x 22.9 x 9.7 mm [S: Pololu #4984], held by its five 0.1 in pins. It goes
  on its supplied male pin header (owner, 2026-11-09).
- This board's holes are H1, H2 and H4, so the module's own two M2 holes go unused.
- It dissipates 0.64 to 2.54 W in typical service (section 1.7), facing the enclosure floor.
- Its clearance to the floor below the standoffs is not recorded (open item 23).
- **The module's large-hole row faces the board.** The row is VIN, GND, GND, VOUT from the EN
  end (Pololu's picture, per the owner, 2026-11-09). This board does not use it.
  - The footprint draws those holes at x 41.33 and y 42.16 (VIN), 45.66, 49.16 (both GND) and
    52.66 (VOUT) [M: footprint drawing, not checked against the module in hand].
  - Q2's pad 1 (GND) is 1.88 mm from the VIN hole, edge to edge. Q1's pad 1 (GND) is 1.51 mm
    from a GND hole [M].
  - A Q2 lead that reaches the VIN hole shorts VIN to GND behind F1 (section 5).
- **Do not fit a metal screw in U4's M2 hole at (43.36, 56.68).** R6's pad 2 (GND) and R7's pad
  2 (PSU_SENSE) overlap that hole in plan [M]. A metal screw there could bridge the two pads.
- **35 plated pads lie inside U4's courtyard** [M: DRC]. They carry +3V3, MODEM_OFF, PSU_SENSE,
  PSU_ADC, MODEM_EN and both transistor bases as well as GND. Their solder tails come through
  under the module.
  - The back silk at U4 reads "Trim flush, Kapton over hole row on the module back" [M].
  - The gap the male header leaves between the board and the module is not recorded (open
    item 29).

**Under the XIAO** (about 10 mm clearance, owner; the 3D model gives 11.0 mm) [M: overlap with
U1's outline]:
- R1 to R5.
- C3 and C7: body 3.6 mm [S: distributor listings for K104K10X7RF53L2].
- H2 and its screw head.
- Pad 3 and about 2.2 mm of the body of Q1 and of Q2. The TO-92 body is 4.6 mm tall [S: Diotec
  2N3904 datasheet, version 2026-03-10, p. 3]. Its seated height on formed leads is not
  recorded; it has to stay under the XIAO (open item 29).

**Under the INA260** [M]: C2, H1 and its screw, and one end of R8. R8's courtyard overlaps U2's,
which is one DRC error (section 7).

**Under U3** [M]: C1, and H4 with its screw.

**Resistors:** R1 to R8 now lie flat, on 5.08 mm axial footprints with 0.7 mm drills
(`R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm`) [M].
- Revisions 1 to 4 described upright resistors on 2.54 mm pads, kept under 8 mm tall (owner,
  2026-11-08). That limit no longer applies to them.
- The parts are Stackpole RNMF14 mini metal film (owner, 2026-11-08).
- The body is 3.30 x 1.78 mm [S: Stackpole RNF/RNMF datasheet, 3/30/2023, p. 2]. They give
  1 % / ±50 ppm on the R6/R7 divider [S: p. 1].
- The board's Value fields now name them [M]: R1 10 kΩ, R2, R3, R4 and R7 100 kΩ, R5 22 kΩ,
  R6 18 kΩ, R8 4.7 kΩ.

**Assembly order:**
1. Solder the parts that go under the modules before their sockets.
2. Trim every solder tail under U4 flush, and tape the module's hole row with Kapton.
3. Fit U4 on the bottom side.
4. Fit each screw before the module above it: H1 before the INA260, H2 before the XIAO and H4
   before U3. The module has to come out to reach its screw again.

## 7. Verification status (2026-11-10)

| Check | Result |
|---|---|
| DRC, 16:06 board | 98 violations, 45 errors, 0 unconnected, 41 schematic-parity items [M: `kicad-cli pcb drc`, all severities, schematic parity on]. The zone refill was not repeated on this save. The 15:22 save gave 95, 45, 0 and 41, the same with and without a refill; the 2026-11-09 20:12 save gave 90, 43, 0 and 38 [M] |
| DRC errors by type | 35 PTH inside courtyard, all under U4. 6 NPTH inside courtyard and 3 courtyard overlaps, all from the three REF** screw placeholders over H1, H2 and H4. 1 courtyard overlap between R8 and U2. No clearance, copper or unconnected errors [M]. These fit parts deliberately placed under the modules (section 6), but each one has not been reviewed [I]. Review each, and give each deliberate one a DRC exclusion with a comment saying why (open item 24). |
| DRC warnings by type | 16 silk over copper, 14 library-footprint mismatch, 10 silk-to-edge, 8 silk overlap, 3 co-located holes (screw placeholders over H1/H2/H4), 2 text height [M]. Against 15:22 that is 4 more silk-to-edge, from the new terminal's outline, and 1 fewer silk overlap [D] |
| Schematic parity vs 16:06 board | 41 [M], with the same count in each class as at 15:22: 17 footprint-to-symbol mismatches (BUS, C7, R1 to R7); 12 field mismatches; 5 net conflicts (BUS pads 1 to 3, F1 pad 1, PSU_SENSE pad 1); 1 footprint missing from the board (MODEM); 4 extra on the board (R8 and the three REF** placeholders); 2 duplicate references (REF**). The schematic has not followed the board since 2026-11-08 (open item 5) |
| Netlist, read from the 15:22 board's pads | Agrees with sections 3, 4 and 4.7, and with the pins firmware V4.0 uses [M] |
| Fabrication limits, 16:06 board | Smallest plated drill 0.30 mm, via annular ring 0.15 mm, narrowest track 0.20 mm, copper to the outline's centre line 0.50 mm [M]. Each clears the OSH Park 2-layer limit: 10 mil drill, 5 mil annular ring, 6 mil trace and space, 15 mil board-edge keepout, which are 0.254, 0.127, 0.1524 and 0.381 mm [S: OSH Park 2-layer service page, read 2026-11-10; D: mil x 0.0254]. The review tool's profile holds the same four figures. Its verdict, "OUTSIDE OSH LIMITS: hole-to-hole edge gap, mask web, different-net pads", comes only from the three REF** screw placeholders |
| GND pour | 15:22 board: 13 islands on the front and 6 on the back, each tied to GND by a via or a plated pad; one GND via, at (35.05, 39.05), sat only partly inside the front fill [M]. 16:06 board: of 84 GND vias the check flags one, at (16.75, 66.75), added beside the terminal. It is 9/16 inside the fill on both layers and 0.37 mm from BUS pad 1 [M]. It still connects: DRC reports 0 unconnected. The islands were not recounted on this save |
| Track widths against load, 16:06 board | Every track was measured by net and layer [M: `pcbnew`]. BUS 2.5 mm. VIN 1.85 to 2.1 mm on the path to U4, 1.6 mm on the branch to U3. +12V_MODEM 2.0 to 2.5 mm. +3V3 1.5 mm trunk, 0.30 mm branches. PSU_SENSE 0.30 to 0.50 mm. Signals 0.20 to 0.25 mm. No via on BUS, VIN or +12V_MODEM. At a 10 °C rise the copper carries 4.65 A at 2.5 mm, 3.95 A at 2.0 mm, 3.74 A at 1.85 mm, 3.36 A at 1.6 mm, 3.21 A at 1.5 mm, 1.45 A at 0.50 mm, 1.00 A at 0.30 mm and 0.74 A at 0.20 mm [D: IPC-2221 external, 0.048 x ΔT^0.44 x A^0.725, 35 µm]. Against those: 2.15 A peak on BUS and VIN (rise 1.7 °C at 2.5 mm, 2.8 °C at 1.85 mm), 1.49 A on +12V_MODEM (1.1 °C at 2.0 mm), under 0.14 A on +3V3 [D: 0.45 W ÷ 3.3 V, section 1.7], and signal currents of milliamps. **Every net passes** |
| Track widths against the protection behind them | Behind F1 (3.15 A): section 4.1; the worst is 47 °C on the 1.6 mm branch at 6.62 A for up to 30 min [D]. Ahead of F1: the 2.5 mm BUS track rises 57 °C at the battery lead's 10 A fuse [D]. Behind U4: 2.0 mm rises 18 °C at U4's 5.1 A output limit [D; S: Pololu #4984], and the modem lead has its own 3 A fuse. Behind U3: 0.30 mm rises about 3 °C at 600 mA [D; section 4.2]. **PSU_SENSE is the exception:** its 0.30 mm copper has no fuse behind it until the lead is fused (section 3; open item 25) |
| Thermal reliefs, 16:06 board | Both GND zones use thermal reliefs with 0.5 mm spokes and a 0.5 mm gap; every spoke measured 0.49 to 0.50 mm wide [M: fill sampled on a ring around each pad]. Every GND pad has at least 2 spokes on each layer: BUS pad 2 has 4 + 4 (front + back), U4's GND pins 4 + 4 and 2 + 2, U3, U2 and C4 2 + 2, Q1 and Q2 3 + 3, the rest 2 to 4 per layer. BUS, VIN and +12V_MODEM pads connect by tracks, not zones. The GND lead carries at most about 0.66 A (section 1.3), which is 0.08 A per spoke at BUS pad 2 [D: 0.66 ÷ 8]. Even the 10 A upstream fuse through those 8 spokes is 1.25 A each, under the 1.45 A a 0.5 mm spoke carries at a 10 °C rise [D]. **All pass** |
| Schematic ERC | Not re-run. It was 0 on 2026-11-08 18:48 [M] |
| BOM CSV in the board folder | **Stale.** The 2026-11-08 16:09 export lists three 2-pole terminal blocks and 5 % carbon-film R1 to R5, with no R6 to R8 and no C7 [M] |
| Terminal block against its footprint | **Resolved on the 16:06 board.** The footprint is 3.81 mm pitch with 1.1 mm holes [M], and the part is 3.81 mm with a 1.1 mm hole [S: Phoenix 5442769 catalogue sheet, section 3] (open item 26, closed) |
| Datasheets read for revision 6 | F1's link and holder, the 3-pole terminal, the PSU's overload wording, U3, U4's current curve, the INA260 breakout's print, the OSH Park limits, and the ESP-IDF and ESPHome pages section 8 cites. Each is cited where it is used and listed under Sources |
| Datasheets supplied by the owner for revision 7 | The 2-pole terminal (Phoenix 5442756), the hook-up wire (CnC Tech UL 1569) and the enclosure's blade fuses (Littelfuse MINI 32 V). The part numbers on the wire and the fuses in hand were not read against those sheets. The terminal's print has no dimensioned drawing (open item 30) |
| Fabricated / assembled / powered | **No** |
| U4 pin order on the actual module | EN is next to VIN on the module's 0.1 in row (owner, 2026-11-10). The footprint agrees: pad 1 MODEM_EN, pad 2 VIN, pads 3 and 4 GND, pad 5 +12V_MODEM [M] (open item 8, closed) |
| Rev 4 firmware | V4.0 written. Its configuration is valid and it compiles on ESPHome 2026.10.2: real compile, exit 0, and `-Wall -Wextra` adds no warning to the deployed firmware's baseline [M, 2026-11-09]. **Never flashed or bench-tested** (section 8.1) |
| System, section 1 (2026-11-09) | PSU set point 13.6 V and the new pack (owner). The installed PSU's OVP range, U4's output and the new pack's capacity are **not checked** (open items 11, 13 and 14) |

## 8. Firmware requirements for Rev 4

**Why these matter.** Hardware cannot tell a correct HIGH on GPIO5 from a wrong one (section
1.2). Revision 3 adds the requirements below from the peer review (C1, C2, S2, S3). Each one
closes a case where a wrong MODEM_OFF sheds the modem with a full pack, or where the pack runs
down with no warning (section 5).

Firmware V4.0 now implements them. Section 8.1 says how, which values are still placeholders,
and where it departs from this list.

- **GPIO5 (MODEM_OFF):** output, LOW at a cold boot and on restore (modem on). Drive HIGH only
  when battery ≤ 11.8 V **and** mains is absent [S: schematic note].
  - **Only valid readings can shed.** The battery test passes only on N consecutive valid
    INA260 readings at or below 11.8 V.
    - A reading is valid only if it is fresh from this poll, not NaN, and in a plausible range.
    - A NaN, a stale value or a 0 V from a failed read never counts toward a shed. On any doubt,
      the modem stays on.
    - The N consecutive readings also debounce the trip against the XB7's peaks, which draw
      1.82 A at 11.8 V (section 1.7).
    - V4.0 uses N = 10 and a range of 5.0 to 16.0 V, both placeholders (section 8.1; open
      item 28).
  - **Mains is absent only when debounced.** PSU_ADC must read below the mains-present threshold
    for longer than the HDR decay (open item 6).
  - **Latch the shed.** Once GPIO5 goes HIGH, keep it HIGH for the rest of the outage. Do not
    release it because the bus recovers above 11.8 V after the load drops; that would cycle the
    modem. Release only on mains, debounced for longer than the HDR decay.
  - **Release the hold on every mains poll, not just on the edge.** On debounced mains, drive
    GPIO5 LOW, then call `gpio_hold_dis`.
    - A held pad keeps its level until the hold is released. On release "the gpio will be set
      to the default mode, so, the gpio will output the default level if this function is
      called. If you don't want the level changes, the gpio should be configured to a known
      state before this function is called" [S: ESP-IDF v5.5.5 GPIO reference, ESP32-C3,
      `gpio_hold_dis`, read 2026-11-10]. That is why the LOW comes first.
    - Q2 hides a stuck HIGH while mains is up. It shows only at the next outage, as a shed with
      a full pack (section 5).
  - **Read it back.** Configure GPIO5 as input and output and read the pad at every poll. Alert
    when the level read differs from the level commanded, and whenever it reads HIGH with mains
    present (open item 16).
  - **Own the pin from the first instruction.** Keep GPIO5 out of ESPHome's `switch` and
    `output` components.
    - A GPIO switch is set up at priority 800 and can restore a saved state. `on_boot` runs at
      600 by default, after it: the page gives "Defaults to `600`", and at 800 "This is where
      all hardware initialization of vital components is executed" [S: esphome.io, ESPHome core
      configuration, `on_boot`, read 2026-11-10].
    - Drive GPIO5 from a lambda at a priority above 800 that reads the wake cause first.
    - On ESPHome 2026.10.2, the version V4.0 was compiled on, hardware components and restoring
      globals are set up at priority 800 and data components at 600 [S: `esphome/core/component.h`
      and `components/globals/globals_component.h` in that release]. V4.0's lambda runs at 900.
    - That it runs first on the device is still to be seen on hardware (open item 28).
  - **On a timer wake from survival sleep, it stays HIGH only if PSU_ADC still reads mains
    absent.** If mains is back, drive it LOW and release the hold. Survival sleep reboots the
    ESP every 120 s [S: README, Operating Modes item 7]. A firmware that drives GPIO5 LOW at
    every boot would power the modem up at every wake [D].
  - **Commissioning test** (open item 17):
    1. Force a shed on battery.
    2. Let survival sleep start.
    3. Restore mains, and wait two wake periods.
    4. Cut mains again.
    5. Pass: the modem stays on. That proves the hold was released.
  - The deployed firmware already reads the wake cause (`ups-monitor.yaml`, line 590).
  - **Deep-sleep hold.** On the ESP32-C3, `gpio_hold_en` alone does not hold a digital pad
    through deep sleep; `gpio_deep_sleep_hold_en` is also needed [S: ESP-IDF GPIO reference,
    ESP32-C3].
  - Whether the held level survives the ROM boot on a timer wake is not documented there. Test
    it (open item 7).
- **GPIO4 (PSU_ADC):** ADC at 12 dB attenuation, averaged.
  - Multiply by 118/18 = 6.556 nominal [D], then replace that with DMM ÷ reading. V4.0 still
    holds the nominal 6.556.
  - The mains-present threshold must sit between the 0.10 V backfeed [M] and the 13.6 V set
    point.
  - To time the HDR decay, sample faster than the decay itself. A slow poll gives only a bound.
- **On battery comes from PSU_ADC, not from a bus threshold.**
  - The deployed firmware sets `on_battery` when the bus falls below 13.15 V [S: README]. That
    is 50 mV under the old 13.2 V float [D: 13.2 − 13.15].
  - Revision 2 gave 23.3 mV here, from the README. The README's own figures do not support it:
    its 13.1970 V mean is 47.0 mV above 13.15 V [D].
  - At a 13.571 to 13.587 V float that threshold is 0.42 to 0.44 V down [D]. A full pack could
    hold the bus above it for some time on battery [I].
- **Re-derive on this pack.** The discharge-phase thresholds (Plateau ≥ 12.65 V, Knee 12.40 to
  12.65 V, Cliff ≤ 12.40 V), the runtime estimator's capacity and the Ri baselines were set on
  the previous pack, at a 13.3 V float [S: README].
  - The host-shutdown ladder (`cliff_imminent`, `voltage_warning`, `voltage_critical`) has no
    host to shut down on this system (section 1.1).
  - Set the replacements from this pack's first discharge (open item 14).
  - **The 11.8 V shed threshold is inherited too** [S: schematic note]. It was set on the
    previous pack. Re-derive it from the same discharge.
- **Survival-sleep entry.** The deployed firmware enters on the load collapse at the BP-65's trip
  (on battery, −0.30 A < I < +0.20 A) [S: README].
  - With no BP-65, that collapse is the board's own shed. Entry therefore follows the shed.
  - The board's own draw after a shed, about −35 mA, sits inside that window [D].
  - **Enter only when the shed is latched,** not on the current window alone (peer review, S3).
    With the PSU_SENSE wire off, a pack at float on mains reads "on battery" with a current near
    0 A, which also sits inside the window.
- **Plausibility alerts** (peer review, C2 and S3). These raise an alert only. Neither one drives
  GPIO5, and neither overrides Q2 (open item 18).
  - **PSU running, bus not fed:** PSU_ADC reads mains present while the INA260 reads a
    sustained discharge of about 1 A, the modem's load (section 1.7). Wait longer than the HDR
    decay before alerting. Q2 blocks every shed in this state, so this alert is the only
    warning before the BMS cutoff.
  - **The mirror:** PSU_ADC reads mains absent while the INA260 reads the pack charging or
    holding at float. This means the PSU_SENSE wire is off.
- **Unchanged from the deployed firmware:**
  - INA260 on I2C GPIO6/7, at the address set by the module's A0 jumper (0x40 on this build)
    [S: firmware header].
  - Alert on GPIO3, now pulled up by R1. Do not carry over any GPIO5 Alert workaround for
    Rev 1's routing (section 4.7): GPIO5 is MODEM_OFF on this board.
  - DS18B20 on GPIO10.
- Run the ESP firmware validation gate (compile, not just config-valid) before flashing. V4.0
  passed it on 2026-11-09 (section 7). Run it again after any edit.

### 8.1 What firmware V4.0 implements

Everything in this section is read from [`ups-monitor-rev4.yaml`](ups-monitor-rev4.yaml), V4.0
[S]. The firmware compiles (section 7). **It has never been flashed, so nothing below has run
on hardware.**

**Pin ownership and boot:**
- GPIO5 appears only in one script, `modem_off_set`. No ESPHome switch or output uses it.
- The script sets the level, configures the pad as input and output with no pulls, and sets
  the level again. It then enables both holds (`gpio_hold_en`, `gpio_deep_sleep_hold_en`) or
  releases both.
- It does not call `gpio_reset_pin`, which would enable the pad's pull-up.
- An `on_boot` lambda at priority 900 drives the pad LOW and releases the holds on every wake
  except a survival timer wake.

**Supervisor, once a second:**
- **Mains:** present when PSU_ADC x 6.556 is at or above 7.0 V. The state changes only after
  10 polls agree, in either direction. A NaN counts as absent. "Mains Present" publishes
  nothing until that debounce has run once.
- **Shed:** only with mains debounced absent and 10 consecutive valid readings at or below
  11.80 V. A reading is valid when it is fresh, not NaN, and between 5.0 and 16.0 V.
- **Latch:** held in RAM. It releases on debounced mains.
- **Pad:** rewritten and read back at every poll. Two mismatches raise "MODEM_OFF Readback
  Fault".

**Survival sleep:**
- **Entry:** shed latched, on battery, and −0.30 A < I < +0.20 A for 30 s.
- The pad is latched HIGH with both holds as the last action before sleep.
- The ESP wakes every 120 s, for at most 10,800 wakes, which is 15 days [D: 10,800 x 120 s].
- **On each timer wake:**
  1. Read the pad as an input before anything else. LOW means the hold was lost, and "Shed
     Hold Lost Count" goes up by one.
  2. Sample PSU_ADC.
  3. Read the INA260's bus voltage, with up to two re-reads 20 ms apart.
  4. Leave survival sleep if an exit below applies. Otherwise latch the pad HIGH again and
     sleep.
- **Exits.** Each one drives the pad LOW and releases the holds:

| Reason | Condition |
|---|---|
| 1 | PSU_ADC reads mains present on two samples 50 ms apart |
| 5 | The bus reads at or above 13.0 V on both reads while PSU_ADC reads absent |
| 2 | The INA260 is unreadable, or its reading is implausible |
| 3 | The wake count reaches 10,800 |

**Alerts.** Both only raise an entity. Neither drives GPIO5:
- **"PSU Running Bus Not Fed":** mains present and current below −0.50 A, for 60 s.
- **"PSU Sense Lost":** mains absent, with either current above +0.20 A, or the bus above
  13.15 V and the current within ±0.20 A, for 60 s.

**New entities:** Mains Present, Modem Shed, MODEM_OFF Readback Fault, PSU Running Bus Not Fed,
PSU Sense Lost, PSU Sense Voltage, Modem Shed Count and Shed Hold Lost Count.

**Placeholders.** None of these values is measured. Each stays a placeholder until the
measurement named beside it (open item 28):

| Substitution | Value | Set it from |
|---|---|---|
| `psu_divider_ratio` | 6.556 | DMM ÷ reading at first power |
| `mains_present_v` | 7.0 V | The HDR decay (open item 6). It must sit between the 0.10 V backfeed and 13.6 V |
| `mains_debounce_polls` | 10 | The HDR decay (open item 6) |
| `shed_voltage` | 11.80 V | This pack's first discharge (open item 14) |
| `shed_valid_reads_n` | 10 | The XB7's peaks on that discharge |
| `shed_plausible_v_min`, `shed_plausible_v_max` | 5.0 V, 16.0 V | Owner's choice |
| `psu_not_feeding_i_a` | −0.50 A | The modem's measured draw on this board |
| `plausibility_alert_delay` | 60 s | The HDR decay (open item 6) |
| `survival_exit_v` | 13.0 V | The shed pack's resting voltage (open item 14) |

**Where V4.0 departs from section 8:**
1. **A second way out of survival sleep.** Section 8 releases the shed only on mains. V4.0 also
   leaves survival sleep on exit reason 5.
   - It covers a PSU_SENSE wire that is off when mains returns: the charging pack lifts the
     bus, and PSU_ADC never sees it.
   - It relies on 13.0 V sitting above the voltage a shed pack rests at. That is not measured
     [I: falsified by a shed pack resting at or above 13.0 V; open item 14].
2. **The fail-safe exit turns the modem on.** On exit reason 2 the ESP boots normally, with the
   modem on. This follows "on any doubt, the modem stays on". On a depleted pack it runs the
   pack toward the BMS cutoff (section 5).
3. **The latch does not survive a reboot.** Any reboot during a shed turns the modem back on
   until the supervisor earns the shed again, about 20 s later (section 5).
4. **Between about 3.0 to 3.3 V and 7.0 V on PSU_SENSE, the firmware reads mains absent while
   Q2 still holds the modem on** (section 4.4). A shed commanded in that band takes effect
   only when the HDR output decays through Q2's threshold (open item 6).

**Comments in V4.0 that still describe the deployed board.** They do not change behaviour:
- Lines 84, 1255 to 1256 and 2303 call TB2 a JST-XH in the order 3V3, DQ, GND, and say the
  sensor module's built-in pull-up means no external resistor. On Rev 4, TB2 is a screw
  terminal in the order 3V3, GND, DQ, and R8 is on the board (sections 3 and 4.6).
- Lines 85 and 3126 to 3130 call the Alert pull-up R2. On Rev 4 it is R1 (section 4.6).

## 9. Open items

**Items 1, 4, 5 and 10 are board edits. Close them before the board is ordered** (peer
review). Item 26 was one; the 16:06 board closes it. Revision 6 closes items 20, 21, 26 and 27
and narrows items 8, 9, 11, 23 and 25 from the datasheets read on 2026-11-10. Revision 7
closes item 8 and narrows items 21 and 30, from the owner's answer and the three sheets the
owner supplied that day.

1. **TB2:** the pin order differs from the deployed board. The 15:22 board labels the pads "+",
   "GND" and "DQ" in pad order, but "GND" still sits 1.08 mm from pad 3 (DQ) and 1.46 mm from
   pad 2 [M]. Move it, or meter the pins before connecting the sensor.
2. ~~**1-Wire pull-up:** where is the deployed DS18B20's pull-up?~~ **RESOLVED 2026-11-08:** it
   is in the sensor lead (owner). The 15:22 board adds R8 as well; see item 27.
3. ~~**Back silk:** the "Board Size" text is stale.~~ **RESOLVED on the 15:22 board:** it reads
   38mm x 53.25mm, which is the outline [M].
4. **REF\*\* screw placeholders:** three remain, over H1, H2 and H4. They cause 9 DRC errors,
   5 parity items and the fabrication tool's only out-of-limits verdict (section 7). The owner
   deletes them when the board is finalised.
5. **Schematic:** it trails the board by 41 parity items (section 7): the 3-pole terminal, the
   horizontal resistors, R8, the BUS net name and the PSU_SENSE pad 1 change.
   **BOM CSV** (2026-11-08 16:09) predates all of those; regenerate it from the board.
   **R8 is DNP** (item 27), but the 16:06 board does not mark it so [M]. Set its "Do not
   populate" attribute first, or the regenerated BOM will list it.
6. **HDR-60-12 decay:** how long the output takes to fall after AC loss is unmeasured. It sets
   the delay before a shed takes effect. On section 1.8's bracket the shed comes 3 to 9.6 h into
   an outage [I], so a decay of seconds or minutes would not matter. It also sets the debounce
   on mains in section 8.
7. **GPIO5 through deep sleep:** if the pin is not held, the modem turns back on during survival
   sleep. Section 8 gives the ESP32-C3's hold calls and the timer-wake boot path to test.
   V4.0 makes both hold calls and counts a lost hold (section 8.1). The bench test is still
   open.
8. ~~**U4:** confirm the 0.1 in row pin order on the module in hand.~~ **RESOLVED 2026-11-10:**
   EN is next to VIN on the module's pin-header row (owner). The footprint has MODEM_EN on
   pad 1 and VIN on pad 2 [M].
   - Pololu's page says VIN, GND and VOUT are on both rows and EN on the small row only
     [S: Pololu #4984, read 2026-11-10]. Its top-view picture shows two square pads side by
     side at positions 3 and 4 of the 5-hole row, where the footprint has GND and GND [M].
   - That the square pads are the grounds is read from a picture with no labels [I: falsified
     by a meter between those pads and the module's GND]. The owner's answer settles which end
     is EN.
9. **Resistors:** the board's fields now name the RNMF14 parts (section 6); the BOM is still
   to be regenerated (item 5). ~~**INA260 standoff:** check whether a breakout mounting hole
   lines up with H1.~~ **RESOLVED 2026-11-10:** neither does; H1's standoff is a rest under the
   breakout (section 6).
10. **The BUS terminal's net name:** BATT_RAW invited wiring it to Battery+. That would take the
    modem's ~1 A out of the INA260's view on battery (section 1.3).
    - The 15:22 board names the net BUS and marks the pole "+" [M]. The schematic still says
      BATT_RAW.
    - Draw the current enclosure wiring (replaced 2026-10-31 to 11-04, owner), with the
      unfused 16 AWG BUS lead and the modem's return on the GND bus.
11. **HDR-60-12 OVP range on the installed unit:** 14.2 to 16.2 V on the 2026-10-09 datasheet,
    13.8 to 16.2 V in `docs/bom.md` and `docs/specifications.md`.
    - At 13.6 V the worst-case output is 13.898 V (section 1.5), so the 13.8 V floor would leave
      no margin. The OVP latches.
    - Find which applies from the unit's label or datasheet revision.
    - Re-read 2026-11-10: the 2026-10-09 sheet gives 14.2 to 16.2 V on p. 2 [S]. The
      repository's 13.8 V has no recorded source, so only the unit or an older sheet can
      settle it.
12. **Which pack:** is the new pack in service the "second, new" Cyclenbatt used on the top-off
    bench from 2026-10-28 (Top-Off §11.1)? If so, its label, its BMS cuts at 14.310 to 14.315 V
    and its bench history apply to it (section 1.6).
13. **U4's output** at TP +12V MODEM at first power, against the XB7's lowest input on record,
    11.71 V (section 1.4).
14. **First discharge of this pack** to the 11.8 V shed, coulomb-counted by the INA260. It sets
    the runtime (section 1.8) and the firmware's phase thresholds (section 8).
15. **Shed logic** (section 8). **Written in V4.0, with placeholder values, and untested**
    (section 8.1; item 28):
    - the latch and its release on debounced mains;
    - LOW and then `gpio_hold_dis` at every mains poll;
    - the valid-reading rule, with N and the plausible range set;
    - GPIO5 out of the switch and output components, in a lambda above priority 800;
    - both ESPHome priorities confirmed on the version in use.
16. **GPIO5 readback:** the pin as input and output, alerting on a mismatch and on HIGH with
    mains present (section 8). Written in V4.0, untested.
17. **Commissioning test:** shed, sleep, restore mains, wait two wake periods, then cut mains.
    The modem must stay on (section 8).
18. **Plausibility alerts:** PSU running with the bus not fed, and the mirror case (section 8).
    Written in V4.0, with placeholder thresholds, untested.
19. **First recharge:** log its peak current into the pack against the 5.0 A label
    (section 1.5).
20. ~~**HDR-60 overload type:** confirm whether the datasheet says "constant-current limiting" or
    only hiccup below 50 % (section 1.5).~~ **RESOLVED 2026-11-10:** it says both. Constant
    current from 50 to 100 % of rated output voltage, hiccup below 50 % [S: HDR-60-SPEC,
    2026-10-09, p. 2].
21. ~~**F1's rating.** The owner gave 2 to 2.5 A on 2026-11-08, and revision 3 chose 2.5 A. The
    15:22 board's F1 field names a 3.15 A link (section 4.1). Confirm which is intended, and
    read that link's datasheet.~~ **RESOLVED 2026-11-10: 3.15 A** (owner), Schurter SPT
    0001.2509. Its datasheet and the holder's drawing were read and show no safety issue
    (section 4.1). One point stays on record: the link's maximum dissipation at 1.5 times its
    rated current, 4.0 W, is above the holder's 1.6 W rated power acceptance [S: both sheets,
    section 4.1].
    The enclosure's fuses are recorded (owner, 2026-11-09):
    - 3 A on the modem lead, between terminal pin 1 and the barrel jack;
    - 7.5 A on PSU positive;
    - 10 A on the battery lead.

    The BUS lead pair is 16 AWG, about 6 in long, with no fuse of its own (owner, 2026-11-09).
    Revision 7, from the sheets the owner supplied on 2026-11-10 (section 4.1):
    - the BUS lead is UL 1569 hook-up wire, 105 °C and 300 V. Its sheet has no current rating,
      so the 10 A fuse upstream still rests on the US code's benchmark for 16 AWG, read from
      secondary sources only;
    - the enclosure fuses are Littelfuse MINI, 32 V. In a hard short F1 melts first on typical
      I²t; around 13 A the two fuses' gates overlap, so the order is not guaranteed.

    Still open:
    - the PSU fuse. The PSU's 7.20 A overload ceiling is over the 6.4 A that sheet allows a
      7.5 A link at 20 °C [S: Littelfuse, p. 3] (section 1.5). Decide after the first
      recharge's logged peak (item 19). A larger link there needs the PSU-positive wire's
      gauge, which is not recorded;
    - the part numbers on the wire and the fuses in hand, not yet read against those sheets.
22. **OEM adapter:** on hand (owner, 2026-11-09). Keep the XB7's NBC56B120460VU beside the UPS
    as a one-plug bypass (section 5).
23. **U4 at low input:** ~~Pololu's output-current-versus-input curve at 10.0 V and 11.8 V
    against the 1.49 A peak.~~ **Curve read 2026-11-10:** about 2.4 A and 2.65 A, both above
    1.49 A (section 4.3). Still open: at first power, check its temperature and its clearance
    to the floor.
24. **DRC:** review each of the 45 errors, and give each deliberate one a commented exclusion
    (section 7). Nine go when the REF\*\* placeholders are deleted (item 4).
    - Three +12V_MODEM track joins near (34.2, 56.5) on the back overlap without sharing an end
      point [M]. They are connected (0 unconnected). Snap the ends when the layout is tidied.
25. **PSU_SENSE lead:** fuse it at the tap at 0.5 A (revision 4 said about 0.5 to 1 A). The
    board's 0.30 mm sense copper has no other protection (sections 3 and 7). Record where it
    taps relative to the 7.5 A fuse, and move it to the bus side of that fuse if it is not
    already there (section 3). Pad 1 of that terminal stays unconnected, and no PSU ground wire
    goes to it (owner, 2026-11-10).
26. ~~**Terminal block pitch:** the 3-pole footprint is 3.50 mm pitch, and its Value names
    Phoenix 5442769, which is listed at 3.81 mm (section 3). Measure the part in hand, then
    change the footprint or the part. **Do not order the board before this is settled.**~~
    **RESOLVED on the 16:06 board:** the owner changed the footprint to 3.81 mm, and it matches
    Phoenix's sheet for 5442769 in pitch and hole (section 3).
27. ~~**Two 1-Wire pull-ups:** R8 on the board and the one in the sensor lead sit in parallel
    (section 4.6). Read the lead's value, and decide whether to fit R8.~~ **RESOLVED
    2026-11-10:** R8 is not fitted; the sensor in service has its pull-up in its head (owner).
    Marking R8 DNP on the board is under item 5.
28. **Firmware V4.0 before service** (section 8.1):
    - first flash, then the bench tests in items 7 and 17;
    - every placeholder in section 8.1's table replaced by its measurement;
    - the boot lambda seen to run before any other component touches GPIO5;
    - the comments that still describe the deployed board corrected.
29. **Clearances to check on the assembled board** (section 6):
    - the gap between the board and U4 on its male header, with every tail under it trimmed
      flush and the module's hole row taped;
    - no metal screw in U4's M2 hole beside R6 and R7;
    - the seated height of Q1 and Q2 under the XIAO.
30. **The 2-pole PSU_SENSE terminal, Phoenix 5442756:** ~~its own sheet was not read.~~ **Sheet
    read 2026-11-10** (supplied by the owner): 3.81 mm pitch, 2 positions, 13.5 A and 200 V,
    and the footprint's pitch matches it (section 3). The print has no dimensioned drawing, so
    the pin and hole are still taken from the 3-pole part of the same series [I: falsified by
    the part not seating in its footprint]. Try the part in the board before soldering.

## Sources

- [ESP32-C3 Series Datasheet v2.4 (Espressif)](https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf): Table 2-1; §5.5, Tables 5-5 and 5-6, p. 56.
- [Seeed XIAO ESP32C3 wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/): pin map.
- [Pololu #4984 S13V25F12](https://www.pololu.com/product/4984): output, EN pull-up and threshold, input range, reverse-voltage protection, quiescent current, size, efficiency range; read again 2026-11-10 for the 5.1 A output current limit, which row carries EN, the [maximum continuous output current graph](https://a.pololu-files.com/picture/0J12094.600.png?9e7667921971a0e351911e9fdbb6cf1f) and the top-view picture.
- [Pololu #5592 D24V7F3](https://www.pololu.com/product/5592), read 2026-11-10: input range, 600 mA, protections.
- [Mean Well HDR-60 series datasheet](https://www.meanwell.com/Upload/PDF/HDR-60/HDR-60-SPEC.PDF), file dated 2026-10-09: the HDR-60-12 column; p. 2 read again 2026-11-10 for the overload and over-voltage wording.
- [ESP-IDF GPIO reference, ESP32-C3](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32c3/api-reference/peripherals/gpio.html), v5.5.5, read 2026-11-10: `gpio_hold_en`, `gpio_hold_dis`, `gpio_deep_sleep_hold_en`.
- [Pololu #5382 ideal diode](https://www.pololu.com/product/5382), read 2026-11-10: 4 to 60 V, 10 A, < 10 mΩ, LM74700-Q1.
- [ESPHome core configuration](https://esphome.io/components/esphome.html), read 2026-11-10: `on_boot` and its priority list.
- [Schurter SPT 5x20 datasheet](https://www.schurter.com/en/datasheet/typ_SPT_5x20.pdf), dated 2026-07-21, pp. 1 to 4: rows 0001.2509 (3.15 A) and 0001.2508 (2.5 A).
- Würth Elektronik drawing 696 108 003 002, rev D (2017-03-14): F1's holder. Held in the board folder, not in this repository.
- [Phoenix Contact 5442769, BC-381X9-3 GN, catalogue sheet](https://res.cloudinary.com/sonepar-fr/raw/upload/s--uF4eHqZQ--/v1/documents/126/phoenix-contact-5442769-fr.pdf), dated 2023-10-31, pp. 1 to 5, in French, from a distributor's mirror: Phoenix's own site refused the request.
- [OSH Park 2-layer service](https://docs.oshpark.com/services/two-layer/), read 2026-11-10: fabrication limits.
- [Adafruit INA260 breakout, downloads](https://learn.adafruit.com/adafruit-ina260-current-voltage-power-sensor-breakout/downloads), read 2026-11-10: fabrication print.
- NEC 240.4(D)(2), from secondary sources only, read 2026-11-10: [Mike Holt forum](https://forums.mikeholt.com/threads/10-amp-breaker-on-16-wire-is-it-legal.2567028) and [IAEI Magazine](https://iaeimagazine.org/electrical-fundamentals/the-evolution-of-the-10-ampere-branch-circuit/). The code text was not read.
- Peer review of revision 2 (2026-11-08, local time; not published): findings C1, C2, S1 to S6 and the minor items carried into revision 3.
- ESP32-C3 datasheet v1.2, in the repository: [`esp32-c3_datasheet.pdf`](../UPS-Monitor/esp32-c3_datasheet.pdf), Table 14 (input-high level).
- XB7: [`docs/specifications.md`](../docs/specifications.md), [`docs/wiring.md`](../docs/wiring.md), [`docs/voltage-drop-analysis.md`](../docs/voltage-drop-analysis.md); reports [05-06](../reports/UPS_Report_2026-05-06.md), [08-31](../reports/UPS_Report_2026-08-31_Boost_Integration.md) and [09-15](../reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md); [survival-sleep design v12](../UPS-Monitor/UPS_SurvivalSleep_Design_Summary_v12.md).
- PSU and battery history: [`docs/component-selection.md`](../docs/component-selection.md), [`docs/bom.md`](../docs/bom.md), [README](../README.md), [Top-Off design](../Top-Off-Charger/top-off-charger-design.md) §4.1, §9 to §11.
- [Stackpole RNF/RNMF datasheet](https://www.seielect.com/catalog/SEI-RNF_RNMF.pdf), rev 3/30/2023: pp. 1, 2, 7.
- [element14: K104K10X7RF53L2](https://nz.element14.com/vishay/k104k10x7rf53l2/cap-0-1-f-50v-10-x7r/dp/2860096): body height.
- Schematic notes in `UPS-Monitor-Rev 4.kicad_sch` (not yet in this repository).
- Rev 4 firmware: [`ups-monitor-rev4.yaml`](ups-monitor-rev4.yaml), V4.0 (section 8.1).
- ESPHome 2026.10.2 source: `esphome/core/component.h` (setup priorities) and `esphome/components/globals/globals_component.h`.
- Diotec 2N3904 datasheet, version 2026-03-10, p. 3: TO-92 outline. Held in the board folder, not in this repository.
- Digi-Key listings, read 2026-11-10: [Phoenix Contact 5442769](https://www.digikey.at/en/products/detail/phoenix-contact/5442769/4390288) (3 positions, 3.81 mm) and [5442756](https://www.digikey.com.au/en/products/detail/phoenix-contact/5442756/4390287) (2 positions, 3.81 mm). The 3-pole part's Phoenix sheet is listed above and the 2-pole part's below.
- Supplied by the owner 2026-11-10, held in the board folder, not in this repository: Phoenix Contact, "PCB terminal block - BC-381X9- 2 GN - 5442756", catalogue print dated 11/10/2014, 2 pages; CnC Tech, "UL 1569 Hook-Up Wire", P/N 1569-XX-1-0500-0XX-1-TS, 2 pages; Littelfuse, "MINI Series Blade Fuses, Rated 32V" datasheet, revised 2024-09-27, 3 pages.
- Deployed firmware header: [`ups-monitor.yaml`](../UPS-Monitor/ups-monitor.yaml).
- Deployed board: [`UPS-Monitor-THT.kicad_pcb`](../UPS-Monitor/UPS-Monitor-THT.kicad_pcb).
- Pending item on Rev 1's ALERT routing: [CHANGELOG.md](../CHANGELOG.md).

## Revision history

| Rev | Date | Change |
|---|---|---|
| 1 | 2026-11-08 | First issue |
| 2 | 2026-11-09 | System scope (owner): a UPS dedicated to the XB7, with no host or boost and no BP-65, the HDR-60-12 at 13.6 V, and a new Cyclenbatt pack. Section 1 rewritten, with the topology, the modem, the PSU, the battery, the load budget and a runtime bracket. Sections 4.4 and 4.5 reworked at 13.6 V. Section 4.3 gains U4's ratings. Two failure modes, four firmware requirements and open items 10 to 14 added |
| 3 | 2026-11-09 | Peer review of revision 2. Section 1.2's third promise narrowed to a loss of function, with what hardware cannot close. Section 8 gains the shed latch, the hold release on every mains poll, the GPIO5 readback, the valid-reading rule, boot ownership of GPIO5 above priority 800, survival-sleep entry tied to the shed, plausibility alerts both ways, and a commissioning test. Six failure modes and open items 15 to 24 added. Recharge at 160 % (section 1.5), F1 at 2.5 A (section 4.1), U4 at low input (section 4.3), the x 0.88 floor (section 1.4), and a 128 Wh runtime anchor (section 1.8). Corrected: EN is an active-high enable, not active-low (section 4.3); 50 mV, not 23.3 mV (section 8); the BMS figures are [I] for this pack (section 1.6). Then the owner's fuse ratings and the OEM adapter on hand, with the PSU fuse's margin (sections 1.5, 4.1, 5 and 9) |
| 4 | 2026-11-09 | Owner's wiring answers. The battery lead lands on INA260 VIN− (as in section 1.3 and the firmware header). The 3 A fuse sits between the MODEM terminal and the barrel jack, downstream of U4. The PSU_SENSE lead is unfused. Added a recommended fuse at the PSU_SENSE tap and a tap on the bus side of the 7.5 A fuse (section 3), the BUS lead's fuse and sizing (section 4.1), one failure mode, and open item 25 |
| 5 | 2026-11-10 | Brought into line with the board saved 2026-11-10 15:22 and with firmware V4.0. Board: one 3-pole terminal replaces the BUS and MODEM blocks, and the modem's return lands on the enclosure GND bus (sections 1.3, 2 and 3); the net is named BUS; PSU_SENSE pad 1 has no net; R8 is a 1-Wire pull-up on the board (section 4.6); R1 to R8 lie flat on 5.08 mm footprints and the fields name the 1 % parts (sections 4.5 and 6); the outline is 38.00 x 53.25 mm [M]; track widths, track resistance and F1's 3.15 A field (sections 1.7 and 4.1); the BUS lead is 16 AWG and unfused (owner). Section 6 rewritten, with the clearances under U4 and under each module. Section 7 re-run on the 15:22 board. Firmware: new section 8.1 records what V4.0 implements, its placeholders, four departures from section 8 and its stale comments. Four failure modes added. Open items 3 resolved, 1, 4, 5, 7, 9, 10, 15, 16, 18, 21 and 24 updated, 26 to 29 added. Corrected: revisions 1 to 4 said the board had no 1-Wire pull-up, true of the saves they described |
| 6 | 2026-11-10 | Brought into line with the board saved 2026-11-10 16:06 and the owner's decisions of that day. The 3-pole terminal's footprint is 3.81 mm and matches the part (section 3; item 26 closed). F1 is 3.15 A, with the link's and holder's datasheets read and no safety issue found (section 4.1; item 21 closed). R8 is not fitted (section 4.6; item 27 closed). PSU_SENSE pad 1 stays unconnected by decision (section 3). Datasheets read: the PSU's overload wording (item 20 closed), U3, U4's current curve, the INA260 print, OSH Park's limits, and the ESP-IDF and ESPHome pages (sections 1.5, 4.2, 4.3, 6, 7 and 8). Section 7 re-run on the 16:06 board, with every track width and thermal relief checked against its load and its protection. PSU_SENSE fuse tightened to 0.5 A (item 25). Items 8, 9, 11 and 23 narrowed; item 30 added. Corrected: revision 5 said the board's GND lead carries the same current as its BUS lead; it carries the difference between input and output (section 1.3) |
| 7 | 2026-11-10 | The owner's answer on U4 and three datasheets the owner supplied. EN is next to VIN on U4's row, as on the footprint (sections 4.3 and 7; item 8 closed). The 2-pole terminal's catalogue print confirms its pitch and ratings but has no dimensioned drawing (section 3; item 30 narrowed). The BUS lead is UL 1569 hook-up wire, 105 °C and 300 V (section 4.1). The enclosure fuses are Littelfuse MINI 32 V: F1 melts first in a hard short on typical I²t, the two fuses' gates overlap around 13 A, and the 3 A modem link's figures are added (section 4.1). New finding: the PSU's 7.20 A overload ceiling is over the 6.4 A that sheet allows a 7.5 A link at 20 °C (section 1.5; item 21) |
