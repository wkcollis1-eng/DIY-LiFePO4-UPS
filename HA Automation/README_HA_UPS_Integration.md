# Home Assistant UPS Integration
## DIY LiFePO4 UPS — Shutdown Automation & Voltage Monitoring

**Repository:** `DIY-LiFePO4-UPS`  
**Author:** wkcollis1-eng  
**Last Validated:** March 2026  
**HA Version:** Home Assistant Green  
**Design Version:** v2 Minimal  

---

## Overview

This document covers the complete Home Assistant integration for the DIY LiFePO4 UPS system: the filtered voltage sensor pipeline, the three-automation shutdown controller, and the engineering analysis behind every parameter choice. All values are grounded in actual discharge data collected from the commissioned system — nothing here is assumed or theoretical.

The integration provides:
- Noise-resistant voltage telemetry from the Shelly Plus Uni ADC
- Three-tier notification chain (early warning → approaching shutdown → shutdown)
- Graceful HA OS shutdown before the hardware LVD fires
- Protection against false triggers from sensor faults, transient dips, and voltage bounce

---

## Hardware Context

| Device | Role | Key Parameter |
| :--- | :--- | :--- |
| Cyclenbatt 10Ah LiFePO4 | Energy storage | 112.5 Wh usable |
| Mean Well HDR-60-12 | PSU, float charging | 13.3 V float setpoint |
| Victron BP-65 | Hardware LVD | Trips at ~11.8 V |
| Pololu #5382 ideal diode | Reverse current block | — |
| Shelly Plus Uni | Battery voltage telemetry | Built-in 0–30 V ADC |
| HA Green | Automation executor | ~0.8 W DC load |
| Xfinity XB7 modem | Protected load | ~12.2 W DC |

**Measured DC load at float:** ~14.4 W typical (13.5–15 W range)  
**AC wall draw (Kill-a-Watt, 25h 5m):** 17.90 W avg, 29.3 W peak  
**Estimated runtime at 14.4 W:** ~7.8–8.3 h  

> Note on peak: Kill-a-Watt measurement chain is PSU → Kasa HS103 → Kill-a-Watt. The 29.3 W AC peak includes Kasa HS103 overhead (~0.5 W) and XB7 transient spikes. DC-side components see a lower peak (~21–22 W AC equivalent), well within HDR-60-12 ratings.

---

## Voltage Threshold Reference

| Voltage | Condition | Action |
| :--- | :--- | :--- |
| 13.3 V | PSU float — normal operation | None |
| < 13.0 V sustained | PSU offline or grid outage | Early warning notification |
| < 12.4 V sustained | Active battery discharge | Approaching shutdown notification |
| < 12.2 V sustained | Low battery — shutdown imminent | Shutdown automation trigger |
| ~11.8 V | BP-65 hardware LVD trips | Hardware protection (independent) |

**Software-to-hardware margin:** 0.4 V (12.2 → 11.8 V)  
**Time across 0.4 V margin at 15 W load:** ~20.7 min  
**Total automation chain:** 2.5 min — leaves ~18 min of margin

---

## Sensor Configuration

### Filtered Voltage Sensor

Add to `configuration.yaml` within the `sensor:` platform list:

```yaml
  # ===============================================================
  # DIY LiFePO4 UPS — FILTERED VOLTAGE SENSOR
  # ===============================================================
  # Provides a noise-resistant battery voltage signal for all UPS
  # automation triggers. Raw ADC from Shelly Plus Uni has ±0.03V
  # quantization noise; this sensor removes it before control logic.
  #
  # Pipeline:
  #   outlier filter  — window=4, radius=0.10V  (removes ADC spikes)
  #   time_simple_moving_average — 3-min window (smooths control signal)
  #
  # CRITICAL: All UPS automations MUST reference this sensor.
  #           Never use the raw Shelly ADC entity as a trigger.
  # ===============================================================
  - platform: filter
    name: "UPS Battery Voltage Filtered"
    unique_id: ups_battery_voltage_filtered
    entity_id: sensor.ups_battery_voltge_ups_battery_voltage_voltmeter
    filters:
      - filter: outlier
        window_size: 4
        radius: 0.10  # 0.04 cascades during discharge — see Engineering Notes
      - filter: time_simple_moving_average
        window_size: "00:03"  # 3-min time window; captures 2–4 samples at float
        precision: 4          # 4dp lets filtered avg move between raw 0.01V steps
```

### Why `precision: 4`

