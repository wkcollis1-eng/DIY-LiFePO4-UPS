# UPS Monitor Rev 4: a discrete 12 V buck to replace U4

Status: **design note, not yet placed or built.** It replaces U4, the Pololu #4984
module (S13V25F12), with a discrete buck converter on the Rev 4 board:
- a TI LM25085 controller driving a P-channel switch;
- a TI TPS3701 for output over-voltage protection.

The owner places it in KiCad. Nothing in here has been measured on a board yet.

The file keeps its first name. Its first version (commit 0a6fa9e) described an
LTC3789 4-switch buck-boost with 36 BOM lines. The owner accepted buck-only
operation on 2026-11-12 (D4, section 10), and this version replaces that design.
The BOM is now 21 lines.

Provenance tags, as used throughout this repo:

- **[S]** spec: the document and page or section are named.
- **[D]** derived: arithmetic on [S] or [M] values, with the formula shown or named.
- **[I]** inferred: a model not yet tested. Each one names what will confirm or
  refute it (the bench test, section 9).
- **[M]** measured.

Sources:

- **LM25085** = TI SNVS593J: electrical table, §7.3-7.4, §8.2.2, Fig 26, §10.1.
- **TPS3701** = TI SBVS240C: electrical table p5, pin functions, Fig 3, §8.1.
- **FDS4685** = onsemi FDS4685/D Rev 3: p2 pinout and ratings, Fig 7, thermal notes.
- **B540C** = Diodes Inc. DS13012 Rev 19: thermal table, Fig 1.
- **MBR0530** = onsemi MBR0530T1/D Rev 9.
- **WSL** = Vishay 30100. **TNPW** = Vishay 28758. Both rev 10-Apr-2026.
- **SVPF** = Panasonic OS-CON SVPF series, 28-Jun-19.
- **FR** = Panasonic FR series, 01-Sep-25, p5 table.
- **Murata** = GRM reference sheets for the four part numbers in section 11
  (Mar 2016). None carries a part-specific DC-bias curve.
- **SRR1260** = Bourns SRR1260 series datasheet. Ratings carried from this note's
  first version.
- **Design doc** = `ups-monitor-rev4-design.md`, rev 8.

## 1. What U4 has to do, and what it must survive

