# UPS Monitor Rev 4: firmware V4.3 validation review (2026-11-16)

This review checks `ups-monitor-rev4.yaml` against the component datasheets and the ESPHome
2026.10.2 documentation. It follows the V4.2 review (`ups-monitor-rev4-v4.2-review.md`), which
settled the ESPHome-source questions, and it covers what that review left unchecked: the
ESP32-C3, INA260 and DS18B20 datasheet items, the entity metadata, and the tooling address.

**Result:** three corrections, no change to any pin, threshold, interval, filter or UPS logic.
The firmware is **not bench-tested**. Nothing here makes it ready to deploy; section 5 lists
what the bench still has to show.

Tags: [M] measured, [S] from a named document, [D] arithmetic on [M] or [S], [I] inferred and
not yet tested.

## 1. Version and build

| Item | Value |
|---|---|
| ESPHome version used | 2026.10.2. It is the version esphome.io showed on 2026-11-16, and the installed and latest version of the owner's Device Builder add-on that day [M]. No newer stable release existed. |
| `esphome config` | "Configuration is valid!", 0 WARNING lines, 0 ERROR lines [M] |
| `esphome compile` | Exit 0. `main.cpp.obj` rebuilt after the edit; 0 `error:` and 0 `warning:` lines in the log [M] |
| `-Wall -Wextra` over the generated `main.cpp` | 0 diagnostics in `main.cpp` or the YAML lambdas [M] |
| Image | Flash 985,656 B of 1,835,008 B; RAM 116,322 B of 321,296 B [M]. V4.2 was 985,700 B and 116,322 B [M: V4.2 review §2.1]. |
| Structural check | 7 anchored replacements, each matched once. Reversing them reproduces V4.2 byte for byte [M]. Non-comment lines: 2,273 → 2,271; three differ (section 2). CRLF line endings kept. `restore_value: yes` 33 → 33; `restore: true` 5 → 5. |