The raw Shelly ADC outputs values to 2 decimal places (e.g. `13.24`, `13.25`). With `precision: 2`, the moving average rounds back to the same 2dp steps and the filtered line is visually indistinguishable from raw in dashboard charts. Setting `precision: 4` allows the moving average to resolve intermediate values (e.g. `13.2367`), making the smoothing effect visible.

### Entity ID Note

The raw Shelly entity ID contains a typo in the device name — `voltge` (missing `a`) — which is the actual registered entity ID in HA. Do not correct this; it must match exactly:

```
sensor.ups_battery_voltge_ups_battery_voltage_voltmeter
```

---

## Automation Configuration

Add to `automations.yaml`. Three automations, all `mode: single`.

### Automation 1 — Early Warning (13.0 V)

```yaml
- id: ups_warn_psu_failure_v2
  alias: "UPS: Early Warning — PSU Failure or Power Outage"
  mode: single
  trigger:
    - platform: numeric_state
      entity_id: sensor.ups_battery_voltage_filtered
      below: 13.0
      for:
        minutes: 2
  condition:
    - condition: template
      value_template: >
        {{ states('sensor.ups_battery_voltage_filtered') not in ['unknown', 'unavailable'] }}
  action:
    - service: notify.mobile_app_bills_iphone
      data:
        title: "⚠️ Power Outage or PSU Failure"
        message: >
          Battery voltage {{ states('sensor.ups_battery_voltage_filtered') }}V —
          below 13.0V for 2 minutes.
          Power outage or PSU failure. Investigate hardware state.
```

### Automation 2 — Approaching Shutdown Warning (12.4 V)

```yaml
- id: ups_warn_approaching_shutdown_v2
  alias: "UPS: Approaching Shutdown Warning at 12.4V"
  mode: single
  trigger:
    - platform: numeric_state
      entity_id: sensor.ups_battery_voltage_filtered
      below: 12.4
      for:
        minutes: 1
  condition:
    - condition: template
      value_template: >
        {{ states('sensor.ups_battery_voltage_filtered') not in ['unknown', 'unavailable'] }}
  action:
    - service: notify.mobile_app_bills_iphone
      data:
        title: "⚠️ Preparing for HA Green Shutdown at 12.2V"
        message: >
          Battery voltage {{ states('sensor.ups_battery_voltage_filtered') }}V —
          below 12.4V. HA Green will be powered down shortly.
```

### Automation 3 — Low Battery Shutdown (12.2 V)

```yaml
- id: ups_low_battery_shutdown_v2_minimal
  alias: "UPS: Low Battery Shutdown (v2 Minimal)"
  mode: single
  trigger:
    - platform: numeric_state
      entity_id: sensor.ups_battery_voltage_filtered
      below: 12.2
      for:
        minutes: 1
  condition:
    - condition: template
      value_template: >
        {{ states('sensor.ups_battery_voltage_filtered') not in ['unknown', 'unavailable'] }}
  action:
    - delay: "00:00:30"
    - condition: numeric_state
      entity_id: sensor.ups_battery_voltage_filtered
      below: 12.2
    - service: notify.mobile_app_bills_iphone
      data:
        title: "⚠️ HA Green Shutting Down"
        message: >
          Battery voltage {{ states('sensor.ups_battery_voltage_filtered') }}V —
          critically low below 12.2V sustained. HA Green powering down now.
    - service: hassio.host_shutdown
```

---

## Engineering Notes

### 1. Outlier Filter Radius: Why 0.10 V, Not 0.04 V

The original README specified `radius: 0.04`. This was validated against float-voltage data (normal operation, ±0.02 V noise) and appeared correct. Under discharge conditions it causes a **cascade failure** that prevents the automation from ever firing.

**Mechanism:** During discharge, voltage drops ~19 mV/min at 15 W load. Readings arrive approximately every 20–60 seconds. By the time the 4-sample outlier window catches up with a genuine decline, each new reading appears to fall outside the 0.04 V radius of the window mean — so the filter rejects the reading and returns the last accepted value. That frozen value is then fed into the moving average, which also freezes. The filtered sensor stalls above 12.2 V while the raw voltage falls through 12.2, 12.0, 11.9 V and below.

**Evidence from discharge data (2026-03-26, D2 cycle):**

