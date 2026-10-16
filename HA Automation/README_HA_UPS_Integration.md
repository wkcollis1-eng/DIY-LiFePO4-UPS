# Home Assistant UPS Integration
## The `ups_*_v3` shutdown chain

**Current as of:** 2026-10-16. Firmware [`ups-monitor.yaml`](../UPS-Monitor/ups-monitor.yaml) V1.20. Automations as published in [home-assistant-config `automations.yaml`](https://github.com/wkcollis1-eng/home-assistant-config/blob/9d047f8b18e00fd706fe7374b6f372e5915f28ce/automations.yaml) at commit `9d047f8`.

**Replaces:** the March 2026 version of this document. That version covered the Shelly Plus Uni ADC, a Home Assistant filter sensor and three voltage-threshold automations (`ups_*_v2`). It is kept in the git history at [`cc00ab4`](https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS/blob/cc00ab466fa47154abf10b86ce3630a56225f509/HA%20Automation/README_HA_UPS_Integration.md).

This page covers the Home Assistant side of the system:
- which entities the chain reads;
- what each of the five automations does;
- why each guard is there.

The system itself, the full protection ladder and the test record are in the [README](../README.md#operating-modes-and-protection-ladder). The automation YAML is linked from this page, not copied into it, so only one copy has to be kept correct.

---

## Division of labour

The monitor's firmware decides what state the UPS is in. Home Assistant decides what to do about it.

- **ESPHome monitor.** It computes every state the chain uses:
  - on battery;
  - the voltage thresholds;
  - the slope detector;
  - the runtime estimate;
  - the outage statistics.

  Every voltage and slope threshold, and every debounce time, lives in the firmware. The one threshold in Home Assistant is the 8 min runtime trigger. Home Assistant does no filtering of its own, so the filter sensor from the March 2026 design is gone.
- **Home Assistant.** It turns those states into phone notifications and a call to `hassio.host_shutdown`.
- **Victron BP-65.** It disconnects the loads at 11.80 V, after its delay, whatever Home Assistant does [S, BP-65 manual]. Once the host is down, it is the only protection left.

Home Assistant runs on the host it shuts down. After `hassio.host_shutdown`, nothing on the Home Assistant side acts again until the host boots.

---

## Entities

| Entity | True when / value | Debounce | Read by |
| :--- | :--- | :--- | :--- |
| `binary_sensor.ups_monitor_on_battery` | V < 13.15 V | on 10 s, off 60 s | all five |
| `binary_sensor.ups_monitor_voltage_warning` | V < 12.40 V and I < −0.10 A | on 30 s | 2, 3 |
| `binary_sensor.ups_monitor_cliff_imminent` | EMA slope < −10.0 mV/min, V < 12.65 V and I < −0.10 A | on 180 s, off 30 s | 3 |
| `binary_sensor.ups_monitor_voltage_critical` | V < 12.20 V and I < −0.10 A | on 10 s | 4 |
| `sensor.ups_monitor_runtime_remaining_minutes` | the firmware's linear runtime estimate | — | 2 (message text), 3 |
| `sensor.ups_monitor_battery_voltage` | INA260 bus voltage | — | message text |
| `sensor.ups_monitor_total_outages` | outage counter, kept in flash | — | 1, 5 |
| `sensor.ups_monitor_last_outage_*`, `sensor.ups_monitor_last_recharge_peak_current` | the last outage's duration, Ah, Wh, capacity used, start and minimum voltage, and peak recharge current, published when `on_battery` clears | — | 5 |

Every threshold and debounce time in the table is a V1.20 substitution or filter [S, [`ups-monitor.yaml`](../UPS-Monitor/ups-monitor.yaml)]. Current is negative when the pack is discharging.

The slope is an EMA that updates every 60 s, so the 180 s hold spans three updates [S, `ups-monitor.yaml` V1.20 `cliff_imminent` comment].

The entity IDs come from the firmware's `friendly_name` ("UPS Monitor") and each entity's `name:`. If you rename either, the IDs change.

The firmware also exposes three binary sensors that no automation reads:
- `Knee Approaching`: slope < −3.0 mV/min, held 120 s;
- `LVD Imminent`: within 0.10 V of the 11.80 V LVD;
- `INA260 Alert`: this one [cannot fire on the Rev 1 board](../README.md#firmware-ups-monitoryaml-v120).

---

## The five automations

| # | Automation | Trigger | Conditions | Action |
| :--- | :--- | :--- | :--- | :--- |
| 1 | [`ups_outage_start_v3`](https://github.com/wkcollis1-eng/home-assistant-config/blob/9d047f8b18e00fd706fe7374b6f372e5915f28ce/automations.yaml#L3875) | `on_battery` from `off` to `on` | `on_battery` not unknown or unavailable | notify: voltage, time, outage number |
| 2 | [`ups_voltage_warning_v3`](https://github.com/wkcollis1-eng/home-assistant-config/blob/9d047f8b18e00fd706fe7374b6f372e5915f28ce/automations.yaml#L3914) | `voltage_warning` to `on` | `on_battery` is `on` | notify: voltage, runtime estimate |
| 3 | [`ups_graceful_shutdown_v3`](https://github.com/wkcollis1-eng/home-assistant-config/blob/9d047f8b18e00fd706fe7374b6f372e5915f28ce/automations.yaml#L3980) | `voltage_warning` on; `cliff_imminent` on; runtime below 8 min; every minute | see below | notify, wait 30 s, revalidate, `hassio.host_shutdown` |
| 4 | [`ups_critical_shutdown_v3`](https://github.com/wkcollis1-eng/home-assistant-config/blob/9d047f8b18e00fd706fe7374b6f372e5915f28ce/automations.yaml#L4091) | `voltage_critical` to `on` | `on_battery` is `on` | notify, then `hassio.host_shutdown` at once |
| 5 | [`ups_ac_restored_v3`](https://github.com/wkcollis1-eng/home-assistant-config/blob/9d047f8b18e00fd706fe7374b6f372e5915f28ce/automations.yaml#L4132) | `on_battery` from `on` to `off` | `on_battery` not unknown or unavailable | notify: the last outage's statistics |

All five are `mode: single`. The line links are pinned to commit `9d047f8`; on a later commit, search the file for the automation id.

**The `from:` guards on 1 and 5 (added 2026-07-03).** Without them, every ESPHome reconnect fired a false alert:
- `unavailable` → `on` sent a false outage alert;
- `unavailable` → `off` sent an "AC Restored" with garbage statistics.

These reconnects are routine: the XB7 cycles its Wi-Fi access points.

### 3: Graceful shutdown

1. **Trigger.** Whichever of the four triggers arrives first.
2. **Conditions.**
   - `on_battery` is `on`, and is not unknown or unavailable.
   - For the every-minute trigger only: `voltage_warning` is on, or `cliff_imminent` is on, or the runtime estimate is above 0 and below 8 min. The three edge triggers imply their own condition. Without this check, the every-minute trigger would notify once a minute for the whole outage.
3. **Notify** "Host shutting down in 30 s". This goes out first, so a record exists even if the shutdown follows.
4. **Wait 30 s.**
5. **Revalidate.**
   - (a) `on_battery` must still be on. If it is not, AC is back and the run ends.
   - (b) At least one of the three conditions in step 2 must still hold. (b) accepts `voltage_warning`, so a brief `cliff_imminent` bounce does not abort a shutdown the warning would justify.
6. **Shut down:** `hassio.host_shutdown`.

**Why the every-minute trigger exists (added 2026-07-03).** The other three triggers fire on an edge. Suppose a run aborts at step 5 while one of them is still latched on. No new edge arrives, and without the every-minute trigger the chain would never try again. When the host is not on battery, the every-minute trigger does nothing.

**A failed condition ends the run silently.** No message reports the abort. The phone keeps the "shutting down in 30 s" notification for a shutdown that did not happen (see the record below).

### 4: Hard fallback

`voltage_critical` calls `hassio.host_shutdown` immediately, with no wait and no revalidation. It covers three cases:
- the graceful run is still in its 30 s wait;
- `hassio.host_shutdown` failed;
- the graceful path never fired.

Automation 4 is separate from automation 3, so 3's `mode: single` cannot block it.

---

## What the record shows

The README's [protection ladder](../README.md#operating-modes-and-protection-ladder) has the full record. The points that bear on the automations:

- **First run end to end, 2026-05-06.** `cliff_imminent` fired at 12.431 V and triggered the graceful shutdown. HA's recorder stopped at 13:40:17 UTC [M, [05-06 report](../reports/UPS_Report_2026-05-06.md) §2].
  - HA was back online at 14:05:32 UTC, before `on_battery` cleared at 14:06:52. So automation 5's on → off trigger occurred with HA running [M, same timeline].
  - When the trigger fired, the runtime estimate read 50.79 min. The measured time remaining was 18.8 min [M, n = 1, 05-06 report §3.5]. That gap is why the runtime trigger is a backstop, not the primary path.
- **In the boost era, every graceful attempt aborted at least once before one held.** On 2026-09-01 and 2026-09-15, `cliff_imminent` fired, the run aborted at the 30 s revalidation, and a later trigger held [D, the firmware replayed on both runs, [09-15 report](../reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md) §6.1, n = 2].
  - The slope term's noise is sd 18.7–24.0 mV/min against the −10 mV/min threshold, which it crossed 21 and 12 times [M, n = 2 runs, 09-15 report §6.1].
- **An abort costs a false alarm.** On 2026-09-15, the aborted run had already sent "Host shutting down in 30 s". That first trigger came 1 h 2 m 31 s before LVD [M, 09-15 report §6].
- **V1.20 raised `cliff_imminent`'s hold from 60 s to 180 s** to stop those aborts.
  - Measured: every knee excursion below −10 mV/min lasted 1–2 slope updates, never 3 [M, n = 2 runs, 09-15 report §6.1.1].
  - Not yet measured: whether a 180 s hold still fires promptly in a genuine cliff.
- **Automation 4 has not been exercised.**
  - 2026-05-06: the bus first crossed 12.20 V at 13:48:07 UTC, after HA was down [M, 05-06 report §2].
  - 2026-09-15: the trigger that held fired at 12.532 V, so the bus was still above 12.20 V when HA went down [D, from the 09-15 report §1 timeline].
  - 2026-09-01: the bus never fell below 12.565 V [M, 09-15 report §6.1].

---

## Known gaps

- **AC returning before LVD leaves the host off.** `hassio.host_shutdown` leaves the N100DC soft-off with DC still applied. The boost keeps its rail up until the BP-65 trips. So if AC returns after a graceful shutdown but before LVD, the host stays off until someone presses its power button, and so does this chain. The README's [unattended-recovery gap](../README.md#unattended-recovery-gap) section has the detail and the planned fix.
- **No message reports an aborted graceful run.** See automation 3 above.
- **Message texts carry this system's numbers.** Automations 2 to 4 quote times to LVD derived for the 2.089 A load measured on 2026-08-29 [D, [08-31 report](../reports/UPS_Report_2026-08-31_Boost_Integration.md) §6.3]. Recompute them for your own load.

---

## Adapting the chain

- **Notify service.** The deployed chain sends to a phone's `mobile_app` service. Substitute your own, e.g. `notify.mobile_app_<your_phone>`.
- **Entity IDs.** Check them in Developer Tools → States before pasting. They depend on the firmware's `friendly_name` and entity names.
- **Thresholds.** The voltage and slope thresholds live in the firmware, so changing one means reflashing the monitor, not editing Home Assistant. Only the 8 min runtime trigger is in the automation.
- **`hassio.host_shutdown`** is a Supervisor action. It exists on Home Assistant OS and Supervised installs, not on Container or Core.

---

## Revision History

| Date | Change |
| :--- | :--- |
| March 2026 | Shelly-era chain (`ups_*_v2`): a filter sensor on the Shelly ADC, with automations at 13.0, 12.4 and 12.2 V [S, the [`cc00ab4`](https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS/blob/cc00ab466fa47154abf10b86ce3630a56225f509/HA%20Automation/README_HA_UPS_Integration.md) version]. Its outlier-filter finding is recorded there: at radius 0.04 V the filtered voltage froze during a discharge, so the shutdown could never have fired [M, 2026-03-26]. |
| 2026-05-06 | First end-to-end run of the `ups_*_v3` chain on the INA260 monitor, via `cliff_imminent` |
| 2026-07-03 | `from:` guards on automations 1 and 5; every-minute trigger on automation 3 |
| 2026-08-31 | Message texts updated for the boost-era load; "HA Green" became "Host" [S, 08-31 report §6.3] |
| 2026-09-16 | Firmware V1.20: `cliff_imminent` hold raised from 60 s to 180 s |
| 2026-10-16 | This document rewritten for the `ups_*_v3` chain |
