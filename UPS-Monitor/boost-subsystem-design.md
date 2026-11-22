# 18 V Boost Power Subsystem — Design Specification

**Subsystem:** 12 V bus → 18 V regulated feed for ASRock N100DC-ITX (Home Assistant host)
**Parent system:** DIY LiFePO4 UPS (`wkcollis1-eng/DIY-LiFePO4-UPS`)
**Date:** 2026-07-20 · **Version:** BOOST-DS-r2 · **Status:** Design complete — pending bench validation (§10) · **r2 2026-11-19:** as-built integrated PCB and EN-control operating spec added as §12 · **2026-11-22:** the September cut readings identified (§12.4 rule 5)

Every numeric claim in this document carries its basis inline. Figures marked **[est.]** are engineering estimates, **[unpub.]** rest on unpublished vendor data, and **[meas.]** are measured. Anything not [meas.] that gates a pass/fail is listed in §10.

---

## 1. Purpose and unattended moment

Provide a regulated ~18 V rail to the N100DC-ITX from the UPS 12 V battery bus, replacing the HA Green's direct-bus feed, without degrading the validated four-tier protection ladder or endangering the co-resident XB7 modem on the shared bus.

**The unattended moment (design cornerstone):** an AC outage with nobody home. The subsystem must (a) carry the host through switchover with the rail continuously inside the N100DC's input window, (b) hold the rail clean until the 12.2 V graceful-shutdown tier completes, (c) permit a monitor-commanded shed after shutdown, and (d) deliver a clean, non-damaging re-energization when AC returns so the host auto-boots. "Working" is defined at those four instants, not as uptime.

**Failure philosophy:** the topology is chosen to *fail downward* — every credible regulation failure passes the raw 11.8–13.3 V bus to the output, which is below the host's 17.1 V floor. The host stops; it is not damaged. The only damage vector is a >20.9 V excursion, and §8 enumerates and bounds every path to one.

---

## 2. System context

```
AC ─▶ Mean Well HDR-60-12 (13.3 V float) ─▶ MOSFET ideal diode ─┐
                                                                 ├─▶ 12 V bus
Cyclenbatt 12V 10Ah LiFePO4 (10 A BMS) ─────────────────────────┘
                                                                 │
        12 V bus ─▶ Victron BP-65 (LVD 11.8 V, reconnect 12.8 V/30 s)
                 ─▶ [THIS SUBSYSTEM]
                    Vin carrier ─▶ Pololu U3V70A (set ~18 V) ─▶ Vout carrier
                 ─▶ fused 5 A lead, 2 ft 22 AWG, Tensility 10-02937 5.5×2.5 mm
                 ─▶ ASRock N100DC-ITX 19 V DC-in jack
```

Co-loads on the 12 V bus (outside this subsystem, inside its blast radius): Xfinity XB7 (~12.2 W DC [meas.]), UPS monitor (XIAO ESP32-C3 + INA260 + DS18B20 via D24V7F3, ~30–40 mA [meas.]). The INA260 sits in the main load path and coulomb-counts the whole system, including this subsystem's input current.

**r2 (2026-11-19):** the as-built UPS for this subsystem carries **no XB7** (owner, 2026-11-19: "no modem ... the ups with asrock pc and pololu"). Its bus loads are the host through this subsystem and the monitor. The XB7 figures in §3 (R5), §7 and §10 (V3) describe the earlier shared-bus plan; §12.5 gives the consequence at LVD.

---

## 3. Requirements

| ID | Requirement | Value / basis |
| :-- | :-- | :-- |
| R1 | Output rail inside N100DC input window at the board's jack, all modes | 17.1–20.9 V (ASRock manual: 19 V ±10 %) |
| R2 | Support measured host load | 0.44 A mean / 1.1 A peak @ 18 V [meas., from 8.0 W DC mean / ~19.6 W DC peak] |
| R3 | Operate across full bus range | 11.8 V (LVD floor) – 13.3 V (float) |
| R4 | Never exceed the 10 A BMS discharge rating on battery-only power | Structural, not probabilistic (§7) |
| R5 | Not disturb XB7 operation on the shared bus (noise, sag, dropout) | XB7 validated envelope 11.71–13.11 V at terminals |
| R6 | Survive/enable unattended: no soft-start hiccup; clean EN re-enable from 0 V | §10 scope gate |
| R7 | No damage to host from any single component failure or correct procedure | §8 |
| R8 | Runtime after integration ≥ shutdown-ladder needs | ~2.3 h to LVD (53.3 Wh [meas.] ÷ 23.2 W) vs ladder span of minutes |

