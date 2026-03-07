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

## [2026-03-06b] — 2026-03-06

### Changed
- Updated combined power measurement: 74.1h test, 1.182 kWh, 13.17W DC average
- Added peak load measurement: 21.4W AC / 17.66W DC
- Updated total system load estimate: ~13.8W DC (combined + Shelly + BP-65)
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