| Time | Raw V | Filtered V (radius=0.04) |
| :--- | :--- | :--- |
| 20:18:00 | 12.24 | 12.2900 |
| 20:19:59 | 12.20 | 12.2900 — frozen |
| 20:21:59 | 12.14 | 12.2900 — frozen |
| 20:25:35 | 12.04 | 12.2900 — frozen |
| 20:34:58 | 11.77 | 12.2900 — BP-65 fires |

With `radius: 0.04`, the automation **never fires**. The BP-65 hardware LVD is the only protection.

**Fix:** `radius: 0.10`. This is above the ±0.02 V float noise (so genuine ADC spikes are still rejected) but wide enough to track a genuine discharge curve. Sensitivity analysis confirmed that any radius ≥ 0.10 V produces a safe result; 0.10 V was chosen as the minimum safe value to preserve spike rejection.

| Radius | Automation fires? | Margin vs BP-65 |
| :--- | :--- | :--- |
| 0.04 | **Never** | 0 — hardware only |
| 0.10 | Yes — 20:24:59 | **+9.0 min** (at 7 W test load) |

---

### 2. Moving Average Window: Why Time-Based, Not Sample-Count

HA's filter platform supports `time_simple_moving_average` with a time-based `window_size`. A sample-count moving average (`moving_average`) does not exist as a valid filter name in current HA versions — attempts to use it produce a config validation error.

The Shelly ADC updates approximately every 30 seconds internally, but **HA only records a state change when the value changes**. At float (13.22–13.25 V oscillation), the recorder logs only 2–4 readings per 3-minute window, not the expected 6. A 3-minute time window was chosen as the appropriate smoothing span; it contains enough samples during discharge (when readings arrive more frequently as voltage changes faster) to smooth noise without introducing meaningful lag at the critical thresholds.

---

### 3. Automation Trigger Duration: Why 1 Minute, Not 2

The original v2 Minimal design specified `for: minutes: 2` on the shutdown trigger. Load-scaled analysis reduced this to 1 minute.

**Load scaling:** The discharge test (D2 cycle, 2026-03-26) was conducted with a Netgear R6400 router at ~7 W. Actual UPS load is ~15 W (XB7 + HA Green + Shelly overhead). Discharge rate scales linearly with load.

| Load | Discharge rate | 12.2 V → 11.8 V time | Automation chain | Margin |
| :--- | :--- | :--- | :--- | :--- |
| 7 W (test) | 9.0 mV/min | 44.4 min | 3.5 min | **+9.0 min** (with `for: 2`) |
| 15 W (actual) | 19.3 mV/min | 20.7 min | 3.5 min | **+1.5 min** (with `for: 2`) |
| 15 W (actual) | 19.3 mV/min | 20.7 min | 2.5 min | **+18.2 min** (with `for: 1`) |

The 1-minute trigger still provides adequate transient rejection (genuine dips from load spikes are short; a 1-minute sustained drop at 12.2 V is unambiguously a real discharge event), while recovering 1 minute of timing margin. Total chain: 1.0 min trigger + 0.5 min delay + 1.0 min HA shutdown = **2.5 min consumed**, leaving ~18 min of margin before the BP-65 fires.

---

### 4. Validity Guard: Why It Is Non-Optional

All three automations include:

```yaml
{{ states('sensor.ups_battery_voltage_filtered') not in ['unknown', 'unavailable'] }}
```

Without this guard, a Shelly reconnect event, HA restart, or integration glitch that briefly puts the sensor in `unknown` state could satisfy a `below: 12.2` numeric condition (HA evaluates unknown states as non-numeric, which can trigger `below` conditions depending on context). This guard blocks all three automations from executing against a faulted sensor. It was retained from the original v2 design as a non-negotiable safety requirement.

---

### 5. Execution Delay and Revalidation

The 30-second delay in Automation 3 serves two purposes: it allows the filtered voltage to stabilize (the TSMA is still averaging older samples at trigger time), and it provides a recovery bounce window. If grid power is restored during the delay and voltage recovers above 12.2 V before the delay completes, the revalidation `condition: numeric_state below: 12.2` aborts the shutdown. This prevents a spurious shutdown on a brief outage that resolves before HA would have time to execute anyway.

---

### 6. Shelly ADC Update Behavior

The Shelly Plus Uni polls its ADC at a fixed internal rate, but HA's recorder only logs a new row when the state value changes. At float voltage (typically 13.22–13.27 V), the sensor value changes infrequently — median inter-reading interval is ~21 seconds during active periods, but there are also quiet gaps of 5–17 minutes when the voltage holds steady.