---

## 4. Architecture and bill of materials

| Element | Part | Key data | Basis |
| :-- | :-- | :-- | :-- |
| Regulator | Pololu U3V70A | Boost, 4.5–20 V out via 11-turn pot (set ~18 V); 10 A cycle-by-cycle input limit, ~6 A prolonged; η ~90 % at this ratio; ceramic-only onboard I/O caps; true shutdown via EN; soft-start; reverse/short/OTP/UVLO protection | Pololu product data |
| Vin carrier | KiCad PCB 17×30.5 mm, OSH Park 2 oz/0.8 mm ENIG | 220 µF/50 V KEMET A7C hybrid + 10 µF/50 V TDK X7R; EN broken out (testpoint + header) | Pololu 0J16 input-bulk guidance ("more is better" on input) |
| Vout carrier | Same PCB family | **100 µF/50 V Panasonic EEH-AZA1H101B hybrid** (28 mΩ, 2 A/100 kHz, D10/5 mm, AEC-Q200) + 10 µF/50 V TDK X7R | §5 sizing analysis |
| Lead | 2 ft, 22 AWG twisted pair, 5 A fuse | 64.6 mΩ round trip; ~1–1.5 µH [est.] | §6 |
| Plug | Tensility 10-02937, 5.5×2.5 mm center-positive | — | — |
| EN control (as built, r2) | XIAO D3/GPIO5 → R2 100k → 2N3904 Q1 pulls EN low; AC (PSU_SENSE) → 2N3904 Q2 holds Q1 off. Supersedes the planned N-FET pulldown | Monitor-commanded shed after graceful shutdown; AC forces the boost on in hardware | §12.3 |

Setpoint: 18.0 V, trimmer **lacquered after setting** (same practice as the HDR-60 float trimmer). Optional hardening: 20 V-standoff TVS (SMCJ20A class) at the barrel jack — decide after the §10 scope session.

---

## 5. Output capacitor sizing (the governing analysis)

Requirement: a local, moderately damped reservoir at the boost output node — not additional bulk for the N100DC, whose own input caps sit past the lead inductance and cannot decouple the regulator's terminal at switching frequency. Target band 47–100 µF; **100 µF selected**. The selection is made robust to the two unpublished U3V70A parameters (switching frequency, loop bandwidth) as follows.

**5.1 Lower bound — load step, bounded without knowing loop bandwidth.**
ΔV = ΔI·t/C with ΔI = 1 A (margin over the 0.44→1.1 A measured swing) and loop lag bounded pessimistically at 50 µs [est.; typical boosts 10–30 µs]:
- 100 µF → 0.50 V dip → 17.5 V ≥ 17.1 V floor. **Passes at the pessimistic bound.**
- 47 µF → 1.06 V dip → 16.94 V < floor. Fails the same bound.

