import json
import os
import time
import urllib.request
from datetime import datetime

HA_URL = os.environ.get("HA_URL", "http://10.0.0.210:8123")
TOKEN = os.environ["HA_TOKEN"]

SCRATCH = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRATCH, "ups_poll_state.json")

POLL_INTERVAL = 20  # seconds between polls
HEARTBEAT_EVERY = 15  # polls (~5 min at 20s)
MAX_RUNTIME_S = 4 * 3600  # safety cap
SLOPE_WINDOW_S = 180  # window for IR-compensated dV/dt regression

THRESHOLDS = [12.65, 12.40, 12.20, 11.80]  # cliff-gate, warning, hard-fallback, LVD

ENTITIES = [
    "binary_sensor.ups_monitor_on_battery",
    "binary_sensor.ups_monitor_voltage_warning",
    "binary_sensor.ups_monitor_voltage_critical",
    "binary_sensor.ups_monitor_knee_approaching",
    "binary_sensor.ups_monitor_cliff_imminent",
    "binary_sensor.ups_monitor_lvd_imminent",
    "binary_sensor.ups_monitor_battery_fully_charged",
    "binary_sensor.ups_monitor_ina260_alert",
    "sensor.ups_monitor_battery_voltage",
    "sensor.ups_monitor_battery_current",
    "sensor.ups_monitor_battery_power",
    "sensor.ups_monitor_battery_temperature",
    "sensor.ups_monitor_esp32_internal_temperature",
    "sensor.ups_monitor_voltage_slope",
    "sensor.ups_monitor_discharge_phase",
    "sensor.ups_monitor_runtime_remaining_minutes",
    "sensor.ups_monitor_ah_delivered_this_outage",
    "sensor.ups_monitor_wh_delivered_this_outage",
    "sensor.tv_room_ups_monitor_apparent_ri",
]


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def api_states():
    req = urllib.request.Request(
        HA_URL + "/api/states", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    return {e["entity_id"]: e["state"] for e in data if e["entity_id"] in ENTITIES}


def ff(states, eid, default=None):
    v = states.get(eid)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "start_ts": time.time(),
        "poll_count": 0,
        "manual_ah": 0.0,
        "manual_wh": 0.0,
        "baseline_fw_ah": None,
        "baseline_fw_wh": None,
        "prev_ts": None,
        "prev_v": None,
        "prev_i": None,
        "slope_window": [],  # list of [ts, v]
        "last_phase": None,
        "last_binary": {},
        "fail_count": 0,
        "phase_since_ts": None,
    }


def save_state(s):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE_FILE)


def raw_slope_mv_per_min(window):
    # window: list of [ts, v], oldest first. Simple endpoint slope over the window.
    if len(window) < 2:
        return None
    (t0, v0), (t1, v1) = window[0], window[-1]
    dt_min = (t1 - t0) / 60.0
    if dt_min <= 0:
        return None
    return (v1 - v0) * 1000.0 / dt_min


def next_threshold(v):
    below = [t for t in THRESHOLDS if t < v]
    return max(below) if below else None


