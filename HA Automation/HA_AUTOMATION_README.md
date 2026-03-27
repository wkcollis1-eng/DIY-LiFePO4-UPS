# Home Assistant UPS Automation

Home Assistant automation, sensor filtering, and Lovelace dashboard configuration for the DIY LiFePO4 UPS. Part of the [DIY-LiFePO4-UPS](https://github.com/wkcollis1-eng/DIY-LiFePO4-UPS) project.

---

## Hardware Context

| Device | Role in Automation |
|---|---|
| Shelly Plus Uni | Battery voltage (ADC) + temperature (DS18B20) telemetry |
| Victron BP-65 | Stage 2 hardware LVD at 11.8V — independent of HA |
| Kasa Smart Plug | PSU AC input control + grid presence detection |
| HA Green | Runs this automation; shuts itself down gracefully at 12.2V |
| Xfinity XB7 | On UPS — does **not** cold boot on outage; only needs WAN reconnect |

Both the HA Green and XB7 modem are on the UPS DC bus. The XB7 stays powered through the outage and reconnects WAN when grid returns (~60–90 seconds). This is important for the Kasa availability wait in Phase 4 recovery.

---

## Shelly Entity IDs (Confirmed)

These are the actual entity IDs as registered in HA. Note the typo ("voltge") — this comes from the Shelly device name set during initial configuration and is baked into HA's entity registry.

```
sensor.ups_battery_voltge_ups_battery_voltage_voltmeter   ← voltage ADC
sensor.ups_battery_voltge_ups_temperature_temperature     ← DS18B20 temp
```

To fix the typo: rename the device in the Shelly app → update entity ID in HA Settings → Entity Registry. Not required for function.

# Confirmed entity IDs:
switch.ups_outlet                                         # Confirmed wntity ID for Kasa plug on PSU AC input
notify.mobile_app_bills_iphone                            # mobile notify target
---

## Files in This Directory

| File | Purpose |
|---|---|
| `sensor.yaml` | Filtered voltage sensor + runtime/duration template sensors |
| `scripts.yaml` | `script.ups_graceful_shutdown` — parameterized shutdown with test mode gate |
| `automations.yaml` | Main control loop + temperature automations + watchdog |
| `ui-lovelace.yaml` | Lovelace UPS card (or paste into dashboard editor) |

All content is currently consolidated in `ups_ha_config_v4.yaml` pending deployment split.

---

## Sensor Pipeline

```
sensor.ups_battery_voltge_ups_battery_voltage_voltmeter   (raw Shelly ADC)
    │
    ▼
[Outlier filter: window=4, radius=0.04V]
    │   Validated against 391-sample ADC dataset:
    │   actual noise = 0.06V total spread, pure quantization at 0.01V steps
    │   0.04V radius passes all legitimate readings, rejects genuine spikes
    ▼
[30-second moving average, precision=2]
    │
    ▼
sensor.ups_battery_voltage_filtered   ← used by ALL automations and scripts
```

**Critical:** Never use the raw ADC sensor in automation conditions. The Shelly reports at ~1-second intervals with ±0.03V quantization noise. Using raw values would cause threshold thrashing.

### Derived Template Sensors

| Sensor | Description |
|---|---|
| `sensor.ups_estimated_runtime` | Step-function runtime estimate in minutes based on filtered voltage |
| `sensor.ups_outage_duration` | Live outage duration counter in minutes; updates while flag is on |

---

## Automation Architecture

### Two-Stage LVD Design

The shutdown architecture mirrors telecom DC plant design:

```
13.3V  ── PSU float voltage (normal operation)
13.0V  ── Phase 1 / Phase 1b discriminator (real outage vs. Kasa flap)
12.2V  ── Stage 1 LVD: HA graceful shutdown (software)
12.0V  ── PSU failure fallback: emergency shutdown (software)
11.8V  ── Stage 2 LVD: Victron BP-65 hard cutoff (hardware, independent)
```

Stage 2 is fully independent of HA. Even if HA crashes or the automation fails, the BP-65 protects the battery.

### Graceful Shutdown Script (`script.ups_graceful_shutdown`)

Both software shutdown paths (Phase 2 and Phase 3) route through a shared script rather than inline sequences. This provides:

- **Single control point for `hassio.host_shutdown`** — one place to modify the shutdown sequence
- **Test mode gate** — `input_boolean.ups_test_mode` checked here; blocks the actual hardware call while allowing all upstream logic and notifications to run normally
- **Parameterized behavior** — caller specifies `delay_seconds` and `voltage_threshold`; the script re-checks voltage after the delay and aborts if it has recovered

| Caller | delay_seconds | voltage_threshold | Rationale |
|---|---|---|---|
| Phase 2 (PSU failure) | 15 | 12.0V | At 12.0V there is <20 min to BP-65 cutoff; shorter buffer |
| Phase 3 (Stage 1 LVD) | 25 | 12.2V | HA Green disk sync observed at 12–18s; 25s conservative |

### Main Control Loop (`UPS: Power Outage Management`)

**Mode:** `restart` — always responds to the most recent telemetry. Stale queued events are discarded, which is correct for a threshold-based control system.

#### Triggers

| ID | Trigger | Filter |
|---|---|---|
| `grid_down` | Kasa plug → unavailable | 60-second confirmation |
| `low_battery` | Filtered voltage < 12.2V | 1-minute confirmation |
| `psu_failure` | Filtered voltage < 12.0V | 30-second confirmation |
| `grid_up` | Kasa plug ← unavailable | immediate |
| `grid_up` | `homeassistant` start event | immediate |

The 60-second filter on `grid_down` is critical. Kasa plugs frequently show `unavailable` during:
- HA restarts (integration re-poll delay, typically 30–90s)
- Kasa cloud hiccups
- Router DHCP renewals

Most false-unavailable events resolve within 45 seconds.

#### Variables Block

The main automation captures `voltage` and `runtime` once at trigger time via a `variables:` block. These are used in notification messages for Phases 1, 1b, 2, and 3. Phase 4 recovery uses `states()` directly since voltage is read after a 10-minute wait and the trigger-time snapshot would be stale.

#### Phase 1 — Grid Down

Fires when Kasa is offline for 60s **and** `ups_outage_active` is `off` **and** `voltage < 13.0V`.

The voltage discriminator is the v3 fix: during a real outage the PSU loses AC and battery voltage drops below float (13.3V) within seconds. A Kasa cloud flap with PSU still running keeps voltage above 13.0V and falls through to Phase 1b instead.

The `ups_outage_active = off` guard is essential — without it, a Wi-Fi flap during a real outage resets `ups_outage_start` to the flap timestamp, corrupting the duration calculation.

Sets `ups_outage_start` via `input_datetime` — this persists through hardware shutdown, so when HA cold-boots after the outage the duration calculation in Phase 4 is still accurate.

#### Phase 1b — Kasa Flap Discriminator

Reached only when Kasa goes offline 60s but filtered voltage stays above 13.0V — PSU still running. Sends a non-alarmist monitoring notification without setting the outage flag.

Prior to v3, this branch was unreachable: Phase 1 had no voltage condition, so it always fired first in the `choose:` block. The mutual exclusion on 13.0V makes Phase 1b reachable.

#### Phase 2 — PSU Failure Fallback

Fires when filtered voltage drops below 12.0V **regardless of Kasa state**.

Covers: PSU internal failure, blown F1 or F2 fuse, ideal diode failure. These faults leave the Kasa plug online (AC present) while the battery drains uncontrolled. Without this trigger the automation would never detect the fault.

Includes Shelly availability guard — see Reliability Notes below.

Calls `script.ups_graceful_shutdown` with `delay_seconds: 15, voltage_threshold: 12.0`.

#### Phase 3 — Low Battery Graceful Shutdown (Stage 1 LVD)

Fires when filtered voltage < 12.2V for 1 minute **and** outage is active.

Calls `script.ups_graceful_shutdown` with `delay_seconds: 25, voltage_threshold: 12.2`.

**`hassio.host_shutdown` vs `homeassistant.stop`:** `homeassistant.stop` halts the HA software but leaves the HA Green Linux OS running and drawing power. `hassio.host_shutdown` powers down the hardware, allowing a clean cold boot when DC power is restored. Must be verified on hardware before marking Commit 2 complete.

**Verification procedure:**
1. Developer Tools → Services → `hassio.host_shutdown`
2. Confirm HA Green power LED goes completely dark
3. Unplug 12V DC barrel connector, wait 10 seconds, reconnect
4. Confirm clean cold boot

#### Phase 4 — Recovery (Nominal)

Fires on `grid_up` (Kasa available or HA startup) when outage flag is on.

Sequence:
1. Wait for Kasa to become available (timeout 2 min, fail-secure)
2. Wait for filtered voltage > 12.8V — BP-65 Setting 7 reconnect threshold (timeout 10 min, fail-secure)
3. Wait 45 seconds — BP-65 internal 30-second reconnect delay + device stabilization
4. Send "Power Restored" notification with total outage duration
5. Clear `ups_outage_active`

**Why wait for 12.8V:** The BP-65 reconnects loads at 12.8V. From 11.8V, the HDR-60-12 charges a 10Ah battery to 12.8V in well under 10 minutes. This is not a wait for full recharge — it's a wait for the specific reconnect threshold. The 10-minute timeout is appropriate and will not routinely expire.

**`continue_on_timeout: false`:** Both wait_templates halt the sequence on timeout rather than proceeding. This prevents a false "Power Restored" notification when recovery actually failed (PSU fault, Kasa offline permanently, etc.). The outage flag stays on and the watchdog clears it after 4 hours.

---

## Temperature Automations

### High Temperature Alert (`UPS: High Battery Temperature Alert`)

Threshold: **40°C** sustained for 5 minutes.

LiFePO4 cycle life degrades above 45°C. At 40°C the alert gives time to investigate before damage occurs. The enclosure has 6 × ¼″ ventilation holes (3 intake low / 3 exhaust high) which should keep internal temps within 3°C of ambient under normal conditions (~27°C summer maximum in East Hampton installation).

### Charge Inhibit — Below Freezing (`UPS: Low Temperature Charge Inhibit`)

Threshold: **0°C** (inhibit) / **5°C** (restore, hysteresis).

LiFePO4 cells suffer permanent lithium plating if charged below 0°C. The automation cuts the Kasa plug (disables PSU) to stop charging. Loads remain on battery during inhibit — monitor voltage manually if this fires. 5°C hysteresis prevents rapid PSU cycling.

Test mode blocks the Kasa `switch.turn_off` / `switch.turn_on` calls while still allowing the inhibit/restore notifications to fire. This is intentional: during simulation testing you want to see the notification without actually cutting PSU power to a running system.

This is an unlikely scenario for an indoor East Hampton installation but correct to have documented and implemented.

---

## Watchdog (`UPS: Reset Stale Outage Flag`)

If `ups_outage_active` stays on for 4+ hours with grid present and battery above 12.6V, a recovery sequence timed out with `continue_on_timeout: false` and left the flag stuck.

Without the watchdog, a single failed recovery permanently blinds the automation to all future outage events — Phase 1 never fires because `ups_outage_active` is never `off`.

Watchdog condition uses `not unavailable` rather than `state: on` for the Kasa check — this correctly detects grid presence regardless of whether the plug is switched on or off.

---

## Test Mode (`input_boolean.ups_test_mode`)

**Purpose:** Run the full automation logic end-to-end — including all notifications and state machine transitions — without issuing real hardware commands.

**What test mode blocks:**
- `hassio.host_shutdown` — guarded inside `script.ups_graceful_shutdown`
- `switch.turn_off` (PSU charge inhibit cutoff)
- `switch.turn_on` (PSU charge inhibit restore)

**What test mode does NOT block:**
- All notifications (you want to see these during testing)
- `input_boolean` and `input_datetime` state changes
- Phase 1/1b/2/3/4 condition evaluation
- Watchdog

**Simulation procedure:**
1. Create `input_boolean.ups_test_mode` helper (toggle, default OFF)
2. Turn test mode **ON** in HA UI
3. Switch phone to cellular
4. Unplug Kasa — confirm Phase 1 notification within 60–65 seconds
5. Wait or manually set `input_boolean.ups_outage_active` to simulate low battery path
6. Confirm `script.ups_graceful_shutdown` is called but HA Green stays running
7. Replug Kasa — confirm Phase 4 recovery notification
8. Turn test mode **OFF** before live deployment

---

## Reliability Notes

### Kasa False-Unavailable Events

Kasa plugs cloud-poll by default. False-unavailable events are common and expected. Mitigations in this config:

1. **60-second `for:` filter** on `grid_down` — most flaps resolve within 45 seconds
2. **Phase 1b discriminator** — alerts without setting flag when voltage contradicts a real outage (>13.0V)
3. **PSU failure fallback at 12.0V** — catches real faults even when Kasa is incorrectly online

Optional additional hardening not implemented here:
- Enable local Kasa control via `python-kasa` to eliminate cloud dependency
- Add `ping` binary sensor to router or gateway as secondary grid indicator

### Shelly Unavailability and the Float(0) Trap

When `sensor.ups_battery_voltage_filtered` is `unavailable` or `unknown`, template expressions using `| float(0)` return 0.0V. Without guards, the `low_battery` trigger would fire immediately on Shelly reconnect during normal AC-on operation — issuing a spurious `hassio.host_shutdown`.

Both Phase 2 and Phase 3 include explicit conditions blocking execution when the filtered sensor is `unavailable` or `unknown`. This is the most important reliability fix in the config.

---

## Helpers Required

Create in Settings → Devices & Services → Helpers before deploying:

| Helper | Type | Purpose |
|---|---|---|
| `input_boolean.ups_outage_active` | Toggle | Tracks active outage state; guards Phase 1 against timer resets |
| `input_datetime.ups_outage_start` | Date and Time | Outage start timestamp; survives hardware shutdown for accurate duration |
| `input_boolean.ups_test_mode` | Toggle | Dry-run gate; blocks hardware actions while preserving logic and notifications |

---

## Voltage Threshold Reference

| Voltage | Meaning | Action |
|---|---|---|
| 13.3V | PSU float — normal operation | None |
| 13.2V | Top of battery operating range | None |
| 13.0V | Phase 1 / 1b discriminator | Real outage vs. Kasa flap |
| 12.8V | BP-65 Setting 7 reconnect threshold | Loads restored after outage |
| 12.2V | Stage 1 LVD — ~20% SOC remaining | HA graceful shutdown |
| 12.0V | PSU failure fallback threshold | Emergency shutdown |
| 11.8V | Stage 2 LVD — BP-65 hard cutoff | Hardware load disconnect |

---

## Known Edge Case: The Deadlock State

### What It Is

A specific timing scenario where HA Green will not automatically recover:

1. Outage long enough to drop voltage below 12.2V → Phase 3 fires → `hassio.host_shutdown` executes
2. AC grid restores **before** battery reaches 11.8V BP-65 cutoff
3. PSU resumes charging; battery voltage recovers to 13.3V float
4. HA Green hardware remains powered by battery throughout — **no cold boot occurs**
5. OS is halted; automation cannot run; Kasa cannot be commanded

HA stays in a halted "zombie" state indefinitely. This is not detectable remotely.

### Why It Cannot Be Automated Away

The automation that would detect and fix the deadlock runs on HA — which is halted. The Shelly remains powered and could theoretically trigger a Kasa cycle, but Shelly scripting (mJS) would need to be pre-programmed to call the Kasa cloud API directly without HA as intermediary. Not implemented in this version.

### Manual Recovery Procedure

**Use cellular data, not WiFi through the XB7.**

1. Open Kasa app → turn PSU plug **OFF**
2. Wait **10–20 minutes** for battery to drain from ~12.0–12.2V to 11.8V BP-65 cutoff
3. BP-65 disconnects loads — HA Green powers off cleanly
4. Turn PSU plug **ON** via Kasa app
5. Battery charges; BP-65 reconnects at 12.8V → HA Green cold boots cleanly
6. Phase 4 recovery automation runs on startup; "Power Restored" notification fires

The `input_datetime.ups_outage_start` value is preserved through this entire sequence, so the final outage duration in the notification is accurate from the original grid failure.

### How Likely Is This?

Requires: outage long enough to hit 12.2V (>~6 hours at 14.5W load on a full 10Ah battery) but short enough to not reach 11.8V. A narrow window. In practice, outages either resolve quickly (well before 12.2V) or last long enough for the BP-65 to cut cleanly.

---

## Commit Sequence

### Commit 1 — Logic (Current)
- `sensor.yaml` with filtered voltage and template sensors
- `scripts.yaml` with `script.ups_graceful_shutdown`
- `automations.yaml` with all four automations
- Create helpers in HA UI (including `input_boolean.ups_test_mode`)
- Deploy and confirm sensors are reading correctly

### Hardware Assertion (Before Commit 2)
- [ ] Manually trigger `hassio.host_shutdown` from Developer Tools → Services
- [ ] Confirm HA Green LED goes completely dark
- [ ] Disconnect and reconnect 12V DC barrel — confirm clean cold boot
- [ ] Compare `sensor.ups_battery_voltage_filtered` vs raw ADC in history graph — confirm smoothing visible

### End-to-End Simulation (Test Mode ON)
- [ ] Set `input_boolean.ups_test_mode` ON
- [ ] Switch phone to cellular
- [ ] Unplug Kasa — confirm Phase 1 "Power Outage" notification within 60–65 seconds
- [ ] Confirm `ups_outage_active` set to ON
- [ ] Monitor voltage drop — confirm Phase 3 "Critical Battery" notification at 12.2V
- [ ] Confirm `script.ups_graceful_shutdown` called but HA Green stays running (test mode active)
- [ ] Replug Kasa — confirm "Power Restored" notification with correct duration
- [ ] Verify `ups_outage_active` cleared after notification
- [ ] Set `input_boolean.ups_test_mode` OFF for live deployment

### Commit 2 — Verified
- Update `CHANGELOG.md`: move HA automation to `[2026-03-11] — Verified`
- Note `hassio.host_shutdown` confirmed on HA Green hardware

---

## Entity ID Quick Reference

```yaml
# Shelly sensors (confirmed)
sensor.ups_battery_voltge_ups_battery_voltage_voltmeter   # raw ADC voltage
sensor.ups_battery_voltge_ups_temperature_temperature     # DS18B20 temperature

# Filtered sensor (created by sensor.yaml)
sensor.ups_battery_voltage_filtered

# Template sensors (created by sensor.yaml)
sensor.ups_estimated_runtime
sensor.ups_outage_duration

# Script (created by scripts.yaml)
script.ups_graceful_shutdown

# Helpers (created manually in HA UI)
input_boolean.ups_outage_active
input_datetime.ups_outage_start
input_boolean.ups_test_mode      ← new in v4; turn ON for simulation testing


```

Note: `ups_battery_voltge` has a typo (missing 'a') from the original Shelly device name. Entity IDs are correct as shown — do not "fix" the spelling without also updating the entity registry in HA.
