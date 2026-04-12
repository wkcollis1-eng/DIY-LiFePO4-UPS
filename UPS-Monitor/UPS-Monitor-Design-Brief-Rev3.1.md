# UPS-MONITOR-V2 | Design Brief
**Revision 3.1** • 2026-04-11
**Lead Engineer:** William Collis 
**Project Link:** [github.com/wkcollis1-eng/DIY-LiFePO4-UPS](https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS)

---

> [!CAUTION]
> **CRITICAL SAFETY WARNING: 12V BACKFEED RISK**
> VBUS is tied directly to `LOAD_OUT` at the U3 VIN node. **NEVER** connect USB while 12V power is present. This will backfeed 12V into the host PC, causing permanent hardware damage. Always disconnect 12V before connecting USB. Flash initial firmware via USB, then use OTA exclusively.

---

## 1. Purpose
Supplemental monitoring board for a 12V LiFePO4 UPS protecting a Home Assistant Green (~3W) and Xfinity XB7 modem (~14W). This board replaces the Shelly Plus Uni as a strict hardware superset, offering higher precision and lower power draw (~243mW vs ~500mW). It provides real-time current, power, and hardware-accumulated energy/charge via a Texas Instruments INA228 (20-bit I2C power monitor), reported to Home Assistant via ESPHome.

## 2. Revision History

| Rev | Date | Changes |
| :--- | :--- | :--- |
| 2.0 | 2026-04-10 | Initial design - 45×35mm. |
| 2.1 | 2026-04-10 | Board enlarged to 55×40mm for DFM; buck, INA228, and ESP32 zones isolated. |
| 3.0 | 2026-04-11 | Expanded to 65×50mm. Complete re-route (F.Cu Power / B.Cu Signals). Added USB notch. |
| 3.1 | 2026-04-11 | **DFM Correction:** Added R5 (VBUS filter), R3 (Address pulldown). Fixed VBUS routing error. Corrected C8 value to 1µF for 10ms boot delay. (33 components total). |

## 3. System Topology
Board is inserted post-Victron BP-65. Board power is derived from `LOAD_OUT` via an internal AP63203 buck; the board's own power consumption (~243mW) is included in shunt measurements (zero blind spot).

```text
AC Grid → Mean Well HDR-60-12 (13.3V float)
  → Pololu Ideal Diode
    → Cyclenbatt 10Ah LiFePO4
      → Victron BP-65 LVD (11.8V trip)
        → [J1 BATT_IN] ── THIS BOARD ── [J2 LOAD_OUT]
                                |
               ┌────────────────┴────────────────┐
               ↓ [F3: 2A]                        ↓ [F4: 5A]
           HA Green (~3W)                   XB7 Modem (~14W)
```

## 4. Hardware Specifications

| Parameter | Specification |
| :--- | :--- |
| **Dimensions** | 65 × 50 mm (Rev 3.1) |
| **Layers** | 2 (Front/Back) |
| **Copper Weight** | 2oz (70µm) |
| **Substrate / Finish** | FR4 1.6mm / ENIG |
| **Trace Width** | 3.0mm (Power Path) / 0.25mm (Signal/Kelvin) |
| **USB Interface** | USB-C (Native ESP32-C3 CDC/JTAG) |
| **Antenna** | Integrated PCB Antenna (Keepout: X=60-65mm) |
| **Manufacturer** | PCBWay (Contact: Aran) |

## 5. Component List (Key Items)

| Ref | Value | Package | Notes |
| :--- | :--- | :--- | :--- |
| **U1** | ESP32-C3-MINI-1-N4 | LGA-54 | Controller |
| **U2** | INA228AIDGST | MSOP-10 | 20-bit I2C Power Monitor |
| **U3** | AP63203WU-7 | SOT-23-6 | 13.3V→3.3V Buck (η≈87%) |
| **R_SHUNT** | 10mΩ 1% | WSK2512 | 4-Terminal Kelvin Shunt |
| **L1** | 4.7µH 2.6A | IHLP-5050EZ | Low DCR Buck Inductor |
| **TVS1** | SMAJ15CA | SMA | 15V Bidirectional Clamp |
| **J1, J2** | WAGO 2060-452 | SMD | 2-Pole Wire Entry |
| **J4** | USB4135-GF-A | Edge Mount | USB-C (Backfeed risk) |
| **C8** | 1µF 10V | 0402 | ESP32 EN RC Delay (τ=10ms) |
| **R5** | 10Ω 5% | 0402 | INA228 VBUS series filter |

## 6. Net Definitions

| Net | Voltage | Description |
| :--- | :--- | :--- |
| `BATT_IN` | 11.8–13.3V | Shunt input (Battery side) |
| `LOAD_OUT` | 11.8–13.3V | Shunt output; feeds U3 and VBUS sense |
| `VBUS_FILT` | ≈LOAD_OUT | Filtered sense voltage for INA228 Pin 9 |
| `SHUNT_HI/LO` | ≈12V | Kelvin matched pair (0.25mm width) |
| `+3V3` | 3.27V | Buck output; logic rail |
| `SDA / SCL` | 3.3V | I2C Bus (GPIO8 / GPIO1) |
| `DS18B20` | 3.3V | OneWire bus (GPIO2) |
| `USB_DM / DP` | USB | Native USB diff-pair (GPIO18/19) |