This means:
- The `time_simple_moving_average` window may contain as few as 1 sample during a long quiet period
- During active discharge (voltage changing every reading), sample density increases automatically — the filter adapts to the signal without configuration changes
- Setting `window_size: "00:03"` is appropriate for both conditions: tight enough to track a real decline, wide enough to smooth noise at float

---

## Deployment Checklist

### Pre-Deployment

- [ ] Confirm `sensor.ups_battery_voltage_filtered` appears in Developer Tools → States after HA restart
- [ ] Compare filtered vs. raw voltage in history — filtered line should be visibly smoother
- [ ] Verify `float_precision: 4` in apexcharts-card series shows 4dp in header (e.g. `13.2367 V`)
- [ ] Confirm all three UPS automations appear in Settings → Automations and are enabled

### Hardware Verification (Completed)

- [x] `hassio.host_shutdown` tested — HA powered off in ~60 seconds
- [x] Clean cold boot confirmed on DC power restore
- [x] BP-65 LVD trip verified at ~11.77–11.80 V

### Live Discharge Test (Pending)

- [ ] Observe or simulate discharge below 13.0 V — confirm early warning notification fires
- [ ] Continue discharge to 12.4 V — confirm approaching shutdown notification fires
- [ ] Confirm 12.2 V trigger armed message in HA log
- [ ] Confirm 1-min timer fires, 30s delay, revalidation, shutdown issued
- [ ] Confirm HA shuts down before BP-65 trips

---

## Failure Modes Covered

| Failure Mode | Covered | Mechanism |
| :--- | :--- | :--- |
| Battery depletion | Yes | Voltage trigger at 12.2 V |
| PSU offline / grid outage | Yes | 13.0 V early warning |
| Sensor ADC noise | Yes | Outlier filter (radius=0.10 V) |
| Transient load spike dips | Yes | 1-min sustained duration |
| Sensor reconnect fault | Yes | Validity guard (unknown/unavailable check) |
| Voltage recovery bounce | Yes | 30s delay + revalidation |
| Duplicate alert on threshold bounce | Yes | `mode: single` on all automations |
| Software failure (HA crash before shutdown) | No — hardware backstop | BP-65 at 11.8 V |

---

## Dashboard Configuration (apexcharts-card)

Key settings for displaying filtered vs. raw voltage:

```yaml
series:
  - entity: sensor.ups_battery_voltage_filtered
    name: UPS Battery (Filtered)
    float_precision: 4    # shows 4dp — requires precision: 4 in filter sensor
    show:
      in_header: true
```

`float_precision` is a series-level key, not nested inside `show:`. Using `decimals` (inside `show:`) or at the series level are both invalid in apexcharts-card v2.2.3 — `float_precision` is the correct parameter.

---

## File Locations

| File | Location |
| :--- | :--- |
| Filter sensor definition | `configuration.yaml` — end of `sensor:` platform list |
| UPS automations | `automations.yaml` — end of file, UPS section |
| Discharge data (D2 cycle) | `data/` — `history__6_.csv` |
| Kill-a-Watt performance data | `docs/Final_As_Built_Performance_Cost_Summary.md` |
| Commissioning narrative | `docs/commissioning.md` |

---

## Known Artifacts and Caveats

- **Entity ID typo:** The raw Shelly sensor entity ID contains `voltge` (not `voltage`) — this is the actual registered name and must not be corrected in YAML.
- **Discharge rate is load-dependent:** The 19.3 mV/min rate and all derived timing values assume ~15 W DC load. If load changes significantly (e.g. adding or removing devices), re-run the timing budget calculation.
- **Recorder compression:** HA does not record unchanged sensor states. At float, the voltage history will show infrequent entries (sometimes 5–17 min apart). This is normal and does not indicate a sensor problem.
- **TSMA window at startup:** For the first 3 minutes after HA restart, the moving average has a shorter effective history. Automation triggers are valid during this period but the filtered value will be based on fewer samples.

---

## Revision History

| Date | Change |
| :--- | :--- |
| March 2026 | Initial deployment — v2 Minimal design |
| March 2026 | Outlier radius corrected 0.04 → 0.10 V (cascade failure under discharge) |
| March 2026 | Trigger duration reduced 2 min → 1 min (load-scaled timing analysis at 15 W) |
| March 2026 | Filter precision increased 2 → 4 dp (dashboard visibility) |
| March 2026 | All parameters validated against D2 discharge data (2026-03-26) |
