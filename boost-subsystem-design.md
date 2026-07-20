# 18 V Boost Power Subsystem — Design Specification

**Subsystem:** 12 V bus → 18 V regulated feed for ASRock N100DC-ITX (Home Assistant host)
**Parent system:** DIY LiFePO4 UPS (`wkcollis1-eng/DIY-LiFePO4-UPS`)
**Date:** 2026-07-20 · **Version:** BOOST-DS-r1 · **Status:** Design complete — pending bench validation (§10)

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
| EN control (planned) | XIAO GPIO → level-safe N-FET pulldown on EN (EN idles at VIN ~12.5 V) | Monitor-commanded shed after graceful shutdown | No respin — EN already on header |

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
- **OP-2 — DR-1 latch:** no boost enable on battery-only power. Enforced in monitor firmware; also the manual rule.
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

## Appendix — Sources
Pololu U3V70A product/family pages (limits, true shutdown, ceramic-only I/O, soft-start); Pololu app note 0J16 (LC spikes, ESR damping); Pololu forum #25178 incl. staff confirmation (no Cout required; empirical soft-start into ~66 µF); ASRock N100DC-ITX manual (19 V ±10 %); Panasonic EEH-AZA1H101B datasheet; parent repo README + commissioning reports (INA260 capacity, IR, load measurements, automation validation); Cyclenbatt pack spec (10 A BMS, per owner); board file `Pololu_U3V70A_Vout.kicad_pcb`.