## 7. Routing Strategy
*   **F.Cu (Power Only):** High-current paths (`BATT_IN`, `LOAD_OUT`), `+3V3` spine, and `SW_BUCK` node. No signals on F.Cu except short stubs transitioning to B.Cu.
*   **B.Cu (Signals + GND):** All logic traces (SDA, SCL, USB, EN, BOOT). Covered by a solid GND pour with >24 stitching vias to F.Cu.
*   **Isolation:** `SW_BUCK` node isolated from sense traces by >3mm. Kelvin sense traces are matched length (±2mm) and routed as a pair.

## 8. Key Design Decisions
*   **INA228:** Selected for `reset_on_boot: false` support, preserving hardware energy registers across ESP32 restarts.
*   **AP63203 Buck:** Efficient 12V→3.3V conversion (Tj=32°C). Eliminates the ~4W heat dissipation issue of linear regulators at peak WiFi TX.
*   **VBUS Tie:** Simplifies logic power during programming but necessitates the "No 12V with USB" constraint.
*   **F.Cu/B.Cu Separation:** Resolved 94 DRC crossings found in Rev 2.1 by strictly segregating power and signal layers.

## 9. Critical Errors Fixed (Rev 3.1)
*   **R5 (10Ω):** Added to `VBUS_FILT` path. Required by datasheet for ESD/transient protection.
*   **VBUS Routing:** Fixed Rev 3.0 error where a 12V stub hit the `SCL` pad.
*   **C8 (1µF):** Corrected from 100nF to provide a 10ms delay, ensuring the 3.3V rail stabilizes before the ESP32 exits reset.
*   **R3 (10kΩ):** Added pulldown for INA228 A0/A1 to confirm I2C address `0x40`.

## 10. Power Budget (Typical)
*   **ESP32-C3:** ~150mW
*   **Buck Losses:** ~85mW (at 87% efficiency)
*   **INA228 + Misc:** ~8mW
*   **Total:** **~243mW** (Approx. $3.10/year operational cost).

## 11. ESPHome Configuration Summary
```yaml
i2c:
  sda: GPIO8
  scl: GPIO1  # GPIO9 is a strapping pin; do not use.

sensor:
  - platform: ina2xx_i2c
    model: INA228
    address: 0x40
    shunt_resistance: 0.010
    max_current: 5.0
    reset_on_boot: false # CRITICAL: Preserves Energy/Charge registers
    energy:
      name: "UPS Accumulated Energy"
    power:
      name: "UPS Power"
    bus_voltage:
      name: "UPS Voltage"
    current:
      name: "UPS Current"
```

## 12. Functional Test Specification
1.  **Visual:** Verify R5 presence and U2/U3 solder integrity.
2.  **Logic Power:** Apply 12V to J1. Verify 3.27V at `+3V3` rail.
3.  **VBUS Sense:** Measure voltage at U2 Pin 9 (should be ≈J1 voltage).
4.  **Comm:** Flash via USB (12V disconnected). Perform I2C scan; verify ACK at `0x40`.
5.  **Calibration:** Verify current reading against DMM in series with a known resistive load.

## 13. Gerber Export Process
**Warning:** Use the Python `pcbnew` API. `kicad-cli` may fail to fill zones properly for 2oz copper.
1.  Load Board.
2.  Run `ZONE_FILLER`.
3.  Execute Plot Controller.
4.  Verify `B.Cu` file size is ~44KB (indicates successful copper pour).

## 14. Known Issues & Open Items

| Item | Status | Notes |
| :--- | :--- | :--- |
| **USB Backfeed** | **Active** | 12V must be disconnected before USB connection. Permanent design constraint. |
| **Rev 3.1 Fab** | **Pending** | Rev 3.0 Gerbers were submitted; Rev 3.1 corrections must be sent to Aran/PCBWay before production. |
| **Energy Validation** | **Pending** | Hardware energy accumulation requires 24h validation against calibrated reference. |
| **LVD Automation** | **Open** | HA-side logic for 12.2V pre-emptive shutdown is in development. |
| **Footprint Cleanup** | **Resolved** | Removed `R_SHUNT_HI/LO` phantom footprints from BOM/CPL. |

---

## 15. Operational Specifications

| Parameter | Specification | Notes / Reference |
| :--- | :--- | :--- |
| **Input Voltage Range** | 11.8 V – 13.3 V | `BATT_IN` / `LOAD_OUT` nets (Post-LVD trip to Charger Float). |
| **Max Continuous Current** | 5 A | Limited by F4 fuse; 3.0 mm power traces. |
| **Shunt** | 10 mΩ ±1% Kelvin | WSLT2512R0100FEA (True 4-terminal sensing). |
| **Measurement Capabilities** | V, I, P, Energy, Charge, Temp | TI INA228 (20-bit ADC); hardware accumulation. |
| **Board Self-Consumption** | ~243 mW (Typ) | Included in shunt measurements (zero blind spot). |
| **Power Supply** | AP63203 Buck | Derived from `LOAD_OUT`; +3.27 V output at η ≈ 87%. |
| **External Sensor** | DS18B20 (1-Wire) | J3 Header (VCC/DATA/GND) with 4.7 kΩ pull-up. |
| **Communications** | WiFi / I2C | ESP32-C3; SDA = GPIO8, SCL = GPIO1. |
| **Programming** | USB-C / OTA | Initial flash via USB; **Disconnect 12V first.** |
| **Connectors** | WAGO 2060-452 / USB-C | High-current SMD terminal blocks; edge-mount USB. |
| **PCB Mechanical** | 65 × 50 mm | 2-layer FR4, 2 oz Cu, ENIG finish. |
| **Transient Protection** | SMAJ15CA TVS | Bidirectional clamp on input rail. |