# System Specifications

---

## Electrical

| Parameter | Value | Notes |
|---|---|---|
| Input Voltage | 85–264VAC, 47–63Hz | Universal AC input |
| PSU Float Voltage | 13.3V DC | Set on HDR-60-12 pot; matches LiFePO4 resting voltage |
| Battery Voltage Range | 11.8–13.3V | Victron BP-65 cutoff to full charge (float equilibrium) |
| Device Input Voltage Range | 11.74–13.26V | At device terminals after wiring drop (see [voltage-drop-analysis.md](voltage-drop-analysis.md)) |
| Typical Load Current | 1.029A @ 13.3V | ~13.68W measured DC / 13.3V |
| Peak Load Current | 1.582A @ 11.8V | 18.67W simultaneous peak load / 11.8V |
| Battery Capacity | 10Ah nominal | ~125Wh energy storage (10Ah × 12.5V avg) |
| Usable Capacity | ~9Ah | 13.3V → 11.8V range; 112.5Wh (9Ah × 12.5V avg) |

## Performance

| Parameter | This DIY UPS | Commercial SLA UPS |
|---|---|---|
| Runtime @ 13.39W measured | ~8.2 hours | 2–2.5 hours |
| Switchover Time | <1ms | 4–10ms |
| Battery Lifespan | 7–10 years | 2–3 years |
| Output Regulation | 11.73–13.26V (battery-tracked) | Within device ±10% tolerance envelope |
| Annual Electricity Cost | ~$41/yr | ~$51/yr |

> Runtime is calculated from 9Ah usable × 12.5V average ÷ 13.68W typical load = 8.2 hours. Power measurements derived from Kill-a-Watt AC readings converted to DC using 82.5% efficiency assumption.

## Device Power Requirements

### Home Assistant Green

| Parameter | Value | Calculation Details/Assumptions |
|---|---|---|
| Input Voltage | 12V DC nominal (±10% inferred; not manufacturer-published) | — |
| Connector | 5.5mm × 2.1mm barrel jack, center-positive | — |
| Typical Power | 0.73W DC (0.061A) | Measured AC: 0.043 kWh over 48.4603 hours. Avg AC = 0.887W. DC = 0.887W × 82.5% eff. |
| Maximum Power | 2.56W DC (0.213A) | Measured AC peak 3.1W × 82.5% eff. 12W (1A) spec. |

### Xfinity XB7 Cable Modem

| Parameter | Value | Calculation Details/Assumptions |
|---|---|---|
| Input Voltage | 12V DC nominal (±10% inferred; not manufacturer-published) | — |
| Connector | Proprietary Comcast/Xfinity barrel jack | — |
| Typical Power | 12.14W DC (1.012A) | Measured AC: 1.066 kWh over 72.4417 hours. Avg AC = 14.715W. DC = 14.715W × 82.5% eff. |
| Maximum Power | 16.75W DC (1.396A) | Measured AC peak 20.3W × 82.5% eff. 36W (3A) spec. |

### Combined System Load

| Parameter | Value | Calculation Details/Assumptions |
|---|---|---|
| Typical Combined Power | ~13.68W DC | HA Green + XB7 13.17W (measured over 63.67 hours) + Shelly 0.50W (eco mode est.) + BP-65 0.018W (parasitic) |
| Typical Combined Current | 1.029A @ 13.3V | Typical power / 13.3V (float max). At 12.5V avg discharge: 13.67W / 12.5V ≈ 1.094A |
| Peak Power | ~18.67W DC | HA Green + XB7 17.655W (measured) + Shelly 1.0W + BP-65 0.018W (simultaneous peak load) |
| Peak Current | 1.582A @ 11.8V | Peak power / 11.8V (LVD min) |
| Design Margin | Peak 1.582A vs. F4 5A fuse (65A BP-65 capacity) | 16AWG conductors rated ~13A in free air. F3=2A protects HA Green branch; F4=5A protects XB7 branch |

> Input voltage tolerance (±10%) is an engineering inference based on IEC 62368-1 / UL 62368-1 design practice for 12V DC input rails. Neither Nabu Casa nor Comcast publish explicit input voltage ranges for these products. The system's 11.74–13.26V device terminal envelope falls within this inferred tolerance (10.8V–13.2V).

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

## Monitoring (Shelly Plus Uni)

| Metric | Sensor | Update Rate |
|---|---|---|
| Battery Voltage | ADC1 | 5 seconds |
| Battery Temperature | DS18B20 | 30 seconds |
| Battery SoC (calculated) | Derived from ADC1 | 5 seconds |
| Runtime Remaining (calculated) | Derived from ADC1 | 5 seconds |