47 µF is safe only if the unpublished loop happens to be fast; 100 µF is safe across the whole plausible range. Sized for the bound, not the hope. (The N100DC's own caps assist beyond ~3 µs — lead di/dt ≈ V/L ≈ 0.4 A/µs — but their value is [unpub.], so they are margin, not a dependency.)

**5.2 Ripple — insensitive to switching frequency.**
Worst duty at the LVD floor: D = 1 − 11.8/18.5 = 0.362. Capacitive term at a pessimistically low 300 kHz: ΔV = Io·D/(f·C) = 1.1×0.362/(300 k×100 µ) ≈ 13 mV. ESR term: I_L ≈ Io/(1−D) = 1.72 A, ~2.2 A at ripple peak × 28 mΩ ≈ 62 mV. ESR dominates from 200 kHz to 2 MHz; total <0.1 V against a ±1.9 V window. The fsw unknown is immaterial to sizing.

**5.3 Upper bound — soft-start inrush arithmetic (why not 220 µF).**
Cap charging current = C·dV/dt; at a fast 1 ms ramp to 18.5 V, 100 µF draws 1.85 A output-side → input ≈ 1.85/(1−D)/η ≈ **3.2 A**. At 220 µF: **~7.1 A**, crowding both the regulator's 10 A cycle limit and the 10 A BMS rating before the N100DC's own [unpub.] input bulk is added. 100 µF leaves the inrush budget to the one capacitance that cannot be specified.

**5.4 Why not zero.** Pololu confirms no external Cout is required (forum, staff), but deletion removes the damped local node while removing nothing from the inrush problem (dominated by the N100DC's caps, still present), and leaves ceramic-only output noise feeding an undamped cable tank. The hybrid's ESR zero at 1/(2π·28 mΩ·100 µF) ≈ 57 kHz makes it ~28 mΩ resistive above that — the damping element the 0J16 principle calls for. Empirical support: the family has been scoped soft-starting cleanly into ~66 µF external tantalum from an adequate source.

**Verdict:** 100 µF is the unique value that passes the worst-case loop bound (where 47 fails), keeps startup input at ~⅓ of the cycle limit (where 220 doesn't), and drops into the D10/5 mm footprint.

---

## 6. Interconnect design (2 ft, 22 AWG)

| Check | Chain | Result |
| :-- | :-- | :-- |
| Voltage drop | 16.1 mΩ/ft × 4 ft = 64.6 mΩ; ×1.1 A | 71 mV peak — 8 % of sag budget |
| Dissipation | I²R = 1.1²×0.0646 | 78 mW peak |
| Ampacity | 22 AWG chassis ~7 A vs 0.44 A mean | ~16× margin |
| Fuse coordination | Wire fusing current ~41 A (Onderdonk) vs 5 A fuse; sustained 5 A < 7 A chassis rating | Fuse protects wire — correct ordering |
| Damping | ζ = (R/2)√(C/L); R ≈ 28 mΩ ESR + 65 mΩ wire + ~20 mΩ connector [est.] = 113 mΩ; L ≈ 1.5 µH [est.]; C ≈ 300 µF board-side [unpub. assumption] → ζ ≈ 0.80 | Near-critically damped |

Note the self-compensation: wire R and L scale together with length, so ζ is roughly length-invariant — and 22 AWG's resistance *is* the damping. A heavier gauge would ring harder. Twist the pair (lowers L, shrinks loop area; no downside).

---

## 7. Bus integration constraints (10 A BMS = 10 A boost limit)

The BMS discharge rating equals the regulator's cycle-by-cycle input limit. Analysis:

- **Steady state:** worst sustained battery draw = 2.1 A boost (at LVD floor) + 1.2 A XB7 + 0.04 A monitor ≈ **3.4 A vs 10 A** — ~3× margin. Closed.
- **Soft-start on battery only:** current-limited charging averages ~8–9 A at the bus plus the XB7's 1.2 A ≈ 10–11 A — at/over the rating. Whether the BMS trips depends on its unpublished overcurrent delay curve. **Not acceptable as a designed event.**
- **Soft-start with AC present:** the HDR-60 sources up to 4.5 A of the demand through the ideal diode; battery share of a 10 A event ≈ **5.5 A** — inside the rating with no trip-curve assumptions.

**Design rule DR-1 (structural fix, zero cost):** *the boost is only ever enabled with AC present.* First power-on and AC-restore already satisfy this (BP-65 reconnects 30 s after the PSU is live). The EN-shed firmware shall **latch EN low for the remainder of any outage once a shed has occurred**; re-enable requires confirmed AC return. This converts the BMS exposure from probabilistic to impossible-by-construction, and is operationally correct anyway (re-booting the host into a depleted bank buys nothing).

**Bus sag / XB7 hold-through:** pack IR ~260 mΩ at low SoC [meas., OCV-rebound-derived — overstates pure ohmic IR]. A multi-amp ms-scale soft-start average can sag the shared bus ~0.5–1.5 V. Under DR-1 the PSU stiffens the bus during every enable, but the sag channel is retained in the §10 scope session as verification.

**PSU headroom:** post-outage recharge current drops from 4.5 A to ~2.8 A with ~1.7 A of loads on the 60 W PSU → recharge stretches ~1.6×. Functional; update Mode 6 in the parent README.

---

## 8. Overvoltage / host-damage analysis (paths to >20.9 V)

Baseline: 20.9 V is the *specification* ceiling; the true damage threshold is unpublished and likely higher, but is treated as the line.

| # | Mechanism | Bound / mitigation | Status |
| :-- | :-- | :-- | :-- |
| 1 | Input LC spike pass-through (boost forwards VIN > VOUT via sync FET; Pololu measured ~2× spikes on hot-connect through long leads) | 220 µF Vin hybrid damps; **procedure OP-1 (§9)** removes the host from every connect transient | Procedural-lapse-only after OP-1 |
| 2 | Current-limit-exit overshoot at end of soft-start (integrator wind-up; ΔV ≈ I·t_lag/C_total) | 2 A × 100 µs [est.] / 110 µF ≈ 1.8 V → ~19.8 V peak, 1.1 V under ceiling; board caps only improve it | Bounded; **scope-gated** (§10) |
| 3 | Inductor energy dump | ½L·ΔI² into 110 µF: V_pk = √(18² + L·ΔI²/C) ≈ 18.01 V with L ≈ 3.3 µH [est.], ΔI = 4 A | Closed by arithmetic |
| 4 | Setpoint/feedback failure (pot drift; wiper-open) | Lacquer closes drift; wiper-open is the residual single-point failure, excursion uncharacterized | Only path with no mitigation — the case for the optional TVS |

All *undervoltage* failures (module dead, EN shed, LVD, sag) pass ≤13.3 V to a 17.1 V-floor host: non-damaging by construction. Residual electrical damage probability with OP-1, lacquer, and a passed scope gate: ~1 % class over system life, dominated by paths 1 (procedural lapse) and 4. The dominant real threat to the host remains filesystem corruption from hard power loss — addressed by the four-tier ladder plus BIOS *Restore on AC/Power Loss = Power On* (required setting, see OP-3).

---

## 9. Operating procedures

- **OP-1 — Energization order (teardown/reconnect):** *battery last-off, first-on; barrel jack last-on, first-off.* Equivalently, jumper EN low at the Vin-carrier header across any battery connection, then release for a controlled soft-start. Rationale: the BP-65's own reconnect is not a hot-plug (short in-enclosure wiring into the damped 220 µF input — no 2× ring geometry); the manual battery connect is, and OP-1 ensures the host is never present for it. Plugging the barrel into a stabilized 18 V rail is a designed-for, brick-equivalent event (ζ ≈ 0.8, §6). Note: the future GPIO EN control cannot cover the connect instant itself (XIAO boot ~1–2 s while EN idles at VIN) — OP-1 remains the teardown procedure permanently.
- **OP-2 — DR-1 latch:** no boost enable on battery-only power. Enforced in monitor firmware; also the manual rule. The firmware rule is specified in §12.4 (r2).
- **OP-3 — BIOS:** *Restore on AC/Power Loss = Power On* — required for unattended recovery.
- **OP-4 — Spares:** EEH-AZA1H101B replenishment ~43 weeks; hold spares.

---

## 10. Validation gate (open — blocks "ready to deploy")

One bench session, four channels: **Vout at the boost**, **Vout at the board jack**, **12 V bus**, **battery current (INA260 log, ~1.1 ms conversions — resolves the ms-average the BMS filters)**.

| Test | Condition | Pass criteria |
| :-- | :-- | :-- |
| V1 | First power-on into N100DC, AC present | No soft-start hiccup/restart; Vout peak < 20.9 V with margin (expected ≤ ~19.8 V); no sustained ring |
| V2 | EN re-enable from 0 V into cold N100DC, AC present | Same as V1; battery-side ms-average ≤ ~6 A |
| V3 | Bus during V1/V2 with XB7 attached | No XB7 reboot; bus excursion brief and recovering |
| V4 | Load step (host boot / burst) | Jack voltage ≥ 17.1 V throughout |
| V5 | Barrel insertion into live 18 V rail | No overshoot > 20.9 V at the board |

Closes on measurement the assumptions marked [est.]/[unpub.] in §§5.1, 6, 7, 8.2. **If V1/V2 fail (hiccup):** add inrush limiting (NTC, series R, or controlled EN soft-enable) — *do not shrink the output cap*; the event is dominated by the N100DC's input capacitance. If V5 shows overshoot: fit the SMCJ20A TVS. If measured sag is the tighter side of the window, nudge the setpoint to 18.5 V (rebalances the 0.9 V sag / 2.9 V overshoot budgets).

---

## 11. Verification matrix

| Req | Method | Status |
| :-- | :-- | :-- |
| R1 | Analysis (§5, §8) + V1/V2/V4/V5 | Analysis complete; bench open |
| R2 | INA260 measurement (parent repo) | **Closed [meas.]** |
| R3 | Boost regulation (Pololu data) + parent commissioning | **Closed** |
| R4 | DR-1 structural rule + V2 current log | Rule adopted; bench open |
| R5 | §7 analysis + V3 | Analysis complete; bench open |
| R6 | V1/V2 | Open |
| R7 | §8 + OP-1 + lacquer | Closed on paper; V5 confirms |
| R8 | 53.3 Wh ÷ 23.2 W arithmetic on measured values | **Closed [meas.]** |

**Confidence statement:** ~90 % on paper that the subsystem integrates reliably (with DR-1 adopted); moves to ~95 % on a passed §10 session, residual being first-real-outage unknowns.

---

## 12. As-built PCB and EN-control operating spec (r2, 2026-11-19)

This section uses the R15 tags: **[M]** measured, **[S]** spec with source, **[D]** derived with the formula, **[I]** inferred and not yet tested. It records the board as it stands and the behaviour the next monitor firmware must implement. No firmware implements it yet: the deployed `ups-monitor.yaml` is written for the UPS-Monitor-THT Rev 1 board and uses neither GPIO4 nor GPIO5.

### 12.1 Board

- File `UPS for HA with Boost.kicad_pcb` (KiCad file version 20260206), the owner's working copy; there is no schematic. Every board figure below comes from a pcbnew inventory of that file [M].
- One board now carries the monitor and this subsystem, replacing the separate Vin and Vout carriers of §4.
- Power path: 4-pole `BUS` terminal, 1 BUS+, 2 GND, 3 BP+ (from the BP-65 output), 4 18 V out [M].
  - BUS+ → F2 → `+3V3_Fused` → D24V7F3 VIN. Despite its name, `+3V3_Fused` carries the ~12 V bus.
  - BP+ → F1 → `V_FUSED` (220 µF bulk `220uF`, 10 µF C6) → U3V70A VIN.
  - U3V70A VOUT → `18V_OUT` (100 µF `100uF`, 10 µF C5) → BUS.4 → the 5 A fused output lead → N100DC.
  - GND: BUS.2 goes to the common star ground shared by the battery, PSU and BP-65. The host's 18 V return lands on that star (owner, 2026-11-19).
- The U3V70A's printed pin order matches the footprint (owner, 2026-11-19).
- The U3V70A footprint has 9 pads in two rows 30.4 mm apart, and the numbers 1-4 repeat across the rows on different nets [M]:
  - input row: 1 EN, 2-3 GND, 4-5 VIN;
  - output row: 1-2 GND, 3-4 VOUT.
  - Name these pins by net, never by pad number. Nets pushed from a schematic would give every pad of one number the same net, joining EN to GND and VIN to VOUT [I: KiCad pad-number behaviour, not tested here; falsified by Update PCB from Schematic on a sandbox copy].

### 12.2 Components

Fuse values to fit (same footprint, DIN0309 Ø 3.2 mm, 0.80 mm drill [M]):

| Ref | On the board file | Fit | Why |
| :-- | :-- | :-- | :-- |
| F1 | 3.5 A | **Littelfuse 0251005.MXL, 5 A** | Opens in 1 s or less at the BMS's 10 A [S: Littelfuse 251 rev GK p1, 200 % point]. Derated 3.75 A [D: 5 x 0.75] against 2.46 A, the highest outlet sample [D: 29.0 W / 11.8 V; M: Kasa outlet power, n = 450,427, 2026-11-05..11-19, 2 s poll]. Body 3.18 mm max, lead 0.64 mm [S: p3] |
| F2 | 0.75 A | **Littelfuse 0251002.MXL, 2 A** | The D24V7F3 socket is Pololu #1013, 3 A [S: pololu.com item 1013]. Opens in 1 s or less at 4 A [S: p1]. The 1.5 mm trace carries 3.2 A at a 10 C rise [D: IPC-2221, 1 oz] |

Residual on F1: at 5 A the U3V70A's two VIN header pins carry 2.5 A each [D], and Pololu publishes no pin rating [S: pololu.com/product/2890].

**Duplicate reference C5 [M]:** two footprints carry C5. One is the 0.1 µF disc at (74.17, 66.37) on `+3V3_Fused`, the D24V7F3 input. The other is the 10 µF disc at (96.45, 69.50) on `18V_OUT`. A BOM or assembly note cannot tell them apart; rename one before ordering.

Full reference list, generated from the board inventory [M] (values truncated at 34 characters):

| Ref | Footprint | Value |
| :-- | :-- | :-- |
| 100uF | CP_Radial_D10.0mm_P5.00mm | CAP ALUM HYBRID 100UF 20% 50V TH, |
| 220uF | CP_Radial_D10.0mm_P5.00mm | CAP ALU HYBRID RADL 220UF 50V, A7C |
| BUS | TerminalBlock_Phoenix_MKDS-1-4-3.81_1x04_P3.81mm_Horizontal | TerminalBlock_Phoenix_MKDS-1-4-3.8 |
| C1 | C_Disc_D5.0mm_W2.5mm_P2.50mm | CAP CER 10UF 25V X5R RADIAL, FG18X |
| C2 | C_Disc_D3.8mm_W2.6mm_P2.50mm | CAP CER 0.1UF 50V X7R RADIAL, K104 |
| C3 | C_Disc_D3.8mm_W2.6mm_P2.50mm | CAP CER 0.1UF 50V X7R RADIAL, K104 |
| C4 | C_Radial_D6.3mm_H11.0mm_P2.50mm | CAP ALUM 47UF 20% 50V RADIAL TH, E |
| C5 | C_Disc_D3.8mm_W2.6mm_P2.50mm | CAP CER 0.1UF 50V X7R RADIAL, K104 |
| C5 | C_Disc_D6.0mm_W4.4mm_P5.00mm | 10 µF ±10% 50V Ceramic Capacitor X |
| C6 | C_Disc_D6.0mm_W4.4mm_P5.00mm | 10 µF ±10% 50V Ceramic Capacitor X |
| C7 | C_Disc_D3.8mm_W2.6mm_P2.50mm | CAP CER 0.1UF 50V X7R RADIAL, K104 |
| C8 | C_Disc_D3.8mm_W2.6mm_P2.50mm | CAP CER 10000PF 50V X7R RADIAL, K1 |
| F1 | R_Axial_DIN0309_L9.0mm_D3.2mm_P12.70mm_Horizontal | 3.5 A 125 V 125 V Fuse Board Mount |
| F2 | R_Axial_DIN0309_L9.0mm_D3.2mm_P12.70mm_Horizontal | FUSE BRD MT 750MA 125VAC/VDC AXL, |
| H1 | MountingHole_3.2mm_M3 | M3 |
| H2 | MountingHole_3.2mm_M3 | M3 |
| H3 | MountingHole_3.2mm_M3 | M3 |
| Q1 | TO-92_Inline_Wide | 2N3904 |
| Q2 | TO-92_Inline_Wide | 2N3904 |
| R1 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 10k RNMF14FTC10K0 |
| R2 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 100K RNMF14FTC100K |
| R3 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 100K RNMF14FTC100K |
| R4 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 100K RNMF14FTC100K |
| R5 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 22k RNMF14FTC22K0 |
| R6 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 18K RNMF14FTC18K0 |
| R7 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 100K RNMF14FTC100K |
| R8 | R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal | 4.7K RNMF14FTC4K70 |
| TB2 | TerminalBlock_TE_282834-4_1x04_P2.54mm_Horizontal | TerminalBlock_VN04A1500000G_1x04_P |
| U1 | XIAO_ESP32C3_Socketed | Xiao ESP32C3 |
| U2 | PinSocket_1x08_P2.54mm_Vertical | Adafruit INA260 |
| U3 | PinSocket_1x03_P2.54mm_Vertical | Pololu D24V7F3 |
| U3V70A | PinHeader_1x05_P2.54mm_Vertical | Pololu U3V70A |
### 12.3 EN-control circuit

- **U3V70A EN** (net `ENABLE`) has a 100 kΩ pull-up to the module's reverse-protected VIN; below 0.4 V the module is off with true shutdown [S: pololu.com/product/2890].
- **Q1** 2N3904: E to GND, C to `ENABLE`. Its base node takes R2 100k from D3/GPIO5, R3 100k to GND, C8 10 nF to GND and Q2's collector. Q1 on means EN low, which means the boost is off.
  - D3 high gives Q1 about 20 µA of base current [D: (3.3 - 0.65) V / 100k - 0.65 V / 100k]. Q1 then sinks the EN pull-up's ~133 µA [D: 13.3 V / 100k].
- **Q2** 2N3904: base from `PSU_SENSE` through R4 100k with R5 22k to GND; collector on Q1's base. With AC present Q2 holds Q1 off, so **the boost is on whenever AC is present, whatever D3 does**. Base current is about 97 µA at 13.3 V [D: (13.3 - 0.65) / 100k - 0.65 / 22k].
- **PSU_SENSE** (TB2.4) reads 0 V with AC off (owner, 2026-11-19). R7 100k / R6 18k with C7 0.1 µF feed `PSU_ADC` on D2/GPIO4: 2.03 V at the 13.3 V float [D: 13.3 x 18k / 118k].
- **D3 floating** (XIAO in reset, unflashed or dead): R3 holds Q1 off, so the boost runs. The circuit fails toward power.

XIAO ESP32-C3 pin map, from the board nets [M]:

| XIAO pin | GPIO | Net | Use |
| :-- | :-- | :-- | :-- |
| D1 | GPIO3 | /Alert | INA260 ALERT |
| D2 | GPIO4 | PSU_ADC | AC present (ADC) |
| D3 | GPIO5 | /MODEM_OFF | EN control through Q1. The net name is a leftover: there is no modem |
| D4 | GPIO6 | /SDA | I2C to the INA260 socket |
| D5 | GPIO7 | /SCL | I2C to the INA260 socket |
| D10 | GPIO10 | /GPIO10_DQ | DS18B20 1-Wire (TB2.2) |
| D0, D6-D9 | | unconnected | |

### 12.4 Mode of operation (what the firmware must do)

| State | Condition | D3 | Boost |
| :-- | :-- | :-- | :-- |
| AC present | `PSU_ADC` above the AC threshold | Low once AC has been present for 60 s continuously | On (Q2) |
| Outage, host running | AC absent; battery discharge above the host-off threshold | Low | On |
| Shed | AC absent; battery discharge at or below the host-off threshold for 30 s | **High, held** | Off |
| Monitor not running | D3 floating | - | On (R3) |

1. **Shed.** When AC is absent and the battery current has sat at the host-off level for 30 s, drive D3 high. One stateless test covers three cases:
   - after the ladder's graceful shutdown, with the host in soft-off;
   - after a BP-65 LVD cut, when the boost is unpowered;
   - a battery-only power-up, where nothing draws during the BP-65's 30 s reconnect delay. That is DR-1 (§7).
2. **Release.** Drive D3 low once `PSU_ADC` has shown AC continuously for 60 s. Q2 has already turned the boost on the moment AC returned. The 60 s only decides what a short blip does: if AC drops again inside the minute, the host loses 18 V again early in its boot.
3. **Never release on battery.** No path drives D3 low while AC is absent. Missing data means no new decision: if the INA260 or ADC reading is unavailable, D3 keeps its state. AC still releases a shed, through Q2 and then rule 2.
4. **Keep D3 through resets and sleep.**
   - While D3 is high, hold the pad (ESP32-C3 GPIO hold). A software restart, OTA, the task and interrupt watchdogs and deep-sleep wakes are core resets and keep it [S: ESP32-C3 TRM v1.4 s5.9 p167, s6.1.3 p192].
   - If the firmware deep-sleeps (survival mode) while shed, the hold must last through the sleep.
   - On boot, do not release a held D3 until the first valid `PSU_ADC` and INA260 readings call for it.
   - A power-on, brown-out, RESET-button or RTC-watchdog system reset clears the hold [S: TRM Table 6.1-1 p193]. D3 then floats, the boost restarts, and the host boots on battery once. The rule sheds again after the ladder's next shutdown. This is the accepted residual.
5. **Thresholds.**
   - AC: about 1.0 V on `PSU_ADC` [D: midway between 0 V and 2.03 V].
   - Host-off: **not yet set.** It needs one reading on battery on this UPS, on the INA260 as wired (its power terminals are wired off-board [M]): the host shut down. The threshold must sit clearly between that and the running draw.
   - Running draw, N100 alone on the bus (owner, 2026-11-04): median 0.907 A discharge, 0.66-1.23 A [M: `sensor.ups_monitor_battery_current`, n = 85 change-only rows at ~5 s after the first 30 s of the owner's AC-cut test, 2026-11-04 21:49:47-21:56:47 EST, bus 13.11-13.21 V]. A lower bus should raise it [I: constant-power boost load, report §3.2; falsified by a lower reading nearer the 12.2 V tier].
   - The two September cuts read about 2.0 A: medians 2.065 A on 09-16 and 2.011 A on 09-18 [M: same sensor, n = 97 and 70 rows]. That matches the shared bus with the XB7. What was on the bus then is open (§12.6). **Answered 2026-11-22:** the N100 and the XB7 were both on the UPS at both cuts (owner), and the outlet's Kasa plug agrees. Its hourly means read 30.63 W before the 09-16 16:00 EDT cut and 30.15 W before the 09-18 21:05 cut, and its daily medians 29.08–30.49 W from 09-01 to 10-30, against 13.97–14.30 W from 11-05 to 11-22 with the N100 alone, median 14.20 W [M: `sensor.ups_outlet_current_consumption`, HA long-term statistics]. That is about 16 W more [D: 30.15 and 30.63 − 14.20], which matches the 1.10 and 1.16 A more battery current at the cuts, 14.5–15.3 W at 13.2 V [D: 2.011 and 2.065 − 0.907 A]. So both September readings are N100 plus XB7, and 2026-11-04's 0.907 A is the only N100-alone reading.
   - Host-off, a loose bound until it is read:
     - On 2026-09-15 the bus still drew ~1.40 A after the shutdown, with the XB7 on it. The XB7 and monitor alone drew ~1.18 A on 2026-05-06 [M: report §3, §4.2].
     - That puts the shut-down host plus the boost's own draw at roughly 0 to 0.2 A [D: 1.40 - 1.18; I: two runs at different states of charge, falsified by the direct reading].
   - The 2.089 A in the `ups-monitor.yaml` header is the whole earlier shared bus, XB7 included [S: report §4.6 Test C], not this host.

### 12.5 LVD evidence (2026-09-15 full-discharge test, earlier shared-bus system)

Source: `reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md` §1 and §3.
- The BP-65 tripped at 10:47:18 EDT, 102 s after the first sample below 11.800 V [D: 10:45:36 to 10:47:18; M: report §1]. The last telemetry before the trip read 11.675 V at 10:47:07.7 [M: report §1].
- After the trip the pack rested at 11.9275 V, rising to 11.9762 V by 11:00:09, at about 0 A [M: report §1, n = 1 outage, 13 min]. The BP-65 reconnects only above 12.8 V for 30 s (§2); the rebound came nowhere near it. Not established: the rest voltage over hours.
- After the host's graceful shutdown that bus still drew ~1.40 A for the remaining ~51 min to LVD, with the XB7 on it [M: report §3; 51 m 26 s from ICMP sustained-down to the trip, report §6]. The XB7 and monitor alone drew ~1.18 A on 2026-05-06 [M: report §4.2].
- This UPS has no XB7, so after the ladder's shutdown nothing large drains the pack, and the LVD may not come before AC returns [I: wrong if the shut-down host draws close to its running current]. If 18 V never drops, BIOS *Restore on AC/Power Loss* (OP-3) never fires and the host stays off with AC back. **Rule 1's shed, not the BP-65, is what makes the host restart.**
- That day the pack delivered 2.5331 Ah / 31.821 Wh to LVD [M: report Abstract]. R8's 53.3 Wh is the 2026-05-06 coulomb count [S: report §4.2].

### 12.6 Open

- The host-off threshold (§12.4 rule 5): one reading on battery, host shut down.
- What was on the bus at the 2026-09-16 and 09-18 cuts (§12.4 rule 5): asked of the owner. **Answered 2026-11-22:** the N100 plus the XB7 (§12.4 rule 5).
- Duplicate reference C5 (§12.2): the owner's call.
- The firmware for this board's pin map: not written.
- §10 bench validation: still open.

---

## Appendix — Sources
Pololu U3V70A product/family pages (limits, true shutdown, ceramic-only I/O, soft-start); Pololu app note 0J16 (LC spikes, ESR damping); Pololu forum #25178 incl. staff confirmation (no Cout required; empirical soft-start into ~66 µF); ASRock N100DC-ITX manual (19 V ±10 %); Panasonic EEH-AZA1H101B datasheet; parent repo README + commissioning reports (INA260 capacity, IR, load measurements, automation validation); Cyclenbatt pack spec (10 A BMS, per owner); board file `Pololu_U3V70A_Vout.kicad_pcb`.
