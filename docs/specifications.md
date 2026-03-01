# System Specifications

---

## Electrical

| Parameter | Value | Notes |
|---|---|---|
| Input Voltage | 85–264VAC, 47–63Hz | Universal AC input |
| PSU Float Voltage | 13.3V DC | Set on LRS-100-12 trimmer pot; matches LiFePO4 resting voltage |
| Battery Voltage Range | 11.8–13.25V | Victron BP-65 cutoff to full charge |
| Device Input Voltage Range | 11.71–13.16V | At device terminals after wiring drop at 2A |
| Typical Load Current | 1.5A | 18W combined |
| Peak Load Current | 4A | 48W worst case |
| Battery Capacity | 10Ah nominal | ~128Wh energy storage |
| Usable Capacity | ~9Ah | 13.25V → 11.8V range |

## Performance

| Parameter | This DIY UPS | Commercial SLA UPS |
|---|---|---|
| Runtime @ 18W | 6.5 hours | 2–2.5 hours |
| Switchover Time | <1ms | 4–10ms |
| Battery Lifespan | 5–10 years | 2–3 years |
| Output Regulation | 11.71–13.16V (battery-tracked) | Within device ±10% tolerance envelope |
| Annual Electricity Cost | ~$58/yr | ~$52/yr |

> Runtime is calculated from 9Ah usable × 12.5V average ÷ 18W typical load. XB7 power consumption validated via 3-day Kill-a-Watt measurement (14.7W average, 20.3W peak).

## Device Power Requirements

### Home Assistant Green

| Parameter | Value |
|---|---|
| Input Voltage | 12V DC nominal (±10% inferred; not manufacturer-published) |
| Connector | 5.5mm × 2.1mm barrel jack, center-positive |
| Typical Power | 3W (0.25A) |
| Maximum Power | 12W (1A) |

### Xfinity XB7 Cable Modem

| Parameter | Value |
|---|---|
| Input Voltage | 12V DC nominal (±10% inferred; not manufacturer-published) |
| Connector | 5.5mm × 2.1mm barrel jack, center-positive |
| Typical Power | 14.7W (1.22A) — *measured via Kill-a-Watt: 1.066 kWh over 3 days 26 min 30 sec* |
| Maximum Power | 20.3W (1.69A) peak measured; OEM adapter rated 12V/4.6A (36W) |

### Combined System Load

| Parameter | Value |
|---|---|
| Typical Combined Power | ~18W (3W + 14.7W + ~1W Shelly) |
| Typical Combined Current | 1.5A @ 12V |
| Peak Power | 32W (12W + 20.3W measured peaks) |
| Peak Current | 2.7A @ 12V |
| Design Margin | 33% above typical at 2A continuous |

> Input voltage tolerance (±10%) is an engineering inference based on IEC 62368-1 / UL 62368-1 design practice for 12V DC input rails. Neither Nabu Casa nor Comcast publish explicit input voltage ranges for these products. The system's 11.71–13.16V device terminal envelope falls within this inferred tolerance.

## Protection

| Protection | Implementation | Threshold |
|---|---|---|
| Over voltage — Battery | LRS-100-12 OVP | 13.8–16.2V |
| Over voltage — Secondary | Battery BMS | 14.4–14.6V |
| Under voltage — Primary | Victron BatteryProtect BP-65 | 11.8V (Setting 7, MOSFET disconnect) |
| Under voltage — Secondary | Battery BMS | 10.0V |
| Overcurrent — Battery | Battery BMS | 10A |
| Reverse Current | Ideal Diode | Automatic blocking |
| Over temperature — Battery | DS18B20 + HA alert | 40°C warning |

## Monitoring (Shelly Plus Uni)

| Metric | Sensor | Update Rate |
|---|---|---|
| Battery Voltage | ADC1 | 5 seconds |
| Battery Temperature | DS18B20 | 30 seconds |
| Battery SoC (calculated) | Derived from ADC1 | 5 seconds |
| Runtime Remaining (calculated) | Derived from ADC1 | 5 seconds |
