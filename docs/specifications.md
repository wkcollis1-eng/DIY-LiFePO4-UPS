# System Specifications

---

## Electrical

| Parameter | Value | Notes |
|---|---|---|
| Input Voltage | 85–264VAC, 47–63Hz | Universal AC input |
| PSU Float Voltage | 13.3V DC | Set on HDR-60-12 trimmer pot; matches LiFePO4 resting voltage |
| Battery Voltage Range | 11.80–13.20V | Victron BP-65 cutoff to float equilibrium at 2A charge |
| Device Input Voltage Range | 11.71–13.11V | At device terminals after wiring drop at 2A (worst-case) |
| Typical Load Current | ~1.2A | ~14.5W DC combined (see Device Power Requirements) |
| Peak Load Current | ~1.7A | ~20.2W DC estimated peak |
| Battery Capacity | 10Ah nominal | ~125Wh energy storage (10Ah × 12.5V avg) |
| Usable Capacity | ~9Ah | 13.20V → 11.8V range; 112.5Wh (9Ah × 12.5V avg) |

---

## Performance

| Parameter | This DIY UPS | Commercial SLA UPS |
|---|---|---|
| Runtime @ 14.5W DC | ~7.8 hours | 2–2.5 hours |
| Switchover Time | <1ms | 4–10ms |
| Battery Lifespan | 10–20 years | 2–3 years |
| Output Regulation | 11.71–13.11V (battery-tracked, 2A worst-case) | Within device ±10% tolerance envelope |
| Annual Electricity Cost | ~$46/yr | ~$52/yr |

> Runtime calculated from 9Ah usable × 12.5V average ÷ 14.5W DC typical load. The UPS delivers 12V DC directly to devices, bypassing OEM AC adapters and their associated losses. XB7 DC load derived from Kill-a-Watt AC measurement at 88% adapter efficiency (DoE Level VI, model NBC56B120460VU). HA Green DC load estimated at ~1.1W assuming 85% adapter efficiency (not characterized; conservative). Runtime using AC wall figures (16.0W) would be ~7.0 hours.

---

## Device Power Requirements

### Home Assistant Green

| Parameter | Value |
|---|---|
| Input Voltage | 12V DC nominal (±10% inferred; not manufacturer-published) |
| Connector | 5.5mm × 2.1mm barrel jack, center-positive |
| Typical Power — AC wall | ~1.3W (0.11A) — implied from combined Kill-a-Watt minus XB7 |
| Typical Power — DC at device | ~1.1W — estimated at 85% adapter efficiency (not characterized) |
| Maximum Power | 12W (1A) |

### Xfinity XB7 Cable Modem

| Parameter | Value |
|---|---|
| Input Voltage | 12V DC nominal (±10% inferred; not manufacturer-published) |
| Connector | 5.5mm × 2.1mm barrel jack, center-positive |
| OEM Adapter | Model NBC56B120460VU, 12.0V/4.6A output, DoE Level VI (≥88% efficiency) |
| Typical Power — AC wall | 14.7W (1.22A) — *measured via Kill-a-Watt: 1.066 kWh / 72.4 hr = 14.7W avg* |
| Typical Power — DC at device | ~12.9W (1.07A) — derived at 88% adapter efficiency |
| Maximum Power — AC wall | 20.3W (1.69A) peak measured |
| Maximum Power — DC at device | ~17.9W (1.49A) — derived at 88% adapter efficiency |

### Combined System Load

| Parameter | AC Wall (measured) | DC at Devices (derived) |
|---|---|---|
| Typical Combined Power | ~16.0W | ~14.5W |
| Typical Combined Current | ~1.3A @ 12V | ~1.2A @ 12V |
| Peak Power | ~23.0W (measured) | ~20.2W (derived at 88%) |
| Peak Current | ~1.9A @ 12V | ~1.7A @ 12V |
| Kill-a-Watt Measurement | 2.538 kWh / 158.8 hr = 16.0W avg, 23.0W peak | — |

> Kill-a-Watt measurement ran 6 days 14h 50min through OEM AC adapters. Average confirmed stable across three successive measurement windows (72.4h XB7-only, 118.25h combined, 135.0h combined, 158.8h combined), all combined windows showing 16.0W avg. DC figures derived by removing adapter losses — these are the relevant figures for UPS runtime since the UPS feeds devices directly at 12V DC. XB7 adapter efficiency: 88% (DoE Level VI confirmed from adapter label, model NBC56B120460VU). HA Green adapter efficiency: 85% assumed (not characterized). Input voltage tolerance (±10%) is an engineering inference based on IEC 62368-1 / UL 62368-1 design practice. Neither Nabu Casa nor Comcast publish explicit input voltage ranges for these products.

---

## Protection

| Protection | Implementation | Threshold |
|---|---|---|
| Over voltage — Battery | HDR-60-12 OVP | 13.8–16.2V |
| Over voltage — Secondary | Battery BMS | 14.4–14.6V |
| Under voltage — Primary | Victron BatteryProtect BP-65 | 11.8V (Setting 7, MOSFET disconnect) |
| Under voltage — Secondary | Battery BMS | 10.0V |
| Overcurrent — Battery | Battery BMS | 10A |
| Reverse Current | Ideal Diode | Automatic blocking |
| Over temperature — Battery | DS18B20 + HA alert | 40°C warning |

---

## Monitoring (Shelly Plus Uni)

| Metric | Sensor | Update Rate |
|---|---|---|
| Battery Voltage | ADC (ANALOG IN, white wire) | 5 seconds |
| Battery Temperature | DS18B20 via DATA (blue wire) | 30 seconds |
| Battery SoC (calculated) | Derived from ADC | 5 seconds |
| Runtime Remaining (calculated) | Derived from ADC | 5 seconds |