Bench Build B (this file plus the two edits of the bench procedure's Appendix A) also compiled:
exit 0, `main.cpp.obj` built, 0 `error:` lines [M].

The compile ran in a sandbox with placeholder secrets. It proves the file builds; it does not
prove anything about behaviour on the board.

## 2. Change table

| # | Before (V4.2) | After (V4.3) | Why | Source |
|---|---|---|---|---|
| C1 | `wifi:` `use_address: 10.0.0.232` | Line removed. The resolved config now reads `use_address: ups-monitor-rev4.local` [M]. | 10.0.0.232 is the address in `UPS-Monitor/ups-monitor.yaml`, the deployed Rev 1 board, and Home Assistant's ESPHome entry for that board uses it today [M]. Both files also name the same API key secret. So `esphome logs`, `esphome run` and the dashboard, given the Rev 4 file, targeted the Rev 1 board. The bench procedure's NET log column and its "use OTA after that" step both depend on this address. | esphome.io/components/wifi, `use_address`: "Manually override what address to use to connect to the ESP. Defaults to auto-generated value." |
| C2 | "Battery Fully Charged": `device_class: battery_charging` | No device class | Home Assistant shows that class as "Charging" when ON. This sensor is ON when the pack is full and idle at float, so the display said the opposite. No device class means "full". Name and entity ID are unchanged. | home-assistant.io/integrations/binary_sensor, device class `battery_charging`: on shows "Charging", off shows "Not charging". |
| C3 | Comments named `ups-monitor.local` and the `sensor.ups_monitor_…` prefix | A dated correction added under each; the original text stays | Both are the Rev 1 board's names. This board is `ups-monitor-rev4`, friendly name "UPS Monitor Rev 4". | The file's own `substitutions:` block |
| — | Header and boot log line say V4.2 | V4.3 | The boot line identifies the flashed build. | — |

**What C1 does not settle.** Whether the Rev 1 board would have accepted an upload built from
this file was not tested: the two files use different OTA authentication. The log connection
uses the shared API key and would have connected [I]; that is falsified if `esphome logs` on
V4.2 fails to authenticate against the Rev 1 board. It should not be tried on the deployed
board.

## 3. Inventory and per-component validation

Identity first: each row names the document and whether it covers the part on this board.

| Component | Firmware use | Checked against | Verdict |
|---|---|---|---|
| ESP32-C3 (XIAO), strapping pins | Uses GPIO3, 4, 5, 6, 7, 10 | "ESP32-C3 has three strapping pins: GPIO2, GPIO8, GPIO9" [S: ESP32-C3 Series Datasheet v1.2, §2.4, in `UPS-Monitor/`]. None is used. | PASS |
| GPIO5, MODEM_OFF | Raw ESP-IDF output with readback and deep-sleep hold | GPIO5 (MTDI) is on the VDD3P3_RTC domain [S: same, pin table]. It is not among the pins with power-up glitches, which are MTCK (GPIO6), MTDO (GPIO7), GPIO10, U0RXD and GPIO18 [S: same, Table 7]. | PASS on documents. Whether the hold survives the ROM boot is open item 7 (bench T5). |
| GPIO4, PSU_ADC | `adc`, `attenuation: 12db`, `samples: 8`, 5 s, × 6.556 | ADC1_CH4 is on this pin [S: pin table]. Effective range at ATTEN3 is 0 to 2500 mV [S: Table 15]. The pin sees 2.074 V at the 13.6 V set point and 2.471 V at the PSU's 16.2 V over-voltage ceiling [D: V ÷ 6.556]. Averaging is the datasheet's own advice [S: Table 15, note 1]. | PASS. The 6.556 ratio is nominal until bench T1 replaces it. |
| GPIO6 / GPIO7, I2C | 400 kHz, `scan: false` | Both pins have a low-level power-up glitch [S: Table 7], before the bus is in use. | PASS |
| INA260 (Adafruit #4226) | `ina260` at 0x40, plus raw reads of registers 01h, 02h, 06h | A1 = GND, A0 = GND gives 1000000b = 0x40 [S: TI SBOS656C, Table 2]. "Fast mode (1 kHz to 400 kHz)" [S: same, bus overview]. LSB 1.25 mA and 1.25 mV [S: register table]; the raw-read lambdas use 0.00125. CVRF is bit 3 of the Mask/Enable register [S]. Limits 36 V and 15 A continuous [S] against a 13.6 V bus and at most 7.2 A [D: design doc 1.5]. Power-down current 2 µA maximum [S: electrical characteristics]. That the breakout leaves A0 and A1 low is the design document's statement, not re-checked on the module. | PASS |
| INA260 ALERT, GPIO3 | Passive input, pull-up, 200 ms filter | Open-drain output with R1 10 kΩ to 3.3 V (design doc 4.6). The firmware never enables an alert function. | PASS |
| DS18B20, GPIO10 | `dallas_temp`, 30 s, `filter_out: 85.0`, then °C to °F | "The power on reset register value is +85°C"; conversion "750 ms (max.)" at 12 bits; supply 3.0 to 5.5 V; ±0.5 °C from −10 to +85 °C [S: Dallas DS18B20 datasheet, preliminary edition]. The filter runs before the °F conversion, so it compares °C. | PASS, with two limits: the current Analog Devices edition could not be downloaded, and the probe's own marking has not been read, so that it is a genuine DS18B20 is [I]. |
| PSU sense thresholds | `mains_present_v` 7.0 V, 10-poll debounce | 7.0 V lies between the 0.10 V backfeed and the 13.6 V set point (design doc 8). | PASS on logic. The debounce against the PSU's decay is bench T2. |
| Mean Well HDR-60-12 | None directly; it sets the float | Design doc 1.5 quotes the manufacturer's sheet. Not re-fetched in this pass. | NOT RE-CHECKED |
| U4, Pololu #4984 (S13V25F12) | Enable pin only, through Q1 | Design doc 4.3. Not re-fetched in this pass. | NOT RE-CHECKED |
| U3, Pololu D24V7F3 | None | — | No firmware interaction |
| `u4-discrete-buck-boost.md` | None | A design note for a possible later U4, not a Rev 4 part. Not reviewed in this pass. | Out of scope |
| Battery pack | Every voltage threshold | No cell or pack datasheet exists in the repository; only the label and the bench notes (design doc 1.6). | CANNOT VALIDATE against a datasheet. See section 5. |
| Wi-Fi, API, OTA, logger, deep sleep | As configured | Config valid on 2026.10.2 with 0 warnings [M]: no deprecated or removed key. | PASS; C1 FIXED |
| Entity metadata | 50 sensors, 20 binary sensors | Units, device classes and state classes read for every entity. | C2 FIXED. Section 6 lists gaps left alone. |

## 4. Safety audit

| Question | Finding |
|---|---|
| Can the firmware overcharge the pack? | No. It has no control over charging. Charge voltage is the PSU's 13.6 V set point, 3.40 V per cell [D: 13.6 ÷ 4], under the label's 14.4 to 14.6 V. Termination is the PSU's constant voltage and the BMS. |
| Can it deep-discharge the pack? | The shed at 11.80 V is the only disconnect above the BMS's 10.0 V cut, a 1.80 V gap [D]. The shed needs 10 consecutive fresh, in-range readings with mains debounced absent, so a failed sensor never sheds; it also never protects. After a shed the node sleeps, waking every 120 s. After 10,800 wakes, 15.0 days [D: 10,800 × 120 s ÷ 86,400], it stays awake and draws its own load until the BMS cuts. |
| Can a fault be masked? | "Voltage Warning", "Voltage Critical" and "LVD Imminent" compare the last published value and do not test its age. A frozen INA260 keeps them quiet. "INA260 Data Fresh" is the detector for that and must be alerted on in Home Assistant. |
| Charge current | The recharge peak can pass the label's 0.5 C, 5.0 A (design doc 1.5, open item 19). The firmware records the peak and raises no alert. |
| Charge temperature | The label allows charging only above 32 °F. The firmware reports temperature and raises no alert. Nothing on this board can stop a charge. |
| Thresholds | The shed voltage, the phase limits, the capacity and the survival limits are still the previous pack's values, marked as placeholders in the file (open item 14). None was changed here: no datasheet supports a different number. |
| Pins | No pin changed. |

## 5. Bench checklist additions

The bench procedure (`ups-monitor-rev4-bench-procedure.md`) stays the procedure. Its test
bodies were not re-read or changed in this pass. Where it says "V4.2", read "V4.3": the boot
line now reads `UPS Monitor Rev 4 V4.3 boot complete`. The table maps each area to the test
that covers it and adds the steps that were missing.

| Area | Covered by | Added steps |
|---|---|---|
| Address (new, do first) | — | ☐ Before any `esphome logs` or OTA, run `esphome config ups-monitor-rev4.yaml` and confirm `use_address:` is not 10.0.0.232. ☐ Confirm the log's boot line says "Rev 4 V4.3". ☐ If the add-on shows the board offline, reserve an address for this XIAO's MAC and add `use_address:` with it. |
| I2C scan | T1 (boot line names 0x40) | The firmware sets `scan: false`. ☐ In Build B only, set `scan: true` and confirm the UART log lists exactly one device, at 0x40. ☐ In Build P, confirm "INA260 Healthy" and "INA260 Data Fresh" are ON. |
| ADC against a DMM | T1 | ☐ Also record the reading at 0 V and at one mid point (about 7 V, the mains threshold) on supply B. The one-point calibration only fixes the set point. |
| Charge and discharge | T11 | ☐ Record "Last Recharge Peak Current" against 5.0 A (open item 19). ☐ Record the battery temperature at the start of the recharge. |
| Cutoff | T4, T5, T8 | No addition. |
| OTA | — | ☐ After the USB flash, upload Build P by OTA and confirm the boot line and "ESPHome Version". ☐ Repeat once with mains absent on the bench rig above the shed voltage; confirm "Total Outages" and the Ah counters are unchanged by the reboot. ☐ Never OTA while the shed is latched. |
| Reboot | T9, T10 | ☐ Press "Restart" on mains: MODEM_EN stays high on the scope throughout; "Modem Shed Count" does not change. |
| Wi-Fi loss and recovery | — | ☐ On mains, switch the bench AP off for 20 minutes, then on. Record: when the fallback AP appears (default `ap_timeout` is 90 s [S: esphome.io wifi]), whether the node reboots at the 15-minute Wi-Fi timeout (the page says that timeout "Does not apply when in access point mode"), and when telemetry returns. Pass: MODEM_EN stays high throughout, telemetry returns with no manual action, and "Total Outages" and "Modem Shed Count" are unchanged. ☐ Repeat on battery above the shed voltage. |

## 6. Left unchanged, with the reason

- **Device class `duration`** on "Runtime Remaining", "Runtime Remaining Minutes", "Last Outage
  Duration" and "PSU Decay To Threshold", and a state class on "Total Outages", "Modem Shed
  Count" and "Shed Hold Lost Count". They are valid options, not errors. Adding a state class
  starts long-term statistics in Home Assistant, which is the owner's choice.
- **"On Battery" and "Mains Present" use device class `power`.** Home Assistant shows it as
  On/Off, which reads correctly for both.
- **One API key secret for two boards.** The Rev 4 file names the Rev 1 board's key. It works,
  but a key per board would have stopped the tooling connecting to the wrong one. A change
  needs a new secret, which only the owner can create.
- **The two identical INA260 read blocks** in `onset_capture` and `recharge_capture`. Merging
  them is a refactor of capture code with no bench behind it.
- **`power_save_mode: none`** against the ESP32 default of LIGHT [S: esphome.io wifi], the
  100 ms onset cadence and the 120 s wake interval. The V4.2 review holds these for the bench.

## 7. Open risks and assumptions

**Needs the bench:**
1. GPIO5 hold through deep sleep and the ROM boot (open item 7, T5).
2. That the priority-900 lambda owns GPIO5 before anything else drives it (open item 28, T3).
3. The PSU's output decay against the mains debounce (open item 6, T2).
4. Every threshold inherited from the previous pack (open item 14, T11).
5. The recharge peak against 5.0 A and against the 7.5 A PSU fuse (open item 19).
6. Wi-Fi loss behaviour with the fallback AP enabled (section 5).
7. Name resolution of `ups-monitor-rev4.local` from the add-on, now that C1 relies on it.

**Open without a bench:**
8. The fallback AP and captive portal use the shared AP password. If that password is known
   outside the house, a Wi-Fi loss opens a way into the node.
9. No alert exists for charge current, for charging below 32 °F, or for the 15-day end of
   survival sleep.

**Assumptions:**
- The Rev 1 board stays in service at 10.0.0.232 beside the Rev 4 board (design doc 1.1 puts
  them on separate systems).
- No address is reserved for the Rev 4 board: it has not been flashed or joined to the network
  (the owner, 2026-11-16). None was invented.
- The sensor head is a genuine DS18B20 and the INA260 breakout's address pins are low.
- The ESP32-C3 datasheet in the repository is v1.2 (2022). The design document quotes v2.4 for
  the ADC error figure; the items checked here were read from v1.2 only.
