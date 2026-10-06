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

## [2026-10-06] — 2026-10-06

### Changed
- `Top-Off-Charger/pcb/`: the owner's re-laid board, `Top Off Charger- Oct 2026.kicad_pcb` (saved 2026-10-06 15:16:19; 29.5 × 78 mm, was 31.5 × 95), and its `.kicad_pro` replace v7. The `.kicad_pro` differs only in the default pad width for new pads and the last plot path, so the design rules are unchanged. DRC gives 0 errors, 26 warnings (all silk or library) and 0 unconnected; schematic parity did not run, as there is no schematic. The Gerbers have not been exported from this layout.
- `Top-Off-Charger/top-off-charger-design.md` rev 0.7, for that layout. TB1's pins are swapped, so the PSU's +V lands on the lower screw. The terminal blocks are named as Phoenix 5442756 (O9 closed). The LED moved and turned 180°, XIAO D6/D7 became unplated holes, and three signals moved to B.Cu. The assembly order is set for the parts under the modules. §7.3 compares the electrical figures with rev 0.6, including what the B.Cu tracks cost the ground pour. Its §15 lists the changes.

### Fixed
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
