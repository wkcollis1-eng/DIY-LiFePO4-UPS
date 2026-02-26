# Component Selection Rationale

---

## Mean Well LRS-100-12 Power Supply

Selected primarily for its over voltage protection characteristics. OVP range of 13.8–16.2V provides a hard ceiling above the 13.3V float setpoint, protecting the battery from accidental overcharge if the trimmer is bumped or drifts.

Additional factors: 88% efficiency at rated load, compact 30mm low-profile form factor, universal AC input (85–264VAC), convection cooling (no fan to fail), 677,400-hour MTBF (MIL-HDBK-217F at 25°C). Output voltage adjustable from 10.2–13.8V via onboard trimmer — trimmer is set to 13.3V and lacquered after adjustment.

At the 18W typical system load (~1.5A), the PSU operates at approximately 18% of its 8.5A rated capacity. Light loading reduces thermal stress and extends service life.

---

## Cyclenbatt 12V 10Ah LiFePO4 Battery

LiFePO4 chemistry selected over SLA for:

- Thermal stability: thermal runaway threshold above 270°C, non-flammable under normal conditions
- Cycle life: rated 5000+ cycles vs. 200–500 for SLA
- Calendar life: 5–10 years expected at 13.3V float vs. 2–3 years for SLA at conventional float voltage
- Weight: approximately 40% lighter than equivalent SLA

Built-in 10A BMS provides cell-level over-voltage (14.4–14.6V), under-voltage (10.0V), and overcurrent protection as a secondary layer behind the system-level protections.

The 10Ah capacity provides approximately 6.3–6.5 hours runtime at the measured/estimated 17–18W combined load.

---

## Pololu Ideal Diode (4-60V, 10A) — Pololu #5382

A MOSFET-based ideal diode rather than a conventional Schottky diode eliminates the 0.6–0.7V forward voltage drop that would otherwise reduce the PSU-to-battery charging voltage. The MOSFET approach has approximately 5mΩ effective resistance at operating current — contributing only ~10mV drop at 2A vs. 600–700mV for a Schottky.

Function: blocks reverse current from battery to PSU during AC failure. Without this, the battery would attempt to back-power the PSU through its output terminals.

Two units purchased; one installed, one spare.

---

## Victron BatteryProtect BP-65 (LVD)

See [design-rationale.md](design-rationale.md) for the relay module comparison.

Key specifications relevant to this installation:

- Setting 7: 11.8V disconnect / 12.8V reconnect — appropriate for LiFePO4 at this load level
- MOSFET Rds(on): ~3mΩ typical (community-validated; not published in datasheet)
- 90-second disconnect delay: prevents LVD trip on brief voltage sag from inrush or transient load
- Over voltage protection: load disconnected if input exceeds 16.3V (12V system)
- Current consumption: 1.4mA with BLE on — negligible impact on battery runtime
- Bluetooth programming via VictronConnect app; thresholds are user-defined (not just preset table values)

---

## Shelly Plus Uni

Provides native Home Assistant integration via WiFi with no ESPHome coding required. Two analog inputs (ADC) and DS18B20 1-Wire temperature sensor support in a single module.

Pin 3 (Analog In) bridged to Pin 1 (V+) provides direct battery voltage sense — used as the primary low-battery warning trigger at 12.2V, giving Home Assistant time to initiate graceful HA Green shutdown before the Victron BP-65 LVD cutoff at 11.8V.

The DS18B20 sensor is placed on the battery surface and provides temperature telemetry with a 40°C HA alert threshold.

Update rates: voltage every 5 seconds, temperature every 30 seconds.

---

## LeMotech Junction Box

IP65-rated ABS enclosure with flame-retardant rating. The 9.6″×7.6″×4.5″ interior provides adequate space for all components with room for cable management. Rubber gasket seal on lid. Pre-punched knockouts accept the 1/2" NPT cable glands.

ABS self-extinguishing rating is appropriate for an enclosure containing a lithium battery and 120VAC wiring. The enclosure is not thermally sealed — IP65 refers to dust and water ingress, not airtight containment. Passive convection through the gasket joint is sufficient for the ~10W heat dissipation at typical load.

Physical AC/DC segregation: PSU (AC input side) is mounted on the left; battery, BP-65, and DC components occupy the center and right. AC and DC cable glands are on opposite sides of the bottom face.
