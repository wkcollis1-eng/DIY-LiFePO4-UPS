# UPS Monitor Rev 4: a discrete 12 V buck-boost to replace U4

Status: **design note, not yet placed or built.** It replaces U4, the Pololu #4984
module (S13V25F12), with a discrete 4-switch buck-boost on the Rev 4 board. The
owner places it in KiCad. Nothing in here has been measured on a board yet.

Provenance tags, as used throughout this repo:

- **[S]** spec: the document and page are named.
- **[D]** derived: arithmetic on [S] or [M] values, with the formula shown or named.
- **[I]** inferred: a model not yet tested. Each one names what will confirm or
  refute it (the bench test, section 9).
- **[M]** measured.

Sources:

- **LTC3789 datasheet** = Linear Technology / Analog Devices 3789fc: Fig 13 on
  p26, pin functions, electrical table, applications text.
- **Design doc** = `ups-monitor-rev4-design.md`, rev 8.
- **AO4882** = AOS datasheet Rev 1.0, Aug 2023, p1-2.
- **SRR1260** = Bourns SRR1260 series datasheet.

## 1. What U4 has to do, and what it must survive

| Requirement | Value | Source |
|---|---|---|
| Output | 12 V into the modem; peak 1.49 A, typical 1.0-1.2 A | [S: design doc §1.7] |
| Modem input window | 10.8-13.2 V (±10 %, design practice; Comcast publishes none) | [S: design doc] |
| Input on mains (float) | 13.571-13.587 V | [D: design doc] |
| Input, topped pack at rest | 14.42 V | [M: owner DMM, design doc] |
| Input ceiling | 16.2 V (the PSU's OVP upper bound, which latches) | [S: design doc] |
| Firmware shed | 11.8 V, on battery only; Q1 pulls the enable line low | [S: design doc §4.4] |
| Floor | 10.0 V (BMS under-voltage cut) | [S previous pack / I this pack: design doc] |
| Off command | Q1 collector on MODEM_EN sinks the pull-up current; Q2 clamps Q1 off while mains is present | [S: design doc §4.4] |

**The moment it must survive.** A mains outage at night, unattended. The block
holds the modem inside its window from 13.58 V down to 11.8 V, turns off when Q1
pulls MODEM_EN low, and comes back when mains returns. The LTC3789 has no thermal
shutdown, so the limits have to keep it cool on their own.

**Where the controller operates** [D: DMAX_BUCK 91.67 % and DMIN_BOOST 8.33 %, from the LTC3789 electrical table]:

| Bus voltage | Region | What switches |
|---|---|---|
| above 13.09 V (12 / 0.9167) [D] | buck | A and B switch; D stays on |
| 11.0 to 13.09 V | buck-boost | all four switches |
| below 11.0 V (12 × 0.9167) [D] | boost | C and D switch; A stays on |

The float (13.58 V) sits in buck. Battery discharge passes through buck-boost on
its way down to the 11.8 V shed. The boost region is reached only between the shed
and the BMS floor, which is the case where the shed itself has failed.

## 2. Why the LTC3789

The owner's drivers (2026-11-11):
- minimise height and heat under the board;
- set limits to this application;
- no unneeded features;
- soldering iron only, so no QFN;
- the 0.635 mm pitch is acceptable.

| | LTC3789EGN | LTC3780EG (rejected) |
|---|---|---|
| Package | SSOP-28, 0.635 mm pitch, no exposed pad [S] | SSOP-24 [S: LTC3780 Rev G] |
| θJA | 80 °C/W [S] | 130 °C/W [S] |
| Average output-current limit | yes, IOSENSE± and ILIM [S] | none [S] |
| INTVCC | 5.5 V-class gate drive, EXTVCC usable from VOUT (4.7-14 V) [S] | 6 V INTVCC, EXTVCC switchover 5.7 V [S] |
| Thermal shutdown | **none**: the datasheet text never mentions one [S] | — |

The average-current limit is the deciding feature. It lets the output current be
capped near 2 A, to suit this load, where the Pololu's limit was 5.1 A
[S: design doc §4.3]. The cap also bounds the worst-case heat, which matters
because the chip has no thermal shutdown.

## 3. What changes against the Pololu

| Pololu feature [S: design doc §4.3] | This block |
|---|---|
| Reverse-voltage protection to 20 V | **Open decision D3** (section 10) |
| Soft-start | CSS 22 nF: 5.9 ms nominal, 4.4-8.8 ms [D: tSS = 0.8 × CSS / 3 µA, LTC3789 datasheet] |
| Input UVLO | **Open decision D1.** The RUN divider gives a start point near 6.45 V [D, typical only], which is not a UVLO in the working range |
| Output OVP | **Open decision D2** |
| Over-current limit, 5.1 A | Average output limit 1.92 / 2.00 / 2.10 A (min/typ/max), plus a cycle-by-cycle limit, plus foldback to about ⅓ when VOUT is below 50 % [D/S, section 5] |
| Thermal shutdown | **None.** Worst-case heat is bounded by the current limit instead (section 6) |
| About 500 kHz | 175 / 200 / 225 kHz, set by tying FREQ to SGND [S] |
| Disabled draw 24-118 µA at 11.8 V | 65-85 µA at 11.8 V [D: shutdown IQ 40-60 µA [S] plus 11.8 V / 475k] |
| 22.9 × 22.9 × 9.7 mm module on the bottom side, 2.8 mm floor clearance | All parts on the top side. The tallest is L1 at 6.0 ± 0.5 mm [S: SRR1260]. Nothing hangs below the board |

## 4. Schematic, by pin

Reference designators are in the 400 range so they don't collide with the board's
existing ones; renumber as you like. "VIN" is the board's existing net after F1.
"VOUT" is the net the Pololu's VOUT pin drives today. "MODEM_EN" is the existing
Q1-collector net that went to the Pololu's EN pin.

**Ground.** SGND is a small island under pins 1-15. It joins PGND at exactly one
point, the ground pad of R401 (RSENSE) [S: LTC3789 layout checklist].

### U4: LTC3789EGN, SSOP-28

| Pin | Name | Connects to |
|---|---|---|
| 1 | VFB | Net FB. R410 140 kΩ (1 %) to VOUT, taken at C410 on the system side; R411 10.0 kΩ (1 %) to SGND |
| 2 | SS | C415 22 nF to SGND |
| 3 | SENSE+ | R402 1 kΩ, then a Kelvin trace to R401's **PGND end** [S: Fig 13] |
| 4 | SENSE− | R403 1 kΩ, then a Kelvin trace to R401's **FET-source end** (net RSNS) [S: Fig 13] |
| 5 | ITH | C417 820 pF to SGND; R412 91 kΩ in series with C416 2.7 nF to SGND [I, see 5.6] |
| 6 | SGND | SGND island |
| 7 | MODE/PLLIN | INTVCC: pulse-skip mode (section 5.7) |
| 8 | FREQ | SGND: 175 / 200 / 225 kHz [S] |
| 9 | RUN | MODEM_EN: R420 475 kΩ to VIN, R421 100 kΩ to SGND, Q1 collector, TP401 |
| 10 | VINSNS | VIN, the bus side before R404 [S: Fig 13] |
| 11 | VOUTSNS | VOUT [S: Fig 13] |
| 12 | ILIM | SGND: 48 / 50 / 52.5 mV average-sense limit [S] |
| 13 | IOSENSE+ | R406 100 Ω to R405's **controller-side** end (net VOUT_C) [S: Fig 13] |
| 14 | IOSENSE− | R407 182 Ω to R405's **system-side** end (VOUT). C407 2.2 µF from pin 13 to pin 14, at the pins |
| 15 | TRIM | SGND. Never leave it floating [S] |
| 16 | SW2 | Net SW2 |
| 17 | TG2 | Q402 pin 4 (G1, switch D) |
| 18 | BOOST2 | C409 0.22 µF to SW2; D402 cathode |
| 19 | BG2 | Q402 pin 2 (G2, switch C) |
| 20 | EXTVCC | VOUT [S: recommended for 4.7 V < VOUT < 14 V] |
| 21 | INTVCC | C411 4.7 µF plus C412 0.1 µF to PGND, at the pin; D401 and D402 anodes; U4 pin 7 |
| 22 | VIN | R404 10 Ω from VIN; C413 1 µF to PGND, at the pin [S: Fig 13; 10-15 Ω recommended against back-feed] |
| 23 | BG1 | Q401 pin 2 (G2, switch B) |
| 24 | PGND | PGND |
| 25 | BOOST1 | C408 0.22 µF to SW1; D401 cathode |
| 26 | TG1 | Q401 pin 4 (G1, switch A) |
| 27 | SW1 | Net SW1 |
| 28 | PGOOD | No connection. It is open-drain and unused |

### Switches: two AO4882 (dual N, 40 V, SOIC-8)

The AO4882 pinout is S2 1, G2 2, S1 3, G1 4, D1 5-6, D2 7-8 [S: AO4882 p1]. Its two
FETs are independent, not wired as a half-bridge.

| Package | FET | Drain | Source | Gate |
|---|---|---|---|---|
| Q401 (A + B, input side) | FET1 = A | pins 5-6 to VIN | pin 3 to SW1 | pin 4 to TG1 |
| | FET2 = B | pins 7-8 to SW1 | pin 1 to RSNS | pin 2 to BG1 |
| Q402 (C + D, output side) | FET1 = D | pins 5-6 to VOUT_C | pin 3 to SW2 | pin 4 to TG2 |
| | FET2 = C | pins 7-8 to SW2 | pin 1 to RSNS | pin 2 to BG2 |

The switch node joins pin 3 to pins 7-8, which sit on opposite sides of the
package. Join them with vias (at least two per side, [I]) and a short
bottom-layer link. Do not route between the pins.

### Power path

| Ref | Part | From | To |
|---|---|---|---|
| L401 | 15 µH, Bourns SRR1260-150M | SW1 | SW2 |
| R401 | RSENSE 40 mΩ, 1 %, ≥ 0.5 W, Kelvin footprint | RSNS | PGND |
| R405 | RSENSE2 25 mΩ, 1 %, ≥ 0.5 W, Kelvin footprint | VOUT_C | VOUT |
| D403 | Schottky B240A (40 V, 2 A, SMA) [S: Fig 13 part] | anode on RSNS | cathode on SW1 (across switch B, as Fig 13) |
| D404 | Schottky B240A | anode on SW2 | cathode on VOUT_C (across switch D) |
| D401, D402 | Boost diodes DFLS160 [S: Fig 13 part] | anode on INTVCC | cathode on BOOST1 / BOOST2 |
| C401, C402 | CIN, 10 µF 50 V X7R 1210 | VIN | PGND, at Q401 pins 5-6 and R401 |
| C403 | CIN bulk, 47 µF ≥ 35 V aluminium polymer or electrolytic [I] | VIN | PGND |
| C404, C405 | COUT, 10 µF 25 V X7R 1210 | VOUT_C | PGND, at Q402 pins 5-6 and R401 |
| C410 | COUT bulk, 100 µF 25 V polymer [I] | VOUT | PGND |

## 5. Values and where each comes from

### 5.1 Output voltage
VOUT = 0.8 V × (1 + 140k / 10.0k) = 12.00 V [D]. This keeps Fig 13's 1:14 divider
ratio (Fig 13 uses 20k / 280k [S]) at half the impedance. With 1 % resistors and
the reference tolerance, the worst case is 11.66-12.35 V [D]. That is inside the
modem window and below EXTVCC's 14 V absolute maximum [S].

### 5.2 Inductor: 15 µH, SRR1260-150M
Datasheet ratings [S: SRR1260]:
- 15 µH ±20 %
- RDC 27.0 mΩ max
- Irms 5.00 A at a 40 °C rise
- Isat 4.60 A **typical**, defined at a 25 % inductance drop
- 12.5 × 12.5 × 6.0 mm [S]

Ripple current at 200 kHz [D]:

| Operating point | ΔIL at 15 µH | ΔIL at 12 µH (L −20 %) |
|---|---|---|
| Buck, 13.58 V | 0.465 A | 0.582 A |
| Buck, 14.42 V | 0.671 A | 0.839 A |
| Buck, 16.2 V | 1.037 A | 1.296 A |
| Boost, 10.0 V | 0.556 A | 0.694 A |

The 0.556 A boost ripple is 29 % of the 1.92 A inductor current [D].

**Saturation margin.** The worst-case cycle limit is 3.93 A (section 5.3). Isat is
4.60 A, a *typical* figure with no guaranteed minimum. So the margin is real but
not guaranteed [I]. The bench current-limit test (9.5) checks it.

### 5.3 RSENSE (R401): 40 mΩ
LTC's sizing formulas with IOUT(MAX) 2.10 A [D] give a maximum RSENSE of
51.0 mΩ (buck) and 50.0 mΩ (boost). Dividing by 1.25 for margin gives 40 mΩ.

| Region | Limit |
|---|---|
| Buck (valley sense 73 / 90 / 107 mV [S]) | minimum output capability 1.98 A [D] |
| Boost (peak sense 123 / 140 / 157 mV [S]) | 3.08 / 3.50 / 3.93 A peak inductor current [D] |

### 5.4 Average output limit (R405 RSENSE2): 25 mΩ, ILIM to SGND
48 / 50 / 52.5 mV ÷ 25 mΩ = **1.92 / 2.00 / 2.10 A** [D]. That clears the 1.49 A
load peak [S: design doc §1.7] by 0.43 A at the minimum.

**Filter resistors.** IOSENSE+ sources 18.3 µA and IOSENSE− sources 10 µA with
ILIM low [S]. 100 Ω and 182 Ω make the two IR drops equal (1.83 mV and 1.82 mV)
[D]. Fig 13 uses 100 Ω on both [S]; that leaves a 0.83 mV offset against a 50 mV
threshold [D]. The pins' absolute minimum is −0.3 V [S].

### 5.5 Soft-start, frequency, supplies
- CSS 22 nF gives 5.9 ms nominal (4.4-8.8 ms) [D]. Fig 13 uses 6.8 nF; the slower
  ramp is gentler on the modem's input capacitance.
- FREQ to SGND gives 200 kHz with no part. The lowest standard setting is chosen
  because switching and gate-drive heat scale with frequency, and the inductor is
  sized for it.
- EXTVCC to VOUT means gate drive is taken from 12 V instead of the 13.6-16.2 V
  bus [S: recommended range].
- Boost capacitors: 0.22 µF, as Fig 13. LTC asks for about 100 × Qg; AO4882 Qg is
  6 nC max at 4.5 V [S], so 100 × 6 nC ÷ 5 V = 0.12 µF [D]. *An earlier draft of
  this design used 0.1 µF, which is short of that; corrected 2026-11-12.*

### 5.6 Compensation [I]: RC 91 kΩ, CC1 2.7 nF, CC2 820 pF
These are scaled from Fig 13 (68k / 3300 pF / 1000 pF [S]):
- RSENSE is 4 × Fig 13's and the output capacitance about ⅓ of it [D on S], so the loop
  gain is restored by raising RC by about 1.4 and keeping the RC × CC1 zero near
  the same frequency.
- Crossover is expected at a few kHz [I]. That is well below the boost right-half-
  plane zero: 59 kHz at 10.0 V, 1.49 A, 15 µH [D: fRHPZ = (VOUT/IOUT) × (1−D)² / (2π L)],
  or 49 kHz with L at +20 %.

**Falsifier:** a load step on the bench (9.4). Ringing or overshoot over about
0.3 V means retune.

### 5.7 MODE: pulse-skip (MODE to INTVCC)
Fig 13 ties MODE to SGND, i.e. forced continuous [S].

At this modem's load (about 1 A and up), the inductor current never reaches zero.
The worst valley is 1.49 A − 1.037 A / 2 > 0 at 16.2 V [D], so both modes run
continuously and behave the same.

They differ only at light load (bench, modem rebooting) [S: light-load section]:
- Pulse-skip holds B (buck) or D (boost) off on reverse current, so it never
  pumps current back into the bus.
- Forced continuous would sink up to 160 mV / RSENSE (4 A) into the input when
  the output is high [S/D].

Pulse-skip costs no parts.

### 5.8 RUN network: same behaviour as the Pololu
The Pololu's EN pin had a 475 kΩ internal pull-up [S: design doc §4.3]. R420
(475 kΩ) reproduces it, so Q1 sinks the same current as today. R421 (100 kΩ)
keeps RUN under its 6 V absolute maximum [S].

| Condition | Value |
|---|---|
| RUN at a 16.2 V bus | 3.33 V [D] |
| Start-up point | about 6.45 V typical [D: RUN on 1.22 V typ, plus the 1.2 µA source]. The datasheet gives no min/max for the threshold [S] |
| Q1 sink at 11.8 V | 26.0 µA (forced β 1.24) [D] |
| Q1 sink at 14.42 V | 31.6 µA (forced β 1.50) [D] |

Q1's base current is about 21 µA [D: design doc §4.4], so Q1 stays deep in
saturation. RUN reads under 0.2 V when shed, and below 0.5 V the chip is in
shutdown [S].

## 6. Loss and heat

**Loss** [I]: the switch and inductor figures are [S] (AO4882 RDS(on) at 4.5 V ×
1.3 for heat, Qgd, Coss; SRR1260 RDC). Dead time (50 ns), the Schottky drop
(0.45 V) and IC quiescent current are assumed. Core loss, capacitor ESR and trace
resistance are excluded. Switching loss is taken at the 225 kHz maximum.

| Operating point | 1.20 A out | 1.49 A out | 2.10 A out (at the limit) |
|---|---|---|---|
| Float 13.58 V, buck | 273 mW | 376 mW | 663 mW |
| Shed 11.8 V, buck-boost | 373 mW | 506 mW | 873 mW |
| BMS floor 10.0 V, boost | 364 mW | 517 mW | 945 mW |

For comparison, the design doc's figure for the Pololu is 0.64-2.54 W [D: design doc].

**Where the heat goes at 1.49 A** [I]:
- Float: Q401 89 mW (A 80, B 9), Q402 78 mW (D on), RSENSE2 56 mW, L DCR 60 mW,
  IC 68 mW.
- 10.0 V boost: Q401 124 mW (A on), Q402 131 mW (C 27, D 104).

**Temperature rise** [D on I]. These use AO4882 RθJA 90 °C/W max, which was measured
on 1 in² of 2 oz copper [S]. This board is 1 oz [M], so expect more. The bench
test (9.6) measures it.

| Part | At 1.49 A | At the 2.10 A limit |
|---|---|---|
| Q402 | +12 °C | +23 °C |
| Q401 | +11 °C | +22 °C |
| U4 (68-101 mW at 80 °C/W) | +5 to +8 °C | +5 to +8 °C |
| L401 (DCR only; Irms gives 40 °C at 5.00 A, rise ∝ I²) | +6 °C at 1.92 A | — |

**What replaces the missing thermal shutdown.** The worst sustained case is a faulted
load holding the output at its 2.10 A limit with a 10.0 V bus. That is 945 mW in
total and +23 °C on the hottest package by the model [I]. Bus current is then
(25.2 W + 0.95 W) / 10.0 V = 2.6 A, against F1's 3.15 A link [D on I]. F1's
time-current curve has not been read, so whether F1 opens on a long fault is unknown.

## 7. Area

- Courtyards total about 670 mm² [I].
- With routing, the block is about 30 × 32 mm, 1,300-1,500 mm² [I].
- The board is 37.8 × 51.5 mm [M: board file, 2026-11-11], and the largest free
  rectangle on both layers today is 4.00 × 3.50 mm [M: same]. **The outline has to grow.**

Removing U4 frees its bottom-side area, but the height and heat-under-board driver
says not to fill it with power parts.

Put the block on the top side, on the edge nearest F1 and the modem output
terminal. The VIN run from F1 (2.0 mm today [S: design doc]) and the VOUT run then
stay short. Placement is the owner's call in KiCad.

## 8. Layout rules

1. **All block parts on the top side.** The bottom layer under the block is unbroken
   PGND, apart from the two switch-node via links.
2. **Input hot loop smallest:** C401/C402, Q401 pins 5-6, Q401 pin 1, R401, back to
   C401/C402 ground [S: LTC3789 layout checklist: CIN, A, B, D1 compact].
3. **Output hot loop smallest:** C404/C405, Q402 pins 5-6, Q402 pin 1, R401, back
   [S: C, D, D2, COUT compact]. R401 sits between the two packages.
4. **Kelvin sense:** R402/R403 and R406/R407/C407 sit at the IC pins. Each sense
   pair is routed together, as a pair, from its resistor's pads [S: Fig 14], away
   from SW1, SW2 and L401.
5. **SGND island** under pins 1-15 for the FB, ITH, SS and ILIM parts. It joins
   PGND at R401's ground pad only.
6. **Gate drive:** TG1 runs beside SW1, and BG1/BG2 beside PGND, short. C408/D401
   go at pins 25/27, C409/D402 at pins 18/16, C411/C412 at pins 21/24, C413 at
   pin 22.
7. **FB divider** at pin 1. Take its top from VOUT at C410, routed away from the
   switch nodes.
8. **Switch-node copper** only as big as the current needs. Flood the rest with
   PGND and stitch it [S: layout checklist].
9. **0.635 mm pitch:** gate and sense traces leave the pins at pin width, then
   widen. Check for bridges under magnification before power-up.

## 9. First power, and what each step proves

Use a bench supply with a current limit, and a resistive or electronic load. **No
modem until step 9.8.** Each step's expected value is the falsifier of the claim
named.

1. **Unpowered:** VIN, VOUT_C, VOUT, INTVCC and SW1/SW2 to PGND are not shorts.
   Bridges at the SSOP pitch are the most likely build fault.
2. **No load, 13.6 V, 0.3 A limit:** VOUT is 11.66-12.35 V (section 5.1). Pull
   TP401 low: VOUT decays. Release it: soft-start in 4.4-8.8 ms on a scope
   (section 5.5).
3. **Sweep the input** at 10.0 / 11.8 / 13.58 / 14.42 / 16.2 V, with 1.2 A and
   1.5 A loads. Record VOUT, input current and output current. Efficiency comes
   from that, which tests the loss table in section 6.
4. **Load step** about 0.5 A to 1.5 A at 10.0, 11.8 and 13.58 V. Undershoot and
   overshoot under about 0.3 V, with no sustained ringing, tests section 5.6.
5. **Current limit:** raise the load until VOUT starts to fall. It should fold at
   1.92-2.10 A (section 5.4). Watch for the inductor-current waveform going sharp,
   which means saturation (section 5.2).
6. **Heat:** 1 h at 1.5 A, at 10.0 V and 13.58 V. Take the temperatures of Q401,
   Q402, L401 and U4 against ambient, and compare with section 6.
7. **Shed path,** with Q1 driven on as in service: TP401 reads under 0.2 V and the
   bus draw is 65-85 µA at 11.8 V (section 5.8).
8. **Switch nodes at 16.2 V:** SW1 and SW2 ringing peaks stay well under 40 V
   (AO4882 and LTC3789 SW absolute maximum [S]).
9. **Modem connected,** on mains, then a mains pull to battery.

## 10. Open decisions for the owner

**D1: Hardware input UVLO.** Recommendation: **none**, behaviour as today.
- The firmware shed at 11.8 V and the BMS at 10.0 V are the layers.
- A RUN-divider UVLO only works with a small top resistor. Its threshold is
  1.22 V *typical only* [S], so its trip point would be [I].
- With the 475 kΩ top resistor it cannot work at all. The VIN-referred hysteresis
  is about 4.3 V [D], which puts the restart above the 13.58 V float: the modem
  would never come back on mains.

**D2: Output over-voltage protection.** Recommendation: **include.**
- *Why it's needed:* if R410 (the FB top resistor) opens, or its joint cracks, VFB
  goes to 0 V and the output climbs to whatever the current limit allows. That
  passes both the modem's 13.2 V and EXTVCC's 14 V absolute maximum [S].
- *Trip window:* above 12.35 V (worst-case regulation) and below 13.2 V, so
  0.85 V wide [D].
- *Options:*
  - A zener plus NPN on RUN cannot fit that window: ±5 % on 13 V alone is ±0.65 V,
    plus the Vbe spread [D].
  - A TL431 driving a transistor onto RUN can, with a trip near 12.8 V [I].
- *Independence:* it must not go through Q1, because Q2 holds Q1 off while mains
  is present.
- *Cost:* about 5-7 small parts. It would retry (hiccup) rather than latch.

The detail waits on this decision.

**D3: Reverse-polarity protection.** The Pololu protected to 20 V [S].
- *What happens without it:* a reversed bus puts the LTC3789's VIN pin past its
  −0.3 V absolute minimum [S], and current runs through the body diodes of B and A
  until F1 clears.
- *Options:*
  - none;
  - a shunt Schottky after F1: no loss in normal service, but it only partly
    protects the IC [I];
  - a series P-FET: about 46 mW at 2.15 A with about 10 mΩ [D on I].
- *A board-level question:* the protection on U3 and the rest of the board is not
  recorded. If they are unprotected, a converter-only fix does not save the board.
  Better decided at F1 for the whole board.

**Test point.** Add TP401 on RUN/MODEM_EN. Today the design doc's Q1 saturation
falsifier (MODEM_EN under 0.2 V) has nowhere to be read [S: design doc §4.4].

## 11. Bill of materials

| Ref | Qty | Value / part | Package | Tag |
|---|---|---|---|---|
| U4 | 1 | LTC3789EGN#PBF (or IGN) | SSOP-28 GN, 0.635 mm | [S] |
| Q401, Q402 | 2 | AO4882, dual N 40 V | SOIC-8 | [S] |
| L401 | 1 | Bourns SRR1260-150M, 15 µH | 12.5 × 12.5 × 6.0 mm | [S] |
| R401 | 1 | 40 mΩ 1 % ≥ 0.5 W | 2010/2512, Kelvin | [D] value, [I] part |
| R405 | 1 | 25 mΩ 1 % ≥ 0.5 W | 2010/2512, Kelvin | [D] value, [I] part |
| D401, D402 | 2 | DFLS160 | PowerDI-123 | [S: Fig 13] |
| D403, D404 | 2 | B240A | SMA | [S: Fig 13]; own datasheet not read |
| C401, C402 | 2 | 10 µF 50 V X7R | 1210 | [I] |
| C403 | 1 | 47 µF ≥ 35 V polymer or electrolytic | — | [I] |
| C404, C405 | 2 | 10 µF 25 V X7R | 1210 | [I] |
| C410 | 1 | 100 µF 25 V polymer | — | [I] |
| C407 | 1 | 2.2 µF | 0805 | [S: Fig 13] |
| C408, C409 | 2 | 0.22 µF | 0805 | [S: Fig 13] |
| C411 | 1 | 4.7 µF 10 V X7R | 0805 | [S: ≥ 4.7 µF] |
| C412 | 1 | 0.1 µF | 0805 | [S] |
| C413 | 1 | 1 µF 50 V | 0805 | [S: Fig 13] |
| C415 | 1 | 22 nF | 0805 | [D] |
| C416 | 1 | 2.7 nF C0G | 0805 | [I] |
| C417 | 1 | 820 pF C0G | 0805 | [I] |
| R402, R403 | 2 | 1 kΩ | 0805 | [S: Fig 13] |
| R404 | 1 | 10 Ω | 0805 | [S: Fig 13] |
| R406 | 1 | 100 Ω | 0805 | [S: Fig 13] |
| R407 | 1 | 182 Ω 1 % | 0805 | [D] |
| R410 | 1 | 140 kΩ 1 % | 0805 | [D] |
| R411 | 1 | 10.0 kΩ 1 % | 0805 | [D] |
| R412 | 1 | 91 kΩ | 0805 | [I] |
| R420 | 1 | 475 kΩ 1 % | 0805 | [D] |
| R421 | 1 | 100 kΩ 1 % | 0805 | [D] |
| TP401 | 1 | test point | — | — |

All passives are 0805 or larger, for iron assembly. D2 and D3 parts are not
included until those decisions are made.