def main():
    state = load_state()
    log(
        f"HEARTBEAT: poller (re)starting — poll #{state['poll_count']}, "
        f"manual_ah_so_far={state['manual_ah']:.4f}"
    )

    while True:
        now = time.time()
        if now - state["start_ts"] > MAX_RUNTIME_S:
            log("TEST-END: 4h safety cap reached, stopping poller")
            save_state(state)
            break

        try:
            states = api_states()
            state["fail_count"] = 0
        except Exception as e:
            state["fail_count"] += 1
            log(
                f"FLAG: API fetch failed ({e}); consecutive failures={state['fail_count']}"
            )
            if state["fail_count"] >= 5:
                log(
                    "FLAG: 5 consecutive API failures — WiFi/HA host may be struggling under load. Stopping poller."
                )
                save_state(state)
                break
            time.sleep(POLL_INTERVAL)
            continue

        on_batt = states.get("binary_sensor.ups_monitor_on_battery")
        if on_batt != "on":
            v_last = ff(states, "sensor.ups_monitor_battery_voltage")
            phase_last = states.get("sensor.ups_monitor_discharge_phase")
            fw_ah_last = ff(states, "sensor.ups_monitor_ah_delivered_this_outage")
            log(
                f"TEST-END: on_battery={on_batt} (AC restored or test ended). "
                f"V={v_last} phase={phase_last} manual_ah_tracked={state['manual_ah']:.4f} fw_ah={fw_ah_last}"
            )
            save_state(state)
            break

        v = ff(states, "sensor.ups_monitor_battery_voltage")
        i = ff(states, "sensor.ups_monitor_battery_current")
        p = ff(states, "sensor.ups_monitor_battery_power")
        fw_slope = ff(states, "sensor.ups_monitor_voltage_slope")
        phase = states.get("sensor.ups_monitor_discharge_phase")
        fw_rt = ff(states, "sensor.ups_monitor_runtime_remaining_minutes")
        fw_ah = ff(states, "sensor.ups_monitor_ah_delivered_this_outage")
        fw_wh = ff(states, "sensor.ups_monitor_wh_delivered_this_outage")
        ri_fw = ff(states, "sensor.tv_room_ups_monitor_apparent_ri")
        batt_temp = ff(states, "sensor.ups_monitor_battery_temperature")
        esp_temp = ff(states, "sensor.ups_monitor_esp32_internal_temperature")

        if v is None or i is None:
            log("FLAG: voltage/current unavailable while on_battery=on")
            time.sleep(POLL_INTERVAL)
            continue

        if state["baseline_fw_ah"] is None:
            state["baseline_fw_ah"] = fw_ah if fw_ah is not None else 0.0
            state["baseline_fw_wh"] = fw_wh if fw_wh is not None else 0.0
            log(
                f"HEARTBEAT: baseline captured — V={v:.3f} I={i:.3f}A P={p} phase={phase} "
                f"fw_ah={fw_ah} fw_wh={fw_wh} fw_rt={fw_rt}min ri_fw={ri_fw}"
            )

        # --- binary sensor transition watch ---
        for bkey in [
            "binary_sensor.ups_monitor_voltage_warning",
            "binary_sensor.ups_monitor_voltage_critical",
            "binary_sensor.ups_monitor_knee_approaching",
            "binary_sensor.ups_monitor_cliff_imminent",
            "binary_sensor.ups_monitor_lvd_imminent",
            "binary_sensor.ups_monitor_ina260_alert",
        ]:
            cur = states.get(bkey)
            prev = state["last_binary"].get(bkey)
            if prev is not None and cur != prev:
                log(
                    f"EVENT: {bkey} {prev} -> {cur} at V={v:.3f} I={i:.3f}A phase={phase}"
                )
            state["last_binary"][bkey] = cur

        # --- phase transition watch ---
        if state["last_phase"] is not None and phase != state["last_phase"]:
            dwell_min = (
                (now - state["phase_since_ts"]) / 60.0
                if state["phase_since_ts"]
                else None
            )
            dwell_s = f"{dwell_min:.1f}min" if dwell_min is not None else "?"
            log(
                f"EVENT: phase {state['last_phase']} -> {phase} at V={v:.3f}, dwell in prior phase={dwell_s}"
            )
            state["phase_since_ts"] = now
        if state["phase_since_ts"] is None:
            state["phase_since_ts"] = now
        state["last_phase"] = phase

        # --- coulomb-counting cross-check ---
        if state["prev_ts"] is not None:
            dt_h = (now - state["prev_ts"]) / 3600.0
            avg_i = (abs(i) + abs(state["prev_i"])) / 2.0
            avg_p = abs(p) if p is not None else avg_i * v
            state["manual_ah"] += avg_i * dt_h
            state["manual_wh"] += avg_p * dt_h

            if fw_ah is not None and state["baseline_fw_ah"] is not None:
                fw_delta_ah = fw_ah - state["baseline_fw_ah"]
                if fw_delta_ah > 0.1:
                    rel_diff = abs(state["manual_ah"] - fw_delta_ah) / fw_delta_ah
                    if rel_diff > 0.10:
                        log(
                            f"FLAG: coulomb-count drift — manual={state['manual_ah']:.4f}Ah vs "
                            f"firmware_delta={fw_delta_ah:.4f}Ah ({rel_diff * 100:.1f}% diff)"
                        )

        # --- IR-compensated slope vs firmware EMA slope ---
        # Raw terminal voltage moves with every load-current wiggle (V = OCV + I*R),
        # which swamped a short endpoint-difference slope even after step-resetting
        # (2026-09-15: -44.9, -70.3, -3.2 mV/min inside 90s with no real trend change).
        # Subtract I*R per sample using the most recent settled Ri so the slope tracks
        # the OCV depletion trend, not load noise. R held fixed for the window (only
        # updates when firmware publishes a new settled-step Ri, which is rare).
        r_ohm = (ri_fw / 1000.0) if (ri_fw is not None and ri_fw > 0) else None
        ocv_proxy = (v - i * r_ohm) if r_ohm is not None else v
        state["slope_window"].append([now, ocv_proxy])
        state["slope_window"] = [
            w for w in state["slope_window"] if now - w[0] <= SLOPE_WINDOW_S
        ]
        raw_slope = raw_slope_mv_per_min(state["slope_window"])

        window_span_s = (
            (state["slope_window"][-1][0] - state["slope_window"][0][0])
            if len(state["slope_window"]) >= 2
            else 0
        )
        slope_reliable = len(state["slope_window"]) >= 4 and window_span_s >= 120
        cliff_bs = states.get("binary_sensor.ups_monitor_cliff_imminent")
        # DEBOUNCE (2026-09-15): once in Knee/Cliff, rising Ri makes ordinary load noise
        # swing this signal past -10 mV/min every other poll — diagnosed and confirmed
        # against firmware's own slope + the March validation report (Ri dominates near
        # the knee). Re-flagging every ~20-40s adds nothing once the pattern is known,
        # so only resurface it every 5 min, OR immediately if firmware's cliff_imminent
        # itself changes state (handled separately in the binary-sensor watch above).
        SLOPE_FLAG_DEBOUNCE_S = 300
        can_flag_slope = (
            now - state.get("last_slope_flag_ts", 0)
        ) >= SLOPE_FLAG_DEBOUNCE_S

        if (
            slope_reliable
            and raw_slope is not None
            and raw_slope <= -10
            and v < 12.65
            and cliff_bs != "on"
            and can_flag_slope
        ):
            log(
                f"FLAG: IR-compensated slope {raw_slope:.1f} mV/min (OCV-trend, {window_span_s:.0f}s window) "
                f"already past cliff threshold (-10) at V={v:.3f}, but cliff_imminent binary_sensor still "
                f"'{cliff_bs}' — EMA lag or automation not armed yet (debounced {SLOPE_FLAG_DEBOUNCE_S}s)"
            )
            state["last_slope_flag_ts"] = now

        # --- dual runtime ETA: IR-compensated slope extrapolation to LVD vs firmware's power-based estimate ---
        if (
            slope_reliable
            and raw_slope is not None
            and raw_slope < -1
            and fw_rt is not None
            and fw_rt > 0
            and can_flag_slope
        ):
            eta_lvd_min = (v - 11.80) * 1000.0 / abs(raw_slope)
            if eta_lvd_min > 0:
                rel = abs(eta_lvd_min - fw_rt) / max(fw_rt, 1e-6)
                if rel > 0.30 and abs(eta_lvd_min - fw_rt) > 10:
                    log(
                        f"FLAG: runtime ETA disagreement — slope-extrapolated={eta_lvd_min:.1f}min "
                        f"vs firmware runtime_remaining={fw_rt:.1f}min (ocv_slope={raw_slope:.1f}mV/min over "
                        f"{window_span_s:.0f}s, fw_slope={fw_slope}) — NOTE: this proxy holds Ri fixed at the "
                        f"last settled value, so it will UNDERSTATE the true cliff if Ri is actually rising "
                        f"(debounced {SLOPE_FLAG_DEBOUNCE_S}s)"
                    )
                    state["last_slope_flag_ts"] = now

        # --- current-step log (informational only — see note below) ---
        # apparent_ri (H:/esphome/ups-monitor.yaml:1384) only publishes inside a
        # "settled-step" branch gated on a rest/load voltage pair meeting a stability
        # band; it does NOT recompute from live V/I every cycle. Confirmed 2026-09-15:
        # it read identically (67.3143692016602) across the whole test so far, before
        # and during discharge. A per-poll noisy 20s-cadence delta is not the same
        # measurement, so this is logged for the record only, never compared/flagged.
        if (
            state["prev_i"] is not None
            and abs(i - state["prev_i"]) > 0.3
            and state["prev_v"] is not None
        ):
            di = i - state["prev_i"]
            dv = v - state["prev_v"]
            r_mohm = abs(dv / di) * 1000.0
            log(
                f"EVENT: current step {state['prev_i']:.3f}->{i:.3f}A, instantaneous R={r_mohm:.1f}mOhm "
                f"(informational — not comparable to apparent_ri, a settled-step sample, currently {ri_fw})"
            )

        # --- thermal safety check ---
        if batt_temp is not None and batt_temp >= 100:
            log(
                f"FLAG: battery temp {batt_temp:.1f}F approaching 104F(40C) alert threshold"
            )

        # --- LVD proximity safety flag ---
        if v < 11.90:
            log(
                f"FLAG: V={v:.3f} approaching BP-65 hardware LVD (11.80V) — margin {v - 11.80:.3f}V"
            )

        state["prev_ts"] = now
        state["prev_v"] = v
        state["prev_i"] = i
        state["poll_count"] += 1

        if state["poll_count"] % HEARTBEAT_EVERY == 0:
            fw_delta_ah = (
                (fw_ah - state["baseline_fw_ah"])
                if (fw_ah is not None and state["baseline_fw_ah"] is not None)
                else None
            )
            log(
                f"HEARTBEAT: V={v:.3f} I={i:.3f}A P={p} phase={phase} "
                f"raw_slope={raw_slope if raw_slope is None else round(raw_slope, 1)}mV/min fw_slope={fw_slope} "
                f"fw_rt={fw_rt}min manual_ah={state['manual_ah']:.4f} fw_delta_ah={fw_delta_ah} "
                f"batt_temp={batt_temp}F esp_temp={esp_temp}F ri_fw={ri_fw}"
            )

        save_state(state)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