| Requirement | Value | Source |
|---|---|---|
| Output | into the modem; peak 1.49 A, typical 1.0-1.2 A | [S: design doc §1.7] |
| Modem input window | 10.8-13.2 V (12 V ±10 %). The owner confirmed on 2026-11-12 that the output and the OVP trip may sit anywhere inside it | [S: design doc; owner] |
| Input on mains (float) | 13.571-13.587 V | [D: design doc] |
| Input, topped pack at rest | 14.42 V | [M: owner DMM, design doc] |
| Input ceiling | 16.2 V (the PSU's OVP upper bound, which latches) | [S: design doc] |
| Firmware shed | 11.8 V, on battery only | [S: design doc §4.4] |
| Floor | 10.0 V (BMS under-voltage cut) | [S previous pack / I this pack: design doc] |
| Off command | Q1's collector (net MODEM_EN) pulls low. Q2 clamps Q1 off while mains is present | [S: design doc §4.4] |
| Heat | Enclosure 10 × 6 × 5 in, vent holes, no fan | [owner, 2026-11-12] |

**The moment it must survive.** A mains outage at night, unattended.
- The block holds the modem inside its window from the 13.58 V float down to the
  11.8 V shed.
- It turns off when Q1 pulls MODEM_EN low, and comes back when mains returns.
- If its feedback divider fails, the TPS3701 shuts it down at 12.37-12.66 V,
  before the modem's 13.2 V.

## 2. Why this design

**The owner's decisions** (2026-11-11 and 2026-11-12):
- D1: no hardware input UVLO.
- D2: output OVP, included.
- D3: no reverse-polarity protection.
- D4: buck-only, accepted.
- Soldering iron only: no QFN; 0.635 mm pitch is acceptable; an exposed pad only if
  it can surely be hand-soldered. No part here has one.
- Height is no longer a constraint (this supersedes 2026-11-11's "minimise
  height"). Heat is a concern.

**Buck-only (D4).** The LM25085 can hold its switch on 100 % of the time. Once the
bus falls to within about 0.12 V of the set point, the output follows the bus down.
- The output stays above 10.8 V down to a bus of about 10.92 V at 1.2 A, or 10.95 V
  at 1.49 A [D: 10.8 V + I × (RSEN + RDS(on) + DCR), 0.102 Ω].
- What is given up is the 12 V hold between about 11 V and the BMS's 10.0 V cut.
  That range is reached only when the 11.8 V shed has failed.

**Why the LM25085** [S: LM25085]:
- The VSSOP-8 (DGK) version has no exposed pad. The HVSSOP and WSON versions do.
- It drives a P-channel switch: no bootstrap, and 100 % duty is possible (§7.1).
- Its input range is 4.5-42 V.
- Pulling RT below 0.73 V shuts it down (§7.4.2). Q1 and the OVP chip each need only
  an open collector or open drain onto that one pin.
- Soft-start is internal and re-arms when RT is released (§7.3.9).
- It has an internal thermal shutdown at 170 °C typical (§7.3.10).
- Constant on-time control, so there is no compensation network to tune.
- Its current limit is cycle-by-cycle, followed by a forced off-time that
  lengthens as the output falls (§7.3.4-7.3.5).

**Rejected along the way:**

| Part | Why not |
|---|---|
| LTC3789 (this note's first version) | 36 BOM lines, no thermal shutdown, and buck-boost is not needed after D4 |
| LTC3851A | VOUT 0.8-5.5 V, so it cannot make 12 V [S: LTC3851A datasheet] |
| LTC7803, LTC3891 | The exposed pad is the ground connection [S: their datasheets] |
| LM3489 | TI warns that start-up into full load may need a higher limit, and ICL_ADJ is only 3-7 µA [S: SNVS443C §7.3.3] |

## 3. What changes against the Pololu

| Pololu feature [S: design doc §4.3] | This block |
|---|---|
| Output 12 V | 11.37 / 11.56 / 11.65 V typical at a 12.0 / 13.58 / 14.42 V bus. Worst case 11.09-12.32 V over 12.0-16.2 V (section 5.1) [D on S] |
| Reverse-voltage protection to 20 V | None (D3) |
| Soft-start | Internal, 1.4 / 2.5 / 4.3 ms (min/typ/max) [S: LM25085 electrical table] |
| Input UVLO | None in the working range (D1). Standby below about 4.5 V [S: LM25085 §7.4.1] |
| Output OVP | TPS3701: trips at 12.37 / 12.52 / 12.66 V and restarts on release (section 5.7) |
| Over-current limit, 5.1 A | Peak limit 1.99 / 2.80 / 3.62 A, cycle-by-cycle, with a forced off-time (section 5.4) |
| Thermal shutdown | Controller only, 170 °C typical [S: LM25085 §7.3.10] |
| About 500 kHz | 195 kHz typical at float, 161-251 kHz over the on-time tolerance [D on S] |
| Disabled draw 24-118 µA at 11.8 V | 0.21-0.34 mA [D: IQ 175 / 300 µA typ / max [S], which excludes RT, plus the RT current, 32-40 µA]. At most 8.2 mAh a day [D: 0.34 mA × 24 h] |
| 22.9 × 22.9 × 9.7 mm module, bottom side | Discrete parts. The tallest is C401, 11.5 mm [S: FR] |

## 4. Schematic, by pin

Reference designators are in the 400 range, so they don't collide with the board's
existing ones; renumber as you like. The controller takes the designator U4, since it
takes the Pololu's place. Net names:

| Net | Meaning |
|---|---|
| VIN | The board's existing net after F1 |
| VOUT | The net the Pololu's VOUT pin drives today (+12V_MODEM) |
| MODEM_EN | The existing Q1-collector net. It now lands on RT |
| SRC | R401 / Q401-source junction |
| SW | Switch node: Q401 drain, D401 cathode, L401 |

### U4: LM25085MM/NOPB, VSSOP-8 (DGK), no exposed pad

| Pin | Name | Connects to |
|---|---|---|
| 1 | ADJ | R403 2.80 kΩ to VIN, with C405 1 nF in parallel. Both go to R401's VIN pad [S: §7.3.4, Eq 9] |
| 2 | RT | R404 365 kΩ to VIN; MODEM_EN (Q1 collector); U401 pin 6 (OUTB); TP401 |
| 3 | FB | R405 15.0 kΩ to VOUT; R406 1.87 kΩ to GND; C406 15 nF across R405 |
| 4 | GND | GND |
| 5 | ISEN | SRC, by a Kelvin trace from R401's Q401-side pad [S: pin functions] |
| 6 | PGATE | Q401 pin 4 (gate) |
| 7 | VCC | C404 1 µF to pin 8, at the pins. D402 cathode, anode to GND [S: §7.3.6, §8.2.2.10] |
| 8 | VIN | VIN, by a Kelvin trace from R401's VIN pad. C402 1 µF to pin 4, at the pins [S: §8.2.2.8] |

### Q401: FDS4685, P-channel 40 V, SO-8

Pins 1-3 source to SRC; pin 4 gate to U4 pin 6; pins 5-8 drain to SW
[S: FDS4685 p2].

### U401: TPS3701DDCR, SOT-6 (the D2 OVP)

| Pin | Name | Connects to |
|---|---|---|
| 1 | OUTA | No connection |
| 2 | GND | GND |
| 3 | INA | GND. Comparator A is unused, so OUTA sits low with nothing to sink [D: open drain, no pull-up] |
| 4 | INB | R407 309 kΩ to VOUT; R408 10.2 kΩ to GND; C408 1 nF to GND |
| 5 | VDD | VOUT. C409 0.1 µF to GND, at the pin [S: pin functions] |
| 6 | OUTB | RT (U4 pin 2) |

### Power path

| Ref | Part | From | To |
|---|---|---|---|
| C401 | CIN 100 µF 35 V aluminium, EEU-FR1V101 | VIN | GND |
| C403 | 1 µF 50 V X7R | VIN at R401 | GND at D401's anode, closing the CIN-Q401-D401 loop [I] |
| R401 | RSEN 40 mΩ 1 %, WSL2010R0400FEA, Kelvin | VIN | SRC |
| Q401 | FDS4685 | SRC (source) | SW (drain) |
| D401 | Schottky B540C-13-F | anode on GND | cathode on SW |
| L401 | 15 µH, SRR1260-150M | SW | VOUT |
| R402 | Ripple resistor 0.10 Ω 1 %, WSL0805R1000FEA | VOUT | C407 + |
| C407 | COUT 100 µF 25 V polymer, 25SVPF100M | R402 | GND |

The modem lead and R405's top both take VOUT at the L401 / R402 node, as Fig 26 does
[S: LM25085 Fig 26].

### Q1, unchanged

Q1's collector net (MODEM_EN) now lands on U4's RT pin instead of the Pololu's EN pin.
The logic is the same: Q1 on means the converter is off. The firmware does not change.
- RT current is 32 µA at 11.8 V and 39 µA at 14.42 V [D: (VIN - 0.1 V) / 365 kΩ].
- Q1's base current is about 21 µA [D: design doc §4.4], so its forced β is 1.5-1.9.
  It stays saturated, far below RT's 0.73 V threshold [S].

## 5. Values and where each comes from

### 5.1 Output voltage, and why every resistor is 0.1 %

G = 1 + R405 / R406 = 1 + 15.0k / 1.87k = 9.021 [D]. G × VREF = 11.28 V typical
[D: VREF 1.225 / 1.25 / 1.275 V, S: LM25085 electrical table].

**The ripple offset.** The LM25085 starts each on-time when FB falls to VREF, so it
regulates the ripple's valley, not its middle. With C406 across R405, the ripple at
VOUT reaches FB at about full size. So the average output sits above G × VREF by G
times half the ripple:

    VOUT ≈ G × (VREF + Vpp / 2),   Vpp = IOR × (R402 + ESR)
    IOR  = (VIN - VOUT - I × (RSEN + RDS(on) + DCR)) × tON / L

The ripple grows with VIN, with the on-time tolerance (-22 / +21 %, S: tON-2
560 / 720 / 870 ns) and with L's tolerance (±20 %, S: SRR1260).

**How the corners are built:**
- *Maximum:* maximum gain, VREF 1.275 V, tON +21 %, L -20 %, R402 +1 %, ESR 24 mΩ
  [S: SVPF max].
- *Minimum:* the opposite, with ESR 0.
- *Load and resistors:* 1.2 A. Every resistor is ±0.1 % plus 25 ppm/K over 30 K
  [S: TNPW].
- *On-time:* tON = k × (1.45 × 10⁻⁷ × (RT + 1.4) / (VIN - 1.56 + RT / 3167) + 50 ns),
  RT in kΩ [S: LM25085 Eq 3].

| Bus | VOUT min / typ / max [D on S] | Switching frequency, typ [D on S] |
|---|---|---|
| 12.0 V | 11.09 / 11.37 / 11.61 V | 188 kHz |
| 12.6 V | 11.14 / 11.44 / 11.74 V | 191 kHz |
| 13.0 V | 11.17 / 11.49 / 11.82 V | 193 kHz |
| 13.58 V (float) | 11.21 / 11.56 / 11.93 V | 195 kHz (161-251) |
| 14.42 V | 11.26 / 11.65 / 12.07 V | 198 kHz |
| 16.2 V | 11.35 / 11.80 / 12.32 V | 203 kHz |

The output ripple at VOUT peaks at 0.116 V p-p, at 14.42 V [D: IOR max 0.932 A ×
(0.101 + 0.024) Ω].

**Why 0.1 %.**
- *With 1 % thick-film resistors (100 ppm/K) in both dividers:* at 14.42 V,
  regulation's worst maximum is 12.262 V and the OVP's worst minimum is 12.107 V.
  The two bands overlap by 0.155 V [D]. A unit could trip its own OVP on a topped
  pack.
- *With 0.1 % TNPW:* the gap is 0.309 V [D].

*An earlier estimate in the design discussion said 1 % resistors fitted with
0.2-0.25 V margins. It left out the ripple offset. Corrected 2026-11-12, before this
note was written.*

### 5.2 Ripple injection: R402 0.10 Ω, C406 15 nF [S: LM25085 §8.2.2.7.1, Fig 26]

TI asks for at least 25 mV p-p at FB for stable constant-frequency operation
[S: §8.2.2.6], and gives R402 ≥ 25 mV / IOR(min) [S: Eq 28].

| Bus | FB ripple, typ [D] | FB ripple, worst corner [D] |
|---|---|---|
| 12.0 V | 19.5 mV | — |
| 12.6 V | 37.1 mV | 17.7 mV |
| 13.0 V | 48.0 mV | 24.4 mV |
| 13.2 V | 53.2 mV | 27.6 mV |
| 13.58 V | 62.7 mV | 33.5 mV |
| 14.42 V | 82.0 mV | — |

The worst corner is the one that makes the ripple smallest: maximum gain and VREF,
tON -22 %, L +20 %, R402 -1 %, ESR 0, with VOUT solved at that corner.

**The trade-off, and the choice:**
- So 25 mV holds typically from about 12.2 V up, and at the worst corner from about
  13.05 V up.
- A larger R402 lowers those points, but it raises the ripple offset in 5.1 and
  closes the OVP gap:
  - 0.12 Ω gives 28.8 mV at 13.0 V worst corner, but the gap falls from 0.309 V to
    0.242 V [D].
  - 0.15 Ω leaves a 0.149 V gap [D].
- **0.10 Ω is kept** because a false OVP trip reboots the modem (5.7). Too little
  ripple is expected to cost only irregular switching while still regulating [I].
  Bench step 3 looks for it.
- If the bench shows irregular switching on the battery plateau, fit 0.12 Ω
  (WSL0805R1200FEA, same footprint) and re-check the OVP gap.

*An earlier figure in the design discussion paired the short on-time with the
lowest output voltage. It gave 34.0 mV at 13.0 V worst corner, which is optimistic;
corrected 2026-11-12.*

C406 ≥ 3 × tON(max) / (R405 ∥ R406) = 3 × 6.26 µs / 1663 Ω = 11.3 nF, so 15 nF
[S: Eq 29; D: tON at 11.8 V, +21 %].

### 5.3 On-time: R404 (RT) 365 kΩ

- **Switching frequency** is 188-203 kHz typical over 12.0-16.2 V (table in 5.1)
  [D on S: Eq 3]. It is chosen low because switching and gate-drive heat scale with
  frequency.
- **Shortest on-time** is 2.84 µs, at 16.2 V with tON -22 % [D]. TI's floor is
  150 ns [S: §7.3.2].
- **Dropout:** at the low end the controller simply holds the switch on (100 % duty).

### 5.4 Current limit: R401 40 mΩ, R403 (RADJ) 2.80 kΩ, C405 (CADJ) 1 nF

**The limit.** ICL = IADJ × RADJ / RSEN [S: Eq 9], with these inputs:
- IADJ 32 / 40 / 48 µA and comparator offset ±9 mV [S: electrical table];
- R401 ±1 %, R403 ±0.1 %.

That gives **1.99 / 2.80 / 3.62 A** peak [D]. CADJ 1 nF is TI's recommended value
[S: §7.3.4].

**Why that value:**
- *Needed:* ICL ≥ 1.49 A + IOR(max at 14.42 V) / 2 = 1.49 + 0.932 / 2 = 1.96 A [D].
- *Where VOUT starts to fall at 13.58 V:* an output current of 1.65 / 2.52 / 3.41 A
  [D: ICL - IOR / 2].

**Short circuit.** The inductor current cannot ratchet up (no runaway) at any
tracked corner. At 14.42 V with VOUT at 0, the off-time volt-seconds exceed the
on-time volt-seconds:

| Corner | On-time | Off-time |
|---|---|---|
| min | 0.77 V·µs | 3.00 V·µs |
| typ | 1.97 V·µs | 4.42 V·µs |
| max | 3.31 V·µs | 6.04 V·µs |

These figures are [D on S]. tON-4 and tOFF(CL) move together [S: footnote 4].

**What a modem-lead short does:**
- The diode carries nearly all of about 2.8 A typical, 3.6 A at most.
- That is 1.1 W typical and up to 1.5 W [D: I × VF; VF about 0.40-0.42 V, S: B540C
  Fig 1, typical], a rise of +55 to +75 °C [D: 50 °C/W].
- The 3 A fuse on the modem lead may not open: 3.6 A is 120 % of its rating, and
  the 297 MINI holds 110 % for 100 h and opens 135 % in 0.75-600 s [S: Littelfuse
  297 MINI].
- The diode's 150 °C limit holds as long as the air around it stays under about
  75 °C [D]. The enclosure air temperature is not known [I]; bench step 7 measures
  the rise.

### 5.5 Inductor: 15 µH, SRR1260-150M

Ratings [S: SRR1260]:
- 15 µH ±20 %;
- RDC 27.0 mΩ max;
- Irms 5.00 A at a 40 °C rise;
- Isat 4.60 A *typical*, defined at a 25 % inductance drop;
- 12.5 × 12.5 × 6.0 mm.

The worst peak is the 3.62 A limit. Isat has no guaranteed minimum, so the margin
is real but not guaranteed [I]; bench step 5 checks it.

### 5.6 Capacitors and the VCC clamp

**CIN, C401: EEU-FR1V101** [S: FR p5]:
- 35 V, 100 µF, 8 × 11.5 mm, 3.5 mm lead spacing;
- 950 mA rms, 0.056 Ω.

TI asks for an rms rating above IOUT / 2, which is 0.75 A at 1.49 A [S: §8.2.2.8].

**C402 and C403, 1 µF X7R:**
- C402 sits at U4's VIN and GND pins [S: §8.2.2.8].
- C403 closes the switching loop at Q401 and D401 [I, practice].
- Their DC-bias loss at 13-16 V is not on the Murata sheets [I].

**COUT, C407: 25SVPF100M** [S: SVPF]:
- 25 V, 100 µF, E7 case 8 × 6.9 mm;
- 24 mΩ max, 3.2 A rms.

Its rms ripple is at most 0.30 A [D: 1.04 A / √12, at 16.2 V]. The 25 V rating also
covers a shorted Q401, which puts the bus on VOUT.

**CVCC, C404: 1 µF**, between VIN and VCC. VCC sits about 7.7 V below VIN
[S: §7.3.6]. TI's typical value is 0.47 µF and its maximum recommended value is
1 µF [S: §8.2.2.10]. 1 µF also covers the X7R's loss at 7.7 V of bias [I].

**D402: MBR0530T1G, VCC clamp** [S: §7.3.6].
- *Why:* if VIN drops below about 8 V, VCC can be pulled below GND. TI recommends
  a Schottky from VCC to GND.
- *Ratings* [S: MBR0530]: 30 V, 0.5 A. In service it sees at most 8.5 V of reverse
  bias [D: 16.2 V - 7.7 V], well inside the 30 V rating.

### 5.7 OVP (D2): U401 TPS3701, R407 309 kΩ, R408 10.2 kΩ, C408 1 nF

**Trip point.** Trip = VIT+(INB) × (1 + R407 / R408) [S: TPS3701 §8.1].

The inputs [S: TPS3701 electrical table p5]:
- VIT+(INB): 397 / 400 / 403 mV;
- input current: ±25 nA, through the 9.87 kΩ Thevenin resistance;
- resistors: ±0.1 %.

The trip is **12.37 / 12.52 / 12.66 V** [D].

**Margins** [D]:
- 0.309 V above regulation's worst maximum at 14.42 V, and 0.54 V below 13.2 V.
- At a 16.2 V bus, regulation's worst maximum (12.32 V) is still below the trip's
  minimum.
- The release point is the trip less 0.06 / 0.16 / 0.38 V [D: hysteresis
  2 / 5.2 / 12 mV × 31.3].

**Filter.** C408 1 nF with 9.87 kΩ gives τ = 9.9 µs [D]. TI shows 1-10 nF on the
input as optional [S: §8.1]. The comparator itself needs about 7 µs at large
overdrive, 22 µs near threshold [S: Fig 3, typical].

**What a trip does.**
- OUTB pulls RT low, so the controller stops.
- The output falls under the modem's load to the release point, OUTB lets go, and
  soft-start restarts the reference from 0 V.
- While the reference climbs, the modem drains C407 at about 12 V/ms
  [D: 1.2 A / 100 µF], so the output dips to about 3 V before it recovers
  [D: crossing of the decay with the 2.5 ms typical ramp].
- **So every trip reboots the modem.** A persistent fault cycles it. This is why the
  gap above regulation matters more than the ripple margin in 5.2.

**Supply from VOUT.** VDD takes 8 / 11 µA [S], and only while the converter runs.
- Start-up is not blocked: below its UVLO (1.3 / 1.5 / 1.7 V), OUTB is
  high-impedance [S: electrical table, note 2].
- VOUT's soft-start ramp, about 124 µs/V at the fastest [D: 11.3 V in 1.4 ms], is
  far slower than the 15 µs/V the power-on spec assumes [S: note 1].

**Sinking RT.** OUTB pulls the RT current, 44 µA at most [D: 16.2 V / 365 kΩ], to
well under 0.25 V
[S: VOL 250 mV max at 3 mA]. Its 10 / 300 nA off-state leakage is negligible against
RT's 32 µA [S].

**What D2 covers.**
- It covers an open or cracked R405 (FB pulled to 0 V, full duty), or anything else
  that makes the controller drive the output up.
- It is independent of Q1, so it works on mains, when Q2 holds Q1 off.
- The LM25085's own FB over-voltage comparator (VREF + 350 mV [S]) uses the same
  divider as the regulation loop, so it cannot catch R405 failing.

**What D2 does not cover.**
- *A shorted Q401.* That passes the bus straight to the modem: 13.6-14.4 V, and up
  to 16.2 V. Stopping the controller does not open a shorted switch.
- *Fast faults [I].* During the trip delay the output can keep rising at up to
  24 mV/µs [D: (3.62 - 1.2) A / 100 µF]. A fast fault may peak a few tenths of a
  volt above the trip for tens of microseconds, near 13.2 V.

### 5.8 Shutdown and restart

- **Shutdown:** RT below 0.73 V typical (50 mV hysteresis) holds the gate off and
  turns the VCC regulator off [S: §7.4.2]. The draw in this state is in section 3.
- **Restart:** releasing RT restarts soft-start: 1.4 / 2.5 / 4.3 ms from a 0 V
  reference [S: §7.3.9, electrical table].
- **Start-up into the modem [I]:** charging C407 at the fastest ramp needs 0.83 A
  [D: 100 µF × 11.6 V / 1.4 ms], on top of the modem's own draw. That approaches the
  1.99 A minimum limit.
  - During an overload the reference follows FB down and does not latch [S: §7.3.9].
    So the output climbs as fast as the limit allows.
  - Whether the modem, if it behaves as a constant-power load at low voltage,
    stalls the climb is [I]. Bench step 4 tests it.

## 6. Loss and heat

The figures below are [D on S], with these assumptions:
- *Typical values:* Qg 25.5 nC at the 7.7 V gate swing [S: FDS4685 Fig 7, read off
  the curve; the table's 19 nC is at 5 V], IIN 1.25 mA [S], VF 0.36 V
  [S: B540C Fig 1].
- *Maximum values:* RSEN 40 mΩ, DCR 27 mΩ.
- *The switch's two terms are [I]:* 35 mΩ hot RDS(on), and a 10 ns transition for
  switching loss.

| Bus | 1.2 A out | 1.49 A out | Efficiency at 1.2 A |
|---|---|---|---|
| 12.0 V | 255 mW | 339 mW | 98.2 % |
| 13.58 V (float) | 305 mW | 394 mW | 97.8 % |
| 14.42 V | 331 mW | 422 mW | 97.7 % |
| 16.2 V | 381 mW | 477 mW | 97.4 % |

Efficiency = VOUT × I / (VOUT × I + loss) [D].

**Where it goes at float, 1.2 A** (mW):

| Part | Loss |
|---|---|
| IC (gate drive + IIN) | 84.5 |
| Switch | 60.2 (44.3 conduction + 15.9 switching) |
| Diode | 59.2 |
| RSEN | 50.6 |
| Inductor DCR | 39.6 |
| Dividers | 8.3 |
| R402 + ESR | 2.9 |

**Temperature rise above the air beside each part** [D]:

| Part | At 1.2-1.49 A | θJA used |
|---|---|---|
| U4 | +11 to +16 °C | 153 °C/W [S: LM25085, VSSOP] |
| Q401 | +7 to +12 °C | 125 °C/W, minimum pad [S: FDS4685 note 1c]; 50 °C/W on 1 in² of 2 oz |
| D401 | +1 to +7 °C | 50 °C/W [S: B540C, 8 mm² pads] |

The θJA figures are for the datasheets' test boards. This board's copper weight and
pad areas will give different figures [I]; bench step 7 measures them. The whole block puts 0.26-0.48 W into the enclosure.

The worst sustained case is a modem-lead short, in 5.4.

## 7. Area

- Courtyards total about 600 mm² [I: estimated from the package outlines]. KiCad's
  courtyards give the real figure.
- The largest parts:
  - L401, 12.5 × 12.5 mm;
  - C401, 8 mm diameter, radial;
  - C407, E7 8 × 8 mm footprint;
  - D401, SMC.
- The board is 37.8 × 51.5 mm [M: board file, 2026-11-11]. The largest free
  rectangle on both layers then was 4.00 × 3.50 mm [M: same]. **The outline has to
  grow.**
- Put the block on the edge nearest F1 and the modem output terminal, so the VIN
  and VOUT runs stay short. Placement is the owner's call in KiCad.

## 8. Layout rules

1. **Switching loop smallest:** C401 / C403, R401, Q401, D401's anode, back to
   C401 / C403 ground. D401's anode to CIN ground must be short and direct
   [S: §10.1].
2. **Output loop:** D401, L401, R402 / C407, back to D401 [S: §10.1].
3. **At U4's pins** [S: §10.1]:
   - C402 across pins 8 and 4;
   - C404 across pins 8 and 7;
   - D402 across pins 7 and 4.
4. **Kelvin sense:**
   - U4 pin 8, R403 and C405 take VIN from R401's VIN pad.
   - Pin 5 takes SRC from R401's Q401-side pad.
   - Route the two as a pair, away from SW and L401 [S: §7.3.4, "Kelvin
     connections"].
5. **FB at pin 3:** R405, R406 and C406 sit at the pin. R405's top comes from the
   L401 / R402 node, routed away from SW. TI's comparators are fast and respond to
   short noise pulses [S: §10.1].
6. **SW copper** only as big as the current needs, to limit EMI [S: §10.1].
7. **U401 near U4 pin 2:**
   - OUTB's run to RT is short.
   - R407's top comes from VOUT.
   - C408 sits at U401 pin 4, and C409 at pin 5.
8. **Heat:** the VSSOP has no pad. Wide copper on U4's GND and VIN pins helps
   [S: §10.1].
9. **0.65 mm pitch on U4:** check for bridges under magnification before power-up.

## 9. First power, and what each step proves

Use a bench supply with a current limit, and a resistive or electronic load. **No
modem until step 10.** Each step's expected value is the falsifier of the claim it
names.

1. **Unpowered: check for shorts.**
   - VIN, VOUT and SW are not shorted to GND.
   - VCC is not shorted to VIN.
   - Bridges at U4's pitch are the most likely build fault.
2. **First power: 13.6 V, 0.3 A supply limit, 100 Ω load.**
   - VOUT is near 11.2-11.9 V. The light-load value is not computed [I].
   - Pull TP401 low: VOUT decays.
   - Release it: soft-start in 1.4-4.3 ms on a scope (5.8).
3. **Regulation sweep at 1.2 A** (about 9.6 Ω) at 12.0 / 12.6 / 13.0 / 13.58 /
   14.42 / 16.2 V.
   - Record VOUT against the table in 5.1.
   - Record the switching frequency at SW, and the FB ripple.
   - Record input and output power, which tests section 6.
   - Look for irregular switching between 12.0 and 13.2 V (5.2).
   - The OVP must stay silent at every point, 16.2 V included.
4. **Start-up into load** at 12.0 V and 13.58 V:
   - first into 1.2 A constant current;
   - then into constant power, about 14 W, with the load's turn-on voltage near 9 V.
   - VOUT must reach its band each time. A stall tests the [I] in 5.8.
5. **Current limit.** Raise the load until VOUT starts to fall.
   - At 13.58 V that should be at 1.65-3.41 A (5.4).
   - Watch the inductor current for a sharpening ramp, which means saturation (5.5).
   - Then a hard short at the output terminal: the current must stay bounded, and
     the diode temperature must level off.
6. **OVP fires (D2).** At 13.58 V, 1.2 A, tack 10 kΩ across R406.
   - That makes G 10.52, so the output aims at about 13.2-13.5 V [D].
   - OUTB must pull RT low, and VOUT must cycle without passing about 13.2 V on the
     scope.
   - Remove the 10 kΩ; step 3's 16.2 V point shows the OVP silent.
7. **Heat:** 1 h at 1.5 A, at 12.0 V and 13.58 V, inside the enclosure if possible.
   Take U4, Q401, D401, L401 and R401 against the air beside them, and compare with
   section 6.
8. **Shed path,** with Q1 driven on as in service:
   - TP401 reads under 0.2 V;
   - VOUT is 0;
   - the bus draw is 0.21-0.34 mA (section 3).
9. **SW node at 16.2 V:** ringing stays well under the 40 V ratings of Q401 and D401
   [S].
10. **Modem connected,** on mains, then a mains pull to battery, then a shed and a
    release (soft-start back).

## 10. Decisions

Closed by the owner, 2026-11-11 and 2026-11-12:

- **D1, hardware input UVLO: none.** The firmware shed at 11.8 V and the BMS cut at
  10.0 V are the layers. The LM25085's own standby below about 4.5 V is not a UVLO
  in the working range.
- **D2, output OVP: included.** Section 5.7. It retries (restarts) rather than
  latching. Each trip reboots the modem.
- **D3, reverse-polarity protection: none.** A reversed bus would forward-bias D401
  and Q401's body diode until F1 clears. Protection, if it is ever wanted, is
  better done at F1 for the whole board.
- **D4, buck-only: accepted.** Section 2.

**Open:**
- **R402 0.10 Ω vs 0.12 Ω (5.2).** 0.10 Ω is fitted; bench step 3 decides.
- **Start-up into the modem (5.8).** Bench step 4 decides.

**Test point.** TP401 on RT / MODEM_EN. Q1's saturation (under 0.2 V) and the OVP's
action are both read there.

## 11. Bill of materials

| Ref | Qty | Part | Package | Tag |
|---|---|---|---|---|
| U4 | 1 | TI LM25085MM/NOPB | VSSOP-8, no pad | [S] |
| U401 | 1 | TI TPS3701DDCR | SOT-6 | [S] |
| Q401 | 1 | onsemi FDS4685, P-channel 40 V | SO-8 | [S] |
| D401 | 1 | Diodes B540C-13-F, Schottky 40 V 5 A | SMC | [S] |
| D402 | 1 | onsemi MBR0530T1G, Schottky 30 V 0.5 A | SOD-123 | [S] |
| L401 | 1 | Bourns SRR1260-150M, 15 µH | 12.5 × 12.5 × 6.0 mm | [S] |
| R401 | 1 | Vishay WSL2010R0400FEA, 40 mΩ 1 % | 2010, Kelvin | [S] part, [D] value |
| R402 | 1 | Vishay WSL0805R1000FEA, 0.10 Ω 1 % | 0805 | [S] part, [D] value |
| R403 | 1 | Vishay TNPW08052K80BEEA, 2.80 kΩ 0.1 % | 0805 | [D] |
| R404 | 1 | Vishay TNPW0805365KBEEA, 365 kΩ 0.1 % | 0805 | [D] |
| R405 | 1 | Vishay TNPW080515K0BEEA, 15.0 kΩ 0.1 % | 0805 | [D] |
| R406 | 1 | Vishay TNPW08051K87BEEA, 1.87 kΩ 0.1 % | 0805 | [D] |
| R407 | 1 | Vishay TNPW0805309KBEEA, 309 kΩ 0.1 % | 0805 | [D] |
| R408 | 1 | Vishay TNPW080510K2BEEA, 10.2 kΩ 0.1 % | 0805 | [D] |
| C401 | 1 | Panasonic EEU-FR1V101, 100 µF 35 V | radial 8 × 11.5 mm, 3.5 mm | [S] |
| C402-C404 | 3 | Murata GRM21BR71H105KA12, 1 µF 50 V X7R | 0805 | [S] part, [I] DC bias |
| C405, C408 | 2 | Murata GRM216R71H102KA01, 1 nF 50 V X7R | 0805 | [S] |
| C406 | 1 | Murata GRM219R71H153KA01, 15 nF 50 V X7R | 0805 | [S] part, [D] value |
| C407 | 1 | Panasonic 25SVPF100M, 100 µF 25 V polymer | E7, 8 × 6.9 mm | [S] |
| C409 | 1 | Murata GRM21BR71H104KA01, 0.1 µF 50 V X7R | 0805 | [S] |
| TP401 | 1 | test point | — | — |

All passives except the power parts are 0805, for iron assembly. The TNPW part numbers
follow Vishay's code: value, B = ±0.1 %, E = 25 ppm/K, EA = packaging [S: TNPW].
