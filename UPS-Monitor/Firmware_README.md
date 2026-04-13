***

```markdown
# UPS-Monitor-V2 ESPHome Firmware

![ESPHome](https://img.shields.io/badge/ESPHome-2024.5.0-blue)
![ESP32-C3](https://img.shields.io/badge/ESP32--C3-MINI--1-green)

Production-grade firmware for the **UPS-Monitor-V2** board – a high-precision power monitor for 12V LiFePO₄ UPS systems.  
Built around the **Texas Instruments INA228** (20-bit, hardware energy accumulation) and an **ESP32-C3** with OTA updates.

---

## ⚠️ CRITICAL SAFETY WARNING – READ BEFORE POWERING

> **VBUS is tied directly to LOAD_OUT. NEVER connect USB while 12V power is present.**  
> This will backfeed 12V into your PC’s USB port and **permanently damage the host computer**.

- **Initial firmware flash:** Only with **12V disconnected** (power via USB only).
- **After first flash:** Use **OTA (Over-The-Air)** exclusively. Never plug USB again while the board is powered.

---

## Table of Contents
1. [Features](#-features)
2. [Prerequisites](#-prerequisites)
3. [Installation](#-installation)
4. [Home Assistant Integration](#-home-assistant-integration)
5. [Recommended Automations](#-recommended-home-assistant-automations)
6. [Calibration & Verification](#-calibration--verification)
7. [Troubleshooting](#-troubleshooting)
8. [License](#-license)

---

## ✨ Features

- **High-precision monitoring**  
  - Voltage, current, power, energy (kWh), charge (Ah).
  - INA228: 20-bit ADC, 128× hardware averaging, 4.12 ms conversion time.
  - Hardware energy registers preserved across reboots (`reset_on_boot: false`).

- **Self-diagnostics & Fault Detection**  
  - Power cross-check (INA228 power vs V×I).
  - Data confidence metric (0–100%).
  - Energy monotonicity guard.
  - I²C bus watchdog with auto-recovery.
  - Alerts for brownout, degraded mode, and unstable measurements.

- **Environmental Monitoring**  
  - DS18B20 battery temperature (1-Wire).
  - INA228 die temperature.
  - ESP32 internal temperature.

- **System Observability**  
  - WiFi RSSI, uptime, reset reason.
  - 5-state LiFePO₄ state classification: `FLOAT`, `ABSORPTION`, `NORMAL_LOAD`, `HEAVY_LOAD`, `CRITICAL`.
  - Load capacity percentage (based on 5A fuse).
  - Voltage rate of change (dV/dt).

- **Remote Management**  
  - Encrypted Home Assistant API.
  - OTA updates with safe-mode rollback.
  - Manual energy reset via HA button or service.
  - Optional web server for local debugging.

---

## 📦 Prerequisites

*   **Hardware:** UPS-Monitor-V2 board (Rev 3.1 or later) with ESP32-C3-MINI-1, INA228, and DS18B20 connected.
*   **Software:**  
    *   [ESPHome](https://esphome.io/) (2024.5.0 or newer).
    *   Home Assistant (optional, but recommended).
    *   USB-C cable (for initial flash only).

---

## 🔧 Installation

### 1. Clone or copy the configuration
Create a new file `ups-monitor-v2.yaml` with your firmware configuration.

### 2. Set up secrets
Create a `secrets.yaml` file next to your main configuration to store sensitive data:

```yaml
# secrets.yaml
wifi_ssid: "YourWiFiSSID"
wifi_password: "YourWiFiPassword"
fallback_password: "fallback123"
ota_password: "your_secure_ota_password"
web_username: "admin"
web_password: "your_web_password"
api_encryption_key: "your_long_encryption_key"
```

*Note: Generate the API encryption key using `esphome config ups-monitor-v2.yaml`.*

### 3. First Flash (USB – 12V DISCONNECTED)
1.  **Ensure no 12V power** is connected to `J1 (BATT_IN)`.
2.  Connect the board to your PC via USB-C.
3.  Compile and flash:
    ```bash
    esphome run ups-monitor-v2.yaml
    ```

### 4. Find DS18B20 Address
Check the ESPHome logs for the following line:
`Found sensor 0x1234567890ABCDEF`.
Copy that address into the `dallas:` section of your YAML.

### 5. OTA Updates (All future flashes)
Once the device is on your network, **use OTA exclusively**:
```bash
esphome run ups-monitor-v2.yaml --device ups-monitor-v2.local
```
> **Never use USB again while 12V is connected.**

---

## 🏠 Home Assistant Integration

The following entities are exposed to Home Assistant:

### 📊 Sensors
| Entity | Unit | Description |
| :--- | :--- | :--- |
| `ups_bus_voltage` | V | Battery / bus voltage (post-LVD) |
| `ups_current` | A | Load current |
| `ups_power` | W | Instantaneous power |
| `ups_accumulated_energy` | kWh | Lifetime energy (hardware accumulated) |
| `ups_accumulated_charge` | Ah | Lifetime charge (ampere-hours) |
| `ups_battery_temperature` | °C | DS18B20 temperature |
| `ups_data_confidence` | % | 0–100% measurement quality indicator |

### 🔔 Binary Sensors
| Entity | Description |
| :--- | :--- |
| `ups_low_voltage_alert` | Voltage below threshold (load-aware) |
| `ups_near_max_load` | Current > 4A (80% of 5A fuse) |
| `ups_brownout_event` | Voltage < 11.6V under load |

### 🔘 Buttons & Lights
| Entity | Purpose |
| :--- | :--- |
| `button.reset_ups_energy_counters` | Reset energy/charge registers |
| `light.ups_status_led` | On-board Blue LED control |

---

## 🤖 Recommended Home Assistant Automations

### Notify on Low Voltage
```yaml
alias: "UPS Low Voltage Alert"
trigger:
  - platform: state
    entity_id: binary_sensor.ups_low_voltage_alert
    to: "on"
action:
  - service: notify.mobile_app_your_phone
    data:
      message: "UPS voltage below 12.2V – battery discharging"
```

### Graceful Shutdown
```yaml
alias: "UPS Critical – Shutdown Modem"
trigger:
  - platform: numeric_state
    entity_id: sensor.ups_bus_voltage
    below: 11.8
    for: "30s"
action:
  - service: switch.turn_off
    target:
      entity_id: switch.xfinity_modem
```

---

## 🧪 Calibration & Verification

1.  **Zero current offset:** Disconnect all loads. Read `sensor.ups_current`. Apply that value as an `offset` in your YAML filter.
2.  **Voltage calibration:** Measure `J1` with a DMM. Adjust the multiplier in `bus_voltage` filters until the reported value matches your DMM.
3.  **Shunt validation:** Apply a known DC load (e.g., 2.00A) and verify the reading is within ±2%.

---

## 🐞 Troubleshooting

| Issue | Likely Cause | Solution |
| :--- | :--- | :--- |
| **No WiFi** | Wrong credentials | Check `secrets.yaml` and signal strength. |
| **INA228 reads NaN** | I²C bus lock | Watchdog will auto-recover; check for loose wiring. |
| **DS18B20 not found** | Missing pull-up | Verify 4.7kΩ pull-up resistor on GPIO2. |
| **OTA fails** | Network Firewall | Ensure port 8266 is open on your network. |

---

## ⚖️ License

This firmware is provided under the **MIT License**. Use at your own risk. The author is not responsible for hardware damage caused by improper connection or ignoring the USB backfeed warning.

---
*Last updated: 2026-04-13*
```
