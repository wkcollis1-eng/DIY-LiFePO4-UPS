import subprocess
import time
from datetime import datetime

TARGETS = {
    "xfinity_xb7_gateway": "10.0.0.1",
    "ha_host": "10.0.0.210",
    "ups_esp32_monitor": "10.0.0.232",
}

PING_TIMEOUT_MS = 1000
CYCLE_SLEEP_S = 3
MAX_RUNTIME_S = 4 * 3600
DOWN_CONFIRM = (
    2  # consecutive failed pings before declaring "down" (avoid single-drop noise)
)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def ping_once(ip):
    # 2026-09-15: returncode alone is NOT reliable — Windows ping.exe counts a local
    # "Destination host unreachable" (the CALLER's own stack reporting no route, not
    # the target) toward "Received" packets. Confirmed by hand: pinging a genuinely
    # down host produced "Reply from 10.0.0.105 [this PC]: Destination host
    # unreachable." and this loop read that as the target being up. Require the
    # literal target IP as the replier and reject any unreachable/TTL-expired text.
    r = subprocess.run(
        ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), ip],
        capture_output=True,
        text=True,
    )
    out = r.stdout or ""
    if "unreachable" in out.lower() or "expired" in out.lower():
        return False
    return f"Reply from {ip}:" in out


def main():
    # Start every target as UNKNOWN, not "up" — 2026-09-15: seeding "up": True meant
    # the very first successful reply (real or not) never even logged a transition,
    # and the asymmetric 1-success-vs-2-failures debounce below caused a confirmed
    # false "back UP" report on ha_host that the ping content-fix above should have
    # already prevented; UP_CONFIRM is kept as a second, independent layer.
    UP_CONFIRM = 2
    state = {name: {"up": None, "fail_streak": 0, "ok_streak": 0} for name in TARGETS}
    start = time.time()
    log(
        "HEARTBEAT: net_watch starting — pinging "
        + ", ".join(f"{n}({ip})" for n, ip in TARGETS.items())
    )
    cycle = 0
    while True:
        now = time.time()
        if now - start > MAX_RUNTIME_S:
            log("TEST-END: 4h safety cap reached, stopping net_watch")
            break

        results = {}
        for name, ip in TARGETS.items():
            ok = ping_once(ip)
            results[name] = ok
            s = state[name]
            if ok:
                s["fail_streak"] = 0
                s["ok_streak"] += 1
                if s["up"] is not True and s["ok_streak"] >= UP_CONFIRM:
                    log(f"EVENT: {name} ({ip}) back UP (confirmed x{UP_CONFIRM})")
                    s["up"] = True
            else:
                s["ok_streak"] = 0
                s["fail_streak"] += 1
                if s["up"] is not False and s["fail_streak"] >= DOWN_CONFIRM:
                    log(f"FLAG: {name} ({ip}) went DOWN (no reply x{DOWN_CONFIRM})")
                    s["up"] = False

        cycle += 1
        if cycle % 40 == 0:  # ~ every 2 min at 3s cycle
            status = ", ".join(
                f"{n}={'up' if state[n]['up'] else 'DOWN'}" for n in TARGETS
            )
            log(f"HEARTBEAT: {status}")

        time.sleep(CYCLE_SLEEP_S)


if __name__ == "__main__":
    main()
