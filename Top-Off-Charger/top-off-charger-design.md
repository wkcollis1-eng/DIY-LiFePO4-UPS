# LiFePO4 Top-Off / Top-Balance Charger — Design

**System:** bench top-balance hold charger for the UPS's Cyclenbatt 12V 10Ah. **The pack is removed from the UPS for every session** [owner, 2026-09-21], **charged to full on a Dylannet P20 at 5 A, then held at 14.40 V here** [owner, 2026-09-22; §4.3, §10.1].
**Controller:** Battery_Bank-Monitor-THT **V2 Rev 1.1** carrier + XIAO ESP32-C3 + Adafruit INA228 (#5832), a second build of the bank-monitor board ([wiring summary v1.10][ws], cited below as **ws**).
**Document revision:** 0.5 — **pre-build design draft, 2026-09-22.** Nothing here is built or tested. Scoped to the UPS pack and moved here from `Lifepo4-Battery-Banks/Top-Off Charger/` (rev 0.2 is commit `680caed` in that repo). Changes are listed in §15.
**Author:** William Collis (draft prepared with Claude Code)

Provenance tags follow the house convention: **[M]** measured, **[S]** spec (document + page), **[D]** derived (formula shown), **[I]** inferred (with its falsifier). The on-hand fuse has no maker's datasheet, so its interrupt rating is **[I]** (O2). Seller listings are cited as **[listing]**: below [S], because R16 needs a maker's document for the identifier on the unit.

[ws]: https://github.com/wkcollis1-eng/Lifepo4-Battery-Banks/blob/main/INA228%20Monitor/battery-bank-monitor-wiring-summary-v1_10.md

---

## 1. The unattended moment

A session is running and the owner is away. Wi-Fi or Home Assistant is down, the ESP32 hangs, the PSU's voltage regulation fails high, or the pack on the lead never went through the P20.

**"Working" at that moment means:**

1. The session ends by itself within its time cap.
2. The pack never sits above its voltage ceiling for longer than one sample period.
3. No fault the battery can feed can burn a conductor.
4. Nothing restarts a charge after a reboot or an AC blip.
5. The PSU never runs in its overload fault mode beyond a short transient (RQ-12).

Every protection layer in §8 exists for one of those five clauses.

---

## 2. Why this exists

The HDR-60-12 floats the pack at 13.3 V, so the cells never reach balancing voltage. On the 09-15 test the pack delivered 2.5331 Ah LVD-to-LVD, against 4.179 Ah on 05-06 [M, one test each; [09-15 README](../data/2026-09-15_full_discharge_survival_test/README.md)]. Its OCV overlay favours a non-uniform pack. Rev 0.4 made this charger the tool for that report's Open Item 16, a coulomb-counted recharge to termination. **Rev 0.5 does not:** the bulk charge moves to the P20 (§4.1 correction record, §4.3), which counts nothing, so Open Item 16 is not served by this build (O10).

**What it cannot do:** balance a pack whose BMS has no balancer. The Cyclenbatt is sealed, with no balance taps [M, owner-confirmed 2026-09-15], and its label gives no balance details [owner, 2026-09-21]. Documentation cannot settle whether it balances. Two observations bear on it:

- **The success measure** is the matched-load LVD-to-LVD capacity test, before and after (UPS Open Item 14a). Nothing else here shows whether the top-off helped.
- **The current tail at 14.40 V** (FW-6) is the first direct look. A passive balancer bleeding a high cell should hold the charge current above zero at constant voltage [I; falsifier: the logged current at 14.40 V decays toward zero with no floor].

The P20's full charge reaches the capacity the 13.3 V float never uses. The hold here adds time at balancing voltage, and nearly all of it is the current tail FW-6 logs, which is the observation above.

**Deferred: the 500 Ah bank hold** (rev 0.2 profile P2). Adding it back needs a second firmware profile, a busbar pigtail fused for the bank's ≥ 3.6 kA prospective fault current [D, rev 0.2 §6.2], the charger's return on the load side of the bank shunt, and the bank report's ledger fix done first. Nothing in this build blocks it, but V_SET must then stay at or below the bank's 14.58 V measured peak.

---

## 3. Requirements

| ID | Requirement | Value | Basis |
|---|---|---|---|
| RQ-1 | Charge current into the pack | **≤ 5.0 A (0.5 C)** | Owner, 2026-09-21, from the Cyclenbatt documentation |
| RQ-2 | The PSU physically cannot exceed RQ-1, under any overload behaviour | ≤ 3.64 A worst case, at any pack voltage FW-3 admits | [D] §4.1 |
| RQ-3 | Charge stops with no network, no HA, and a hung CPU | — | §1 |
| RQ-4 | Nothing restarts after a reboot or an AC loss | — | §1 |
| RQ-5 | Every conductor the battery can feed is fused at the battery end, with an interrupt rating ≥ the battery's prospective fault current | — | §6 |
| RQ-6 | Battery polarity at the F2 tabs is set **by procedure**: colour-matched QDs, checked before each push-on, with AC off | — | §6.3. Rev 0.2 claimed "reversal impossible" through a keyed connector. That held only for a permanent pigtail, and this pack's tabs are remade every session |
| RQ-7 | The pack is never charged on the UPS bus | Removed from the UPS for every session | Owner, 2026-09-21. XB7 validated envelope 11.71–13.11 V [[boost-subsystem-design.md](../UPS-Monitor/boost-subsystem-design.md) R5] |
| RQ-8 | *Withdrawn in rev 0.3* (bank return on the busbar; bank deferred, §2) | — | — |
| RQ-9 | No charging at or below freezing | Charge only above 32 °F. **Met by siting:** the P20 and this charger are used indoors, in conditioned space. No sensor, no firmware check | Owner, 2026-09-21 (Cyclenbatt label) and 2026-09-22 (siting; rev 0.5 dropped the DS18B20) |
| RQ-10 | Charge voltage within the pack's rating | 14.4–14.6 V | Owner, 2026-09-21, Cyclenbatt label |
| RQ-11 | No charging above the pack's upper charge temperature | The label gives none [owner, 2026-09-22]. **Met by siting**, as RQ-9 | Q2 answered |
| RQ-12 | The PSU runs inside its rating: load ≤ 2.0 A, except a transient no longer than t_ol | 2.0 A [S, HDR-30-SPEC p.2, rated current]; t_ol from T11 | Overload is a "fault condition" [S, p.2]; §4.1 correction record. Enforced by FW-4 |

---

## 4. Part selection

### 4.1 PSU — HDR-30-15, not HDR-60-15

The HDR series has no current setpoint. When a pack below V_SET is connected, the battery holds the output near its own voltage, and the PSU runs at its overload limit: **105–160% of rated output power** [S, HDR-30-SPEC and HDR-60-SPEC, both dated 2026-04-03, p.2]. **In rev 0.5 that happens only as a transient** (RQ-12): the P20 does the bulk charge (§4.3), and this PSU holds a full pack.

| | HDR-60-15 | **HDR-30-15** |
|---|---|---|
| Rated | 4 A / 60 W [S, HDR-60-SPEC p.2] | **2 A / 30 W** [S, HDR-30-SPEC p.2] |
| Adj. range | 13.5–18 V [S] | 13.5–18 V [S] |
| OVP | 18.8–22.5 V [S] | 18.8–22.5 V [S] |
| Efficiency (typ.) | 89% [S] | 89% [S] |
| Current in overload, into 13.2 V | **4.77–7.27 A** [D: 63–96 W ÷ 13.2 V] | **2.39–3.64 A** [D: 31.5–48 W ÷ 13.2 V] |
| Meets RQ-1 (≤ 5.0 A)? | **No**: the upper part of the band exceeds it | **Yes, at the band's ceiling** |

The sibling HDR-60-12 on the UPS was measured inside that band. Its total output was 143.8% of nameplate at 11:00:13, decaying to 96.0% by 11:07:58 [D in the 09-15 README; one recharge, with the true peak earlier and unobserved]. So the band is not a paper number. It was also a transient of minutes, which is the only use of the band rev 0.5 keeps (RQ-12).

**Decision: HDR-30-15.** Its datasheet ceiling (3.64 A [D]) is below RQ-1, whatever the overload circuit actually does. The overload row adds "Constant current limiting within 50% ~ 100% rated output voltage" [S, p.2], so the current does not rise as the pack voltage falls, down to 7.5 V [D: 50% × 15 V]. The 13.2 V figure below is therefore not a limit on validity: 3.64 A bounds every pack voltage FW-3 admits (> 10.0 V).

- The pack took ≥ 4.4465 A on the 09-15 outage recharge [M, one firmware peak, a lower bound], so 3.64 A is inside its service history.
- Heat is 3.71 W at rated load [D: 30 W ÷ 0.89 − 30 W].
- 13.2 V is used as a conservative low battery voltage. The current is lower at any higher voltage.

**Output regulation**, the terms that set the voltage-ceiling margin in §9 [S, HDR-30-SPEC p.2, 15 V column]:

| Spec | HDR-30-15 | At V_SET = 14.40 V |
|---|---|---|
| Voltage tolerance (Note 3: includes setup tolerance, line and load regulation) | ±1.0% [S] | ±144 mV [D: 14.40 × 1.0%] |
| Temperature coefficient (0–50 °C) | ±0.03%/°C [S] | ±108 mV over a 25 °C rise [D: 14.40 × 0.03% × 25; the rise is assumed, not measured] |
| Ripple and noise (max, 20 MHz) | 120 mVp-p | +60 mV peak [D: 120 ÷ 2] |
| Overload behaviour | "Hiccup mode when output voltage <50%"; "Constant current limiting within 50% ~ 100% rated output voltage"; both "recover automatically after fault condition is removed" [S] | Hiccup below 7.5 V [D: 50% × 15 V rated]; constant current above it. O3 closed: read by layout-preserving extraction 2026-09-22, the last clause decoded from private-use glyphs |

Terminals: one **+V**, one **−V**, **AC/L**, **AC/N** [S, HDR-30-SPEC p.4]. The pin numbers do not survive text extraction, so work from the labels on the unit's silk. Class II, with no earth terminal [S, p.4].

> **Correction record (R13), 2026-09-22.** Rev 0.3 and 0.4 made this PSU the bulk charger, running "at its overload limit" for the whole bulk phase. The review that preceded rev 0.5 accepted that and recommended dropping the owner's P20, citing the HDR-60-12's recharge as precedent. The datasheet does not support it: the overload row says the PSU "recovers automatically after **fault condition** is removed" [S, HDR-30-SPEC p.2], and the derating curve's load axis ends at 100% [S, p.3]. The HDR-60-12 precedent was a transient of minutes, 143.8% of nameplate decaying to 96.0% within 8 min [D, 09-15 README, n = 1], while a bulk charge from empty would hold this PSU in overload for 0.8–2.0 h [D: 2.53 Ah ÷ 3.2 A to 4.18 Ah ÷ 2.1 A; the pack's measured capacities, one test each, over the 105–160% band of the 2.0 A rating]. Found when the owner asked for proof that the HDR-30-15 could do the whole charge. Rev 0.5 moves the bulk charge to the P20 and adds RQ-12 and the FW-4 overload stop.

