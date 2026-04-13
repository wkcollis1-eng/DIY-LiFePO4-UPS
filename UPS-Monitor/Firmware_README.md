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