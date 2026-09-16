# Reproduction Guide — 2026-09-15 Full Discharge & Survival Test

Backs `reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md` (**r2** — r1 is superseded; see that report's §10 and its inline R13 corrections). This file is the short "how to check my work" companion — read the report itself for the full analysis.

---

## ⚠ Read this before opening the raw files

Four properties of the InfluxDB data will silently corrupt any re-analysis that does not account for them. All four are [M]. The first three are reproducible from the files in this directory; the fourth bites only on live re-queries.

**1. The export covers 37.5 of ~90 discharge minutes, and the gap does NOT start at the LVD trip.**

| Series | Gap start | Gap end | Duration |
| :--- | :--- | :--- | ---: |
| V | 13:54:30.6Z | 15:01:24.7Z | 4014.1 s (66.90 min) |
| A | 13:54:31.9Z | 15:01:24.7Z | 4012.8 s |
| W | 13:54:30.1Z | 15:01:24.7Z | 4014.6 s |

The gap opens at **13:54:30Z**, when HA's recorder died at the graceful shutdown — **53 minutes before the LVD trip at 14:47:18Z**. Every Knee-HA-down and Cliff figure in the report therefore comes from `esp32_direct_api_log.txt` and the ESPHome capture, **not** from these files. *(r1 of the report and of this README both said the gap ran "from the LVD trip". It does not.)*

**2. There is one phantom sample per series at 15:01:24.73Z. Drop it.**

```
V  13:54:30.641901Z = 12.5302495956421   ->  15:01:24.728230Z = 12.5302495956421
A  13:54:31.898975Z = -1.96474993228912  ->  15:01:24.728682Z = -1.96474993228912
W  13:54:30.147715Z = -25.3829574584961  ->  15:01:24.728887Z = -25.3829574584961
```

Bit-identical to the last pre-gap value in all three series. This is HA's recorder writing last-known state on restart — **not a measurement**. Left in place, it puts a −1.96 A *discharge* point 74 s after charging began. The first true post-recovery samples are at **15:01:25.27Z** (13.0753 V, +3.1862 A).

**3. The InfluxDB measurements are SHARED ACROSS ENTITIES — always filter `entity_id`.**

`A`, `V` and `W` are named after the *unit*, not the device. The database holds **19 entities in `A`** and **24 in `V`**, including the separate 12 V / 500 Ah `battery_bank_monitor_*` pack, the AC-side `ups_outlet_*`, and this pack's former `ups_monitor_bench_*` names (which the May 2026 CSVs use). An unfiltered query silently returns a mixture — during this revision it produced a discharge that never happened, 659 Wh out of a 53 Wh pack, and a 119.0 V starting voltage. Always:

```sql
WHERE ("entity_id"='ups_monitor_battery_current'
    OR "entity_id"='ups_monitor_bench_battery_current')
```

The JSON files in this directory were exported with the filter applied; live re-queries are where the trap bites.

**4. V, A and W are skewed against each other.** A lands **+1.24 to +1.32 s** after V; W lands **−0.43 to −0.53 s** before it [M, n = 12 consecutive]. **r3:** that holds for the *discharge* portion only. The offset is re-drawn at every boot, and the 10:59:47 survival wake falls inside this export — after it, A lands **1.30 s before** V [M, ESPHome log, n = 215]. Report §10.3. On a 5 s grid that is a fifth of a sample period, and it is the dominant error term in every step-resistance derivation. Pair V with I only where the load is steady — **never across a step**.

---

## Files here

| File | What it is |
| :--- | :--- |
| `raw_V.json`, `raw_A.json`, `raw_W.json` | InfluxDB export — `ups_monitor_battery_voltage`/`current`/`power`, query span 2026-09-15 13:16–15:45 UTC. **Coverage span is shorter than the query span — see warning 1 above.** |
| `esp32_direct_api_log.txt` / `esp32_direct_api_script.py` | Direct ESPHome-native-API monitor (bypasses HA) and its log — 93 heartbeats at 60 s + 73 flags at 5 s. Blackout 10:46:28–11:00:19 local. |
| `ha_poller_log.txt` / `ha_poller_script.py` | HA-REST-API monitor. **Carries the 09:34:14 firmware-counter anchor** used for the coulomb-counter cross-check. |
| `network_reachability_log.txt` / `network_reachability_script.py` | Independent ICMP/TCP probes against the XB7 gateway, HA host and ESP32. **Contains the uncorrected tool's three false "back UP" reports (09:55:41, 09:59:04, 10:06:40), preserved deliberately** — the corrected tool restarts at 10:09:26. |
| `live_vs_public_repo.diff` | `diff` of live `H:\esphome\ups-monitor.yaml` against this repo's `UPS-Monitor/ups-monitor.yaml` — 0 lines, both `version: "1.19"`. |

Also used, one level up: `data/logs_ups-monitor-Sept_15_2026_logs.txt` — the owner's independent continuous `esphome logs` capture, 10:04:58–11:18:44 local, 5 s cadence. **This is the only source for the first post-recovery charge reading and for the pre-test `Survival Exit Reason` value.**

---

## Reproducing the key claims

**The capacity shortfall (report §4) — the principal finding.** Two comparisons:

- *Load- and span-matched, vs the 08-31/09-01 test.* Integrate `raw_A.json` and `raw_W.json` from `13:17:00Z` to the first sample at or below **12.565 V** in `raw_V.json` (that is `13:48:00Z`, 12.5460 V). Trapezoid gives **1.0559 Ah / 13.4394 Wh over 31.0 min at 2.043 A mean** (n = 371). The 08-31 report r2 §2 records **1.833 Ah / 23.369 Wh over 54 min at 2.089 A** for the same voltage span. That is **−42.4 % Ah, −42.5 % Wh at matched current**, fourteen days apart. Both this window and the 08-31 window sit entirely inside InfluxDB coverage, so warning 1 does not bite here.
- *LVD-to-LVD, vs 2026-05-06.* 2.5331 Ah / 31.821 Wh against 4.179 Ah / 53.271 Wh = **−39.4 % / −40.3 %**.

**That the coulomb counter is not at fault.** Three checks, all reproducible:
1. `ha_poller_log.txt` line 2 records `fw_ah=0.578883051872253` at 09:34:14. Trapezoid `raw_A.json` over `13:17:00Z`–`13:34:14Z` (n = 206) → **0.5844 Ah**, i.e. **+0.95 %**. Two storage paths, two clocks.
2. Over 10:06:36–10:46:28 the heartbeat counter advances 0.9409 Ah vs 0.9410 Ah by trapezoid on its own published current — **+0.010 %**.
3. The uninstrumented window 09:54:31–10:06:36 must, by difference against the counter, hold 0.2876 Ah → implied mean **1.428 A**, against an independently measured post-shutdown load of ~1.40 A.

**Is it uniform fade or one bad cell?** The pack is sealed — no balance taps, no BMS telemetry — so per-cell voltages are unavailable. The terminal-only substitute uses data already in this repo: `data/Voltage.csv`, `data/Current.csv` and `data/Ah Delivered.csv` hold the **complete 2026-05-06 discharge at 5 s cadence** (n = 2,346 in-window, Ah counter reaching 4.1789). Build pack OCV = `V_loaded + |I| x Ri` against charge removed, normalise each run against **its own** total, and overlay.

Uniform fade predicts the normalised curves overlay. They do not — September sits **60 to 220 mV below** May at every depth (−0.096 V at 5 %, −0.221 V at 50 %, −0.402 V at 95 %), and at matched *absolute* Ah the gap widens monotonically from −134 mV at 0.25 Ah to −924 mV at 2.50 Ah. Sensitivity is `+0.77 V per ohm` of Ri assumed (ΔI ≈ 0.77 A between runs), so sweeping Ri across the whole measured family — 93, 146, 173, 260 mΩ — leaves the depression negative in every cell. That is evidence against uniform fade and for a non-uniform pack. **One confound remains:** the curve is anchored at "charge removed = 0", which assumes both runs started from the same state, and nothing on this system verifies that. Report §4.6 Tests B and C close it.

**What does not explain the shortfall.** Rate effect ≤0.036 Ah (cliff slope measured here at **2.02 V/Ah**, corroborating the 08-31 report's ~1.8 V/Ah); Peukert would need **k = 2.40** against 1.01–1.05 for LiFePO4; float droop ≤0.11 Ah (pre-outage float 13.2047 V vs 13.1970 V post-boost mean); temperature ~0 (77.3–78.2 °F, inside the LFP flat zone). Combined **≤ 9.7 %** of the LVD-to-LVD gap and ~0 % of the load-matched gap.

**Peak recharge current, and why 4.4465 A is a lower bound.** Grep the ESPHome log for `Battery Current` after `11:00:1` — max in the throttled stream is 3.9520 A at 11:00:33. The firmware's own `recharge_peak_a` caught **4.4465 A**, published via `sensor.ups_monitor_last_recharge_peak_current` ~13 s after `on_battery` clears (it is written only in `on_battery`'s `on_release` handler). **But AC return was observed by nothing**: the ESP32 sleeps on a 120 s quantum and woke at 11:00:09, while XB7/host ICMP returned at 10:59:49 — so charging had already run ~60–160 s. The true peak was never sampled.

**That the recharge is PSU-limited.** The Mean Well HDR-60-12 is **54 W / 4.5 A** [S, datasheet; `docs/bom.md` "4.5A/54W"]. The ESPHome log at `11:00:13.671` reads `Battery Power >> 54.627 W` and `Battery Current >> 3.8975 A` — ~~**101 % of the whole supply's nameplate, into the battery branch alone**~~ **r3 (R13): a publish-skew artifact, corrected in report r2 §7.2 but never carried here** — V × I = **50.86 W, 94.2 %** of nameplate, into the battery branch alone, before any share for XB7, host or monitor. The firmware peak of 4.4465 A is **98.8 % of the 4.5 A rating**. *(r1 read the nameplate as "54 A" and concluded the recharge was never PSU-limited. It was PSU-limited throughout.)*

**Was the overage just the BP-65 reconnect hold-off?** Partly — but not for this reading. Grep the ESPHome log for `Battery Current` from `11:00:1` to `11:08`. A BP-65 closure admitting ~2 A of load would step battery current down ~2 A and hold it there; no such step exists. The only excursion is a single −0.907 A dip at `11:00:23` (one second before `Xfinity Modem Online` goes ON) that recovers *above* its pre-dip value by `11:00:33`. ICMP puts XB7 and the host back at **10:59:49**, 24 s before the first charge reading, so loads were already live. The hold-off window was real but closed before any instrument was awake — which is where the true peak lived, unobserved. Adding the measured 26.80 W load: total output runs ~~150.8 %~~ **143.8 % of nameplate at 11:00:13** [D, with the corrected 50.86 W], **decaying to 96.0 % by 11:07:58** — a transient, not a steady state.

**Settling-phase collapse — and its limit.** Load `raw_V.json`, filter `13:16:55Z`–`13:17:15Z`. V falls 13.2047 → 13.0340 within one 5 s sample, past both the 13.15 V and 13.00 V boundaries before `on_battery` registers at 13:17:10. **This bounds Settling at < 5 s at this current; it does not show Settling is absent.** The sampler cannot resolve it (R18).

**The shutdown trigger is noise-dominated (report §6.1) — reproducible at n = 2.** Query the firmware's own published slope, `SELECT "value" FROM "mV/min" WHERE "entity_id"='ups_monitor_voltage_slope'`, over each discharge window. 2026-09-01 gives n=52, sd 18.7 mV/min, **21 crossings** of the −10 mV/min threshold in 52 min; 2026-09-15 gives n=37, sd 24.0, **12 crossings**. Then read `automation.ups_graceful_shutdown_cliff_or_8_min_runtime`: both runs show a trigger that fired, aborted after exactly 30 s, and fired again. Inside the gated region (V < 12.65 V) every excursion below −10 mV/min lasts 1–2 samples and never 3 — which is the basis for the `delayed_on: 180s` recommendation in §6.1.1.

**Why `Apparent Ri` failed its gate — and why r1's reason was wrong.** Filter `raw_A.json` from `13:17:01Z` for 100 s and compute deviation from the arm value (−1.8725 A). You get **16 of 20 samples inside the ±15 % band**, **10 up / 9 down** consecutive differences, CV **6.66 %**, peak-to-peak 22.7 % of mean. That is a bursty load with stationary noise, not a ramp — the 45 s mark simply landed on one of the ~20 % burst excursions. The fix is to compare a **median or windowed mean** against `trig_i`, not a single instantaneous sample; lengthening the dwell would not help.

**Ri reconstructions, and why they are not comparable.** Both use the firmware's own formulas (`H:\esphome\ups-monitor.yaml`, or `UPS-Monitor/ups-monitor.yaml` here — identical, see the diff):
- Apparent Ri: `(rest_v − v_now) / (−i_now) × 1000`, lines 1374–1380.
- Recharge-step Ri: `(vC − vD) / (iC − iD) × 1000`, line 2828.

Eight estimates exist across this dataset spanning **67–260 mΩ**, and **no two methods agree within 30 %**. The onset figure alone swings **90 → 128 mΩ on sample-pairing choice**, because of warning 3. Any Ri trend claim needs one method held fixed across runs; none of these is evidence about capacity in either direction.

**Why each Ri sensor froze.** Read `ups-monitor.yaml` at the lines cited in report §8 — the `restore_value: no`/`yes` declarations (search `g_onset_was_discharging`, `g_last_loaded_v`, `g_onset_r`) settle which ones a reboot can explain. **r3:** only two froze. `Last Onset Step Resistance` updated at 09:17:48 (report §8.2), and a recharge-step value cannot exist after a survival sleep — there is no discharge→charge step to measure (report §8).

**Live-vs-public reconciliation.** `diff "H:\esphome\ups-monitor.yaml" "UPS-Monitor\ups-monitor.yaml"` — 0 lines at test time.

---

## Access needed to re-run any live queries

- HA REST API: `HA_TOKEN` env var, `http://10.0.0.210:8123`
- InfluxDB: `http://10.0.0.210:8086`, database `Home Assistant`, credentials at `H:\secrets.yaml` (`influxdb_user`, `influxdb_pass`) — **do not commit these**, this repo is public
- ESPHome native API: `10.0.0.232:6053`. `esp32_direct_api_script.py` reads the noise PSK from the **`UPS_MONITOR_NOISE_PSK`** environment variable — set it from `api_key_ups_monitor` in `H:\secrets.yaml` before running. It is never inlined in the script; this repo is public.

---

## Conclusions, condensed

- **The pack delivered 42.4 % less charge than it did fourteen days earlier at the same load over the same voltage span.** No rate, Peukert, float or thermal mechanism accounts for more than ~10 % of it. This is the report's principal finding (§4).
- The normalised OCV-vs-charge overlay against May (from CSVs already in this repo) argues **against uniform capacity fade and for a non-uniform pack**, robust to every Ri in the measured family. Per-cell confirmation is impossible — the pack is sealed — so the decisive test is a **matched-load repeat at May's ~1.2–1.4 A** (Open Item 14a) plus a **coulomb-counted recharge to termination** (Open Item 16).
- Full discharge ladder (Settling→Plateau→Knee→Cliff→LVD) measured for the first time; BP-65 trip delay bounded to **90–109 s** against a documented ~102 s.
- Survival mode validated for the first time: 5 clean sleep/wake cycles. `Recovery` exit is reported, but that field held the same value *before* the test, so a fresh write cannot be confirmed from its value alone.
- The recharge was at the HDR-60-12's constant-current limit throughout — **not** pack-limited.
- ~52.8 min of unsupervised margin between HA shutdown and the LVD trip, at this test's reduced post-shutdown load. Real headroom, but gated on characterising capacity first — Open Item 14a is a constant-load discharge and satisfies the margin question in the same run.
- `on_battery` slow-to-clear and `Last Recharge Peak Current` "unknown" were both correct, on-spec behaviour.
- **The shutdown trigger's slope term is noise-dominated, confirmed at n = 2**, and every graceful-shutdown attempt in the record has aborted at least once before succeeding. The fix is a dwell change (`delayed_on: 60s` → `180s`), not a threshold change — report §6.1 and §6.1.1.
- `Apparent Ri` and the recharge-step sensors have named, reproducible failure modes (report §8). ~~`Last Onset Step Resistance` (Open Item 13) and `total_outages` (Open Item 9b) remain unexplained.~~ **r3:** neither was a defect — both updated during the test, at 09:17:48–49 (report §8.2, §9.1). The recharge-step "failure mode" is correct behaviour after survival sleep (report §8).
- Prior-report figures independently re-derived from raw: 2026-09-01 **1.8316 Ah** (−0.1 %) and 2026-08-29 **0.4731 Ah** (−0.3 %). Open Item 15 closed.
