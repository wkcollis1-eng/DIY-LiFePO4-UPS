# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Pending
- Home Assistant automation documentation
- Runtime validation testing (build complete — validation in progress)

---

## [2026-03-10] — 2026-03-10

### Added
- Ventilation holes documented in supplemental-analysis.md: 3 × ¼″ intake (low, PSU wall) + 3 × ¼″ exhaust (high, BP-65 wall)
- Chimney airflow analysis: holes contribute ~0.05W cooling (~1.5% of 3.5W load) — wall conduction dominates at this heat level; ΔT unchanged at ~2.8°C
- IP65 → IP4X rating note added (holes compromise water-jet resistance; non-issue for indoor floor installation)
- Bare wall warts baseline added to cost-analysis.md: ~$41/yr / ~$410 over 10 years; DIY UPS adds only ~$5/yr vs doing nothing
- Battery longevity analysis added to supplemental-analysis.md: 1–2%/yr calendar aging → 10–20 year realistic lifespan at 13.3V float, 63–75°F

### Changed
- **PSU model corrected throughout:** LRS-100-12 → HDR-60-12 (all docs, README, block diagram, datasheet link)
- **Adapter efficiency methodology corrected:** 82.5% assumed → actual measured efficiencies (XB7: 88% DoE Level VI confirmed from adapter label NBC56B120460VU; HA Green: 85% assumed, not characterized)
- **DC load figures corrected:** 13.7W → 14.5W DC typical (XB7 12.9W + HA Green 1.1W + Shelly 0.5W + BP-65 0.018W)
- **Kill-a-Watt measurement updated:** final combined window 2.538 kWh / 158.8 hr = 16.0W avg, 23.0W peak (6 days 14h 50min); average confirmed stable across all measurement windows
- **XB7 standalone measurement note:** reformatted to consistent kWh/hr style: 1.066 kWh / 72.4 hr = 14.7W avg
- **Voltage envelope corrected:** 11.74–13.26V → 11.71–13.11V (2A worst-case) throughout all docs
- **Runtime corrected:** 8.2h → 7.8h (112.5Wh ÷ 14.5W DC); AC-based reference 7.0h added to footnotes
- **Battery lifespan updated:** 7–10 years → 10–20 years throughout all docs
- **Annual electricity corrected:** $41/yr → $46/yr (14.5W DC ÷ 81% PSU efficiency × 8760h × $0.29/kWh)
- **BOM corrected:** 2-in-4-out terminal block replaced with Wago 221-415 lever nuts (10-pack); cost unchanged
- **Voltage drop analysis:** terminal blocks + butt splice → Wago lever nuts; Path 1 segment count corrected to 6; total resistance 40mΩ → 47.1mΩ; currents updated to 1.2A typical / 2.0A worst-case
- **Peak power updated:** 21.5W → 23.0W AC peak (measured); 19.5W → 20.2W DC peak (derived)
- **Thermal analysis:** heat load updated 2.1W → 3.5W; ΔT 1.7°C → 2.8°C; PSU efficiency at operating point corrected to 81%
- **README status:** components ordered/received ✓; combined measurement ✓; separate HA Green baseline item removed; build in progress
- **10-year cost comparison:** DIY total updated ~$654 → ~$714; BE600M1 price corrected $75 → $85; honest context updated to "roughly the same cost"

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
| 2026-03-10 | Build complete; all measurements finalized; documentation corrected |
| 2026-03-06 | README badges and cross-links added |
| 2026-03-01 | Combined system power testing complete |
| 2026-02-15 | Individual device power measurements |
| 2026-01-15 | Initial design documentation |
