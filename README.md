# DIY UPS for Home Assistant Green & Xfinity XB7 Modem

A 12V LiFePO4-based uninterruptible power supply for keeping a Home Assistant Green and Xfinity XB7 cable modem running during grid outages. Built into an IP65 enclosure with Home Assistant monitoring via Shelly Plus Uni.

> **Honest context:** A $75 APC BE600M1 would do the same job out of the box. This build costs roughly $200 more over 10 years than that option. The engineering rationale — longer battery life, faster switchover, direct HA integration, no DC-DC converter voltage regulation — is documented in [design-rationale.md](docs/design-rationale.md). Build this if those tradeoffs matter to you.

---

## System Overview

AC grid powers a Mean Well LRS-100-12 PSU set to 13.3V float, which charges a 12V 10Ah LiFePO4 battery through a MOSFET ideal diode. On grid failure, loads switch directly to battery in under 1ms. A Victron BatteryProtect BP-65 disconnects loads at 11.8V to prevent over-discharge. A Shelly Plus Uni reports battery voltage and temperature to Home Assistant.

```
         AC Power (Wall)
                ↓
┌────────────────────────────────────┐
│  Mean Well LRS-100-12 PSU          │
│  Input: 85-264VAC  Out: 13.3V      │
└────────────────┬───────────────────┘
                 │ 13.3V (float)
                 ↓
┌────────────────────────────────────┐
│  Pololu Ideal Diode (4-60V, 10A)   │
│  Prevents PSU backfeed from batt.  │
└────────────────┬───────────────────┘
                 │
                 ↓
┌────────────────────────────────────┐
│  Cyclenbatt 12V 10Ah LiFePO4       │
│  Built-in 10A BMS, 5000+ cycles    │
└────────────────┬───────────────────┘
                 │
                 ↓
┌────────────────────────────────────┐
│  Victron BatteryProtect BP-65      │
│  LVD: 11.8V (Setting 7)           │
│  Reconnect: 12.8V, 90s delay      │
└────────────────┬───────────────────┘
                 │ 11.71–13.16V at device terminals
            ┌────┴─────┐
          [F3:2A]   [F4:5A]
            │           │
         HA Green    XB7 Modem
           (3W)       (~14W)

┌────────────────────────────────────┐
│  Shelly Plus Uni (Monitoring)      │
│  ADC → Battery Voltage             │
│  GPIO → DS18B20 Temperature        │
│  WiFi → Home Assistant             │
└────────────────────────────────────┘
```

---

## Key Specifications

| Parameter | Value |
|---|---|
| Battery | Cyclenbatt 12V 10Ah LiFePO4 |
| Float voltage | 13.3V (set on PSU trimmer) |
| LVD cutoff | 11.8V (Victron BP-65, Setting 7) |
| LVD reconnect | 12.8V (30s delay after threshold met) |
| Device voltage envelope | 11.71–13.16V at terminals |
| Switchover time | <1ms (MOSFET ideal diode) |
| Typical load | ~17–18W combined |
| Runtime at typical load | ~6.3 hours |
| Enclosure | LeMotech IP65 ABS, 9.6″×7.6″×4.5″ |
| Monitoring | Shelly Plus Uni → Home Assistant |
| Total build cost | ~$234 |

---

## Operating Modes

**Mode 1 — AC Present:** PSU outputs 13.3V through ideal diode; battery held at float equilibrium. Loads draw from PSU, not battery.

**Mode 2 — AC Failure:** PSU output drops to 0V. Ideal diode blocks. Battery feeds loads directly, no interruption.

**Mode 3 — Low Battery (~12.2V):** Shelly detects threshold via ADC. Home Assistant initiates graceful HA Green shutdown; modem continues on battery.

**Mode 4 — LVD Cutoff (11.8V):** Victron BP-65 disconnects loads after 90-second hold-off.

**Mode 5 — AC Restoration:** PSU resumes 13.3V, ideal diode switches source, BP-65 reconnects after 30s hold-off.

---

## Assembly Layout

![Component Layout](assets/UPS_Layout_with_12_Volt_Regulator.png)

*Elevation (top) and plan (bottom) views of LeMotech junction box. Dimensions in inches.*

---

## Documentation

| File | Contents |
|---|---|
| [docs/bom.md](docs/bom.md) | Full bill of materials with vendor, price, and notes |
| [docs/wiring.md](docs/wiring.md) | From/To wiring tables, fuse locations, component mounting |
| [docs/specifications.md](docs/specifications.md) | Electrical, performance, and protection spec tables |
| [docs/design-rationale.md](docs/design-rationale.md) | Build-vs-buy analysis, float charging strategy |
| [docs/component-selection.md](docs/component-selection.md) | Per-component selection rationale |
| [docs/cost-analysis.md](docs/cost-analysis.md) | Build cost breakdown and 10-year lifecycle comparison |
| [docs/safety.md](docs/safety.md) | AC and battery safety procedures |
| [docs/voltage-drop-analysis.md](docs/voltage-drop-analysis.md) | Wiring resistance and voltage drop calculations |

## Datasheets

- [Mean Well LRS-100-12](https://www.meanwell.com/Upload/PDF/LRS-100/LRS-100-SPEC.PDF)
- [Victron Smart BatteryProtect BP-65 — Datasheet](https://www.victronenergy.com/upload/documents/Datasheet-Smart-BatteryProtect-EN.pdf)
- [Victron Smart BatteryProtect — Manual](https://www.victronenergy.com/upload/documents/Manual-Smart-BatteryProtect-EN.pdf)

---

## Status

- [x] Design complete
- [x] Components specified
- [ ] Components ordered / received
- [ ] Build
- [ ] 7-day power measurement baseline (in progress — Kill-a-Watt, devices measured separately)
- [ ] Home Assistant automation documentation

---

## Notes

- Device input voltage tolerance (±10%) is inferred from IEC 62368-1 design practice; neither Nabu Casa nor Comcast publish explicit DC input voltage ranges for these products.
- The PSU output trimmer is set to 13.3V and lacquered. Drift analysis shows expected aging drift of 3–5 mV/year — negligible relative to the 500mV headroom before OVP.
- No DC-DC converter is used. The direct battery feed strategy is documented in [design-rationale.md](docs/design-rationale.md).
