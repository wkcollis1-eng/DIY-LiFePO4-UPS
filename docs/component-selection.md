# Component Selection Rationale

---

## Mean Well HDR-60-12 Power Supply

Selected for its adjustable voltage range and efficiency characteristics:

- Adjustable voltage range (10.2–13.8V) enables precise 13.3V float setting
- 13.3V float operates 1.3V below BMS OVP trip point (14.4–14.6V) for safe margin
- 87% efficiency at 25% load vs 79% for LRS-100-12 at comparable loading
- MTBF 927,600 hrs — 37% higher than LRS-100-12
- Class II design (double-insulated) appropriate for ABS enclosure with no metal surfaces
- DIN rail mount capability, compact form factor
- OVP range of 13.8–16.2V provides a hard ceiling above the 13.3V float setpoint

At the 13.68W typical system load (~1.03A), the PSU operates at approximately 22% of its 4.5A rated capacity. Light loading reduces thermal stress and extends service life.

---

## Cyclenbatt 12V 10Ah LiFePO4 Battery

LiFePO4 chemistry selected over SLA for:

- Thermal stability: thermal runaway threshold above 270°C, non-flammable under normal conditions
- Cycle life: rated 5000+ cycles vs. 200–500 for SLA
- Calendar life: 7–10 years expected at 13.3V float vs. 2–3 years for SLA at conventional float voltage
- Weight: approximately 40% lighter than equivalent SLA

Built-in 10A BMS provides cell-level over-voltage (14.4–14.6V), under-voltage (10.0V), and overcurrent protection as a secondary layer behind the system-level protections.

The 10Ah capacity provides approximately 8.2 hours runtime at the measured 13.68W combined load.

---

## Pololu Ideal Diode (4-60V, 10A) — Pololu #5382

A MOSFET-based ideal diode rather than a conventional Schottky diode eliminates the 0.6–0.7V forward voltage drop that would otherwise reduce the PSU-to-battery charging voltage. The MOSFET approach has approximately 5mΩ effective resistance at operating current — contributing only ~5mV drop at 1A vs. 600–700mV for a Schottky.

Function: blocks reverse current from battery to PSU during AC failure. Without this, the battery would attempt to back-power the PSU through its output terminals (PSU has no reverse protection).

10A rating provides 5× margin over 2A typical load. Two units purchased; one installed, one spare.

---

## Victron BatteryProtect BP-65 (LVD)

See [design-rationale.md](design-rationale.md) for the relay module comparison.

Key specifications relevant to this installation:

- Setting 7: 11.8V disconnect / 12.8V reconnect — appropriate for LiFePO4 at this load level
- MOSFET Rds(on): ~3mΩ typical (community-validated; not published in datasheet)
- 90-second disconnect delay: prevents LVD trip on brief voltage sag from inrush or transient load; adds only ~0.02V additional drop during delay — negligible
- Over voltage protection: load disconnected if input exceeds 16.3V (12V system)
- Current consumption: 1.5mA with BLE on — negligible impact on battery runtime (0.018W parasitic)
- Bluetooth programming via VictronConnect app; thresholds are user-defined (not just preset table values)
- IP67 potted electronics, no calibration drift
- 5-year warranty

---

## DC-DC Converter — Design Decision (Not Purchased)

Originally specified: Mean Well DDR-60G-12 DC-DC converter. After analysis, this was dropped:

- HA Green and XB7 modem accept industry-standard ±10% on 12V rail
- Eliminated DDR-60G-12 saves $33.80 + 2.8W continuous loss (~$5/year electricity savings)
- Design is more reliable and efficient without it

---

## Shelly Plus Uni

Provides native Home Assistant integration via WiFi with no ESPHome coding required. Two analog inputs (ADC) and DS18B20 1-Wire temperature sensor support in a single module.

Pin 3 (Analog In) bridged to Pin 1 (V+) provides direct battery voltage sense — used as the primary low-battery warning trigger at 12.2V, giving Home Assistant time to initiate graceful HA Green shutdown before the Victron BP-65 LVD cutoff at 11.8V (approximately 15–20 minutes of runtime remaining).

The DS18B20 sensor is placed on the battery surface and provides temperature telemetry with a 40°C HA alert threshold.

Update rates: voltage every 5 seconds, temperature every 30 seconds. Power consumption: 0.5W in eco mode.

---

## LeMotech Junction Box

IP65-rated ABS enclosure with flame-retardant rating (UL94 fire safety standards). The 9.6″×7.6″×4.5″ interior provides adequate space for all components with room for cable management. Rubber gasket seal on lid. Pre-punched knockouts accept the 1/2" NPT cable glands.

ABS self-extinguishing rating is appropriate for an enclosure containing a lithium battery and 120VAC wiring — significantly safer than basic polypropylene storage containers. The enclosure is not thermally sealed — IP65 refers to dust and water ingress, not airtight containment. Passive convection through the gasket joint is sufficient for the ~10W heat dissipation at typical load.

Physical AC/DC segregation: PSU (AC input side) is mounted on the left; battery, BP-65, and DC components occupy the center and right. AC and DC cable glands are on opposite sides of the bottom face.
