```markdown
# UPS-Monitor-V2 ESPHome Firmware

![ESPHome](https://img.shields.io/badge/ESPHome-2024.5.0-blue)
![ESP32-C3](https://img.shields.io/badge/ESP32--C3-MINI--1-green)

Production‑grade firmware for the **UPS-Monitor-V2** board – a high‑precision power monitor for 12V LiFePO₄ UPS systems.  
Built around the **Texas Instruments INA228** (20‑bit, hardware energy accumulation) and an **ESP32‑C3** with OTA updates.

---

## ⚠️ CRITICAL SAFETY WARNING – READ BEFORE POWERING

> **VBUS is tied directly to LOAD_OUT. NEVER connect USB while 12V power is present.**  
> This will backfeed 12V into your PC’s USB port and **permanently damage the host computer**.

- **Initial firmware flash:** Only with **12V disconnected** (power via USB only).
- **After first flash:** Use **OTA (Over‑The‑Air)** exclusively. Never plug USB again while the board is powered.

---

## ✨ Features

- **High‑precision monitoring**  
  - Voltage, current, power, energy (kWh), charge (Ah)  
  - INA228: 20‑bit ADC, 128× hardware averaging, 4.12 ms conversion time  
  - Hardware energy registers preserved across reboots (`reset_on_boot: false`)

- **Self‑diagnostics & fault detection**  
  - Power cross‑check (INA228 power vs V×I)  
  - Data confidence metric (0–100%)  
  - Energy monotonicity guard  
  - I²C bus watchdog with auto‑recovery  
  - Brownout, degraded mode, measurement unstable alerts

- **Environmental monitoring**  
  - DS18B20 battery temperature (1‑Wire)  
  - INA228 die temperature  
  - ESP32 internal temperature

- **System observability**  
  - WiFi RSSI, uptime, reset reason  
  - 5‑state LiFePO₄ state classification (FLOAT / ABSORPTION / NORMAL_LOAD / HEAVY_LOAD / CRITICAL)  
  - Load capacity (% of 5 A fuse)  
  - Voltage rate of change (dV/dt)

- **Remote management**  
  - Encrypted Home Assistant API  
  - OTA updates (with safe mode rollback)  
  - Manual energy reset via HA button or service  
  - Optional web server for local debugging

---

## 📦 Prerequisites

- **Hardware:** UPS-Monitor-V2 board (Rev 3.1 or later) with ESP32‑C3‑MINI‑1, INA228, and DS18B20 connected.
- **Software:**  
  - [ESPHome](https://esphome.io/) (2024.5.0 or newer)  
  - Home Assistant (optional, but recommended)  
  - USB‑C cable (for initial flash only)

---

## 🔧 Installation

### 1. Clone or copy the configuration

Create a new file `ups-monitor-v2.yaml` with the content from the [final firmware YAML](link-to-your-yaml-file) (provided separately).

### 2. Set up secrets (sensitive data)

Create a `secrets.yaml` file next to your main configuration (or use ESPHome dashboard secrets). Replace the placeholders:

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

Generate the API encryption key with:
```bash
esphome config ups-monitor-v2.yaml
```
Then copy the generated key into `secrets.yaml`.

### 3. First flash (USB – 12V DISCONNECTED)

1. **Ensure no 12V power** is connected to `J1 (BATT_IN)`.
2. Connect the board to your PC via USB‑C.
3. Compile and flash:
   ```bash
   esphome run ups-monitor-v2.yaml
   ```
   Or use the ESPHome dashboard (Install → Plug into this computer).

4. After successful flash, the device will boot and connect to your WiFi.

### 4. Find your DS18B20 address (once)

Check the ESPHome logs for a line like:
```
Found sensor 0x1234567890ABCDEF
```
Copy that address and replace `0x1234567890ABCDEF` in the `dallas:` section of your YAML. Then re‑flash **via OTA** (see below).

### 5. Calibration (recommended)

- **Voltage:** Measure `BATT_IN` with a trusted DMM. Adjust the `lambda` multiplier in the `bus_voltage` filter:
  ```yaml
  filters:
    - lambda: return x * (DMM_reading / reported_voltage);
  ```
- **Current offset:** With **no load**, note the reported current. That’s your offset. Replace `0.0025` in the `current` filter with that value.

### 6. OTA updates (all future flashes)

Once the device is on your network, use OTA exclusively:
```bash
esphome run ups-monitor-v2.yaml --device ups-monitor-v2.local
```
Or in ESPHome dashboard: **Install → Wireless**.

> **Never use USB again while 12V is connected.**

---

## 🏠 Home Assistant Integration

The device exposes the following entities after being added via the ESPHome integration.

### 📊 Sensors

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.ups_bus_voltage` | V | Battery / bus voltage (post‑LVD) |
| `sensor.ups_current` | A | Load current (includes board self‑consumption) |
| `sensor.ups_power` | W | Instantaneous power |
| `sensor.ups_accumulated_energy` | kWh | Lifetime energy (hardware accumulated) |
| `sensor.ups_accumulated_charge` | Ah | Lifetime charge (ampere‑hours) |
| `sensor.ups_battery_temperature` | °C | DS18B20 temperature |
| `sensor.ina228_die_temperature` | °C | INA228 internal temperature |
| `sensor.esp32_internal_temperature` | °C | ESP32‑C3 chip temperature |
| `sensor.ups_monitor_rssi` | dBm | WiFi signal strength |
| `sensor.ups_monitor_uptime` | s / duration | Time since last reboot |
| `sensor.ups_load_capacity` | % | Current / 5A fuse |
| `sensor.ups_power_error` | W | INA228 power vs V×I difference |
| `sensor.ups_power_error_percent` | % | Relative power error |
| `sensor.ups_voltage_rate` | V/s | Derivative of voltage (dV/dt) |
| `sensor.ups_data_confidence` | % | 0–100% measurement quality indicator |
| `sensor.ups_energy_monotonicity` | binary | 1 if energy decreased unexpectedly |
| `sensor.ups_battery_state_of_health` | % | Lifetime energy vs theoretical 128 Wh (throughput metric) |