### 4.2 Switch — Pololu #2814 (Big MOSFET Slide Switch, MP), not #2815 (HP)

From the comparison table on the Pololu #2814/#2815 product pages [S, read 2026-09-21; footnote 1: "At 12 V with ambient temperature of 22 °C in still air"]:

| | #2814 MP | #2815 HP |
|---|---|---|
| Absolute max / recommended operating voltage | 40 V / 4.5–32 V | 40 V / 4.5–32 V |
| On resistance (max, at 10 V) | 30 mΩ | 8.6 mΩ |
| Continuous current, MOSFETs at 55 °C | 4.0 A | 6.0 A |
| Continuous current, MOSFETs at 150 °C (absolute limit) | 8.0 A | 16 A |
| Price | $5.49 | $8.49 |

**Decision: #2814.**

- At the PSU's 3.64 A worst case [D, §4.1] the #2814 dissipates 0.40 W [D: 3.64² × 0.030 Ω]. That is below the 4.0 A at which Pololu's table puts its MOSFETs at 55 °C in 22 °C still air.
- Its 32 V recommended maximum is above the PSU's 22.5 V OVP ceiling [S, §4.1].
- The ON pin tolerates 30 V independent of VIN, and **"Driving the 'ON' pin low (or leaving it disconnected) will leave the switch off"** [S, #2814 page].
- It saves $3.00 [D: 8.49 − 5.49].

> **Correction record (R13), 2026-09-21.** The review that preceded rev 0.3 read the table's "4.0 A at 55 °C" as an **ambient**-temperature rating and recommended keeping the #2815. The 55 °C is the **MOSFET** temperature, at 22 °C ambient (footnote 1). The owner caught it from the #2814's 8 A spec line, which is the 150 °C absolute-limit figure. Evidence: the #2814 page's comparison table, read 2026-09-21.

### 4.3 Bulk charger — Dylannet P20 (owner's, rev 0.5)

The owner's charger does the bulk charge before every hold session. Everything below comes from the owner's reading of the unit or from the seller's listing; there is no maker's datasheet.

| | Value | Source |
|---|---|---|
| Identity | Dylannet **P20**, maker's part TB-30020A (Huizhou Haitan Technology) | [listing, Amazon B0BM9H759L, read 2026-09-22]. Confirm "P20" on the unit's label (R16) |
| LiFePO4-mode current | 5 / 10 / 20 A selectable; **5 A used** | Owner, 2026-09-22. Meets RQ-1. The listing's own note: "Charge the battery below 10AH with the minimum current" |
| LiFePO4-mode voltage | 14.6 V | [listing]. The top of RQ-10's 14.4–14.6 V |
| End of charge | Enters trickle charging; it **does not turn off** | [listing]. §10.1 disconnects it when it reaches trickle |
| Repair / pulse mode | Lead-acid only; not offered in LiFePO4 mode | Owner, 2026-09-22 |
| Temperature compensation | Automatic winter/summer switching; whether it acts in LiFePO4 mode is not stated | [listing]. Indoor use (RQ-9) |

**Why the P20 and not the HDR-30-15 for bulk:** the P20 is a charger, built to deliver its set current continuously. The HDR-30-15 would deliver bulk current only in its overload fault mode (§4.1 correction record).

**What the P20 does to this design:** the pack arrives having just finished a 14.6 V absorb, so it rests above V_hold, and FW-3 refuses Start until VBUS falls below it (§9). The P20 records nothing, so the approach to the top of charge, where an uneven pack would trip its BMS, happens unlogged. FW-5 still sees a trip during the hold.

---

## 5. Architecture

```text
AC 120 V ─ plug-in COUNTDOWN TIMER (L6, no network) ─ 2-wire cord ─ G1 ─► HDR-30-15 AC/L, AC/N

POWER PATH  (charge current, ≤ 3.64 A)
HDR +V ─► [WP] ─► #2814 VIN ~ VOUT ─► #5382 VIN ~ VOUT ─► INA228 VIN+ ═15 mΩ═ VIN− ─► [WL] ─ G2 ─► S1 ─► 5 A FUSE ─► F2 QD ─► pack +
HDR −V ◄─ [WG] ◄──────────────────────────────────────────────────────────────────────── G2 ──────────────────► F2 QD ─► pack −

[WP]  Wago 3-position, positive splice:  HDR +V · #2814 VIN · V2 board TB1-2 (BATT_RAW)
[WG]  Wago 5-position, GROUND STAR:      HDR −V · V2 board TB1-1 · #2814 GND · #5382 GND · lead −
[WL]  Wago 3-position, lead splice:      INA228 VIN− · lead +   (one port spare)

CONTROL
V2 J2-1 (GPIO4) ────────────────────────► #2814 ON   (direct; on-board R4 + R5 = 20 kΩ to GND holds it off)
V2 J2-2 (GND)   ────────────────────────► #2814 GND

#2814 slide: LOCKED in OFF.  INA228 VBUS jumper: CLOSED.  V2 board R3: NOT FITTED.
```

The order of the power path is deliberate:

- **Switch → ideal diode → shunt.** The switch interrupts forward current. The shunt sees only battery current, not the board's supply.
- **The ideal diode** blocks the battery from back-feeding the PSU (the job it already does in the UPS [[bom.md](../docs/bom.md)]). It does two further jobs here:
  - **It makes L6 end everything.** The board is fed from the PSU side of the switch. Without the diode, AC loss with the switch ON would let the pack back-feed through the switch into the board. The ESP32 would stay up and hold the switch on, and the pack would drain into the PSU output with nothing to stop it. T12 proves this.
  - **It guarantees I ≥ 0 through the shunt.** The VBUS ceiling trip (§9) relies on this.
- **The board is fed upstream of the switch**, from the PSU side. It is alive whenever AC is on, draws nothing from the battery when AC is off, and keeps reading the pack while the switch is open.
- **VBUS is on the battery side.** With the switch open, VIN+ is tied to the battery through the idle shunt, so VBUS reads the pack's open-circuit voltage before every start.
- **The star is [WG].** The charge return (lead −) and the board ground (TB1-1) meet only there. So the charge current never flows in the conductor the INA228 measures VBUS against.

### 5.1 Splice nodes

| Node | Part | Ports used | Conductors landed |
|---|---|---|---|
| **WP** | Wago lever nut, 3-position | 3 of 3 | W3 (from HDR +V, 18 AWG) · W4 (to #2814 VIN, 18 AWG) · W5 (to TB1-2, 22 AWG) |
| **WG** | Wago lever nut, 5-position (**the ground star**) | 5 of 5 | W6 (from HDR −V, 18 AWG) · W7 (to TB1-1, 22 AWG) · W8 (to #2814 GND, 22 AWG) · W9 (to #5382 GND, 22 AWG) · W18 (lead −, 16 AWG) |
| **WL** | Wago lever nut, 3-position | 2 of 3 | W12 (from INA228 VIN−, 18 AWG) · W16 (lead +, 16 AWG) |

Check that the wire range printed on the lever nuts covers 22–16 AWG. Fix all three nodes to the enclosure (a mounting carrier or an adhesive base) so none can float against the PSU (O6).

### 5.2 From/to — inside the enclosure

| W# | From | To | Wire | Termination / notes |
|---|---|---|---|---|
| W1 | AC cord, **hot** conductor (smooth jacket; narrow blade on a polarized plug) | HDR-30-15 **AC/L** | 2-conductor cord, through cord grip **G1** | HDR screw terminal. The cord's plug goes into the countdown timer |
| W2 | AC cord, **neutral** conductor (ribbed jacket; wide blade) | HDR-30-15 **AC/N** | same cord | HDR screw terminal |
| W3 | HDR-30-15 **+V** | **WP** | 18 AWG red | HDR screw terminal → lever nut |
| W4 | **WP** | #2814 **VIN** | 18 AWG red | #2814 input 5 mm terminal block |
| W5 | **WP** | V2 board **TB1-2 (BATT_RAW)** | 22 AWG red | TB1 is a Phoenix MKDS-1.5-3.81 screw terminal [[ws] §4.6]. The board's F1 (1 A SB) protects it. **The board has no reverse protection** [[ws] §4.4]: check TB1 polarity before first power |
| W6 | HDR-30-15 **−V** | **WG** | 18 AWG black | HDR screw terminal → lever nut |
| W7 | **WG** | V2 board **TB1-1 (GND)** | 22 AWG black | Phoenix screw terminal |
| W8 | **WG** | #2814 **GND** (input terminal block) | 22 AWG black | Keeps the #2814 grounded even if the J2 cable is unplugged. It then sees ON disconnected, which is **off** [S, §4.2] |
| W9 | **WG** | #5382 **GND** (either pad; they are one node) | 22 AWG black | 5 mm terminal block or solder. The LM74700 controller needs it |
| W10 | #2814 **VOUT** | #5382 **VIN** | 18 AWG red | #2814 output terminal block → #5382 input |
| W11 | #5382 **VOUT** | INA228 breakout **VIN+** | 18 AWG red | INA228 3.5 mm terminal block. VBUS jumper closed, so VBUS = this node. Confirm 18 AWG fits (O9) |
| W12 | INA228 breakout **VIN−** | **WL** | 18 AWG red | 3.5 mm terminal block → lever nut |
| W13 | V2 board **J2-1 (GPIO4_BTN)** | #2814 **ON** (0.1″ hole) | 24–26 AWG | JST-XH 2-pin housing at J2; solder at the #2814. **Direct, no series resistor** (§7.2). Check the pair before the first AC on (§5.4) |
| W14 | V2 board **J2-2 (GND)** | #2814 **GND** (0.1″ hole) | 24–26 AWG, paired with W13 | ON's signal return. Solder at the #2814. It parallels W7 + W8 at milliamp level and carries no charge current |
| W15 | *Withdrawn in rev 0.3* | — | — | No external pull-down: the #2814 carries its own (§7.2) |

### 5.3 From/to — leaving the enclosure

| W# | From | To | Wire | Termination / notes |
|---|---|---|---|---|
| W16 | **WL** | Splice **S1** → fuse holder, line-side lead | 16 AWG red, through cord grip **G2** | **Lead +.** S1 is a crimped, heat-shrunk butt splice, not a lever nut: this joint is outside the box, on a lead that is handled every session. Length to suit; R_series is measured at T10 |
| W17 | Fuse holder, battery-side lead (**5 A**) | **F2 female QD** → Cyclenbatt **+** | the holder's own lead | **The fuse sits within a few inches of the + tab** (§6.1). Insulated 6.3 mm female QD |
| W18 | **WG** | **F2 female QD** → Cyclenbatt **−** | 16 AWG black, through **G2**, twisted with W16 | **Lead −**, the charge return. Insulated 6.3 mm female QD |
| W19 | *Withdrawn in rev 0.5* | — | — | DS18B20 dropped: RQ-9 and RQ-11 are met by siting (§3). Enclosure temperature comes from the INA228 die (FW-10) |

Not wired in this build: **J1** (OLED, dropped), **TB2** (DS18B20, dropped in rev 0.5), the **ALERT** test point (L4 withdrawn), the INA228's separate VBUS lead (the jumper replaces it).

### 5.4 Build notes

- **First flash by USB with TB1 unplugged** (AC cord unplugged), OTA after that, and never USB with AC on. This carries over the bank build's rule against a 3V3 source conflict between the buck output and the XIAO's USB-fed LDO [[ws] §2.1].
- **Power-up tell:** the status LED is firmware-driven, not a rail indicator. If it is **dark for more than ~10 s** after AC on, the board is not running [[ws] §4.4]. Check TB1 polarity first.
- **Before the first AC on:** DMM continuity from each F2 QD back to its node (+ through the fuse to WL, − to WG), with no continuity between them.
- **Control pair, before the first AC on, XIAO out of its socket:** J2-1 to #2814 ON reads 0 Ω, and J2-1 to GND does **not** read 0 Ω. It reads roughly 10–20 kΩ through the #2814's R4 + R5, with Q3's base junction across R5 depending on the meter. A 0 Ω from J2-1 to GND means the pair is swapped at the #2814, so GPIO4 would drive into ground. This check takes over one of the jobs of the withdrawn Rs (§7.2).

---

## 6. Fusing and the battery connection

### 6.1 Where the fuse goes

The energy that burns wire comes from the **battery**. The PSU limits itself to ≤ 160% of rated power [S] and hiccups below 50% Vout [S, HDR-30-SPEC p.2; O3].

A short in the external lead (a QD touching the wrong tab, chafed insulation) is fed from the battery and never passes a fuse at the charger end. **So the fuse goes at the battery end of the + conductor, as close to the + tab as the holder allows.** Everything downstream of it is then protected: the lead, the splices, and every node inside the enclosure the battery can reach. A second fuse at the charger end would add nothing for battery-fed faults.

The negative conductor is not fused (standard practice: fuse the ungrounded conductor). The UPS's own F2 fuse stays with the UPS harness when the pack comes out, so the charger lead carries its own.

### 6.2 Rating and interrupt capacity

| | |
|---|---|
| Normal current | ≤ 3.64 A [D, §4.1] |
| Fuse | **5 A mini (ATM/APM) blade in an inline holder** (owner, on hand; from an AKOSN assortment kit, Q3 answered 2026-09-22) |
| Prospective fault current | Bounded by the pack and a 10 A BMS, below 1 kA [I; falsifier: none cheap] |
| Interrupt rating | **Unknown.** The kit's listing states no voltage rating, no interrupt rating and no standard [listing, Amazon B0DNC57LR9, read 2026-09-22], and the kit has no maker's datasheet. **RQ-5 cannot be shown met with it:** fit a branded 5 A mini fuse whose maker publishes a DC interrupt rating (O2). Rev 0.2's ATC-5 figure (1,000 A at 32 VDC) came from a distributor listing |

The fuse protects the **wire**. It does not enforce RQ-1: a 5 A fuse carries 5 A indefinitely. RQ-1 is enforced by the PSU choice (§4.1) and the firmware I_max stop (§9).

### 6.3 No alligator clips, and no keyed connector

**Clips are out.** A slipping clip can bridge terminals upstream of the fuse, and clips allow a reversed connection.

**The keyed connector is out too (rev 0.3).** The pack comes out of the UPS for every session, so its F2 tabs are reconnected every time, to the UPS harness and to this lead alike. A keyed connector on the charger would only move the joint where reversal can happen. It would never remove it.

The lead therefore ends in the fuse holder and insulated F2 female QDs (§5.3), and **RQ-6 is met by procedure** (§10.1), as it already is for the UPS's own battery connection.

What reversal would do: with the switch open, a reversed pack puts about −13 V on VBUS and the #5382 output [I]. Treat the INA228 and #5382 as damaged until proven otherwise. FW-3 refuses to start on a reversed or absent pack, because VBUS then reads ≤ 10.0 V. But the damage happens when the QD goes on, before any firmware runs.

### 6.4 Conductors

- **External lead:** 16 AWG, 4.016 mΩ/ft [S, standard AWG table, 20 °C].
- **Internal power path** (W3, W4, W6, W10–W12): 18 AWG, short runs. Board feeds and grounds (W5, W7–W9): 22 AWG.
- **Voltage drop** between VBUS and the pack terminals is I × R_series, where R_series = shunt (15 mΩ [S, Adafruit #5832]) + fuse + both lead conductors + splice + contacts. Measure it once at commissioning (T10). **The firmware does not use it (rev 0.5):** it publishes raw VBUS and I, and V_batt = VBUS − I·R_series is computed in InfluxDB/Grafana, where a revised R_series re-computes history. T10's value also splits FW-12's per-session edge resistance into series and pack parts.
- **Worked example**, lead alone: 5 ft each way of 16 AWG is 40 mΩ [D: 10 ft × 4.016 mΩ/ft], which drops 146 mV at 3.64 A [D]. The drop falls toward zero as the current tapers.

---

## 7. Board configuration — deltas from the bank-monitor build

The board pin map below is from `Battery_Bank-Monitor-THT-V2 - Rev_1.kicad_pcb`. It was cross-checked against the **fabricated copper**: the Gerber F_Cu X2 net attributes (exported 2026-06-25) give the same net on every pin used here, 62 attributed pads, none ambiguous [M, 2026-09-21]. The `.kicad_pcb` was saved after the Gerbers (06-26 22:03), so the Gerbers, not the board file, are the authority for what was built.

| Item | Bank-monitor build | **Charger build** | Why |
|---|---|---|---|
| INA228 onboard 15 mΩ shunt | removed | **KEEP** | It is the charger's shunt. At 3.64 A it drops 55 mV [D], inside the ±163.84 mV range [D: 312.5 nV × 2¹⁹, from `battery-bank-monitor.yaml`]. The board is sold for up to 10 A [S, Adafruit #5832 page] |
| Breakout VBUS jumper | open | **CLOSED** (VBUS = VIN+) | High-side use [S, Adafruit #5832 page]. U2 pin 5 (VBUS) is a carrier no-connect [M, Gerber net attribute N/C], so the closed jumper reaches nothing on the board |
| VBUS lead to busbar | fitted | **none** | VBUS comes from the jumper |
| **R3** (10 kΩ, GPIO4_BTN ↔ +3V3) | fitted | **DO NOT FIT: mandatory** | GPIO4 powers up high-impedance with no internal pull (reset state "1") and is not in the power-up glitch table [S, ESP32-C3 datasheet pp.20–21]. With R3 fitted, ON sits at 2.2 V [D: 3.3 × 20/30, where 30 kΩ = R3 10 kΩ + the #2814's on-board 20 kΩ] through every boot, watchdog reset and flash, above the ~1 V threshold, so **the charger turns on whenever the ESP32 is not running** |
| J2 (GPIO4_BTN / GND) | wake button | **#2814 ON control** (§5.2 W13, W14) | The only broken-out spare pin |
| TB1 feed | positive busbar | **WP (PSU +V), upstream of the switch** | Board alive whenever AC is on; zero battery drain when AC is off |
| TB2 (DS18B20) | battery case | **unused** (rev 0.5) | RQ-9 and RQ-11 are met by siting (§3). Enclosure temperature is the INA228 die (FW-10) |
| J1 (OLED) | fitted | **not fitted** | HA and the ESPHome web page show status; the status LED covers Wi-Fi down (FW-11) |
| ALERT (GPIO5, test point "ALERT") | alert input | **unused** | L4 withdrawn (§8) |
| F1 (1 A slow-blow, BATT_RAW → V_FUSED), U3 D24V7F3 | as built | unchanged | The D24V7F3 takes 4–36 V [[ws] §3.1], which covers the PSU's 22.5 V OVP ceiling [S] |

### 7.1 XIAO pin map (charger)

| XIAO | GPIO | Net | Charger function |
|---|---|---|---|
| D2 | GPIO4 | GPIO4_BTN → J2-1 | **Charge enable** output, active-high. Boot-safe only with R3 not fitted |
| SDA/SCL | GPIO6/7 | SDA/SCL | INA228 |
| D10 | GPIO10 | GPIO10_DQ | Unused (rev 0.5) |
| D7 | GPIO20 | GPIO20LED | Status LED (FW-11) |

### 7.2 Switch control net (off-board)

| Ref | Part | Connects | Purpose |
|---|---|---|---|
| Rs | *Withdrawn in rev 0.4* (owner, 2026-09-21) | — | GPIO4 drives ON directly. The board has no series position on this net: the fabricated copper puts only XIAO D2, R3 pad 1 and J2-1 on GPIO4_BTN [M, Gerber X2 net attributes, 2026-09-21], so the only alternative was a part inline in the wire. The §5.4 continuity check catches a swapped control pair before the first power, and FW-1's 5 mA drive strength limits what the pin pushes if one gets through. **Left uncovered:** +V touching the control wire. That would cost the socketed XIAO, and it turns the charger on whatever the firmware does. That is L6's case, the same as a shorted #2814 |
| — | *(on the #2814)* R4 10 kΩ + R5 10 kΩ | ON → R4 → Q3 base; R5 base → emitter (GND) | **The off-state pull-down, already on the board** [S, Pololu schematic]. With ON floating, R5 holds Q3's base at 0 V and the switch is off. That is Pololu's "leaving it disconnected will leave the switch off". GPIO4's input leakage, at most 50 nA [S, ESP32-C3 datasheet Table 14 p.32], gives at most 1 mV across 20 kΩ [D]. GPIO high drives ON to ~3.3 V at 0.17 mA [D: 3.3 V ÷ 20 kΩ], above the ~1 V threshold [S, §4.2]; R4/R5 halve it onto Q3's base-emitter junction |

> **Correction record (R13), 2026-09-21.** Rev 0.2 and the first draft of rev 0.3 specified an external **Rpd 10 kΩ** (ON → GND at the switch) to hold ON low with GPIO4 high-impedance, and gave ON = 3.0 V [D: 3.3 × 10/11]. Both were written before the switch's schematic was read. The board already has R4 + R5 = 20 kΩ from ON to GND, which does that job, so Rpd was redundant and the 3.0 V omitted the on-board resistors. The owner asked why Rpd was required, and the schematic answered it. Rpd was withdrawn (W15). T1 and T2 now prove the on-board pull-down. Evidence: Pololu "Big MOSFET Slide Switch with Reverse Voltage Protection" schematic (file 0J1071, ©2015), read 2026-09-21.

> **Correction record (R13), 2026-09-21.** Rev 0.3 (`34e4a52`) said the ESP32's leakage across the 20 kΩ was "microvolts". The datasheet's maximum input leakage is 50 nA [S, ESP32-C3 datasheet Table 14 p.32], which gives up to 1 mV [D]. The conclusion stands, because turn-on needs ~1 V, but the figure was wrong. It was found while answering the owner's question about Rs.

**Off at every reset: why GPIO4, and why R3 stays unfitted.** Power-on, an AC blip, a watchdog reset (L3), an OTA reflash or a crash each leave the ESP32 in ROM and the bootloader for a few hundred milliseconds before ESPHome drives GPIO4 low. In that window the hardware alone holds the switch off:

1. GPIO4 returns to reset state "1": input, high-impedance, no pull [S, ESP32-C3 datasheet pin table p.20, key p.21]. It is not in the power-up glitch table [S, Table 7 p.21].
2. With ON undriven, the #2814's R5 holds Q3's base at 0 V and the switch is open [S, Pololu schematic].
3. Leakage gives at most 1 mV against a ~1 V turn-on [D, above].
4. Only then does FW-1 drive GPIO4 low (`restore_mode: ALWAYS_OFF`), confirming a state the hardware already set.

No added part, no firmware and no resistor ratio is involved. Fitting R3 is the one way to break it (§7). T1 and T2 prove it on the hardware.

**GPIO20 (the status LED) is not an alternative control pin.** It resets in state "3", with its internal pull-up on [S, p.20–21]. That would lift ON to ~1.0 V at every reset [D: 3.3 × 20/66, with the pull-up at its typical 45 kΩ (Table 14), R4 1 kΩ and the #2814's 20 kΩ]. The datasheet gives that pull-up no minimum, so no added pull-down could be proven adequate on paper.

**The #2814 slide must be locked in OFF.** External ON control works only with the slide OFF: "if the physical switch is in the 'off' position, the switch state can also be controlled by a digital signal … via the 'ON' control pin" [S, #2814 page]. Glue or lacquer it.

---

## 8. Protection ladder

| Layer | What stops the charge | Catches | Does not catch | Proven by |
|---|---|---|---|---|
| L1 | Firmware normal end: time at voltage (FW-6) | normal completion | everything below | T11 |
| L2 | Firmware hard stops: VBUS ceiling, I_max, PSU overload beyond t_ol, T_max, INA228 loss, BMS-trip signature | PSU regulation fault, sensor faults, a pack that skipped the P20 | firmware logic error, hang | T4, T6–T8, T14 |
| L3 | ESP32 watchdog reset → GPIO4 high-impedance → the #2814's on-board R4 + R5 → OFF | CPU hang | logic error that keeps the loop alive | T3 |
| L4 | *Withdrawn in rev 0.3.* It was INA228 BOVL → ALERT → Dx → ON low. BOVL and the ALERT latch are registers the firmware writes at boot, and an INA228 power-on reset returns them to defaults, so L4 was armed only by the firmware it backed up. L2 (gated by T4 on every firmware edit), L6 and L7 stand behind the same fault | — | — | — |
| L5 | `restore_mode: ALWAYS_OFF` | auto-resume after a blip or reboot | — | T9 |
| L6 | AC **countdown timer** (standalone, no network) | everything electronic, **including a #2814 failed short** | nothing inside its time | T12 |
| L7 | The pack's own BMS (OVP/OCP) | last resort | — | not tested (inside the pack) |
| L8 | Battery-end fuse (§6) | battery-fed faults in the lead or enclosure | over-charge (a fuse is not a limiter) | continuity only |

Pololu's own caveat: *"Do not use this switch as an emergency cutoff or similar safety disconnect in applications where failure to cut power could lead to injury or property damage."* [S, Pololu #2814 page]. MOSFETs usually fail shorted. **The #2814 is the operational stop; L6 and L7 are the safety layers.** L6 ends everything only because the ideal diode stops the pack keeping the board alive (§5).

**Not watched (rev 0.5): the pack's temperature.** With the DS18B20 dropped, a cell heating during the hold is bounded only by T_hold/T_max (FW-6, FW-4), L6 and L7. Accepted with RQ-9/RQ-11's siting.

---

## 9. Firmware requirements (new firmware; not written)

This is a new, small configuration, **not** `battery-bank-monitor.yaml`. It is gated by the `esp-firmware-validation` skill (real compile, `src/main.cpp.o` 0 errors), compiled on the Device Builder add-on's ESPHome version.

**States:** IDLE → CHARGING → DONE | FAULT(reason). DONE and FAULT are latched until acknowledged.

| ID | Requirement |
|---|---|
| FW-1 | Enable switch on GPIO4, `restore_mode: ALWAYS_OFF`, **`drive_strength: 5mA`**. Only the state machine drives it. ON needs 0.17 mA [D: 3.3 V ÷ 20 kΩ], so the weakest setting drives it fully and pushes less into a swapped or shorted control wire. The options are 5, 10, 20 (default) and 40 mA on esp-idf [S, esphome.io pin schema], which the bank firmware already uses. The 5 mA is ESPHome's nominal label; the datasheet characterises only the 40 mA setting [S, Table 14], so the dead-short current is [I] |
| FW-2 | *Withdrawn in rev 0.3* (profile select; bank deferred) |
| FW-3 | Start preconditions: VBUS (switch open) > 10.0 V (Cyclenbatt BMS UVP [[supplemental-analysis.md](../docs/supplemental-analysis.md)]) and **< V_hold**; no latched fault. A reversed or absent pack reads ≤ 10.0 V and is refused. **Why V_hold, not 14.60 V (rev 0.5):** the pack arrives from the P20's 14.6 V absorb [listing] resting above V_hold. Started there, the diode blocks (I = 0) while VBUS ≥ V_hold, and FW-6 would count the pack's own relaxation as time at voltage, so a session could reach DONE having delivered nothing. Counting time only while I > 0 would not fix it: a balanced pack with no balancer legitimately decays toward 0. **Write the test so NaN refuses:** `v > 10.0 && v < V_hold`, never `!(v <= 10.0)` |
| FW-4 | **Hard stops** (any one → switch OFF, FAULT latched): **raw VBUS > 14.60 V** on one averaged sample; I > I_max = 5.0 A (RQ-1); **I > 2.0 A for longer than t_ol → FAULT "overload: pack not pre-charged"** (RQ-12; 2.0 A is the PSU's rated current [S, HDR-30-SPEC p.2], t_ol from T11); session time > T_max; INA228 read failure or NaN on **one** read. **N = 1 (rev 0.5):** §1 clause 2 allows one sample period unobserved, and a missed read is that period; a glitch costs a session, the same safe-direction trade §9 accepts for false trips. The overload stop also enforces §10.1: a pack that skipped the P20 is refused within t_ol instead of holding the PSU in overload |
| FW-5 | **BMS-trip signature:** current falls from charging to ~0 within one sample while VBUS sits at the source voltage → OFF, FAULT "BMS trip", and publish the **raw VBUS and I of the last sample before the step** (V_batt is computed downstream, §6.4). A plain "at voltage and I < tail" rule would read this as "full". This is the first per-cell evidence the sealed pack can give. With a per-cell cutoff V_ovp, a trip at V_batt puts the other three cells at an average of (V_batt − V_ovp)/3 [D]. V_ovp is undocumented for this pack (O7), so the figure stays a formula. **A blown fuse or a QD pulled off gives the same signature**: check continuity before reading it as a BMS trip. If the pack is uneven, session 1 may end here rather than in DONE. That is a designed-for outcome, not a failure. **Thresholds (rev 0.5):** "charging" and "~0" have no values yet. At the tail the step is at most the tail current, so both are set from T11 (O5). Resolution is not the limit: 20.8 µA per shunt LSB [D: 312.5 nV ÷ 0.015 Ω] |
| FW-6 | **Normal end: time at voltage.** Accumulate time with VBUS ≥ V_hold; at T_hold → OFF, DONE. **Log the current throughout and do not act on it.** A taper rule (I < I_tail) could fail to fire precisely when a balancer is bleeding and holding the current up (§2), ending a working session as a T_max FAULT. V_hold, T_hold and T_max are **TBD from T11**. T_hold is bounded by how long the owner accepts the host running with no backup (§10.2) |
| FW-7 | **V_SET = 14.40 V**, inside the Cyclenbatt's 14.4–14.6 V (RQ-10). Dropping the bank removed rev 0.2's reason (the bank's 14.58 V peak), but 14.40 V stays: it is the bottom of RQ-10, and the whole window to the 14.60 V ceiling is the false-trip margin (below). It sits below the P20's 14.6 V absorb [listing], so the hold adds time at balancing voltage, not a further push |
| FW-8 | Sampling ≥ 1 Hz while charging. INA228 averaging window ≥ one 120 Hz ripple period (8.3 ms [D: 1 ÷ 120 Hz]); one conversion cycle is "one sample period" for §1 clause 2. **ESPHome's defaults miss this (rev 0.5):** its INA2xx driver always converts bus, shunt and die temperature (MODE 0x0F [M, source read, ESPHome 2026.8.2 `ina2xx_base.cpp:344`]), and its defaults of 4120 µs × 128 averages give a 1,582 ms cycle [D: 3 × 4.120 ms × 128]; the bank firmware logged the same ~1.58 s cycle in V1.12. FW-10 pins the settings. Termination and stops are local; HA is not in the loop. **`reboot_timeout: 0s` on both `api:` and `wifi:`** (both default to 15 min [S, esphome.io `api` and `wifi` component pages, read 2026-09-21]): a mid-session reboot is safe (FW-1) but discards the session's Ah count, the Open Item 16 measurement. Because ESPHome notes that a full reboot is sometimes needed to recover Wi-Fi [S, `wifi` page], add an interval check that reboots after 15 min without an API client **only while IDLE** |
| FW-9 | Publish to HA: raw VBUS, I, P, Ah this session, time at voltage, state, fault reason, the INA228 die temperature (enclosure; report-only), FW-5's pre-step VBUS and I, and FW-12's edge values. **No V_batt and no R_series in firmware** (rev 0.5, §6.4). **Session Ah is the INA228's hardware CHARGE register**, not a sum in a lambda (R10): ESPHome publishes it (`charge:`, INA228/229 only) and `reset_energy_counters()` zeroes it at Start [M, source read, ESPHome 2026.8.2 `ina2xx_base/__init__.py:74`, `ina2xx_base.cpp:237`]. An INA228 power-on reset also clears it, but that reset ends the session anyway (FW-1). Hold session Ah, FW-5's pre-step VBUS and I, and the end reason in `restore_value` globals, written once at DONE/FAULT, so a later reboot does not lose them. Controls: Start/Stop, fault acknowledge |
| FW-10 | INA228 at boot: shunt 0.015 Ω; ADC range ±163.84 mV; **`adc_time: 1052us`, `adc_averaging: 64`** → 67.3 ms per channel [D: 1.052 ms × 64], above FW-8's 8.3 ms, and a 202 ms cycle [D: 3 × 67.3 ms], inside FW-8's 1 s. Both are valid settings [S, TI INA228 datasheet SLYS021A pp.23–24]. Publish `temperature:` (the die): ±1 °C max at 25 °C, ±2 °C max over −40…+125 °C [S, SLYS021A p.6]. It reads the breakout, which carries the 15 mΩ shunt (0.199 W at 3.64 A [D: 3.64² × 0.015]), so it runs above the enclosure air while current is high [I; falsifier: in T0 it does not move with current]. The XIAO's own sensor is not used: Espressif gives it no accuracy figure and says it reads "higher than the operating ambient" [S, ESP32-C3 datasheet v1.2 §3.3.2 p.19]. No BOVL or ALERT configuration (L4 withdrawn) |
| FW-11 | **Status LED (GPIO20)**, the only local indicator when Wi-Fi is down. IDLE: one short blink every 3 s. CHARGING: 500 ms on / 500 ms off; a hung CPU freezes it on or off. DONE: two short blinks every 3 s. FAULT: 4 Hz |
| FW-12 | **Edge resistance, both switch edges, every session (rev 0.5).** In the same loop pass, capture VBUS and I from the last sample before the edge and from the first full conversion after it (discard the conversion that straddles the edge), and publish both pairs. R_edge = ΔVBUS ÷ ΔI = R_series + the pack's ohmic resistance + whatever polarisation relaxes within one conversion [I; falsifier: session-to-session scatter too large to trend]. Computed downstream, not in firmware. **The pairing must be done here:** HA writes VBUS and I to InfluxDB as separate state changes with their own timestamps, the problem UPS firmware V1.20's paired V/I blocks fixed (UPS Open Item 21). The ON edge carries the session's largest current; the OFF edge carries the tail. Both happen on a full pack indoors, so conditions repeat session to session. Hold FW-10's conversion settings fixed, or the trend breaks |

**Voltage ceiling: 14.60 V on raw VBUS, not on compensated V_batt.**

- **Why raw VBUS is never later.** Charge current flows from VBUS through the shunt and lead into the pack, so V_batt = VBUS − I·R_series. The ideal diode holds I ≥ 0 (§5), so V_batt ≤ VBUS: whenever V_batt exceeds the ceiling, VBUS already has.
- **Why compensation would be worse.** A compensated trip with R_series set too high would read low and fire late, which is the unsafe direction. Tripping on raw VBUS takes a hand-measured constant out of the safety path.
- **False trips are possible and are safe-direction.** In normal operation VBUS ≤ the PSU output, which the datasheet bounds at 14.40 V + 144 mV tolerance + 108 mV drift + 60 mV ripple peak = **14.712 V worst case** [D, §4.1, for an assumed 25 °C rise]. That is above the 14.60 V ceiling. A false trip stops the charge and latches FAULT: it costs a session, not safety. Near the end of charge the current is small, so a compensated trip would have the same exposure.
- **How the margin is established.** T0 measures the real unit warm, T4's no-trip direction runs a full warm session, and FW-8's averaging removes ripple. T0 also logs the INA228 die temperature, which replaces the assumed 25 °C rise with a measured one: the temperature coefficient is specified against ambient, 0–50 °C [S, HDR-30-SPEC p.2].

---

## 10. Procedures

### 10.1 Every session

1. **Remove the pack from the UPS by OP-1**: battery last-off, first-on; EN jumpered low across any battery connection [[boost-subsystem-design.md](../UPS-Monitor/boost-subsystem-design.md) §9]. From this point the host has no backup.
2. **Charge it to full on the P20** (§4.3): LiFePO4 mode, **5 A** (RQ-1). The P20 does not turn off: when it reaches trickle, disconnect it.
3. Countdown timer **OFF** (AC dead).
4. **Polarity check, then connect:** read the pack's + and − markings, then push the **black** QD onto **−** and the **red** (fused) QD onto **+**. Re-read both before step 5 (RQ-6).
5. Set the timer to T_max plus a margin, and switch it on. The board boots with the switch **OFF**, and the LED shows IDLE.
6. In HA or on the ESPHome web page, check VBUS. Fresh off the P20 the pack rests above V_hold, and FW-3 refuses Start until it falls below V_hold (and at or below 10.0 V). Wait for it, then press **Start**.
7. The session ends by itself (DONE or FAULT). Then set the timer **OFF** and remove the red QD, then the black.

### 10.2 Returning the pack to the UPS (RQ-7)

- **Before reconnecting**, read the pack's rest voltage. A freshly topped pack rests above the 13.3 V float [I]. Bleed it to ≤ 13.3 V so the bus stays inside the XB7's validated envelope. Falsifier: the UPS INA260 bus reading right after reconnection. **The bleed load and method are not yet named (O8).**
- Reinstall by OP-1.
- The P20 and this charger are used indoors, in conditioned space (RQ-9, RQ-11). No sensor checks it.
- **Success measure:** the matched-load LVD-to-LVD capacity test, before and after (UPS Open Item 14a).
- The host has no backup from step 1 of §10.1 until reinstall, which now spans the P20 charge, the rest before Start and the hold. T_hold (FW-6) trades balancing time against that window. **That trade is the owner's call.**

### 10.3 Bank

*Withdrawn in rev 0.3*; the bank is deferred (§2).

---

## 11. Commissioning tests — both directions (R2 / R7)

Run T1–T9 and T14 on a **resistive load, no battery**: **10 Ω, ≥ 25 W**, 1.44 A at 14.4 V [D: 14.4 V ÷ 10 Ω], 20.7 W [D: 14.4² ÷ 10], inside the PSU's 2.0 A rating (RQ-12). Each fault test must **fire**, and the clean run must stay **silent**. In every test, the LED pattern must match the state (FW-11).

> **Correction record (R13), 2026-09-22.** Rev 0.4 specified a 5 Ω load, which draws 2.88 A [D: 14.4 V ÷ 5 Ω], above the PSU's 2.0 A rated current [S, HDR-30-SPEC p.2]. Every commissioning test would have run the PSU in its overload fault mode, and if the unit's limit sat below 2.88 A, T0 would have measured a current-limited VBUS instead of the regulation margin. Found while writing RQ-12.

| # | Inject | Must | Silent direction |
|---|---|---|---|
| T0 | — | Trim V_SET = 14.40 V at the PSU terminals, output open, cold. Run the resistive load 30 min with the box closed; log the highest averaged VBUS. Stop, and within 1 min re-read the PSU output open-circuit. **Record the margin, 14.60 V − highest VBUS [M]**, and the INA228 die temperature's rise over the run (§9). If it is under 60 mV [D, ripple peak §4.1], stop: RQ-10 leaves no room to move either number. Lacquer the trimpot | — |
| T1 | Power up with the XIAO **removed** from its socket | Load current 0; ON < 1 V | — |
| T2 | Hold RESET; reflash OTA; power-cycle | ON < 1 V throughout (scope the ON node) | Commanded ON conducts |
| T3 | Test build: infinite loop in a lambda while charging | Watchdog reset → OFF | Normal build runs a full session |
| T4 | Test build: ceiling below V_SET | OFF, FAULT "over-voltage" | Production ceiling (14.60 V): a full **warm** session on the load with no trip |
| T5 | *Withdrawn in rev 0.3* (L4) | — | — |
| T6 | Test build: I_max below the load current | OFF, FAULT "over-current" | — |
| T7 | Unplug the INA228 breakout mid-session; then boot with it unplugged and press Start | OFF, FAULT "sensor"; Start refused (NaN, FW-3) | — |
| T8 | Test build: T_max = 1 min | OFF at 1 min | — |
| T9 | Pull AC mid-session, then restore | Stays OFF | — |
| T10 | On the pack, at a steady known current | DMM at the pack terminals vs VBUS → **R_series** (analysis only: V_batt downstream, and FW-12's split, §6.4) | — |
| T11 | First **supervised** session, on a pack fresh off the P20 | Log the current at 14.40 V (the balancer question, §2); set V_hold, T_hold, T_max, t_ol (how long the opening current stays above 2.0 A) and FW-5's thresholds; note how long the pack takes to rest below V_hold. Session 1 may end in an FW-5 trip | — |
| T12 | Let the countdown timer expire mid-session | Everything dark: LED off, pack current 0. This proves the ideal diode stops the pack keeping the board alive (§5) | — |
| T13 | *Withdrawn in rev 0.5* (DS18B20 dropped) | — | — |
| T14 | Test build: overload threshold below the load current | OFF after t_ol, FAULT "overload" | Production threshold (2.0 A) on the 10 Ω load: a full session, no trip |

Any firmware edit re-runs T1–T4, T6–T9 and T14 (R7: a gate untested against a known-bad input is not a gate).

---

## 12. Open items

| # | Item | Status |
|---|---|---|
| Q1 | Cyclenbatt label: charge voltage, charge temperature range, and does the BMS balance? | **Answered 2026-09-21:** 14.4–14.6 V; charge above 32 °F; no balance details |
| Q2 | Does the Cyclenbatt label give an **upper** charge temperature? | **Answered 2026-09-22:** none on the label. RQ-11 is met by siting |
| Q3 | Is the on-hand 5 A fuse a mini (ATM/APM) or a regular (ATC) blade, and whose make? | **Answered 2026-09-22:** mini (ATM/APM), from an AKOSN assortment kit with no maker's datasheet (O2) |
| Q4 | Which 3-stage charger does the bulk charge, and what are its LiFePO4 voltage, current and end-of-charge behaviour? | **Answered 2026-09-22:** Dylannet P20 at 5 A (§4.3) |
| O1 | Charge current limit | **Closed:** 0.5 C = 5.0 A, owner 2026-09-21 |
| O2 | A fuse whose DC interrupt rating can be cited | The AKOSN kit fuse has no datasheet, so RQ-5 is unproven with it. Buy a branded 5 A mini fuse whose maker publishes a DC interrupt rating, then cite it |
| O3 | HDR-30 overload below 50% Vout (hiccup) | **Closed 2026-09-22:** hiccup below 50% of rated output voltage, constant-current limiting from 50% to 100%, both "recover automatically after fault condition is removed" [S, p.2] (§4.1) |
| O4 | Charger firmware | Not written; FW-1 and FW-3…FW-12 are the spec. The ESPHome facts in FW-8…FW-10 were read in the 2026.8.2 source: re-check them on the Device Builder add-on's version before the compile gate |
| O5 | V_hold, T_hold, T_max, t_ol, FW-5's step and floor thresholds | Set from T11. T_hold is also bounded by the host's no-backup window (§10.2) |
| O6 | Enclosure | ABS, vented, DIN rail offcut, cord grips G1–G2, lever nuts fixed in place. The XIAO's U.FL antenna needs an RF-transparent box [[ws] §8.2, item J] |
| O7 | [component-selection.md](../docs/component-selection.md) gives 14.4–14.6 V as the BMS **over-voltage cutoff**. The label gives that range as the **charge voltage**, so the BMS cutoff value is undocumented [I: a maker would not rate charging at its own cutoff] | Correct that doc (now in this repo); this one does not rely on it |
| O8 | §10.2 bleed to ≤ 13.3 V | No load or method named |
| O9 | INA228 breakout 3.5 mm terminal block wire range | Adafruit lists none; confirm 18 AWG fits (W11, W12) |
| O10 | UPS Open Item 16, a coulomb-counted recharge to termination | **Not served since rev 0.5:** the P20 does the bulk charge and counts nothing. The owner's call whether to serve it another way |

---

## 13. Purchase list

| Item | Price / note |
|---|---|
| Mean Well **HDR-30-15** | $13.50 (Arrow) to $17.76 (TRC), from search listings on 2026-09-21, not read on the vendor pages |
| Pololu **#2814** Big MOSFET Slide Switch, MP | $5.49 [S, Pololu page, 2026-09-21]. Ships with 5 mm terminal blocks and 0.1″ headers |
| Plug-in countdown timer (mechanical or standalone digital, **no Wi-Fi**) | L6 |
| ABS enclosure, vented; DIN rail offcut; 2 cord grips | O6 |
| JST-XH 2-pin housing with crimps | J2 cable, if not on hand |
| One 16–14 AWG heat-shrink butt splice | S1, if not on hand |
| 16 AWG red/black; 18 AWG red/black; 22 AWG red/black; a 24–26 AWG pair; 2-conductor AC cord | if not on hand |
| Branded 5 A mini (ATM) blade fuse with a published DC interrupt rating | O2. Not priced here |
| 10 Ω, ≥ 25 W resistor | Commissioning load (§11), if not on hand |
| Two 2-pin 5 mm terminal blocks for the #5382 | The UPS order bought 4 [[bom.md](../docs/bom.md)]; otherwise solder |

**On hand** [owner, 2026-09-21 and 2026-09-22]: the inline fuse holder and an AKOSN mini-blade kit (no datasheet, O2); F2 female spade QDs; Wago 3- and 5-position lever nuts; the Dylannet P20 (§4.3). From rev 0.2: a V2 Rev 1.1 board and parts, XIAO ESP32-C3, Adafruit INA228, DS18B20 module (unused from rev 0.5), and the spare Pololu #5382 (bought as a pair, one used [[bom.md](../docs/bom.md)]).

**Budget: $43** [owner]. PSU + switch + Pololu shipping comes to $25.44–$29.70 [D: 13.50 or 17.76, + 5.49 + 6.45; the $6.45 is the UPS order's Pololu USPS charge in [bom.md](../docs/bom.md), not a current quote]. That leaves $13.30–$17.56 [D] for the PSU's shipping, the timer, the enclosure, the cord grips and the replacement fuse.

---

## 14. Sources

- Mean Well HDR-30-SPEC and HDR-60-SPEC, both "File Name … 2026-04-03": p.2 (spec table, including tolerance, temperature coefficient, ripple, overload; the overload row read in full by layout-preserving extraction 2026-09-22), p.3 (derating curve), p.4 (terminal assignment; use the unit's silk for pin numbers).
- Pololu product pages #2814 and #2815 (Big MOSFET Slide Switch with Reverse Voltage Protection, MP / HP: comparison table, ON-pin behaviour, prices), and the [Big MOSFET Slide Switch schematic](https://www.pololu.com/file/0J1071/big-mosfet-slide-switch-schematic-diagram.pdf) (©2015: ON → R4 10 kΩ → Q3 base, R5 10 kΩ base-emitter; MP D2 = 16.2 V) and #5382 (ideal diode, LM74700-Q1; VIN / VOUT / GND pads), read 2026-09-21.
- Adafruit #5832 product page (INA228 breakout: 15 mΩ shunt, up to 10 A, VBUS jumper, 3.5 mm terminal block), read 2026-09-21.
- esphome.io `api` and `wifi` component pages: `reboot_timeout`, read 2026-09-21.
- Espressif ESP32-C3 Series Datasheet ([copy in this repo](../UPS-Monitor/esp32-c3_datasheet.pdf)), pp.20–21: IO MUX reset states and power-up glitch table; §3.3.2 p.19: the internal temperature sensor (why it is not used).
- TI INA228 datasheet SLYS021A (January 2021, revised May 2022): p.6 (temperature sensor accuracy), pp.23–24 (conversion times, averaging counts).
- ESPHome 2026.8.2 source, `components/ina2xx_base/` (`__init__.py`, `ina2xx_base.cpp`): conversion mode, defaults, `charge:`, `reset_energy_counters()`. Read locally; the add-on's version governs (O4).
- Seller listings, read 2026-09-22: Dylannet P20 charger (Amazon B0BM9H759L) and AKOSN mini-blade fuse kit (Amazon B0DNC57LR9). Cited as [listing], not [S].
- This repo: [09-15 survival-test README](../data/2026-09-15_full_discharge_survival_test/README.md), [component-selection.md](../docs/component-selection.md), [boost-subsystem-design.md](../UPS-Monitor/boost-subsystem-design.md), [bom.md](../docs/bom.md), [wiring.md](../docs/wiring.md), [supplemental-analysis.md](../docs/supplemental-analysis.md).
- `Lifepo4-Battery-Banks`: [bank-monitor wiring summary v1.10][ws] (board connectors, first-flash rule, DS18B20 module), `INA228 Monitor/battery-bank-monitor.yaml`, and rev 0.2 of this document (commit `680caed`).

---

## 15. Revision history

| Rev | Date | Change |
|---|---|---|
| 0.2 | 2026-09-21 | In `Lifepo4-Battery-Banks/Top-Off Charger/` (`680caed`). Two packs (UPS P1, bank P2); HDR-30-15; #2815; L4 via INA228 ALERT; keyed connector and fused pigtails; OLED optional |
| 0.3 | 2026-09-21 | Moved to this repo. **Scoped to the UPS pack**, with the bank deferred (§2; RQ-8, FW-2 and §10.3 withdrawn). **Voltage ceiling on raw VBUS**, with R_series used for reporting only; the margin is checked against the PSU's datasheet regulation (§9). **L4 withdrawn**, with Dx, W15, T5, BOVL and ALERT handling removed. **OLED dropped**, and the status LED is specified (FW-11). **Keyed connector and pigtail dropped**: the lead ends in the fuse and F2 QDs, and RQ-6 becomes procedural (§6.3). **#2815 → #2814** (§4.2, with an R13 correction record). **Normal end is time at voltage**, with the current logged, not acted on (FW-6). **`reboot_timeout: 0s`**, with an IDLE-only recovery reboot (FW-8). Wago splice nodes and a from/to wiring table (§5). Rs moved to the J2 end. **Rpd withdrawn**: the #2814 has its own 20 kΩ pull-down on ON (§7.2, with an R13 correction record). RQ-11 added (blocked on Q2) |
| 0.4 | 2026-09-21 | **Rs withdrawn** (owner): GPIO4 drives ON directly. A pre-power continuity check (§5.4) and a 5 mA drive strength (FW-1) cover a swapped control pair. §7.2 records the off-at-reset chain and why GPIO20 is not an alternative. The R3 figure is updated (2.2 V). **Leakage figure corrected**, from "microvolts" to ≤ 1 mV (R13, §7.2). Status LED kept (FW-11) |
| 0.5 | 2026-09-22 | **Bulk charge moves to the owner's Dylannet P20 at 5 A** (§4.3); this charger does the top-balance hold only. **RQ-12 and the FW-4 overload stop** keep the HDR-30-15 inside its 2.0 A rating (R13 correction record in §4.1: overload is a fault condition, and rev 0.4 used it for bulk). **DS18B20 dropped**: RQ-9 and RQ-11 met by siting indoors; W19, TB2, GPIO10 and T13 withdrawn; the INA228 die temperature is published for the enclosure (FW-10). **R_series out of the firmware**: raw VBUS and I published, V_batt computed downstream (§6.4); FW-12 records the edge resistance every session. **FW-3 refuses Start above V_hold** (a pack fresh off the P20 would be counted as time at voltage) and on NaN. **FW-4 read failure N = 1.** **FW-8/FW-10 pin the INA228 conversion** (ESPHome's defaults give a 1.58 s cycle). **Session Ah from the INA228 CHARGE register** (FW-9). **Commissioning load 10 Ω** (R13 correction record in §11: rev 0.4's 5 Ω overloaded the PSU). O3 closed; Q2–Q4 answered; O10 added (Open Item 16 no longer served); the fuse needs a branded replacement (O2) |
