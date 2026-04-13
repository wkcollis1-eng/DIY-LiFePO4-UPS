
***

# UPS-Monitor-V2 ESPHome Firmware

![ESPHome Version](https://img.shields.io/badge/ESPHome-2024.5.0+-blue?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-ESP32--C3--MINI--1-green?style=flat-square)
![Sensor](https://img.shields.io/badge/Sensor-TI--INA228-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

Production-grade firmware for the **UPS-Monitor-V2** board—a high-precision power monitor for 12V LiFePO₄ UPS systems. Built around the **Texas Instruments INA228** (20-bit, hardware energy accumulation) and an **ESP32-C3** with OTA updates.

---

## ⚠️ CRITICAL SAFETY WARNING

> [!CAUTION]
> **PERMANENT HARDWARE DAMAGE RISK**
> 
> **VBUS is tied directly to LOAD_OUT. NEVER connect a USB cable while 12V power is present.** 
> This will backfeed 12V into your PC’s USB port and **permanently destroy the host computer**.
>
> *   **Initial Flash:** Only with **12V disconnected** (power via USB only).
> *   **Future Updates:** Use **OTA (Over-The-Air)** exclusively. Never plug USB again while the board is powered.

---

## ✨ Features

### High-Precision Monitoring
*   **INA228 Integration:** 20-bit ADC, 128× hardware averaging, 4.12ms conversion time.
*   **Full Suite:** Monitors Voltage, Current, Power, Energy (kWh), and Charge (Ah).
*   **Persistence:** Hardware energy registers are preserved across reboots (`reset_on_boot: false`).

### Self-Diagnostics & Resilience
*   **I²C Watchdog:** Auto-recovery logic for bus lockups.
*   **Data Integrity:** Power cross-check (INA power vs. calculated $V \times I$) and energy monotonicity guards.
*   **Metric Scoring:** 0–100% Data Confidence metric.

### System Intelligence
*   **State Classification:** 5-state logic: `FLOAT`, `ABSORPTION`, `NORMAL_LOAD`, `HEAVY_LOAD`, and `CRITICAL`.
*   **Thermal Monitoring:** Triple-point sensing (Battery via DS18B20, INA228 Die, and ESP32 internal).
*   **Advanced Metrics:** Voltage rate of change ($dV/dt$) and load capacity percentage relative to the 5A fuse.

---

## 🔧 Installation & Setup

### 1. Configuration Setup
Create your `ups-monitor-v2.yaml` and a companion `secrets.yaml`:

```yaml
# secrets.yaml
wifi_ssid: "Your_SSID"
wifi_password: "Your_Password"
ota_password: "Your_OTA_Password"
api_encryption_key: "Your_Generated_Key"
web_username: "admin"
web_password: "Your_Web_Password"
```

### 2. First Flash (USB Mode)
1.  **Ensure no 12V power** is connected to `J1 (BATT_IN)`.
2.  Connect to PC via USB-C.
3.  Run: `esphome run ups-monitor-v2.yaml`.
4.  Once connected to WiFi, **unplug USB**.

### 3. OTA Updates
From this point forward, update only via WiFi:
`esphome run ups-monitor-v2.yaml --device ups-monitor-v2.local`

---

## 🏠 Home Assistant Integration

The device exposes the following entities via the ESPHome API:

### 📊 Sensors
| Entity | Unit | Description |
| :--- | :--- | :--- |
| `ups_bus_voltage` | V | Battery / bus voltage (post-LVD) |
| `ups_current` | A | Load current (includes board self-consumption) |
| `ups_power` | W | Instantaneous power |
| `ups_accumulated_energy` | kWh | Lifetime energy (hardware accumulated) |
| `ups_accumulated_charge` | Ah | Lifetime charge (ampere-hours) |
| `ups_battery_temperature` | °C | DS18B20 external battery probe |
| `ina228_die_temperature` | °C | INA228 internal temperature |
| `esp32_internal_temp` | °C | ESP32-C3 chip temperature |
| `ups_load_capacity` | % | Current vs. 5A fuse limit |
| `ups_power_error` | W | Difference between INA power register and $V \times I$ |
| `ups_voltage_rate` | V/s | Derivative of voltage ($dV/dt$) |
| `ups_data_confidence` | % | 0–100% measurement quality indicator |

### 🔔 Binary Sensors
| Entity | Description |
| :--- | :--- |
| `ups_monitor_online` | Device connectivity status |
| `ups_low_voltage_alert` | Voltage below threshold (load-aware) |
| `ups_near_max_load` | Current > 4A (80% of fuse limit) |
| `ups_measurement_unstable` | NaN readings or I²C errors detected |
| `ups_brownout_event` | Voltage < 11.6V under load (debounced) |
| `ups_degraded_mode` | High heat (>70°C) or critical WiFi signal (<-85dBm) |
| `ups_energy_rollback` | Energy register rollback/reset detected |

### 📝 Text Sensors
| Entity | Description |
| :--- | :--- |
| `ups_monitor_ip` | Current network IP address |
| `esp_reset_reason` | Last reset cause (Power-on, Watchdog, etc.) |
| `ups_state` | current state (`FLOAT`, `CRITICAL`, etc.) |

### 🔘 Buttons & Controls
| Entity | Description |
| :--- | :--- |
| `reset_energy_counters` | Button to manually reset energy/charge (e.g., after battery swap) |
| `ups_status_led` | Blue status LED toggle |

---

## 🤖 Recommended Automations

### Critical Shutdown
```yaml
alias: "UPS Critical - Shutdown Non-Essential Loads"
trigger:
  - platform: numeric_state
    entity_id: sensor.ups_bus_voltage
    below: 11.8
    for: "30s"
action:
  - service: switch.turn_off
    target:
      entity_id: group.non_essential_equipment
```

### Low Voltage Notification
```yaml
alias: "UPS Alert: Battery Low"
trigger:
  - platform: state
    entity_id: binary_sensor.ups_low_voltage_alert
    to: "on"
action:
  - service: notify.mobile_app_user
    data:
      message: "UPS Battery at 12.2V - Check mains power."
```

---

## 🧪 Calibration & Verification

1.  **Zero Current:** Disconnect all loads. If `ups_current` is not 0.000, note the value and add it as a negative `offset` in the YAML current sensor filter.
2.  **Voltage Match:** Measure `BATT_IN` with a trusted Multimeter. Adjust the `lambda` multiplier in the `bus_voltage` filter: `return x * (DMM_Reading / Reported_Reading);`.
3.  **One-Wire Address:** After first boot, find the DS18B20 address in the logs (e.g., `0x1234...`) and hardcode it in your YAML to improve boot speed.

---

## 🐞 Troubleshooting

| Issue | Likely Cause | Solution |
| :--- | :--- | :--- |
| **No WiFi Connection** | Incorrect SSID/Pass | Verify `secrets.yaml` and 2.4GHz signal. |
| **Sensor Reads 'NaN'** | I²C Bus Lockup | Watchdog will auto-recover; check for loose wiring. |
| **OTA Fails** | Firewall/Network | Ensure port `8266` is open or use `esphome run --device <IP>`. |
| **LED Stays Off** | GPIO Mismatch | Verify board uses GPIO5 for LED; update YAML if required. |

---

## ⚖️ License
Distributed under the **MIT License**. Use at your own risk. The author is not responsible for damage caused by ignoring the USB backfeed warning.

---
*Last updated: 2026-04-13*