### 🔔 Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.ups_monitor_online` | Device connected to HA |
| `binary_sensor.ups_low_voltage_alert` | Voltage below threshold (load‑aware) |
| `binary_sensor.ups_near_max_load` | Current > 4 A (80% of 5 A fuse) |
| `binary_sensor.ups_measurement_unstable` | NaN readings detected |
| `binary_sensor.ups_brownout_event` | Voltage < 11.6 V under load, debounced |
| `binary_sensor.ups_degraded_mode` | RSSI < -85 dBm or ESP temp > 70 °C |
| `binary_sensor.ups_energy_rollback` | Energy register rollback detected |

### 📝 Text Sensors

| Entity | Description |
|--------|-------------|
| `text_sensor.ups_monitor_ip_address` | Current IP address |
| `text_sensor.ups_monitor_ssid` | Connected WiFi SSID |
| `text_sensor.esp_reset_reason` | Last reset cause (e.g., power‑on, watchdog, brownout) |
| `text_sensor.ups_state` | FLOAT / ABSORPTION / NORMAL_LOAD / HEAVY_LOAD / CRITICAL |

### 🔘 Buttons & Lights

| Entity | Purpose |
|--------|---------|
| `button.reset_ups_energy_counters` | Manually reset energy/charge registers (useful after battery replacement) |
| `light.ups_status_led` | Blue LED – can be turned on/off manually or via automation |

### 🛠️ Services

- `esphome.ups_monitor_v2_reset_ups_energy` – same as button, callable from automations.

---

## 🤖 Recommended Home Assistant Automations

Here are example automations to get the most out of the monitor:

### 1. Notify on low voltage
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

### 2. Graceful shutdown of non‑critical loads
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

### 3. Daily energy summary (using HA utility meter)
- Create a utility meter helper for `sensor.ups_accumulated_energy` with daily reset.
- Then create an automation to send a summary at midnight.

---

## 🧪 Calibration & Verification

For best accuracy:

1. **Zero current offset:**  
   Disconnect all loads. Read `sensor.ups_current` after 1 minute. Use that value as `offset` in the YAML’s current filter.

2. **Voltage calibration:**  
   Measure voltage at `J1` with a DMM. Adjust the multiplier in `bus_voltage` filters until reported value matches.

3. **Shunt validation:**  
   Apply a known DC load (e.g., 2.00 A) and verify `sensor.ups_current` reads within ±2%.

4. **DS18B20 address:**  
   After first boot, check logs and hardcode the address to avoid bus scanning issues.

---

## 🐞 Troubleshooting

| Issue | Likely cause | Solution |
|-------|--------------|----------|
| Device not joining WiFi | Wrong SSID/password | Check `secrets.yaml` and signal strength |
| INA228 reads NaN | I²C bus lock | Watchdog will auto‑recover; if persistent, reboot |
| DS18B20 not found | Wrong pin or no pull‑up | Verify wiring and 4.7kΩ pull‑up on GPIO2 |
| OTA fails after first flash | Network firewall | Ensure port 8266 is open, or use `esphome run --device <IP>` |
| LED stays off | GPIO mismatch | Verify your board uses GPIO5 for LED; change YAML if different |

---

## 🔄 Updating Firmware

1. Edit the YAML file (e.g., change thresholds, add sensors).
2. Re‑flash via OTA:
   ```bash
   esphome run ups-monitor-v2.yaml
   ```
   Select “Wireless” when prompted.

Safe mode: if three consecutive boot failures occur, OTA safe mode will roll back to the previous working firmware.

---

## 📚 Additional Resources

- [UPS-Monitor-V2 hardware repository](https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS)
- [ESPHome INA2xx component documentation](https://esphome.io/components/sensor/ina2xx_i2c)
- [INA228 datasheet](https://www.ti.com/product/INA228)

---

## ⚖️ License

This firmware is provided under the MIT License. Use at your own risk – the author is not responsible for damage caused by ignoring the USB backfeed warning.

---

*Last updated: 2026-04-13*
```