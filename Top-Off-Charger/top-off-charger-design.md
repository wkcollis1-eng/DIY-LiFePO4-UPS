# LiFePO4 Top-Off / Top-Balance Charger — Design

**System:** bench top-balance hold charger for the UPS's Cyclenbatt 12V 10Ah. **The pack is removed from the UPS for every session** [owner, 2026-09-21], **charged to full on a Dylannet P20 at 5 A, then held at 14.40 V here** [owner, 2026-09-22; §4.3, §10.1].
**Controller:** the **Top Off Charger PCB** (`Top Off Charger- Oct 2026.kicad_pcb`, §7), one 2-layer board carrying the XIAO ESP32-C3, Adafruit INA228 (#5832), Pololu #2814 switch, Pololu #5382 ideal diode, Pololu D24V7F3 buck and the status LED. It replaces rev 0.5's second build of the bank-monitor board and its Wago-spliced wiring. The bank-monitor build is still cited for the rules that carry over ([wiring summary v1.10][ws], cited below as **ws**).
**Document revision:** 0.8 — **pre-build design draft, 2026-10-08.** The board is laid out (rev 0.7: re-laid smaller, 29.5 × 78 mm, with a Kelvin GND for the INA228; rev 0.8: the power path widened and VIN+ moved to B.Cu), with DRC at 0 errors, 34 warnings (all silk or library) and 0 unconnected. Schematic parity did not run (§7). It is not fabricated, and nothing here is built or tested. Scoped to the UPS pack and moved here from `Lifepo4-Battery-Banks/Top-Off Charger/` (rev 0.2 is commit `680caed` in that repo). Changes are listed in §15.
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

POWER PATH  (charge current, ≤ 3.64 A)      ── board copper ──────────────────────────────────────────────────────────────────────
HDR +V ─► TB1-2 ═BATT_RAW═► U4 #2814 VIN ~ VOUT ═Batt_SW═► U5 #5382 VIN ~ VOUT ═VIN+═► U2 INA228 VIN+ ═15 mΩ═ VIN− ═VIN−═► TB2-1 ─ G2 ─► S1 ─► 5 A FUSE ─► F2 QD ─► pack +
HDR −V ◄─ TB1-1 ◄══════════════════════════════════ GND pour (both layers) ═══════════════════════════════════════ TB2-2 ─ G2 ──────────────────► F2 QD ─► pack −

BOARD SUPPLY (upstream of the switch)
BATT_RAW ─► F1 1 A slow-blow ═V_Fused═► U3 D24V7F3 ═+3V3═► U1 XIAO 3V3 · U2 INA228 VCC

CONTROL  (on-board traces)
U1 D2 (GPIO4) ═GPIO4_SW═► U4 pin 1 ON   (direct; the #2814's own R4 + R5 = 20 kΩ to GND holds it off)
U1 D1 (GPIO3) ═GPIO3═► R1 1 kΩ ═GPIO3_LED═► LED anode;  LED cathode ─► GND      (status LED, §5.5)
U1 SDA / SCL ═► U2 SDA / SCL

#2814 slide: LOCKED in OFF.  INA228 VBUS jumper: CLOSED.  GPIO4_SW: NO pull-up (the board has no position for one; never add one, §7.2).
```

The order of the power path is deliberate:

- **Switch → ideal diode → shunt.** The switch interrupts forward current. The shunt sees only battery current, not the board's supply.
- **The ideal diode** blocks the battery from back-feeding the PSU (the job it already does in the UPS [[bom.md](../docs/bom.md)]). It does two further jobs here:
  - **It makes L6 end everything.** The board is fed from the PSU side of the switch. Without the diode, AC loss with the switch ON would let the pack back-feed through the switch into the board. The ESP32 would stay up and hold the switch on, and the pack would drain into the PSU output with nothing to stop it. T12 proves this.
  - **It guarantees I ≥ 0 through the shunt.** The VBUS ceiling trip (§9) relies on this.
- **The board is fed upstream of the switch**, from the PSU side (BATT_RAW → F1 → U3). It is alive whenever AC is on, draws nothing from the battery when AC is off, and keeps reading the pack while the switch is open.
- **VBUS is on the battery side.** With the switch open, VIN+ is tied to the battery through the idle shunt, so VBUS reads the pack's open-circuit voltage before every start.
- **The ground is the pour, not a star (rev 0.6).** Rev 0.5 made the [WG] lever nut a ground star, so charge current never flowed in the conductor the INA228 measures VBUS against. On the board, pack − (TB2-2) and HDR −V (TB1-1, rev 0.7) both land on the GND pour. The INA228's GND (U2 pin 2) is not on the pour (the owner's 2026-10-06 17:09 save): it is its own net, GND_SENSE, a 0.5 mm track to a net tie on TB2-2's pad. This is a Kelvin connection (§7.3). The charge return therefore no longer crosses copper shared with the INA228's reference, and **VBUS reads high by ≤ 0.20 mV at 3.64 A** [D, §7.3]. Before the Kelvin connection it read high by 0.376–0.382 mΩ × I, 1.37–1.39 mV at 3.64 A. High is the safe direction for the 14.60 V ceiling (§9). It is zero before every start (I = 0, FW-3), and T10 measures it as part of R_series.

### 5.1 Terminal blocks (rev 0.6: replaces the splice nodes)

The rev 0.5 lever nuts WP, WG and WL are gone: their joints are board copper now. Only four wires land on the board, on two 2-position 3.81 mm screw terminals: **Phoenix Contact BC-381X9-2 GN, item 5442756** (owner, 2026-10-06; it is the board's Value field) [S, Phoenix product page for 5442756, owner-supplied text, 2026-10-06]. Its body (7.62 × 7.3 mm, 1.1 mm hole) matches the footprint, `TerminalBlock_Phoenix_MKDS-1-2-3.81_1x02_P3.81mm_Horizontal` (7.61 × 7.3 mm, 1.1 mm drill) [M, board file]. Directions below assume the board is held **component side up, with the INA228 end at the top** (the TB2 end; KiCad's y = 20 mm edge in rev 0.7).

| Block | Pin | Pad | Silk | Net | Wire landed | Which screw |
|---|---|---|---|---|---|---|
| **TB1** (PSU in) | 1 | round | `GND` | GND | W6 from HDR **−V** | the **upper** screw, nearer the XIAO |
| | 2 | square | `+` | BATT_RAW | W3 from HDR **+V** | the **lower** screw, nearer F1 |
| **TB2** (pack lead) | 1 | square | `+` | VIN− (the shunt's low side) | W16, lead **+** | the **right** screw, nearer the board centre |
| | 2 | round | `GND` | GND | W18, lead **−** | the **left** screw, nearer the left edge |

[M, board file saved 2026-10-06 15:16:19 (rev 0.7 layout), pad nets, shapes and positions. **Rev 0.7 swapped TB1's pins** (owner, 2026-10-06: intentional): BATT_RAW moved from pin 1 to pin 2 and GND from pin 2 to pin 1, so `+` is now the **lower** screw. The square pad stayed with `+`. TB2 is unchanged.]

- **TB1's wires enter from the board's left edge**; **TB2's from the top edge**, so the lead leaves the box that way without a hard turn (owner, rev 0.6 layout; both blocks keep their rev 0.6 rotations in rev 0.7 [M]).
- **Rev 0.8: TB1's labels can be read with U4 seated** (O14). TB1 moved 4.5 mm down, its pads now at y 68.5 and 72.31 [D: rev 0.7's + 4.5]. `GND` is at (16.5, 66.0), above the upper screw, and `+` at (17.0, 74.5), below the lower one, both left of U4's outline at x 20.7 [M, board file 2026-10-08 10:48:22]. The screw order is unchanged: **lower screw `+`**.
- **Rev 0.7: TB1's `+` and `GND` silk sat under the #2814.** `GND` is at (22.5, 66.0) mm and `+` at (21.5, 67.5), both inside U4's outline (x ≥ 20.7 mm), so a seated #2814 hides them [M, board file 2026-10-06]. `GND` also sits midway between the two screws (pads at y 64.0 and 67.81). Read them before U4 goes in, or go by the table: **lower screw `+`** (O14).
- **TB2-1's screw is under the INA228.** TB2's `+` silk (20.0, 29.5) and pin 1 (x 20.6) are inside U2's outline (x ≥ 18.5 mm) [M], and the module sits ~10 mm up (owner) over an 8.5 mm block [S]. **Land and torque W16 and W18 before seating U2**, and unseat U2 (AC off) to re-land them. `GND` (15.5, 30.0) is clear. Rev 0.8 leaves TB2 and its `+` where they were, and moves `GND` to (15.5, 29.5), still clear [M].
- **Landing the wires** [S, Phoenix 5442756 page]: 26–16 AWG (to 1.5 mm²), so 16 AWG at TB2 and 18 AWG at TB1 are in range. Strip 5 mm. Torque 0.22–0.25 Nm, holding the housing while tightening. Ferrules are listed only up to 0.5 mm², so land 16 and 18 AWG bare. Do not tin the strands [I: solder creeps under clamp pressure and the joint loosens; general practice, not on the Phoenix page]. Rated 13.5 A (UL 10 A), above the 3.64 A transient (§6.4).
- **Nothing on the board blocks a reversed TB1.** BATT_RAW has no diode or protection part [M, netlist §7]. The #2814 has its own reverse-voltage protection [S, product name, §14], but F1's branch feeds C4 and U3 directly. Check polarity before first power (§5.4).

### 5.2 From/to — inside the enclosure

| W# | From | To | Wire | Termination / notes |
|---|---|---|---|---|
| W1 | AC cord, **hot** conductor (smooth jacket; narrow blade on a polarized plug) | HDR-30-15 **AC/L** | 2-conductor cord, through cord grip **G1** | HDR screw terminal. The cord's plug goes into the countdown timer |
| W2 | AC cord, **neutral** conductor (ribbed jacket; wide blade) | HDR-30-15 **AC/N** | same cord | HDR screw terminal |
| W3 | HDR-30-15 **+V** | board **TB1-2 (BATT_RAW, `+`)** | 18 AWG red | HDR screw terminal → TB1 **lower** screw (§5.1; rev 0.7 moved it). Feeds the power path and, through F1 (1 A SB), the board supply. PSU-fed only: the ideal diode keeps the pack off it (§5) |
| W4, W5 | *Withdrawn in rev 0.6* | — | — | Board copper: the BATT_RAW track to U4 VIN and to F1 (§7) |
| W6 | HDR-30-15 **−V** | board **TB1-1 (GND)** | 18 AWG black | HDR screw terminal → TB1 **upper** screw. The charge return lands here from the pour (§5, §7.3) |
| W7–W14 | *Withdrawn in rev 0.6* | — | — | Board copper. W7–W9 (grounds) → the GND pour; W10 → the Batt_SW track; W11 → the VIN+ track; W12 → the VIN− track; W13/W14 (the J2 control pair) → the GPIO4_SW track, U1 D2 to U4 ON, and the pour. The #2814 and #5382 grounds are their own module pins on the pour (§7) |
| W15 | *Withdrawn in rev 0.3* | — | — | No external pull-down: the #2814 carries its own (§7.2) |

### 5.3 From/to — leaving the enclosure

| W# | From | To | Wire | Termination / notes |
|---|---|---|---|---|
| W16 | board **TB2-1 (VIN−, `+`)** | Splice **S1** → fuse holder, line-side lead | 16 AWG red, through cord grip **G2** | **Lead +.** S1 is a crimped, heat-shrunk butt splice, not a lever nut: this joint is outside the box, on a lead that is handled every session. **24–30 in** (owner, 2026-10-06; §6.4). R_series is measured at T10 |
| W17 | Fuse holder, battery-side lead (**5 A**) | **F2 female QD** → Cyclenbatt **+** | the holder's own lead | **The fuse sits within a few inches of the + tab** (§6.1). Insulated 6.3 mm female QD |
| W18 | board **TB2-2 (GND)** | **F2 female QD** → Cyclenbatt **−** | 16 AWG black, through **G2**, twisted with W16 | **Lead −**, the charge return. Insulated 6.3 mm female QD |
| W19 | *Withdrawn in rev 0.5* | — | — | DS18B20 dropped: RQ-9 and RQ-11 are met by siting (§3). Enclosure temperature comes from the INA228 die (FW-10) |

Not on the rev 0.6 board: an OLED header (dropped in rev 0.3), a DS18B20 terminal (dropped in rev 0.5), an ALERT test point (L4 withdrawn), or a separate VBUS lead (the jumper replaces it). INA228 header pins 5 (VBUS) and 8 have no net [M, board file].

### 5.4 Build notes

- **First flash by USB with AC off** (cord unplugged from the timer), OTA after that, and never USB with AC on. The board puts U3's 3.3 V output straight onto the XIAO's 3V3 pin (§7), so the bank build's rule against a 3V3 source conflict with the XIAO's USB-fed LDO carries over [[ws] §2.1].
- **Power-up tell:** the status LED is firmware-driven, not a rail indicator. GPIO3 resets as an input with no pull and is not in the power-up glitch table [S, ESP32-C3 datasheet pp.20–21], so the LED is dark from reset until the firmware drives it. If it is **dark for more than ~10 s** after AC on, the board is not running [[ws] §4.4]. Check TB1 polarity first, **then the LED's own polarity** (§5.5): a reversed LED is dark forever and fakes this symptom.
- **Staged first power (rev 0.6).** The modules plug into sockets, and every socket accepts a module turned 180° or shifted along the row. Bring the board up one module at a time, AC off for every insertion:
  1. **Bare board** (U1–U4 out; U5 is soldered): DMM TB1-1 to TB1-2 must **not** read a steady short. C4 and C5 charge from the meter, so the reading climbs.
  2. **U4 (#2814) in:** repeat step 1. Turned 180°, the module's GND pin 2 lands on board pad 11 (BATT_RAW) while its pins 9–10 land on GND pads, so TB1 reads a dead short [D, from the pad map, §7]. On AC, that short would hold the PSU in hiccup.
  3. **U3 (D24V7F3) in, U1 and U2 out:** AC on, read **3.3 V** at the U1 socket's 3V3 pin and at U2 socket pin 1. Turned 180°, U3 puts V_Fused on its own output pin. What that does to the +3V3 net depends on the module's internals, which the board review could not settle: whether C4's body blocks the reversed insertion is inconclusive [I; falsifier: the step-3 reading]. That is why U1 and U2 stay out until this reads 3.3 V.
  4. **U2, then U1**, each with AC off.
- **Control net, XIAO out, U4 in, before the first AC on:** the U1 socket's D2 contact to U4 pin 1 (ON) reads 0 Ω, and D2 to GND reads roughly 10–20 kΩ through the #2814's R4 + R5, with Q3's base junction across R5 depending on the meter. A 0 Ω to GND, or an open to ON, means U4 is mis-seated. On the board, copper replaces the J2 cable, so the pair can no longer be swapped; this check now proves the seating. It still does one of the jobs of the withdrawn Rs (§7.2).
- **Before the first AC on:** DMM continuity from each F2 QD back to its terminal (+ through the fuse to TB2-1, − to TB2-2), with no continuity between them.

### 5.5 Status LED: where it goes, and which leg goes in which hole

**Where (rev 0.8).** With the board component side up and the INA228 end at the top, the LED is on the **left edge**, below the XIAO and above TB1, just left of the #2814's outline. Its two holes are 2.54 mm apart, at (15.96, 61.50) and (18.50, 61.50) mm, against the left edge at x 13.45 [M, board file saved 2026-10-08 10:48:22]. It is still turned as in rev 0.7, so the square pad is the **right** hole. But the LED now sits at the other edge, so the square hole is the one **farther from** the edge; in rev 0.7 it was the nearer. The LED is under no module, and no part's outline stands in front of the XIAO's USB-C socket (O12) [M, courtyards and outlines]. R1 (1 kΩ) lies horizontally under the XIAO.

**Where (rev 0.7, superseded).** The LED was on the **right edge**, level with the XIAO's USB-C socket, which opened straight at it: the socket's axis at y 46.0 mm, the LED's centre at y 47.0, its holes at (37.16, 47.00) and (39.70, 47.00) mm [M, board file saved 2026-10-06 15:16:19]. Rev 0.7 **turned it 180°** from rev 0.6.

```text
            INA228 end of the board is UP, component side facing you

                      silk ring: cut FLAT on this side (on the
                      3 mm footprint the flat shows only as two
   left edge          short ticks, above and below the square pad)
   of the board                    │
       │                           ▼              #2814 (U4)
       │       (●)          [■]   ▌               outline ──►
       │      pad 2        pad 1  ▌
       │      ROUND        SQUARE ▌
       │        │             │
       │     LONG leg      SHORT leg
       │     anode (+)     cathode (−)
       │     to R1, XIAO   to GND
       │     D1 (GPIO3)
```

| LED lead | How to recognise it | Goes in | Pad | Net |
|---|---|---|---|---|
| **Cathode (−)** | the **short** leg; the **flat** on the LED's rim is on this side | the **right** hole, toward the #2814 and away from the board edge, on the flat side of the silk ring | **square** (pad 1) | GND |
| **Anode (+)** | the **long** leg | the **left** hole, nearer the board edge | **round** (pad 2) | GPIO3_LED → R1 → GPIO3 |

**Mnemonic: Square = Short = Flat = minus.** The square pad, the short leg and the flat on the rim all mark the same lead, the cathode. The long leg goes in the round hole.

- **What is measured, and what is convention.** The pad shapes, their nets and the flat in the silk are [M], read from the board file: pad 1 is square and on GND, and pad 2 is round and on R1. "Long leg = anode, flat = cathode" is the industry convention. For this part it is **[I]**: Lite-On's LTL-4231N datasheet could not be retrieved (§14).
- **The check that settles it, before soldering and before trimming the legs** (trimmed legs lose the length cue). Put the DMM on diode test, red probe on the long leg and black on the short. The LED should glow faintly and read about 2 V [I: the listing's 2.1 V forward voltage]. If it reads open, swap the probes. If it glows that way round, this part breaks the convention: trust the meter, and put the lead on the **black** probe in the square hole.
- **A reversed LED** sits reverse-biased at 3.3 V and never lights. Whether that is inside its reverse rating is [I] without the datasheet. The real cost is the indicator: a dark LED reads as "board not running" (§5.4), and FW-11's status patterns are lost. The first boot checks it: once HA or the web page shows the node running, the LED must show the IDLE blink.
- **Current:** about 1.2 mA [D: (3.3 V − 2.1 V) ÷ 1 kΩ; Vf from the listing]. Whether that is bright enough in room light is [I]. The falsifier is the first boot. If it is too dim, R1 is the only part to change.
- **Size: 3 mm.** The Value field names the LTL-4231N, which LCSC lists as a 3 mm (T-1) part [listing, C125082]. The owner changed the footprint from `LED_D5.0mm` to `LED_D3.0mm` in v6 (2026-10-03 22:41:30), and that closed Q6. The pads did not move in that edit: same positions, same nets, 1.8 mm pads, 0.9 mm drill [M, v5/v6 diff]. Rev 0.7 then moved and turned the LED (above); pad 1 is now 1.6 × 1.8 mm, pad 2 1.8 mm round, both 0.9 mm drill, same nets [M, board file 2026-10-06]. The Value text still reads "LED GREEN DIFFUSED T/H LED_D5.0mm - LTL-4231N". It is on F.Fab, which is not fabricated, so nothing printed is wrong (O13).
- **USB-C plug clearance: settled in rev 0.8** by the move to the left edge. The LED is now at the XIAO's other end and below it, so a cable's overmold cannot reach it (O12 closed). Rev 0.7's analysis follows. The XIAO sits about 10 mm up on its sockets (owner, 2026-10-06; rev 0.6 said ~8 mm), and in rev 0.7 its USB-C socket points straight at the LED. The LED is 1.0 mm off the socket's axis (it was 7.0 mm in rev 0.6), and its dome starts about 0.5 mm past the XIAO's outline [D: dome centre x 38.43 − 1.5 mm vs outline x 36.4, board file], so a cable's overmold passes **directly over** it. The board's 3D render puts the LED top at about 5.1–5.3 mm and the socket's underside at about 9.7 mm [M, render of the board file's models]. An overmold up to 8 mm thick, centred on the socket, would clear the LED by roughly 2 mm [I: overmold size and a 3.2 mm socket height assumed, not measured]. Whether it clears is not settled (O12). **Dry-fit before soldering:** seat the XIAO, plug a USB-C cable in, and stand the LED in its holes. If they touch, mount the LED flush, or do the one USB flash (§5.4) with the XIAO out of its socket. Every later flash is OTA.

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
- **PSU to board** (W3, W6): 18 AWG, short runs.
- **On the board (rev 0.7):** the power path is 1.5 mm track on F.Cu: BATT_RAW, Batt_SW, VIN+ and VIN−, each a single route [M, board file 2026-10-06]. IPC-2221's external-conductor formula gives 3.21 A at a 10 °C rise and 4.35 A at 20 °C for 1.5 mm of 1 oz copper [D: I = 0.048 · ΔT^0.44 · A^0.725, with A = 81.4 mil²; 1 oz is assumed, not measured]. 2.0 A is the steady case (RQ-12); 3.64 A is a transient no longer than t_ol. The ground is the pour (§7.3). The owner plans to move VIN+ to B.Cu and shorten it (O15, §7.4).
- **On the board (rev 0.8, the 2026-10-08 10:48 save):** each power net is still a single route, now wide [M, board file]:
  - BATT_RAW: 4.0 mm on F.Cu, from TB1-2 through U4 pins 12 and 11.
  - Batt_SW: 2.9–4.0 mm on F.Cu.
  - VIN+: 2.9–4.0 mm on **B.Cu**, with no vias (O15, done).
  - VIN−: 3.85 mm on F.Cu, necking to 1.7 mm for its last ~0.2 mm into U2 pin 6.

  The same IPC-2221 formula gives these rises at 3.64 A: 4.0 mm 2.6 °C, 2.9 mm 4.5 °C and 1.7 mm 10.8 °C. At 2.0 A they are 0.7, 1.2 and 2.8 °C [D]. The formula assumes a long run, so it overstates the short 1.7 mm neck [I].
- **The F1 branch** (BATT_RAW, from U4 pins 11–12 to F1 pin 1) is 2.0 mm, and V_Fused is 1.5 mm. The branch lies upstream of F1, so F1 does not protect it. The PSU's limit does (≤ 3.64 A [D, §4.1]), and the #5382 keeps the pack off BATT_RAW. At 3.64 A, 2.0 mm rises 8.3 °C [D, as above]. The branch's two legs, to U4 pins 11 and 12, form a small loop in parallel with the main run. That loop barely matters: narrowing the branch from 2.95–3.95 mm to 1.5 mm, on a copy of the 08:04 save, moved BATT_RAW's track resistance from 1.172 to 1.177 mΩ [D, §7.4's 2-D solve].
- **Module contacts.** U2's VIN+ and VIN− are one socket contact each, so the whole charge current crosses two Sullins contacts rated 3 A [S, Sullins 0.100″ female header datasheet pp.114–115]. That covers 2.0 A steady. **3.64 A exceeds it**, and is tolerated only as the t_ol transient [I; falsifier: the contact runs warm to the touch after T11's opening minutes]. The #2814 has two contacts on VIN and two on VOUT (§7). U5 is soldered on pin headers. The #5382 is rated 10 A continuous and < 10 mΩ [S, Pololu #5382 product page, read 2026-10-08; the part number is the board's Value field, not read off a unit (R16)].
- **The #2814's contact pairs share the current** (rev 0.8). A network solve of the board copper, with each socket pad tied in through a contact resistance Rc, gives these splits at Rc = 1 mΩ and 5 mΩ [D]:
  - VIN, pin 11 / pin 12: 47.0 / 53.0 and 49.4 / 50.6.
  - VOUT, pin 5 / pin 6: 51.0 / 49.0 and 50.2 / 49.8.

  The busier contact therefore carries ≤ 1.93 A at 3.64 A, under the 3 A rating [D]. With ideal contacts (Rc → 0), the copper alone would put 89 % through pin 12. No real contact is that good [I: falsifier, a Sullins contact resistance below 1 mΩ on pp.114–115]. Rc itself has not been looked up.
- **Voltage drop** between VBUS and the pack terminals is I × R_series, where R_series = shunt (15 mΩ [S, Adafruit #5832]) + U2's VIN− contact + the VIN− track (≈ 5.7 mΩ in rev 0.7 [D: 17.3 mm ÷ 1.5 mm = 11.5 squares × 0.4926 mΩ/sq, at 35 µm and 20 °C; a network solve of the three segments gives 5.67]; rev 0.6's 24.4 mm gave 8.0; rev 0.8 gives 2.36 mΩ [D: 2-D solve, §7.4]) + TB2 + fuse + both lead conductors + splice + QDs + the pour's shared path (≤ ~0.055 mΩ since the 17:09 Kelvin GND, TB2-2's own pad included; it was 0.376–0.382 mΩ [D, §7.3]). VIN+ is upstream of the VBUS sense point, so its track is not in R_series. Measure it once at commissioning (T10). **The firmware does not use it (rev 0.5):** it publishes raw VBUS and I, and V_batt = VBUS − I·R_series is computed in InfluxDB/Grafana, where a revised R_series re-computes history. T10's value also splits FW-12's per-session edge resistance into series and pack parts.
- **Worked example**, lead alone, at the owner's 24–30 in (2026-10-06; W16): 4.0–5.0 ft of 16 AWG conductor, out and back, is 16.1–20.1 mΩ [D: × 4.016 mΩ/ft]. It drops 32–40 mV at 2.0 A and 58–73 mV at 3.64 A [D]. Until this revision the example assumed 5 ft each way: 40 mΩ and 146 mV. At 24–30 in the lead is **less** than the board's 38.10 mΩ of charge-path track (§7.4). In rev 0.8 that track is 12.17 mΩ (§7.4), so the lead is now the larger term. The drop falls toward zero as the current tapers.

---

## 7. The board — Top Off Charger PCB (rev 0.8)

The controller is a purpose-built board, `Top Off Charger- Oct 2026.kicad_pcb` (KiCad 10): two layers, 29.5 × 78 mm in rev 0.7 (rev 0.6 was 31.5 × 95) [M, F.Cu/B.Cu stackup, Edge.Cuts]. It is drawn for OSH Park and replaces rev 0.5's reuse of a bank-monitor V2 board. Everything in this section is read from the board file using kicad-cli 10.0.6 and KiCad's pcbnew Python [M]. Unless a line says rev 0.6, it was read from the rev 0.7 file saved 2026-10-06 15:16:19 (309,671 B), or from the owner's 17:09:17 save (309,654 B), which adds the Kelvin GND (§7.3). The 17:09 save was the file in `pcb/` until rev 0.8 (below). Rev 0.6 was read from v6 (saved 2026-10-03 22:41:30, 318,750 B) and gated on v7 (22:42:18, 318,320 B). Rev 0.7 re-laid the same netlist on a smaller outline. Its net changes are TB1's pin order (§5.1) and, in the 17:09 save, the GND_SENSE net (§7.3). The design rules are unchanged: the `.kicad_pro` differs only in the default pad width for new pads and the last plot path [M, diff]. The 17:09 save's (17:08:40) differs from 15:16's only in the default size and drill of new pads [M, diff].

- **Not yet fabricated.** The board file and its project file (design rules) are the only artifacts. Both are in [`pcb/`](pcb/) (O11). When the Gerbers are exported for the order, they become the authority for what was built, as the V2 Gerbers were for rev 0.5.
- **No schematic.** The board was drawn directly, so the netlist below is the design. KiCad's schematic-parity check therefore cannot run.

**Rev 0.8 (2026-10-08).** The file in `pcb/` is now the owner's 2026-10-08 11:00:58 save (318,992 B, sha256 `e5586ceb07233e71a7556a01576da8c81db629cf90da1182eaa210763013efaf`). Every check in this revision was run on the 10:48:22 save before it (318,536 B, sha256 `9661db54913ce70fbb37433480a5eb0c0172a43b08102493edb6cd6dbcda5b28`). The two differ only in U1's 3D models: the XIAO's model is raised from 8.5 to 11.0 mm, and two pin-header models are added. The copper, pads, vias, zones and text are identical, and DRC gives the same 34 warnings [M: text diff, board dump, DRC set]. The `.kicad_pro`, the same file for both saves, (9,806 B, sha256 `abb4d3f13d19d1a4fbb53a2cd935b50558ca129046a85dc00457706d6852c5eb`) differs from 17:09's only in the default size and drill of new pads [M, diff]. Rev 0.8 keeps rev 0.7's outline, netlist and parts, and changes the copper. The owner made the changes over a series of saves from 2026-10-06 to 10-08. Some of them began as edits a review session wrote into the owner's file on 2026-10-06 (R13, §7.4). The list below is read from the 10:48 file [M]:

- **VIN+ is on B.Cu** (O15): 2.9–4.0 mm wide and 47.3 mm long, from U5 pad 3 to U2 pin 7, with no vias. Both ends are through-hole pads, so the bottom layer reaches them directly.
- **BATT_RAW, Batt_SW and VIN− are 2.9–4.0 mm**, with VIN− necking to 1.7 mm into U2 pin 6. The F1 branch is 2.0 mm (§6.4).
- **Pads enlarged**, for current and for hand soldering:
  - TB1-2, TB2-1 and TB2-2: 3.0 mm. TB1-1: 2.0 mm.
  - U4: pins 11 and 12 3.2 mm (pin 11 3.2 × 2.25), pins 5 and 6 2.1 mm.
  - U5: pins 1 and 3 3.1 mm.
  - U2: pin 7 a 3.0 × 2.1 oval, pin 6 a 2.0 × 1.6 oval.
  - F1: 2.5 mm.
- **TB1-1 and TB2-2 meet the pour through thermal reliefs**, for hand soldering. At 17:09, TB2-2 was solid [M, pad zone_connect] (§7.3).
- **Signals:** GPIO4_SW runs 16.9 mm on B.Cu and 8.7 mm on F.Cu, joined by one via, and still reaches only U1 D2 and U4 pin 1 [M]. SDA and SCL were re-routed on B.Cu.
- **Stitching vias:** 78 → 85, so 86 vias in all, counting GPIO4_SW's.
- **Placement**, against 17:09 [M]. The outline is unchanged. Parts moved:
  - **The LED went from the right edge to the left** (§5.5). Its square hole is now the one away from the edge.
  - TB1 moved 4.5 mm down, which clears its labels from under U4 (§5.1, O14).
  - U4 moved 0.9 mm down, and U5 0.6 mm; U5 is still under U4.
  - R1 moved and turned 180°, and now lies wholly under the XIAO.
  - C2 moved 1.0 mm left and 3.5 mm up. U1 and C3 moved 0.5 mm up.
  - H3 and H4 moved by about 0.5 mm.
  - F1 moved 0.35 mm down, and U3, C1, C4 and C5 0.5 mm.
- **F1 and U3 moved down** in the last save, by 0.15 and 0.2 mm (owner: for clearance). C1, C4 and C5 moved with U3. F1's courtyard now clears U3's by 0.63 mm and C4's by 0.54 mm; they were 0.58 and 0.49 [M, courtyard boxes].
- **The net tie is named NT1** (O16a).

**Gate verdicts, rev 0.8 (the 10:48 save, 2026-10-08):**

- DRC (`--severity-all`, with the board's `.kicad_pro` rules) gives the same result on the saved fill and after a refill: **0 errors, 34 warnings**, **0 unconnected** [M, kicad-cli 10.0.6 JSON, compared as a set]. By class: lib_footprint_issues 2, lib_footprint_mismatch 12, silk_edge_clearance 6, silk_over_copper 8, silk_overlap 6.
- **Against 17:09's 26 warnings, 11 are new and 3 are gone.** None is electrical. The new ones:
  - U2 and U5 no longer match their library footprints, because of the enlarged pads.
  - Module outlines on F.Silk now cross enlarged pads: U2 pin 7 (twice), U4 pins 11 and 12, U5 pins 1 and 3, and C2 pad 2 (U2's outline, twice).
  - U3's outline is clipped by the board edge. This comes from the last save's 0.2 mm move: the outline's bottom line now lies on the edge line, at y 98.0 [M]. U3's pads stay 1.15 mm inside the edge, against the 0.5 mm copper-to-edge rule [M].

  The 3 that are gone are O13(e)'s.
- The saved fill equals a refill: 1258.8 and 1549.5 mm² [M, pcbnew].
- An injected fault made DRC report shorting_items [M]: a GND stitching via moved onto the re-routed V_Fused track.
- Every stitching via lands in both layers' fill: 85 of 85 have their centre and at least 12 of 16 points around them inside each layer's fill [M].
- Schematic parity: **DID NOT RUN** (no `.kicad_sch`). This is a WARN, not a clean result.
- **A save made without a refill can hold copper that only DRC on the saved file catches.** The owner's 09:46 save of 2026-10-08 was made before a refill. Its saved GND fills sat inside the clearance of U4 pins 11 and 12 (BATT_RAW), whose pads that save had enlarged. At pin 12 the gap on B.Cu was 0.000 mm, so the saved copper shorted BATT_RAW to GND. DRC on the saved file gave 4 errors (3 clearance, 1 solder-mask bridge), and a refill cleared them [M]. So press B (Fill All Zones) and save before exporting Gerbers, and run DRC on the saved file as well as with `--refill-zones` (O11).

**Gate verdicts, rev 0.7 (2026-10-06):**

- DRC (`--severity-all --refill-zones`, with the board's `.kicad_pro` rules): **0 errors, 26 warnings** (lib_footprint_issues 2, lib_footprint_mismatch 10, silk_edge_clearance 5, silk_over_copper 3, silk_overlap 6), **0 unconnected**.
- The **17:09 save** gives the same on the saved file and after a refill: 0 errors, 26 warnings, 0 unconnected, and the same 26 entries by type and item [M, kicad-cli 10.0.6 JSON, compared as a set]. An injected fault, a GND track from the stitching via at (23.5, 29.0) onto the GND_SENSE track, made DRC report clearance and shorting_items [M], so GND_SENSE's separation from the pour is checked, not assumed.
- Schematic parity: **DID NOT RUN** (no `.kicad_sch`). This is a WARN, not a clean result.
- None of the 26 warnings is in an electrical class. The silk items worth fixing before the order are in O13 and O14.
- Rev 0.6's v7 gave 0 errors, 26 warnings (lib_footprint_issues 3, lib_footprint_mismatch 9, silk_edge_clearance 5, silk_over_copper 7, silk_overlap 2), 0 unconnected. Re-run on 2026-10-06 under kicad-cli 10.0.6, v7 gave 25: lib_footprint_issues 2, not 3. That class compares footprints against the installed libraries, so the difference is the libraries, not the board [I].

| Ref | Part (from the Value field) | Mounting | Pads → nets |
|---|---|---|---|
| U1 | Seeed XIAO ESP32-C3 | Sullins female sockets, 2 × 1×7, ~10 mm up (owner, 2026-10-06) | 3V3 → +3V3; GND; D1 → GPIO3; D2 → GPIO4_SW; SDA, SCL (§7.1). D3, D6 and D7 are unplated holes |
| U2 | Adafruit INA228 #5832 | Sullins socket, 1×8, ~10 mm up | 1 → +3V3; 2 → GND_SENSE (GND before the 17:09 save, §7.3); 3 → SCL; 4 → SDA; 6 → VIN−; 7 → VIN+; 5 (VBUS) and 8 have no net |
| U3 | Pololu D24V7F3, 3.3 V | Sullins socket, 1×3, ~10 mm up | V_Fused in, GND, +3V3 out |
| U4 | Pololu #2814 Big MOSFET Slide Switch, MP | Sullins sockets, 2 × 1×6, ~10 mm up | 1 (ON) → GPIO4_SW; 11–12 (VIN) → BATT_RAW; 5–6 (VOUT) → Batt_SW; 2–4 and 9–10 → GND; 7–8 have no net |
| U5 | Pololu #5382 ideal diode | **soldered** on pin headers, ~2.54 mm up (owner, 2026-10-03); in rev 0.7 it sits **under U4** | 1 → Batt_SW (from the switch); 3 → VIN+ (to the shunt); 2 and 4 → GND |
| F1 | 1 A slow-blow, 5 × 20 mm, in a Würth 696108003002 holder | soldered | BATT_RAW → V_Fused: the board supply only, not the charge path |
| C1 | 10 µF 25 V X7R, disc | soldered, **under U3's module** | +3V3 |
| C2, C3 | 0.1 µF 50 V X7R, disc | soldered; C3 **under the XIAO** | +3V3; C2 beside U2 |
| C4 | 47 µF 50 V, radial 6.3 × 11 mm | soldered | V_Fused (U3's input) |
| C5 | 0.1 µF 50 V X7R, disc | soldered | V_Fused (U3's input) |
| R1 | 1 kΩ 1/4 W, axial | soldered, **under the XIAO** (partly, before rev 0.8) | GPIO3 → GPIO3_LED |
| LED | Lite-On LTL-4231N, green diffused, 3 mm | soldered; **polarity in §5.5** | pad 1 (square) → GND; pad 2 (round) → GPIO3_LED |
| TB1, TB2 | Phoenix BC-381X9-2 GN (item 5442756), 2-position 3.81 mm screw terminals | soldered | §5.1 |
| NT1 (`REF**` until rev 0.8, O16) | Net tie, KiCad `NetTie-2_SMD_Pad0.5mm` (17:09 save) | F.Cu copper only; nothing to fit | pad 1 → GND, on TB2-2's pad edge at (17.54, 25.17); pad 2 → GND_SENSE |
| H1, H3, H4 | M3 mounting holes, for nylon screws and standoffs (owner, 2026-10-06) | — | no net. In rev 0.7 each is **under a module**: H1 under U2, H3 under U1, H4 under U4 [M]. Rev 0.8 moves H3 and H4 by about 0.5 mm, and each is still under the same module [M] |

The V_Fused capacitors are rated 50 V against the PSU's 22.5 V OVP ceiling [S, §4.1]. C1, at 25 V, sits on 3.3 V.

**Solder the parts that sit under a module first:** C1 under U3, and C3 and R1 under the XIAO. The 2026-10-03 review's 3D render showed C1 clearing U3's underside at the 8.5 mm socket height [D, render]. On the bench, a module that will not seat fully on its socket is the tell. The plan-view courtyards cannot show this, because U3's covers only its 1×3 socket.

**Rev 0.7 adds three steps, all before any module is seated:**

1. **U5 goes under U4.** Solder it, then trim its header pins flush with the top of the #5382's board. Untrimmed, their tips come within about 1.35 mm of U4's underside [D, the board file's 3D models with U4 ~10 mm up]. U5 pin 3 (VIN+) is 2.72 mm from one of U4's 2.18 mm mounting holes [M], whose net is assumed to be GND [I, not read from Pololu's drawing]. That figure is rev 0.7's. In rev 0.8 U4 moved 0.9 mm down and U5 0.6 mm, so the gap changed by no more than 0.3 mm [D]; it was not re-measured.
2. **Fit the board to its standoffs.** H1, H3 and H4 are each under a module, so their nylon screws cannot be reached once the modules are on.
3. **Land TB2's wires.** TB2-1's screw is under U2 (§5.1).

**Netlist** [M, board file 2026-10-06]. The power nets are 1.5 mm track on F.Cu, each a single route; +3V3 and V_Fused are 1.5 mm on F.Cu too. Signals are 0.2 mm, and GND_SENSE 0.5 mm. In rev 0.7, GPIO4_SW, SDA and SCL run on **B.Cu** (24.2, 11.8 and 11.6 mm), through the bottom pour, with no signal vias; GPIO3 and GPIO3_LED stay on F.Cu. Rev 0.6 had every track on F.Cu. §7.3 gives what the B.Cu runs cost the ground. **Rev 0.8** [M, the 10:48 save]: the nets and their pads are unchanged, and only the copper differs. BATT_RAW, Batt_SW and VIN− are 1.7–4.0 mm on F.Cu, and VIN+ is 2.9–4.0 mm on B.Cu (§6.4, §7). V_Fused stays 1.5 mm. GPIO4_SW now changes layer through one via (16.9 mm on B.Cu, 8.7 mm on F.Cu); SDA and SCL stay on B.Cu (11.3 and 12.3 mm).

- **BATT_RAW:** TB1-2, U4 VIN (11, 12), F1.
- **Batt_SW:** U4 VOUT (5, 6), U5 pad 1.
- **VIN+:** U5 pad 3, U2 pin 7.
- **VIN−:** U2 pin 6, TB2-1.
- **V_Fused:** F1, C4, C5, U3 VIN.
- **+3V3:** U3 VOUT, U1 3V3, U2 pin 1, C1, C2, C3.
- **GPIO4_SW:** U1 D2 and U4 pin 1 (ON), and nothing else.
- **GPIO3:** U1 D1 and R1. **GPIO3_LED:** R1 and LED pad 2.
- **SDA / SCL:** U1 to U2 pins 4 / 3.
- **GND:** a pour on both layers, stitched by 78 vias in the 17:09 save (77 at 15:16; rev 0.6: 92; rev 0.8: 85). It reaches 18 pads: TB1-1, TB2-2, U1, U3, U4 (2–4, 9, 10), U5 (2, 4), C1–C5, LED pad 1 and the net tie's pad 1. At 15:16 U2 pin 2 stood where the tie's pad is now (§7.3).
- **GND_SENSE** (17:09 save): U2 pin 2 and the net tie's pad 2, by one 0.5 mm F.Cu track, 8.87 mm. It carries only U2's own supply return, a few mA at most [I], and the tie at TB2-2 is its one join to GND (§7.3).

| Setting | Charger build | Why |
|---|---|---|
| INA228 onboard 15 mΩ shunt | **KEEP** | It is the charger's shunt. At 3.64 A it drops 55 mV [D], inside the ±163.84 mV range [D: 312.5 nV × 2¹⁹, from `battery-bank-monitor.yaml`]. The board is sold for up to 10 A [S, Adafruit #5832 page] |
| Breakout VBUS jumper | **CLOSED** (VBUS = VIN+) | High-side use [S, Adafruit #5832 page]. U2 pin 5 (VBUS) has no net on this board [M, board file v6 and 2026-10-06], so the closed jumper reaches nothing else, and no VBUS lead is needed |
| **No pull-up on GPIO4_SW** | **mandatory**; the board has no position for one | GPIO4 powers up high-impedance with no internal pull (reset state "1") and is not in the power-up glitch table [S, ESP32-C3 datasheet pp.20–21]. A 10 kΩ pull-up (the V2 board's R3) would hold ON at 2.2 V [D: 3.3 × 20/30, where 30 kΩ = R3 10 kΩ + the #2814's on-board 20 kΩ] through every boot, watchdog reset and flash, above the ~1 V threshold, so **the charger turns on whenever the ESP32 is not running** (§7.2) |
| Board supply | **BATT_RAW, upstream of the switch** (TB1-2 in rev 0.7, from PSU +V) | Board alive whenever AC is on; zero battery drain when AC is off |
| F1 (1 A slow-blow, BATT_RAW → V_Fused), U3 D24V7F3 | as on the V2 board | The D24V7F3 takes 4–36 V [[ws] §3.1], which covers the PSU's 22.5 V OVP ceiling [S] |

### 7.1 XIAO pin map (charger)

| XIAO | GPIO | Net | Charger function |
|---|---|---|---|
| D1 | GPIO3 | GPIO3 → R1 → LED | **Status LED** (FW-11), active-high. Reset state "1", no internal pull, not in the glitch table [S, ESP32-C3 datasheet pp.20–21], so the LED stays dark until the firmware drives it |
| D2 | GPIO4 | GPIO4_SW → U4 ON | **Charge enable** output, active-high. Boot-safe because nothing pulls the net up (§7.2) |
| D4 / D5 | GPIO6 / GPIO7 | SDA / SCL | INA228 |
| 3V3, GND | — | +3V3, GND | Supplied by U3 |

Every other XIAO pin has no net [M, board file 2026-10-06]: 5V, D0, D8, D9 and D10 (GPIO10). The footprint's D3 position is a plain non-plated hole. In rev 0.7, **D6 and D7 (GPIO20) are non-plated too**, with 1.02 mm holes, 1.7 mm mask openings and no copper (owner: "to gain clearance for the 3.3 V rail"). In rev 0.6 they were plated pads with no net. Their socket pins pass through unsoldered. The nearest copper is the VIN+ track along the left edge, 0.30 mm outside both mask openings; no +3V3 copper is within 1.5 mm [M]. The SDA track on B.Cu passes 0.25 mm from D3's hole, which is exactly the board's min_hole_clearance of 0.25 mm; DRC passes it [M]. The strapping pins GPIO2 (D0), GPIO8 (D8) and GPIO9 (D9) are among the unconnected pins, so nothing on the board can pull them at boot [S, Seeed XIAO ESP32C3 wiki pin map].

### 7.2 Switch control net (on-board)

| Ref | Part | Connects | Purpose |
|---|---|---|---|
| Rs | *Withdrawn in rev 0.4* (owner, 2026-09-21) | — | GPIO4 drives ON directly. On the board, GPIO4_SW is one 0.2 mm track from U1 D2 to U4 pin 1 (ON), with no other pad on the net [M, board file v6 and 2026-10-06]. Rev 0.7 moved it to B.Cu. There is no series position. The V2 board had none either: XIAO D2, R3 pad 1 and J2-1 only [M, Gerber X2 net attributes, 2026-09-21]. A swapped control pair is no longer possible, because the J2 cable is now copper. The §5.4 continuity check proves U4 is seated, and FW-1's 5 mA drive strength limits what the pin pushes into a fault. **Left uncovered:** +V reaching the track, through a solder bridge or a mis-seated #2814. That would cost the socketed XIAO, and it turns the charger on whatever the firmware does. That is L6's case, the same as a shorted #2814 |
| — | *(on the #2814)* R4 10 kΩ + R5 10 kΩ | ON → R4 → Q3 base; R5 base → emitter (GND) | **The off-state pull-down, already on the board** [S, Pololu schematic]. With ON floating, R5 holds Q3's base at 0 V and the switch is off. That is Pololu's "leaving it disconnected will leave the switch off". GPIO4's input leakage, at most 50 nA [S, ESP32-C3 datasheet Table 14 p.32], gives at most 1 mV across 20 kΩ [D]. GPIO high drives ON to ~3.3 V at 0.17 mA [D: 3.3 V ÷ 20 kΩ], above the ~1 V threshold [S, §4.2]; R4/R5 halve it onto Q3's base-emitter junction |

> **Correction record (R13), 2026-09-21.** Rev 0.2 and the first draft of rev 0.3 specified an external **Rpd 10 kΩ** (ON → GND at the switch) to hold ON low with GPIO4 high-impedance, and gave ON = 3.0 V [D: 3.3 × 10/11]. Both were written before the switch's schematic was read. The board already has R4 + R5 = 20 kΩ from ON to GND, which does that job, so Rpd was redundant and the 3.0 V omitted the on-board resistors. The owner asked why Rpd was required, and the schematic answered it. Rpd was withdrawn (W15). T1 and T2 now prove the on-board pull-down. Evidence: Pololu "Big MOSFET Slide Switch with Reverse Voltage Protection" schematic (file 0J1071, ©2015), read 2026-09-21.

> **Correction record (R13), 2026-09-21.** Rev 0.3 (`34e4a52`) said the ESP32's leakage across the 20 kΩ was "microvolts". The datasheet's maximum input leakage is 50 nA [S, ESP32-C3 datasheet Table 14 p.32], which gives up to 1 mV [D]. The conclusion stands, because turn-on needs ~1 V, but the figure was wrong. It was found while answering the owner's question about Rs.

**Off at every reset: why GPIO4, and why GPIO4_SW has no pull-up.** Power-on, an AC blip, a watchdog reset (L3), an OTA reflash or a crash each leave the ESP32 in ROM and the bootloader for a few hundred milliseconds before ESPHome drives GPIO4 low. In that window the hardware alone holds the switch off:

1. GPIO4 returns to reset state "1": input, high-impedance, no pull [S, ESP32-C3 datasheet pin table p.20, key p.21]. It is not in the power-up glitch table [S, Table 7 p.21].
2. With ON undriven, the #2814's R5 holds Q3's base at 0 V and the switch is open [S, Pololu schematic].
3. Leakage gives at most 1 mV against a ~1 V turn-on [D, above].
4. Only then does FW-1 drive GPIO4 low (`restore_mode: ALWAYS_OFF`), confirming a state the hardware already set.

No added part, no firmware and no resistor ratio is involved. Adding a pull-up to GPIO4_SW is the one way to break it, and the board (rev 0.6 and rev 0.7) has no position for one (§7). T1 and T2 prove it on the hardware.

**GPIO20, the bank board's LED pin, is not an alternative control pin, and it is not used.** It resets in state "3", with its internal pull-up on [S, p.20–21]. That would lift ON to ~1.0 V at every reset [D: 3.3 × 20/66, with the pull-up at its typical 45 kΩ (Table 14), R4 1 kΩ and the #2814's 20 kΩ]. The datasheet gives that pull-up no minimum, so no added pull-down could be proven adequate on paper. The rev 0.6 board moves the LED to GPIO3 (D1). It resets in state "1" with no pull and no glitch [S, pp.20–21], so the LED stays dark through every reset (§5.4).

**The #2814 slide must be locked in OFF.** External ON control works only with the slide OFF: "if the physical switch is in the 'off' position, the switch state can also be controlled by a digital signal … via the 'ON' control pin" [S, #2814 page]. Glue or lacquer it.

### 7.3 Ground: the pour, and what it costs VBUS

The ground is copper pour on both layers, stitched by 78 vias in the 17:09 save (77 at 15:16, 92 in rev 0.6, 85 in rev 0.8), with no star point [M, board file 2026-10-06]. The charge return enters at TB2-2 (pack −) and leaves at TB1-1 (PSU −V; TB1-2 in rev 0.6). The INA228's ground (U2 pin 2) sits on the same pour, so part of the return path is shared with its reference. **VBUS reads high** by the drop across that shared part. The pack's negative terminal sits above U2's ground by I × R_shared. **The owner's 17:09 save removes the shared part** with a Kelvin connection (below). The table, the effect and the B.Cu-track study are the 15:16 save's: the baseline it improved on.

| Case | R_shared, TB2-2 → U2 pin 2: rev 0.6 | rev 0.7, 15:16 | Whole pour, TB2-2 → PSU −V pad: rev 0.6 | rev 0.7, 15:16 |
|---|---|---|---|---|
| 0.1 mm cells, ideal vias | 0.383 mΩ | 0.382 mΩ | 1.720 mΩ | 1.632 mΩ |
| 0.05 mm cells, ideal vias | 0.375 mΩ | 0.377 mΩ | 1.699 mΩ | 1.596 mΩ |
| 0.1 mm cells, 1.5 mΩ per via barrel [I] | 0.407 mΩ | 0.376 mΩ | 1.819 mΩ | 1.749 mΩ |

All rows are [D]. The PSU −V pad is TB1-2 in rev 0.6 and TB1-1 in rev 0.7. **Effect (rev 0.7, 15:16 save):** VBUS reads high by 0.75–0.76 mV at 2.0 A, and by 1.37–1.39 mV at 3.64 A [D: I × 0.376–0.382 mΩ]. Rev 0.6 gave 0.75–0.81 and 1.36–1.48 mV. The lead alone drops 58–73 mV at 3.64 A (§6.4), so the pour is a small term in R_series, and T10 measures R_series whole.

**What rev 0.7 changed [D, differences of the table's rows].** The whole pour fell by 0.070–0.104 mΩ. R_shared moved by −0.001 and +0.002 mΩ in the ideal-via rows, which is inside the 0.006–0.008 mΩ the two cell sizes disagree by, so it is unchanged. In the barrel row it fell by 0.032 mΩ. At 3.64 A, the whole-pour drop is 5.81–6.37 mV and its loss 21.1–23.2 mW [D: I × R, I² × R], against 6.19–6.62 mV and 22.5–24.1 mW in rev 0.6. Both changes are small beside the 58–73 mV in the lead.

- **The B.Cu signal tracks (rev 0.7).** GPIO4_SW, SDA and SCL cut slots in the bottom pour, so they were sized directly. pcbnew refilled the rev 0.7 file three ways and the solver ran on each:
  - **Control: refilled, nothing removed.** Same fill as the saved file, 1278.9 mm² on the zone that pours both layers and 1772.5 mm² on the B.Cu zone [M, pcbnew]. Same results as the table.
  - **SDA and SCL deleted, then refilled.** The B.Cu fill gains 19.5 mm². R_shared 0.441 / 0.432 / 0.437 mΩ and whole pour 1.479 / 1.449 / 1.575 mΩ, in the table's row order.
  - **All three deleted, then refilled.** The fill gains 44.4 mm². R_shared 0.442 / 0.433 / 0.440 mΩ and whole pour 1.452 / 1.423 / 1.531 mΩ.

  So the tracks as laid **raise** the whole pour by 0.173–0.218 mΩ and **lower** R_shared by 0.057–0.064 mΩ [D]. The I²C pair is most of it (+0.146–0.174 and −0.056–0.062 mΩ). It runs from U2 down to the XIAO (x 19–30 mm, y 31.6–38.4), just south of U2 pin 2 and across the return path from TB2 to TB1. GPIO4_SW, down the right side, adds +0.026–0.044 and −0.001–0.003 mΩ. At 3.64 A, that is 0.63–0.80 mV more whole-pour drop and 2.3–2.9 mW more loss, and VBUS reads 0.21–0.23 mV *less* high [D]. Why a slot lowers R_shared [I, no field map was drawn]: it closes off the copper around U2 pin 2 to the south, so little return current flows past the pin and the pin sits nearer TB2-2's potential. **No reroute is needed:** the larger term is under 0.22 mΩ, and the term the INA228 sees moves the right way.
- **The Kelvin GND (owner, 17:09 save).** U2 pin 2 is now its own net, GND_SENSE. A net tie (`NetTie-2_SMD_Pad0.5mm`; its reference is still `REF**`, O16) joins it to GND on F.Cu: pad 1 sits on TB2-2's pad edge at (17.54, 25.17), and a 0.5 mm track runs 8.87 mm from pad 2 to U2 pin 2 [M, board file]. TB2-2's zone connection is Solid. The edit moved one stitching via and added another (77 → 78). The fills changed from 1278.9 to 1270.0 mm² on the two-layer zone and from 1772.5 to 1775.9 mm² on the B.Cu zone [M, pcbnew]. In the table's row order [D, `gnd_drop.py`]:
  - **Whole pour** 1.584 / 1.550 / 1.701 mΩ, down 0.045–0.048 mΩ from 15:16. At 3.64 A it drops 5.64–6.19 mV and loses 20.5–22.5 mW.
  - **The Kelvin residual**, V(TB2-2) − V(tie pad 1), is 0.0049 / 0.0024 / 0.0049 mΩ. The solver holds each pad at one potential, so it leaves out the spreading inside TB2-2's pad, from the pin out to the tie at its edge: 0.047 mΩ on one layer [D: 0.4926 mΩ/sq × ln(1.0/0.55) ÷ 2π, for radial flow from the 1.1 mm hole to the 2.0 mm pad's edge; the radial model is [I]].
  - So **VBUS reads high by ≤ 0.11 mV at 2.0 A and ≤ 0.20 mV at 3.64 A** [D: (0.0049 + 0.05) mΩ × I], down from 0.75–0.76 and 1.37–1.39 mV. That is about one 195.3 µV LSB at most, beside the INA228's own VBUS error of up to ±9.70 mV at 14.40 V [D: 14.40 V × 0.05 % + 2.5 mV, from TI SLYS021A p.5 [S]].
  - **Solid, not a thermal relief.** A relief with 0° spokes was tried and raised the whole pour by about 0.06 mΩ [D]. Solid puts TB2-2's pin straight into the pour on both layers, so it will take more heat to solder than its neighbours [I: falsifier, solder that does not wet the pin's whole ring at the iron's usual setting]. Inspect its fillet from both sides.
  - `gnd_drop.py` prints R_shared only when U2 pin 2 is on GND. On this file it skips that line without saying so (O16), and the residual above is read from its per-pad list.
- **Rev 0.8 (the 2026-10-08 10:48 save).** The tie, its pad positions and its track are unchanged, and its reference is now NT1. TB2-2's pad is now 3.0 mm and TB1-1's 2.0 mm, and both meet the pour through thermal reliefs, for hand soldering [M]. That supersedes "Solid, not a thermal relief" above. There are 85 stitching vias, and the fills are 1258.8 mm² on the two-layer zone and 1549.5 mm² on the B.Cu zone [M, pcbnew; a refill reproduces them]. In the table's row order [D, solver with the fix below]:
  - **Whole pour** 1.965 / 1.932 / 2.054 mΩ, up 0.380 / 0.381 / 0.353 mΩ from 17:09. The two reliefs account for 0.173–0.180 mΩ of that, found by changing only them on a copy of the owner's 2026-10-06 22:29 save [D]. The rest is copper that the wider power tracks, VIN+'s B.Cu run and the larger pads, with their clearances, take out of the pour [I: not split further]. At 3.64 A the pour drops 7.03–7.48 mV and loses 25.6–27.2 mW [D: I × R, I² × R]. The charge-path tracks fell by far more (§7.4), so the loop is lower overall.
  - **The Kelvin residual** is 0.0000 mΩ in all three rows. The tie's pad 1 now lies inside TB2-2's larger pad, so the solver puts both on one node. The spreading inside the pad, from the pin out to the tie, is unchanged at about 0.047 mΩ, because the tie is still 1.0 mm from the pin's centre [D: as above; the radial model is [I]]. So VBUS reads high by ≤ 0.10 mV at 2.0 A and ≤ 0.18 mV at 3.64 A [D: 0.047 mΩ × I].
  - **The repo's `gnd_drop.py` gives a false residual on rev 0.8** (O16). Once TB2-2's pad reaches about 2.5 mm, the tie's pad falls inside it, and the script then reads the residual from the wrong node: it printed 0.240 mΩ on the 08:04 save [D, false]. The figures above come from a copy with one line added, which numbers the tie's node last. The repo's script is not yet fixed.
- **Method.** Finite differences on the GND copper, rasterised at 0.1 mm and 0.05 mm. The model includes both layers' zone fills as KiCad refills them, the GND tracks, and the through-hole GND pads (both layers, each pad one node). It also includes the stitching vias (78 at 17:09, 77 at 15:16), as ideal links or with a barrel resistance. Sheet resistance is 0.4926 mΩ/sq [D: ρ 1.724 × 10⁻⁸ Ω·m, annealed copper at 20 °C, ÷ 35 µm]. 1 A goes in at TB2's GND pad and out at TB1's. The solver finds each by reference and net, not by pad number (R13 note in the code, 2026-10-06: rev 0.7's TB1 swap broke the old pad-2 selection). The solver is [`pcb/gnd_drop.py`](pcb/gnd_drop.py); by default it reads the board file beside it.
- **Solver checks.** A uniform strip, solved by the same code, gave 1.9481 mΩ against 1.9457 mΩ exact. A pour cut in two is refused by its connectivity check, and a board with no TB2 is refused by the pad selection. `python gnd_drop.py --self-test` runs all three.
- **Limits (R11).** Two geometries. Rev 0.6 was computed on v4 (2026-10-03); its copper is byte-identical in v5, v6 and v7, whose diffs touch only silk text, the LED footprint (same pads, same nets) and a 3D-model offset [M]. A re-run on v7 reproduced all three rev 0.6 cases, on 2026-10-03 and again on 2026-10-06 with the fixed solver [M]. Rev 0.7 was computed on the 2026-10-06 15:16:19 file and on the 17:09:17 save. A pcbnew refill reproduces each saved fill exactly [M]. Left out: resistance inside the modules, the socket contacts, the solder joints, and temperature (copper at 20 °C; warmer copper reads higher). The copper thickness, 1 oz (35 µm), is assumed, not measured. The 1.5 mΩ barrel is [I].
- **Falsifier (T10).** With a known charge current flowing, probe the solder joints on the board's underside, not the screws. (1) TB2-2's pin to U2's socket pin 2 (GND_SENSE): ≤ ~0.11 mV at 2.0 A [D, above]. More than 0.5 mV falsifies the Kelvin figures [I: the margin covers a 0.1 mV meter resolution and probe placement]. (2) TB2-2's pin to TB1-1's pin: 3.1–3.4 mV at 2.0 A [D: 1.550–1.701 mΩ × 2.0 A]. More than 5 mV falsifies the pour model [I: the margin covers the 1 oz assumption, warm copper and the pin joints]. If either trips, look for a joint or a thin pour before a modelling error. **R13 (2026-10-06):** rev 0.6 and the first rev 0.7 draft put the probe on TB2-2's screw. That reading includes the terminal's own clamp-to-pin drop, which the model leaves out and which has not been measured [I: about 1 mΩ would add about 2 mV at 2.0 A], so a sound board could have tripped the old 1.5 mV threshold.

### 7.4 Improvement study, and the VIN+ re-route (planned 2026-10-06, done in rev 0.8)

After the Kelvin GND, the owner asked what else would improve the board electrically, and proposed a shorter VIN+ on B.Cu. Figures are [D] on the 17:09 save unless tagged, at 1 oz and 20 °C (§7.3, Limits). Two effects are kept apart:

- **What VBUS reads.** Only copper between the pack and the INA228's reference moves it: the pour's shared path (now ≤ ~0.055 mΩ, §7.3) and the VIN− track, which T10 measures inside R_series (§6.4).
- **What the loop costs.** Every charge-path conductor adds drop and heat: the board's tracks, the pour, the socket contacts and the lead. VIN+ is in the loop but upstream of the VBUS sense point, so changing it changes no reading. A lower loop resistance raises the opening current a little [I: T11 measures it, and FW-4's overload stop and t_ol are set from T11].

**Baseline: the 17:09 save** (309,654 B, sha256 `484347efc18dab8977edf261f263d09099937cb40ec9514db8752c9c1c653b5d`; its `.kicad_pro`, 9,805 B, sha256 `c2c4390b8853b105a179ccb513242b1f844c5a0ecbd582b303f57a4ee791b847`). Both were in [`pcb/`](pcb/) until rev 0.8 replaced them; git keeps them at commit `f77169e`.

| Quantity | 17:09 save | Source |
|---|---|---|
| Charge-path track: BATT_RAW, Batt_SW, VIN+ and VIN− | 38.10 mΩ | [D: each net's segments solved as a network, 0.4926 mΩ/sq, T-junctions split, vias ideal] |
| of which VIN+, U5 pad 3 → U2 pin 7: F.Cu only, 1.5 mm, 77.56 mm | 25.15 mΩ (25.47 taken as one series run) | [D, same] |
| Whole pour, TB2-2 → TB1-1, §7.3's three rows | 1.584 / 1.550 / 1.701 mΩ | [D, `gnd_drop.py`] |
| Kelvin residual, V(TB2-2) − V(tie pad 1), same rows | 0.0049 / 0.0024 / 0.0049 mΩ | [D, `gnd_drop.py`'s per-pad list] |
| Zone fill: two-layer zone / B.Cu zone | 1270.0 / 1775.9 mm², reproduced by a refill | [M, pcbnew] |
| Stitching vias | 78 | [M] |
| DRC | 0 errors, 26 warnings, 0 unconnected: §7's 26 entries | [M, kicad-cli 10.0.6] |

**Options**, at 2.0 A, the steady case:

| Option | Loop | VBUS | Outcome |
|---|---|---|---|
| Kelvin GND for U2 pin 2 | whole pour −0.045–0.048 mΩ | offset 1.37–1.39 → ≤ 0.20 mV at 3.64 A | **Done** (owner, 17:09; §7.3) |
| Widen VIN+ to fill its corridor | 25.5 → 17.3 mΩ: −16 mV, −33 mW | none | Possible. The left-edge run is boxed at 1.65–1.70 mm by TB2-2, U1 and H3, so most of the gain is on the other runs. **Superseded** by the B.Cu route, which rev 0.8 lays 2.9–4.0 mm wide (below) |
| 2 oz copper | track 38.10 → 19.05 mΩ, pour 1.58 → 0.79 mΩ: −38 mV, −76 mW | VIN− 5.67 → 2.84 mΩ, inside R_series, which T10 measures anyway | A fab option, not a layout change. Not taken up |
| Narrow +3V3 from 1.5 to 0.5 mm | F.Cu fill 1270.0 → 1342.3 mm² [M]; whole pour −0.018–0.023 mΩ | none | **Not worth it.** Safe: 0.5 mm carries 1.45 A at a 10 °C rise [D, IPC-2221 as in §6.4, A = 27.1 mil²]. But U3's output to the XIAO's 3V3 pin drops 44.4 mV at 600 mA, the D24V7F3's continuous rating [S, Pololu #5592 page], against 14.8 mV at 1.5 mm. 0.8 mm gives a whole pour within 0.005 mΩ of 0.5 mm's. +3V3 bounds no VIN+ corridor |
| Remote sense of the pack | — | would take R_series out of VBUS | **Rejected.** A loose sense wire would corrupt the reading the 14.60 V ceiling acts on (§9), and the wire would need its own fuse |
| VIN+ on B.Cu, shorter (owner) | about −7.3 mΩ: ~15 mV, ~29 mW [D on a hand route, not laid] | none | **Done** in rev 0.8 (O15 closed): 25.00 → 7.15 mΩ [D, the 2-D solve below], with no vias |

**Why not a straight line.** U5 pad 3 to U2 pin 7 is 37.3 mm straight [D, from the pad coordinates]. On B.Cu that line crosses GPIO4_SW near (28.5, 40.1) and the XIAO's top row of pins (y 38.38), whose gaps are 0.84 mm [M], too narrow for 1.5 mm. XIAO D7 is an unplated hole (§7.1), so the route passes beside it. GPIO4_SW cannot move to F.Cu whole, because there it would cross GPIO3.

**A route that fits**, hand-checked against the board's pads, tracks and holes, not laid: F.Cu from U5 pad 3 along the present route to (14.75, 52.5), between H3 and D7; four vias to B.Cu; B.Cu diagonally between H3 and C3 to (23.75, 43.5); along y 43.5, between the XIAO's top row and R1, to (34, 43.5); up past the right side of XIAO D0 to (37.46, 40.04); and up to U2 pin 7. About 54.2 mm: 17.8 mΩ of track plus ~0.4 mΩ for the vias [I: 1.5 mΩ per barrel, four in parallel], against 25.15 mΩ. It costs:

- GPIO4_SW hops to F.Cu and back, by two vias near (30.7, 42.25) and (32, 44.75), about 0.9 mm from GPIO3 [D, hand clearance].
- About six stitching vias move.
- A 1.5 mm track with 0.5 mm zone clearance each side cuts a 2.5 mm slot diagonally across the B.Cu pour, in the return path from TB2 to TB1. In return the F.Cu pour regains the left-edge and top strips the present route occupies. **Which way the whole pour moves is not known until it is solved.**

The owner's route may differ; the method below applies to whatever is laid.

**Evaluation method**, for the session that reviews the re-route. Run each step on a copy, and give each result against its baseline figure:

1. **Identity.** Copy the saved `.kicad_pcb` and `.kicad_pro` out of the owner's folder (KiCad keeps the original open), and record size, save time and sha256. Diff the board against the 17:09 baseline item by item: footprints, every pad's net, tracks by net and layer, vias and zone fills. Expect changes on VIN+, GPIO4_SW (if it hops) and GND vias only, and **no pad's net**. Name and explain anything else before going on.
2. **DRC**, `--severity-all --refill-zones`. Accept 0 errors and 0 unconnected. Compare the warnings as a set against the baseline's 26, and name any new one. Then inject a fault on the new route, such as a VIN+ via moved onto a GND via, and show that DRC reports it (R7).
3. **Fill.** A pcbnew refill must reproduce the saved fill areas, so the solver reads current copper.
4. **Pour.** Run `gnd_drop.py` on the copy three ways (`--h 0.1`; `--h 0.05`; `--barrel-mohm 1.5`) against 1.584 / 1.550 / 1.701 mΩ. Read the Kelvin residual from the per-pad list (O16) against 0.0049 / 0.0024 / 0.0049 mΩ. It should stay under 0.01 mΩ [I]; a larger one means the new slot changed the copper around TB2-2, so look at the tie's placement.
5. **VIN+.** Solve the VIN+ segments as a network, layer by layer, with each via at 1.5 mΩ [I], against 25.15 mΩ. The hand route predicts ~18.2.
6. **Net change in the loop** = ΔR(VIN+) + Δ(whole pour), in each of the three pour cases. Accept the re-route if all three are negative, and give the change in mV and mW at 2.0 A.
7. **Width and vias.** Keep VIN+ at 1.5 mm, like the rest of the power path; for any narrower segment, redo §6.4's IPC-2221 figure. Record the number of VIN+ vias and their drill. Four would share 3.64 A at 0.91 A each [D]; whether a 0.3 mm via carries that is not checked here.
8. **GPIO4_SW** still reaches U1 D2 and U4 pin 1 and nothing else (§7.2).
9. **Record.** Update §6.4, §7's netlist and verdicts, §7.3's Kelvin figures and this section; close O15; copy the file into `pcb/`; then export the Gerbers (O11).

The track network solve and the DRC set comparison were run with scratch scripts that are not in this repo; the method above is enough to repeat them.

**Outcome: rev 0.8, the owner's 2026-10-08 10:48 save** (§7 gives its identity and gate verdicts). The tracks were wider than some of their pads and joined by overlap, so the one-dimensional network solve above no longer applies. Both columns below therefore use a two-dimensional solve of each net's copper (tracks and pads, 0.05 mm cells, 0.4926 mΩ/sq, current entering and leaving at each pin's drill). On the 17:09 save it gives 37.33 mΩ for the four nets, against the network solve's 38.10.

| Quantity | 17:09 save | 10:48 save | Source |
|---|---|---|---|
| BATT_RAW track | 3.514 mΩ | 1.177 mΩ | [D, 2-D solve] |
| Batt_SW track | 3.469 mΩ | 1.484 mΩ | [D, same] |
| VIN+ track | 25.003 mΩ | 7.148 mΩ | [D, same] |
| VIN− track | 5.345 mΩ | 2.359 mΩ | [D, same] |
| Charge-path tracks, total | 37.33 mΩ | 12.17 mΩ | [D, sum] |
| Whole pour, §7.3's three rows | 1.584 / 1.550 / 1.701 mΩ | 1.965 / 1.932 / 2.054 mΩ | [D, `gnd_drop.py`; the 10:48 column with the tie numbered last, §7.3] |
| Kelvin residual, same rows | 0.0049 / 0.0024 / 0.0049 mΩ | 0.0000 mΩ in each | [D, same] |
| Zone fill: two-layer zone / B.Cu zone | 1270.0 / 1775.9 mm² | 1258.8 / 1549.5 mm² | [M, pcbnew; the 10:48 figures equal a refill] |
| Stitching vias | 78 | 85 | [M] |
| DRC | 0 errors, 26 warnings, 0 unconnected | 0 errors, 34 warnings, 0 unconnected | [M, kicad-cli 10.0.6] |

With the whole pad taken as the contact instead of the drill, the 10:48 tracks give 0.822 / 1.258 / 6.762 / 2.101 mΩ [D], so the drill figures are the conservative ones.

- **Net change in the loop** (step 6). VIN+ fell by 17.86 mΩ and the pour rose by 0.353–0.381 mΩ, so the re-route is accepted in all three pour cases [D]. Taking every change together, the board's share of the loop (tracks plus the pour's barrel row) went from 39.03 to 14.22 mΩ, down 24.81 mΩ [D]. That is 49.6 mV and 99 mW less at 2.0 A, and 90 mV and 329 mW less at 3.64 A [D: ΔR × I, ΔR × I²].
- **The board is now the smallest known term in the loop.** The known parts total 85.3–89.3 mΩ [D: board 14.22 + #2814 30 [S, §4.2, max at 10 V] + #5382 ≤ 10 [S, §6.4] + shunt 15 [S, Adafruit #5832] + lead 16.1–20.1 [D, §6.4]]. It leaves out the module socket contacts, TB1, TB2, the splice, the QDs and the pack, none of which has a figure here. At 3.64 A the known parts drop 0.31–0.33 V [D]. A lower loop raises the opening current, until the PSU's overload limit caps it (§4.1) [I: T11 measures it, and FW-4's overload stop and t_ol are set from T11].
- **Departures from the plan above.**
  - Step 1 expected changes on VIN+, GPIO4_SW and GND vias only. Rev 0.8 also widened every power net, enlarged pads, changed two zone connections and moved parts (§7's rev 0.8 list). Each was named before going on, and **no pad's net changed** [M: the (part, pad, net) sets of the two saves are equal, apart from one XIAO pin with no net, whose pad name went from blank to D6].
  - Step 2's fault was injected on V_Fused, not on VIN+, because VIN+ has no vias in rev 0.8.
  - Step 5 has no barrel term, for the same reason.
  - Step 7: VIN+ is 2.9–4.0 mm, wider than the 1.5 mm asked for, so §6.4's IPC-2221 figures are redone for the new widths.
  - Step 8 holds: GPIO4_SW reaches U1 D2 and U4 pin 1 and nothing else [M].
  - Step 9 is this revision, except the Gerbers (O11).
- **R13 (2026-10-08): some of rev 0.8's copper began as edits written by a review session, not by the owner.** On 2026-10-06 at 20:35, the session reviewing the board wrote a set of scripted edits into the owner's board file (session 4dcbc5e4). One of them widened the power path, and with it the BATT_RAW branch from U4 to F1, from 1.5 to 2.95–3.95 mm. That branch carries only the board supply (§6.4), so its width bought nothing. The same edit set TB1-1's pour connection to solid, which was never weighed against hand soldering. Neither was recorded here. Later review sessions found both and noted them only in their local review notes. The owner returned TB1-1 to a thermal relief in the 2026-10-07 19:09 save and narrowed the branch to 2.0 mm in the 2026-10-08 09:46 save. The rest of that edit, the wider charge path, is in rev 0.8 at the widths §7 lists.

**Limits (R11).** These are copper resistances at 1 oz and 20 °C, computed on one file. They leave out the socket contacts, the solder joints and the modules' own copper, and the via barrel is [I]. Nothing here has been measured on a built board; T10 measures the series path whole.

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
| FW-11 | **Status LED (GPIO3, XIAO D1; active-high, through R1 1 kΩ; §5.5)**, the only local indicator when Wi-Fi is down. IDLE: one short blink every 3 s. CHARGING: 500 ms on / 500 ms off; a hung CPU freezes it on or off. DONE: two short blinks every 3 s. FAULT: 4 Hz |
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
| T7 | **Rev 0.6:** mid-session, hold SDA to GND with a clip lead from U2's SDA pin (pin 4) to a GND point. Then, **AC off**, remove the INA228, power up, and press Start | OFF, FAULT "sensor"; Start refused (NaN, FW-3), with ON < 1 V at U4 pin 1 | — |
| T8 | Test build: T_max = 1 min | OFF at 1 min | — |
| T9 | Pull AC mid-session, then restore | Stays OFF | — |
| T10 | On the pack, at a steady known current | DMM at the pack terminals vs VBUS → **R_series** (analysis only: V_batt downstream, and FW-12's split, §6.4). Also, at the solder joints on the underside (R13: not the screws), mV from TB2-2's pin to U2's socket pin 2: ≤ ~0.11 mV at 2.0 A, and more than 0.5 mV falsifies; and from TB2-2's pin to TB1-1's pin: 3.1–3.4 mV, and more than 5 mV falsifies (§7.3) | — |
| T11 | First **supervised** session, on a pack fresh off the P20 | Log the current at 14.40 V (the balancer question, §2); set V_hold, T_hold, T_max, t_ol (how long the opening current stays above 2.0 A) and FW-5's thresholds; note how long the pack takes to rest below V_hold. Session 1 may end in an FW-5 trip | — |
| T12 | Let the countdown timer expire mid-session | Everything dark: LED off, pack current 0. This proves the ideal diode stops the pack keeping the board alive (§5) | — |
| T13 | *Withdrawn in rev 0.5* (DS18B20 dropped) | — | — |
| T14 | Test build: overload threshold below the load current | OFF after t_ol, FAULT "overload" | Production threshold (2.0 A) on the 10 Ω load: a full session, no trip |

Any firmware edit re-runs T1–T4, T6–T9 and T14 (R7: a gate untested against a known-bad input is not a gate).

**Why T7 changed in rev 0.6.** On the board, the INA228 is in the charge path: VIN+ and VIN− pass through its socket contacts 7 and 6 (§6.4). Unplugging it mid-session would break up to 3.64 A at a socket contact. It would also end the charge by opening the path, so the test could pass without the firmware doing anything. And it would tilt a module carrying ~14 V on pin 7 beside SDA and SCL on pins 4 and 3. Holding SDA low produces the same I2C read failure without touching the power path [I: the ESP32's I2C pins are open-drain, so the short fights only the breakout's pull-ups]. **Never unplug U2 with AC on.**

---

## 12. Open items

| # | Item | Status |
|---|---|---|
| Q1 | Cyclenbatt label: charge voltage, charge temperature range, and does the BMS balance? | **Answered 2026-09-21:** 14.4–14.6 V; charge above 32 °F; no balance details |
| Q2 | Does the Cyclenbatt label give an **upper** charge temperature? | **Answered 2026-09-22:** none on the label. RQ-11 is met by siting |
| Q3 | Is the on-hand 5 A fuse a mini (ATM/APM) or a regular (ATC) blade, and whose make? | **Answered 2026-09-22:** mini (ATM/APM), from an AKOSN assortment kit with no maker's datasheet (O2) |
| Q4 | Which 3-stage charger does the bulk charge, and what are its LiFePO4 voltage, current and end-of-charge behaviour? | **Answered 2026-09-22:** Dylannet P20 at 5 A (§4.3) |
| Q5 | How is U5 (#5382) mounted on the board? | **Answered 2026-10-03:** soldered on pin headers, ~2.54 mm above the board (§7) |
| Q6 | Is the status LED 3 mm (the LTL-4231N in the Value field) or 5 mm (the rev 0.6 draft's footprint)? | **Answered 2026-10-03** by the owner's v6 edit: `LED_D3.0mm`, with the pads unchanged (§5.5) |
| O1 | Charge current limit | **Closed:** 0.5 C = 5.0 A, owner 2026-09-21 |
| O2 | A fuse whose DC interrupt rating can be cited | The AKOSN kit fuse has no datasheet, so RQ-5 is unproven with it. Buy a branded 5 A mini fuse whose maker publishes a DC interrupt rating, then cite it |
| O3 | HDR-30 overload below 50% Vout (hiccup) | **Closed 2026-09-22:** hiccup below 50% of rated output voltage, constant-current limiting from 50% to 100%, both "recover automatically after fault condition is removed" [S, p.2] (§4.1) |
| O4 | Charger firmware | Not written; FW-1 and FW-3…FW-12 are the spec. The ESPHome facts in FW-8…FW-10 were read in the 2026.8.2 source: re-check them on the Device Builder add-on's version before the compile gate |
| O5 | V_hold, T_hold, T_max, t_ol, FW-5's step and floor thresholds | Set from T11. T_hold is also bounded by the host's no-backup window (§10.2) |
| O6 | Enclosure | ABS, vented, DIN rail offcut, cord grips G1–G2; the board on nylon M3 screws and standoffs at H1, H3 and H4 (owner, 2026-10-06; rev 0.6: no lever nuts). In rev 0.7 all three holes are under modules, so mount the board before seating them (§7). The #2814 overhangs the board's right edge in rev 0.7 (owner: intentional): its board by 0.66 mm and its slide knob by about 1.56 mm [D: the module's edge at U4's origin, x 43.66, against the board edge at 43.0; the knob 0.9 mm past the module's board, psw04b]. In rev 0.6, against a 44.0 mm edge, the knob stood 0.56 mm past [D, 2026-10-03 review]. Leave it room. Leave room too for wire entry at TB1 (the left edge) and TB2 (the top edge, §5.1). The XIAO's U.FL antenna needs an RF-transparent box [[ws] §8.2, item J] |
| O7 | [component-selection.md](../docs/component-selection.md) gives 14.4–14.6 V as the BMS **over-voltage cutoff**. The label gives that range as the **charge voltage**, so the BMS cutoff value is undocumented [I: a maker would not rate charging at its own cutoff] | Correct that doc (now in this repo); this one does not rely on it |
| O8 | §10.2 bleed to ≤ 13.3 V | No load or method named |
| O9 | TB1/TB2 part and wire range (rev 0.6; it was the INA228 breakout's 3.5 mm terminal block, which is no longer used because VIN± go through the socket) | **Closed 2026-10-06** (owner): Phoenix BC-381X9-2 GN, item 5442756. It takes 26–16 AWG (0.14–1.5 mm²), so 16 AWG at TB2 (W16, W18) and 18 AWG at TB1 (W3, W6), and is rated 13.5 A (UL 10 A), above 3.64 A [S, Phoenix product page for 5442756, owner-supplied text]. Its 7.62 × 7.3 mm body and 1.1 mm holes match the board's MKDS footprint (§5.1). The board had named only the footprint |
| O10 | UPS Open Item 16, a coulomb-counted recharge to termination | **Not served since rev 0.5:** the P20 does the bulk charge and counts nothing. The owner's call whether to serve it another way |
| O11 | Board files in the repo | **Partly done 2026-10-03:** the board file (v7), its `.kicad_pro` design rules and §7.3's solver are in [`pcb/`](pcb/), so §7's [M] citations can be re-read from this repo. **2026-10-06:** rev 0.7's board file and `.kicad_pro` replace v7's there: the owner's 17:09:17 save, with the Kelvin GND (§7.3). Still open: commit the Gerbers actually sent to OSH Park, which become the authority for what was built. The Gerbers beside the owner's board file predate rev 0.7 [M: written 2026-10-04 17:02, on the old outline], so re-export them, after O15's re-route is evaluated. **Rev 0.8 (2026-10-08):** the 11:00 save (§7: the 10:48 save that was checked, plus 3D models) and its `.kicad_pro` replace rev 0.7's in `pcb/`. Still open: in KiCad, press B (Fill All Zones) and save, run DRC on the saved file, then export the Gerbers from it. The 09:46 save showed why the fill matters: its saved fill shorted BATT_RAW to GND until a refill (§7). There is no schematic, so KiCad's parity check cannot run (§7) |
| O12 | LED vs the USB-C plug | In rev 0.7 the XIAO's USB-C socket points straight at the LED, 1.0 mm off its axis, so a cable's overmold passes directly over the LED. The 3D render gives about 2 mm of clearance for an 8 mm overmold [I, §5.5]; the overmold size is assumed. Dry-fit before soldering the LED (§5.5). **Closed in rev 0.8:** the LED moved to the left edge, below the XIAO, and nothing stands in front of the USB-C [M, §5.5] |
| O13 | Silk and text, before the order | (a) The B.Silk text "Board Size: 31.5mm x 90mm / 1 1/4" x 3 1/2"" is stale: the board is 95 mm long [M, Edge.Cuts]. (b) That text, and the B.Silk "W. Collis", sit over pads (R1; U4 pads 2–5) [M, DRC silk_over_copper]. Whether OSH Park clips silk from pads is not checked. (c) The LED's reference text overlaps U2's outline [M, DRC silk_overlap]. (d) The LED's Value text still names `LED_D5.0mm`. That is on F.Fab, which is not fabricated, so it is a file-only fix. **Rev 0.7 (2026-10-06):** (a) fixed: the text reads "Board Size: 29.5mm x 78mm", which matches Edge.Cuts [M]. (b) fixed: no B.Silk is over a pad [M, DRC]. (c) fixed. (d) still open. (e) new: U1's footprint text and reference sit over H3's hole, and a U1 F.Silk segment crosses LED pad 2 [M, DRC silk_over_copper]. Whether OSH Park clips these is not checked. **Rev 0.8 (2026-10-08):** (e) fixed [M, DRC]. (d) still open. (f) new, from the enlarged pads: the module outlines now cross their own pads, U2's over U2 pin 7 and C2 pad 2 (two warnings each), U4's over pins 11 and 12, and U5's over pads 1 and 3 [M, DRC silk_over_copper]; and U3's outline lies on the board edge at y 98.0, though its pads are 1.15 mm inside [M, DRC silk_edge_clearance]. All are cosmetic; whether the fab clips them is not checked. U3's module now sits flush with the board's end, which matters for an enclosure |
| O14 | TB1's labels hidden under U4 | All of TB1's `+`/`GND` silk sits inside the #2814's outline (x ≥ 20.76 mm [M]), so it is covered once U4 is seated. Read it before U4 goes in, or go by "upper screw `+`" (§5.1). It would be fixed by moving the labels left of x 20.76 mm. **Rev 0.7:** still open. The labels are at x 21.5 (`+`) and 22.5 (`GND`), inside U4's outline at x ≥ 20.7 [M], and the rule is now "**lower** screw `+`" (§5.1). TB2's `+` is likewise under U2. **Rev 0.8:** TB1's part is fixed: the labels are at (16.5, 66.0) `GND` and (17.0, 74.5) `+`, left of U4's outline [M]; the rule is unchanged, "lower screw `+`". TB2's `+` at (20.0, 29.5) is still inside U2's outline at x ≥ 18.5 [M], so that part stays open |
| O15 | VIN+ re-route to B.Cu (owner, planned 2026-10-06) | Open. The owner will move VIN+ to the bottom layer and shorten it. A new session evaluates the saved file by §7.4's method, against its 17:09 baseline, **before** the Gerbers are exported (O11). **Closed in rev 0.8 (2026-10-08).** The owner moved VIN+ to B.Cu, 2.9–4.0 mm wide, with no vias; its track fell from 25.00 to 7.15 mΩ [D], and the evaluation by §7.4's method is that section's Outcome |
| O16 | Two loose ends from the Kelvin edit | Open. (a) The net tie's reference is still `REF**`: rename it (NT1) before the order, and here. (b) `gnd_drop.py` prints R_shared only when U2 pin 2 is on GND, so on the 17:09 file it skips that line without saying so (R8). Fix: print the residual to the GND_SENSE tie's GND pad, or say why it is skipped. **Rev 0.8:** (a) closed, the tie is NT1 [M]. (b) is worse: on rev 0.8 the residual line the script does print is false, because the tie's pad falls inside TB2-2's enlarged pad (§7.3). The fix found is one line that numbers the tie's node last; it is not yet in the repo |

---

## 13. Purchase list

| Item | Price / note |
|---|---|
| Mean Well **HDR-30-15** | $13.50 (Arrow) to $17.76 (TRC), from search listings on 2026-09-21, not read on the vendor pages |
| Pololu **#2814** Big MOSFET Slide Switch, MP | $5.49 [S, Pololu page, 2026-09-21]. Ships with 5 mm terminal blocks and 0.1″ headers |
| Plug-in countdown timer (mechanical or standalone digital, **no Wi-Fi**) | L6 |
| ABS enclosure, vented; DIN rail offcut; 2 cord grips | O6 |
| **Top Off Charger PCB** (rev 0.7, §7) | OSH Park; not priced here. Order from Gerbers re-exported from rev 0.7 (O11), after O13 |
| Sullins 0.100″ female sockets, 8.5 mm: 2 × 1×7 (U1), 1×8 (U2), 1×3 (U3), 2 × 1×6 (U4) | 3 A per contact [S, Sullins catalog pp.114–115]. Cut from longer strips if that is what is on hand |
| Male pins for U5 (#5382), fitted singly | The pads are not on a 0.1″ grid [M, board file v6 and 2026-10-06], so a strip will not fit. Soldered with the module ~2.54 mm up (Q5) |
| Würth **696108003002** 5 × 20 mm PCB fuse holder, and a **1 A slow-blow** 5 × 20 mm fuse | F1 [M, Value field]. The board supply only, not the charge path |
| C1 10 µF 25 V X7R; C2, C3, C5 0.1 µF 50 V X7R; C4 47 µF 50 V radial 6.3 × 11 mm; R1 1 kΩ 1/4 W axial | [M, Value fields] |
| Lite-On **LTL-4231N** green, 3 mm (LCSC C125082) | Status LED [listing]. Polarity: §5.5 |
| TB1, TB2: two Phoenix **BC-381X9-2 GN** (item 5442756), 2-position 3.81 mm PCB screw terminals | O9, closed 2026-10-06 (owner). Not priced here |
| Nylon M3 screws and standoffs, 3 sets (H1, H3, H4) | Owner, 2026-10-06. Fit before the modules (§7) |
| One 16–14 AWG heat-shrink butt splice | S1, if not on hand |
| 16 AWG red/black (W16, W18); 18 AWG red/black (W3, W6); 2-conductor AC cord | if not on hand. Rev 0.6 needs no 22 AWG or 24–26 AWG wire: the board carries those nets |
| Branded 5 A mini (ATM) blade fuse with a published DC interrupt rating | O2. Not priced here |
| 10 Ω, ≥ 25 W resistor | Commissioning load (§11), if not on hand |

**On hand** [owner, 2026-09-21 and 2026-09-22]: the inline fuse holder and an AKOSN mini-blade kit (no datasheet, O2); F2 female spade QDs; Wago 3- and 5-position lever nuts; the Dylannet P20 (§4.3). From rev 0.2: a V2 Rev 1.1 board and parts, XIAO ESP32-C3, Adafruit INA228, DS18B20 module (unused from rev 0.5), and the spare Pololu #5382 (bought as a pair, one used [[bom.md](../docs/bom.md)]). **From rev 0.6 the lever nuts and the V2 board are not used.** Check the V2 parts on hand before buying the board's passives, fuse holder and LED.

**Budget: $43** [owner]. PSU + switch + Pololu shipping comes to $25.44–$29.70 [D: 13.50 or 17.76, + 5.49 + 6.45; the $6.45 is the UPS order's Pololu USPS charge in [bom.md](../docs/bom.md), not a current quote]. That leaves $13.30–$17.56 [D] for the PSU's shipping, the timer, the enclosure, the cord grips and the replacement fuse. **The board and its parts are not in this arithmetic.** Whether they fit the $43 is the owner's call once the OSH Park quote is in.

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
- **Rev 0.6 board:** `Top Off Charger- Oct 2026.kicad_pcb`, the owner's file, read in v4–v7 (2026-10-03, 22:11:51 to 22:42:18) from scratch copies. It was never opened for writing. The reads used kicad-cli 10.0 (`pcb drc --severity-all --refill-zones`, `pcb render`) and an s-expression parse for the pads, nets, tracks and zones. The §7.3 solver is `gnd_drop.py`. v7, its `.kicad_pro` and the solver are in [`pcb/`](pcb/); the Gerbers are not yet (O11).
- **Rev 0.7 board:** the same file, re-laid by the owner, saved 2026-10-06 15:16:19 (309,671 B), read from a scratch copy and never opened for writing. The reads used kicad-cli 10.0.6 (`pcb drc --severity-all --refill-zones`) and KiCad 10.0.6's pcbnew Python (pads, nets, tracks, vias; zone refills for the §7.3 B.Cu cases, saved to scratch files only). It and its `.kicad_pro` replace v7 in [`pcb/`](pcb/).
- Phoenix Contact product page for item 5442756, BC-381X9-2 GN (owner-supplied text, 2026-10-06): 3.81 mm pitch, 7.62 × 7.3 mm, 8.5 mm installed height, 1.1 mm hole, 26–16 AWG (0.14–1.5 mm²), ferrules 0.25–0.5 mm², 5 mm strip, 0.22–0.25 Nm, 13.5 A (UL 10 A).
- Pololu #2814 dimension drawing (psw04b, 2016-01-14) and the #5382 outline DXF (the pads on a 0.150″ pitch), both the owner's copies, read 2026-10-03.
- Sullins 0.100″ female header catalog pages, pp.114–115 (owner-supplied, 2026-10-03): 3 A per contact, 8.50 mm body.
- [Seeed XIAO ESP32C3 wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/): pin map (D1 GPIO3, D2 GPIO4, D4/D5 GPIO6/7, D7 GPIO20) and the strapping pins, read 2026-10-03.
- [LCSC C125082](https://lcsc.com/product-detail/Light-Emitting-Diodes-LED_green_C125082.html) (Lite-On LTL-4231N: 3 mm, green, 2.1 V), read 2026-10-03 and cited as [listing]. Lite-On's own datasheet, DS-20-92-0246, could not be retrieved: the maker's site rejected the request and Mouser timed out. So the "long leg = anode" in §5.5 is convention [I], and a DMM diode test settles it.
- IPC-2221 external-conductor current formula, I = 0.048 · ΔT^0.44 · A^0.725 (A in mil²), as widely published. The standard itself was not read (§6.4).
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
| 0.6 | 2026-10-03 | **A purpose-built board replaces the V2 reuse and the lever nuts** (§7: `Top Off Charger- Oct 2026.kicad_pcb`, v7; DRC 0 errors, 26 warnings, 0 unconnected; schematic parity did not run, as there is no schematic). The modules sit on Sullins sockets, and U5 is soldered on pins (Q5). **TB1/TB2 replace WP/WG/WL**, W4/W5 and W7–W14 become copper, and the J2 control pair is gone, so it can no longer be swapped (§5.1, §7.2). **Status LED moves to GPIO3 (D1)** on a 3 mm footprint (Q6), with a polarity call-out: which leg goes in which hole (§5.5). **Staged first power**, one module at a time (§5.4). **Ground pour** analysed: VBUS reads high by ~0.38 mV/A [D] (§7.3; T10 falsifier). §6.4 adds the board copper and the socket contacts to the conductor checks. **T7 changed**: holding SDA to GND replaces unplugging the INA228, which now carries the charge current (§11). O6 and O9 revised; O11–O14 added. The board file, its `.kicad_pro` and the §7.3 solver are committed in `pcb/` (O11). §13 adds the board's parts and drops the J2, #5382 terminal block and thin-wire rows |
| 0.7 | 2026-10-06 | **Board re-laid smaller** (owner): 29.5 × 78 mm, was 31.5 × 95. DRC 0 errors, 26 warnings, 0 unconnected; schematic parity did not run (§7). The netlist is unchanged except **TB1's pins, which are swapped** (owner: intentional): pin 1 is now GND and pin 2 BATT_RAW, so the PSU's +V goes to the **lower** screw (§5.1, §5.2 W3/W6, O14). **TB1/TB2 named: Phoenix 5442756** (O9 closed), with landing data (§5.1). **Status LED moved and turned 180°**: it now sits in line with the XIAO's USB-C, and its square pad is the right hole (§5.5, O12). XIAO D6/D7 became unplated holes (owner, §7.1). GPIO4_SW, SDA and SCL moved to B.Cu; stitching vias 92 → 77. **Assembly order** for U5 (now under U4), the nylon standoffs and TB2 (§7). **Electrical** [D]: the charge-path tracks fall by 5.59 mΩ (VIN− 8.0 → 5.7, which is in R_series) and the whole pour by 0.070–0.104 mΩ; the VBUS offset is unchanged at ~0.38 mV/A at 15:16 (§6.4, §7.3). The B.Cu tracks were sized by deleting them and refilling: +0.173–0.218 mΩ on the whole pour, −0.057–0.064 mΩ on R_shared; no reroute (§7.3). **`gnd_drop.py` fixed** (R13 note in the code): it selected pad 2 of each terminal block and failed on rev 0.7; it now finds TB2's and TB1's GND pads by reference and net, and its self-test gains a third direction. O6, O11, O13 and O14 revised. **Kelvin GND** (the owner's 17:09 save): U2 pin 2 is now net GND_SENSE, joined to GND at TB2-2's pad by a net tie and a 0.5 mm track. The VBUS offset falls from 1.37–1.39 mV to ≤ 0.20 mV at 3.64 A, and the whole pour by 0.045–0.048 mΩ [D]; DRC is unchanged, the same 26 warnings (§5, §7, §7.3). **The lead is 24–30 in** (owner; W16, §6.4): 16.1–20.1 mΩ, below the board's 38.10 mΩ of charge-path track. **T10's pour probes move to the solder joints** (R13, §7.3). **§7.4** records the improvement study, and the method and baseline for the owner's planned B.Cu VIN+ re-route (O15). O11 revised; O15 and O16 added |
| 0.8 | 2026-10-08 | **Rev 0.8 board** (checked on the owner's 10:48 save; [`pcb/`](pcb/) holds the 11:00 save, which adds only 3D models, §7). **VIN+ re-routed on B.Cu** (O15 closed), 2.9–4.0 mm, no vias. The other charge-path tracks are widened to 2.9–4.0 mm, with VIN− at 3.85 mm necking to 1.7. Pads are enlarged for hand soldering, TB1-1 and TB2-2 are on thermal reliefs, the stitching vias go 78 → 85, and the net tie is named NT1 (O16(a)). DRC 0 errors, 34 warnings, 0 unconnected (+11/−3 against rev 0.7, each named in §7); schematic parity did not run. No pad's net changed [M]. **Electrical** [D, 2-D solve, §7.4]: the charge-path tracks fall from 37.33 to 12.17 mΩ (VIN+ 25.00 → 7.15), and the whole pour rises by 0.353–0.381 mΩ. The board's share of the loop falls from 39.03 to 14.22 mΩ, which is 90 mV and 329 mW less at 3.64 A (§6.4, §7.3). The Kelvin residual is 0.0000 mΩ. **Placement** (§7): the status LED moved to the left edge, below the XIAO, so its **round (anode) hole is now the one nearer the board edge** (§5.5; O12 closed). TB1 moved 4.5 mm down, so its labels can be read with U4 seated (§5.1; O14's TB1 part closed). Other parts made smaller moves. **R13** (§7.4): a review session's 2026-10-06 edits widened F1's board-supply branch for no gain and set TB1-1 solid without weighing hand soldering. The owner has since put TB1-1 back on a relief and narrowed the branch to 2.0 mm. `gnd_drop.py`'s residual is false on rev 0.8 (O16(b)), and its fix is not yet in the repo. O11, O13 and O14 revised; the Gerbers are still to be exported (O11) |
