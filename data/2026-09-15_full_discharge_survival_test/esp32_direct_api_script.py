import asyncio
import os
import time
from datetime import datetime

import aioesphomeapi

HOST = "10.0.0.232"
PORT = 6053

# ESPHome native-API encryption key (`api_key_ups_monitor` in secrets.yaml, the
# same value ups-monitor.yaml references as `key: !secret api_key_ups_monitor`).
# Read from the environment, never inlined: this repo is public, and an inline
# literal here is exactly the class of credential that was published for three
# months in 2026 (see .gitleaks.toml, which exists because of that incident).
#   PowerShell:  $env:UPS_MONITOR_NOISE_PSK = (Select-String -Path H:\secrets.yaml -Pattern 'api_key_ups_monitor').Line.Split(':')[1].Trim()
#   bash:        export UPS_MONITOR_NOISE_PSK='...'
NOISE_PSK = os.environ["UPS_MONITOR_NOISE_PSK"]

HEARTBEAT_EVERY_S = 60
LIVENESS_PROBE_S = 5

entity_names = {}  # key -> ESPHome entity name
latest = {}  # name -> last value
tracked = {"last_phase": None, "last_binary": {}}
_last_heartbeat = 0.0


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def classify_and_store(name, val):
    latest[name] = val

    if name == "Discharge Phase":
        if tracked["last_phase"] is not None and val != tracked["last_phase"]:
            log(f"EVENT: phase {tracked['last_phase']} -> {val}")
        tracked["last_phase"] = val

    elif name in (
        "On Battery",
        "Voltage Warning",
        "Voltage Critical",
        "Cliff Imminent",
        "Knee Approaching",
        "Battery Fully Charged",
        "LVD Imminent",
    ):
        prev = tracked["last_binary"].get(name)
        if prev is not None and val != prev:
            log(f"EVENT: {name} {prev} -> {val}")
        tracked["last_binary"][name] = val

    elif name == "Battery Voltage":
        try:
            v = float(val)
            if v < 11.90:
                log(
                    f"FLAG: V={v:.3f} approaching BP-65 hardware LVD (11.80V) — margin {v - 11.80:.3f}V"
                )
        except (TypeError, ValueError):
            pass

    elif name == "Battery Temperature":
        try:
            t = float(val)
            if t >= 100:
                log(
                    f"FLAG: battery temp {t:.1f}F approaching 104F(40C) alert threshold"
                )
        except (TypeError, ValueError):
            pass


def on_state(state_obj):
    name = entity_names.get(state_obj.key)
    if name is None:
        return
    val = getattr(state_obj, "state", None)
    if val is None:
        return
    classify_and_store(name, val)


def maybe_heartbeat():
    global _last_heartbeat
    now = time.time()
    if now - _last_heartbeat >= HEARTBEAT_EVERY_S:
        _last_heartbeat = now
        keys = [
            "Battery Voltage",
            "Battery Current",
            "Battery Power",
            "Discharge Phase",
            "Runtime Remaining Minutes",
            "Ah Delivered (This Outage)",
            "Wh Delivered (This Outage)",
            "Battery Temperature",
            "Apparent Ri",
            # NVS-persisted survival-mode fields — only meaningful once the device
            # has actually entered/exited deep sleep and reconnected; surfaced here
            # so the post-blackout summary is impossible to miss on the next heartbeat.
            "Survival First Wake Voltage",
            "Survival Min Wake Voltage",
            "Survival Last Wake Voltage",
            "Last Survival Cycles",
            "Survival Exit Reason",
        ]
        snap = {k: latest.get(k) for k in keys if k in latest}
        log(f"HEARTBEAT: {snap}")


async def run_once():
    client = aioesphomeapi.APIClient(HOST, PORT, password=None, noise_psk=NOISE_PSK)
    await client.connect(login=True)
    log("EVENT: connected to ESP32 native API directly (HA-independent)")

    entities, services = await client.list_entities_services()
    entity_names.clear()
    for e in entities:
        entity_names[e.key] = e.name
    log(f"HEARTBEAT: {len(entity_names)} entities discovered")

    client.subscribe_states(on_state)

    try:
        while True:
            await asyncio.sleep(LIVENESS_PROBE_S)
            maybe_heartbeat()
            await client.device_info()  # cheap liveness probe; raises if link is gone
    except Exception as e:
        log(f"FLAG: connection lost ({e})")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def main():
    while True:
        try:
            await run_once()
        except Exception as e:
            log(f"FLAG: connect attempt failed ({e})")
        log("EVENT: retrying connection in 5s")
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
