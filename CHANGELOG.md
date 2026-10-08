# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Pending
- Physical build and assembly
- Home Assistant automation documentation
- Runtime validation testing

---

## [2026-10-08] — 2026-10-08

### Added
- `Top-Off-Charger/pcb/Top Off Charger- Oct 2026.pcb-eval.json` (35c07cc): this board's profile for the Tools repo's pcb-eval tools (netdrop, gnd_drop, dump, tracknet). Since Tools 9273225 those tools hold no board's pads and refuse a board without a profile. It names the pads they held until 2026-10-08. Run on this board with no flag, they print the same figures as before apart from the profile line (whole GND pour 1.9645 mΩ [M, h = 0.1 mm]).

### Changed
- `Top-Off-Charger/pcb/`: the owner's 2026-10-08 11:00:58 save, rev 0.8, replaces the 17:09:17 one (e27eeab). VIN+ is re-routed on B.Cu and the power path is wider; TB1 moved 4.5 mm down so its labels can be read with U4 seated; the LED is on the left edge. All checks ran on the 10:48:22 save; the 11:00 save adds only U1's 3D models and its DRC set is identical. DRC 0 errors / 34 warnings / 0 unconnected [M, kicad-cli DRC with the board's own rules]. Schematic parity did not run (no schematic).
- `Top-Off-Charger/top-off-charger-design.md` rev 0.8 (e27eeab): §6.4's charge-path track resistance 37.33 → 12.17 mΩ [D, 2-D solve, §6.4]; §5.1 and §5.5 for the TB1 and LED moves, with the polarity table rewritten; §7, §7.3 and §7.4 for the rev 0.8 gate verdicts, pour and Kelvin figures, and an R13 record of a review session's 2026-10-06 edits to the board. O12 and O15 closed; O11, O13, O14 and O16 revised. The Gerbers are still to be exported (O11). §7 also gives the LF sha256 git stores for each board file beside the CRLF one KiCad writes (1ef6daa).

### Fixed
- `Top-Off-Charger/pcb/gnd_drop.py` (2389987): from the 2026-10-07 19:09 save on, TB2-2's enlarged pad covers the net tie's GND pad, and the tie's per-pad line read another node's voltage. It printed a Kelvin residual of 0.24–0.26 mΩ [D, false] where the solve gives 0.0000. A pad that loses all its copper to a later pad is now numbered last, and a pad left with no node is refused (O16(b)). Saves from 2026-10-06 15:16 to 22:29 give the same per-pad values as before [M, both scripts on all 17 saves, `--h 0.1`].
- R13, 2026-10-08: e27eeab, 1ef6daa and 2389987 shipped without these entries. They were added afterwards, in a commit of their own.

### Removed
- `Top-Off-Charger/pcb/gnd_drop.py`: moved to the Tools repo as `pcb-eval/solve/gnd_drop.py` (Tools 6fe2087, byte-identical to 2389987), with the other board review tools. Since Tools e273314 the board file is a required argument; its default was the board beside the script. Design doc §7.3 and §7.4 point there.

---

## [2026-10-06] — 2026-10-06

### Changed
- `Top-Off-Charger/pcb/`: the owner's re-laid board, `Top Off Charger- Oct 2026.kicad_pcb` (saved 2026-10-06 15:16:19; 29.5 × 78 mm, was 31.5 × 95), and its `.kicad_pro` replace v7. The `.kicad_pro` differs only in the default pad width for new pads and the last plot path, so the design rules are unchanged. DRC gives 0 errors, 26 warnings (all silk or library) and 0 unconnected; schematic parity did not run, as there is no schematic. The Gerbers have not been exported from this layout.
- `Top-Off-Charger/top-off-charger-design.md` rev 0.7, for that layout. TB1's pins are swapped, so the PSU's +V lands on the lower screw. The terminal blocks are named as Phoenix 5442756 (O9 closed). The LED moved and turned 180°, XIAO D6/D7 became unplated holes, and three signals moved to B.Cu. The assembly order is set for the parts under the modules. §7.3 compares the electrical figures with rev 0.6, including what the B.Cu tracks cost the ground pour. Its §15 lists the changes.
- `Top-Off-Charger/pcb/`: the owner's 17:09:17 save of the same board replaces the 15:16:19 one. It adds a Kelvin GND: U2 pin 2 moves to a new net, GND_SENSE, joined to GND at TB2-2's pad by a net tie and a 0.5 mm track. DRC is unchanged: 0 errors, 26 warnings and 0 unconnected, the same 26 entries. The `.kicad_pro` differs only in the default size and drill of new pads.
- `Top-Off-Charger/top-off-charger-design.md`, still rev 0.7: the Kelvin GND takes the VBUS offset from 1.37–1.39 mV to ≤ 0.20 mV at 3.64 A (§5, §7.3). The lead is 24–30 in (owner), so §6.4's example now drops 58–73 mV at 3.64 A, not 146. New §7.4: the improvement study (Kelvin GND, a wider VIN+, 2 oz copper, a narrower +3V3, remote sense, a B.Cu VIN+), and the baseline and method for evaluating the owner's planned B.Cu VIN+ re-route (O15). O16 records the net tie's `REF**` reference and `gnd_drop.py` skipping R_shared without saying so.

### Fixed
- `Top-Off-Charger/top-off-charger-design.md` §7.3 and T10: the pour check probed TB2-2's screw. That adds the terminal's own clamp-to-pin drop, which is not measured and could trip the 1.5 mV threshold on a sound board. It now probes the solder joints, with new figures (R13 note at the site).
- `Top-Off-Charger/pcb/gnd_drop.py`: it took pad 2 of each terminal block as the GND pads. On the rev 0.7 board TB1's GND is pad 1, so it stopped with "expected two terminal-block GND pads". It now finds TB2's and TB1's GND pads by reference and net (R13 note at the site). `--self-test` adds a third direction: a board with no TB2 must be refused. Re-run on rev 0.6's v7, it reproduces the doc's rev 0.6 figures exactly.

---

## [2026-10-03] — 2026-10-03

### Added
- `Top-Off-Charger/pcb/`: the owner's charger board, `Top Off Charger- Oct 2026.kicad_pcb` (KiCad 10, v7 saved 2026-10-03 22:42:18), and its `.kicad_pro` design rules. DRC with those rules gives 0 errors, 26 warnings (all silk or library) and 0 unconnected. Schematic parity did not run, as there is no schematic. The `.kicad_prl` (per-user view state) is not committed, and the Gerbers are not exported yet.
- `Top-Off-Charger/pcb/gnd_drop.py`: a finite-difference solver for the voltage drop across the GND pour, which the design doc's §7.3 uses. `--self-test` checks it against a uniform strip with an exact answer and confirms that a pour cut in two is refused.

### Changed
- `Top-Off-Charger/top-off-charger-design.md` rev 0.6: a purpose-built board (§7) replaces the reuse of the V2 board and the lever nuts. Screw terminals TB1/TB2 and board copper replace most of the loose wiring. The status LED moves to GPIO3 (D1), on a 3 mm footprint, with a call-out for which leg goes in which pad (§5.5). Other additions: staged first power (§5.4), a ground-pour drop analysis (§7.3, falsified by T10) and the board's parts (§13). T7 now holds SDA to GND instead of unplugging the INA228. Open items O11–O14 are new. Rev 0.5 had no CHANGELOG entry; this one does not backfill it.

---

## [2026-09-21] — 2026-09-21

### Added
- `Top-Off-Charger/top-off-charger-design.md` rev 0.3: a pre-build design for a bench top-off / top-balance charger for the Cyclenbatt, which is removed from the UPS for each session. Moved from `Lifepo4-Battery-Banks/Top-Off Charger/` (rev 0.2, `680caed`) and scoped to this pack only. It includes from/to wiring tables with Wago splice nodes. Nothing is built, and the firmware is not written.

### Changed
- `Top-Off-Charger/top-off-charger-design.md` rev 0.4: the series resistor Rs is withdrawn, so GPIO4 drives the switch's ON pin directly. A continuity check before first power and a 5 mA pin drive strength take over Rs's job. The pin-leakage figure is corrected (R13).

---

## [2026-03-06c] — 2026-03-06

### Changed
- Corrected total system load: ~13.8W → ~13.7W (13.17 + 0.50 + 0.02 = 13.69W)
- Clarified that DC values are estimates based on 82.5% assumed adapter efficiency
- Added "AC Measured" column to README performance table
- Updated terminology: "measured" → "estimated" for DC power values

---

## [2026-03-06b] — 2026-03-06

### Changed
- Updated combined power measurement: 74.1h test, 1.182 kWh, 15.96W AC / 13.17W DC
- Added peak load measurement: 21.4W AC / 17.66W DC
- Updated total system load estimate: ~13.7W DC (combined + Shelly + BP-65)
- Updated documentation in specs, design-rationale, supplemental-analysis

---

## [2026-03-06] — 2026-03-06

### Added
- Badges to README (license, status, runtime, switchover)
- Related Projects section linking to companion repositories
- CHANGELOG.md for version tracking

### Changed
- README header formatting with centered badges

---

## [2026-03-01] — 2026-03-01

### Added
- Combined system power measurement (13.68W DC typical)
- Extended power testing documentation

### Changed
- Updated runtime calculation based on combined load testing

---

## [2026-02-15] — 2026-02-15

### Added
- HA Green power measurement (0.73W DC typical, 2.56W DC peak)
- XB7 modem power measurement (12.14W DC typical, 16.75W DC peak)
- Kill-a-Watt testing methodology documentation

---

## [2026-01-15] — 2026-01-15

### Added
- Initial repository creation
- Complete design documentation
- Bill of materials with vendor links
- Wiring diagrams and specifications
- Design rationale and cost analysis
- Safety procedures
- Voltage drop analysis
- Thermal budget and FMEA
- System architecture diagrams

### Established
- MIT license
- Documentation structure in `/docs/`

---

## Version History Notes

This project uses date-based versioning (`YYYY-MM-DD`) based on significant milestones.

| Version | Milestone |
|:--------|:----------|
| 2026-03-06 | README badges and cross-links added |
| 2026-03-01 | Combined system power testing complete |
| 2026-02-15 | Individual device power measurements |
| 2026-01-15 | Initial design documentation |
