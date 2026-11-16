# UPS Monitor Rev 4 firmware: V4.2 optimization review, and its check

Date: 2026-11-16. Base: `ups-monitor-rev4.yaml` V4.1 (commit 8cafe2e). Toolchain: ESPHome
2026.10.2, which builds with ESP-IDF 5.5.6, on an ESP32-C3.

This file holds two things:
- §1–§4: a check of the 2026-11-15 optimization review against the ESPHome 2026.10.2 source,
  the TI INA260 datasheet and two real compiles. It also covers what was applied as V4.2.
- §5: the review itself, as received.

Where they disagree, §1–§4 win.

Evidence tags follow the design doc:
- [M] measured, here meaning a compile or build log;
- [D] derived;
- [I] inferred;
- [S] a source read for this check: the ESPHome 2026.10.2 package (file named), or TI SBOS656C
  (Rev C, Dec 2016, section named).

**Nothing here has run on hardware. V4.2 is not bench-tested and not flashed.**

---

## 1. Outcome

| # | Review said | Check found | In V4.2 |
|---|---|---|---|
| O1 | OTA `password:` → `encryption:`; then delete `ota_password` from secrets.yaml | The change is sound [S]. The secrets advice is **wrong**: `ota_password` is still read by `UPS-Monitor/ups-monitor.yaml` (deployed) and `Top-Off-Charger/firmware/top-off-charger.yaml`. Deleting it breaks their next build. Measured saving: 1,262 B flash and 32 B RAM, not ~3.5 KB / 60 B [M] | **Applied.** Keep `ota_password` |
| O2 | `board:` → `variant: esp32c3` | Sound [S]. Side effect the review did not list: HA's device "model" changes from `seeed_xiao_esp32c3` to `esp32-c3` [M] | **Applied** |
| O3 | `sdkconfig_options: COMPILER_OPTIMIZATION_SIZE: "y"` | **Changes nothing.** `framework: advanced: compiler_optimization` already defaults to `SIZE`. V4.1's generated sdkconfig already has `CONFIG_COMPILER_OPTIMIZATION_SIZE=y` [S, M]. Spelled as in the review, without the `CONFIG_` prefix, the key would also name no Kconfig symbol, because ESPHome writes user keys verbatim [S]. (I do not have the review's YAML, so I cannot say which spelling it used) | **Not applied** |
| O4 | Delete `lvd_voltage` and the commented power block | Sound: `lvd_voltage` has no `${…}` use [S: grep] | **Applied** |
| O5 | 4.96 ms, not ~8.8 ms; "8.8 ms matched the POR config 0x6127"; cites "Table 6" | 4.96 ms is right [S]. The POR claim is **wrong**: 0x6127 is AVG=1, a 2.2 ms refresh. 8.8 ms is AVG=4 with both conversion times at 1.1 ms. The config field table is Table 5 (Table 6 is Mask/Enable) | **Applied**, with the corrected origin |

V4.2 changes five non-comment lines against V4.1, and no others [M: a diff of every non-comment
line]:
- `lvd_voltage` is deleted;
- `version` "4.1" → "4.2";
- the boot line says V4.2;
- `board:` → `variant:`;
- `password:` → `encryption:`.

No substitution value, interval, threshold or UPS behaviour changed.

---

## 2. Verification

### 2.1 Compile [M]

Both builds ran on ESPHome 2026.10.2 with the native ESP-IDF 5.5.6 toolchain (the default for
`esp32` in this release [S: `components/esp32/__init__.py`, `_resolve_toolchain`]). They used
dummy secrets in a scratch directory, and the same build directory, so the comparison is like for
like.

| | V4.1 (base) | V4.2 | Δ |
|---|---|---|---|
| `esphome config` | valid, 1 warning: "'ota' password wastes significant flash and RAM; using 'encryption' instead is recommended" | valid, 0 warnings | |
| `main.cpp.obj` built, linked, `firmware.factory.bin` and `firmware.ota.bin` created | yes | yes | |
| errors / `warning:` lines | 0 / 0 | 0 / 0 | |
| App image | 0xF10C0 = 987,328 B | 0xF0BD0 = 986,064 B | −1,264 B |
| Flash used (of 1,835,008) | 986,962 B | 985,700 B | −1,262 B |
| RAM used (of 321,296) | 116,354 B | 116,322 B | −32 B |
| `ESPHOME_BOARD` | `"seeed_xiao_esp32c3"` | `"esp32-c3"` | |
| OTA defines | `USE_OTA_ENCRYPTION`, `USE_OTA_PASSWORD` | `USE_OTA_ENCRYPTION`, `USE_OTA_ENCRYPTION_REQUIRED` | |
| `CONFIG_COMPILER_OPTIMIZATION_SIZE` | `y` | `y` | none: O3 is already the default |

Image arithmetic:
- 0xF10C0 = 15 × 65,536 + 0x10C0 = 983,040 + 4,288 = 987,328.
- 0xF0BD0 = 983,040 + 0x0BD0 = 983,040 + 3,024 = 986,064.
- Flash Δ = 986,962 − 985,700 = 1,262 B.

About 10 B of that is the shorter board string: 19 B (`seeed_xiao_esp32c3` + NUL) − 9 B
(`esp32-c3` + NUL). This assumes one copy and was not checked in the map [I]. The rest, about
1.25 KB, is O1.

**Build B** (Appendix A of the bench procedure, applied to V4.2) also compiled: 0 errors and
0 warnings, with `main.cpp.obj` rebuilt and linked [M].

Not run: the host-side lambda tests from the V4.1 review. V4.2 changes no lambda; the only string
that changed is the boot line's version.

### 2.2 O1, OTA encryption [S]

- `components/esphome/ota/__init__.py`: a bare `encryption:` takes the `api: encryption: key`
  (`_resolve_encryption_key`). With `encryption:` present, `USE_OTA_PASSWORD` is not defined, so
  the password-auth path is not built, and `USE_OTA_ENCRYPTION_REQUIRED` is defined.
- `ota_esphome.cpp`: with REQUIRED, a client that does not offer Noise gets
  `OTA_RESPONSE_ERROR_ENCRYPTION_REQUIRED`.
- V4.1 already *offered* encryption: a static API key alone defines `USE_OTA_ENCRYPTION`. What it
  lacked was the requirement. So O1's real effect has two parts. The esphome OTA port refuses
  plaintext uploads, which V4.1 accepted with the password. And the password-auth code is gone.
- `espota2.py` carries the uploader-side plaintext fallback, marked "removed in 2027.3.0". It
  fails closed toward a device whose running firmware does not offer encryption. That does not
  bite here: the bench procedure (§2) makes the first flash over USB, and every later OTA goes to
  a build that offers encryption.
- **Not covered by the key, unchanged from V4.1:** `captive_portal:` auto-loads the
  `ota: platform: web_server` (`components/captive_portal/__init__.py`, `auto_load`). Its
  `/update` exists only on the fallback AP, behind `ap_password`. ESPHome's validator warns only
  when a `web_server:` or `prometheus:` block exposes it on the LAN; this file has neither.
- **Secrets:** `ota_password` appears in three firmware files. They all resolve against the same
  `secrets.yaml` on the HA host (README; `data/2026-09-15_full_discharge_survival_test/README.md`):
  `UPS-Monitor/ups-monitor.yaml:932` and `Top-Off-Charger/firmware/top-off-charger.yaml:294` still
  read it. Keep it.
- **The ~3.5 KB / 60 B figure:** not found in the 2026.10.2 source or on the live OTA docs page.
  The source warning says only "significant". The measured figure is 1,262 B / 32 B. It is smaller
  than a password-only device would save, because the Noise library stays in: the API needs it.

### 2.3 O2, variant [S]

- The ESPHome esp32 docs (fetched 2026-11-16) say of `board:`: "This setting is no longer
  recommended, variant should be used instead".
- `_detect_variant`: with the ESP-IDF toolchain, a variant-only config gets an informational
  board string, `VARIANT_FRIENDLY["ESP32C3"].lower()` = `esp32-c3`, used only for
  `ESPHOME_BOARD`. That string is the `model` field the API sends to HA
  (`api_connection.cpp`, `MODEL = ESPHOME_BOARD`).
- The `seeed_xiao_esp32c3` entry in `boards.py` holds only pin aliases (D0–D10) and the variant.
  Every pin in this file is written as a GPIO number (GPIO3, 4, 6, 7, 10; GPIO5 through
  `GPIO_NUM_5`), so no alias is lost.
- Flash size stays at the 4 MB default (`flash_size`, default `4MB`); the partition table is
  unchanged.

### 2.4 O5, INA260 timing [S: SBOS656C]

Configuration register (§8.6.1, Table 5): bits 11–9 AVG, 8–6 VBUSCT, 5–3 ISHCT, 2–0 MODE.

The platform writes `0b0000001100000111` = 0x0307 (`components/ina260/ina260.cpp`, `setup()`):

| Bits | Field | Value | Meaning |
|---|---|---|---|
| 11–9 | AVG | 001 | 4 averages |
| 8–6 | VBUSCT | 100 | 1.1 ms |
| 5–3 | ISHCT | 000 | 140 µs |
| 2–0 | MODE | 111 | continuous, shunt and bus |

**Refresh = AVG × (VBUSCT + ISHCT) = 4 × (1.1 + 0.14) ms = 4 × 1.24 ms = 4.96 ms.**

The formula is the datasheet's own (§8.4.1). Its example of 588 µs + 588 µs at AVG=4 "results in
the data updating approximately every 4.7 ms": 4 × 1.176 ms = 4.704 ms.

Reset value 0x6127 = `0110 0001 0010 0111`: AVG 000 (1), VBUSCT 100 (1.1 ms), ISHCT 100 (1.1 ms),
MODE 111. Its refresh is 1 × 2.2 ms = 2.2 ms. The old 8.8 ms is 4 × (1.1 + 1.1) ms: AVG=4 with
both conversion times left at reset. The chip never runs that here.

30 ms onset spacing ÷ 4.96 ms = 6.05, so the "≥ 6×" in the review holds.

### 2.5 Other review claims re-read [S]

- **Not YAML-configurable:** INA260 AVG and conversion times. `ina260/sensor.py` offers only
  `bus_voltage`, `current` and `power`.
- **Failed read returns without publishing:** confirmed in `ina260.cpp` `update()`, which returns
  on each failed `read_byte_16`.
- **CVRF clears on a read of 06h:** confirmed (§8.3.3: "Reading the Mask/Enable Register (06h)").
- **Bus-voltage bit 15 is always zero:** confirmed (§8.6.3, Figure 32 note).
  0xFFFF as a current is −1 LSB = −1.25 mA (§8.6.2, two's complement, 1.25 mA LSB).
- **I2C:** fast mode tops out at 400 kHz; high-speed mode, up to 2.94 MHz, needs the HS master
  code (§8.5.3.2, §8.5.3.3.1). Confirmed.
- **Arithmetic only, the source figures not re-read:**
  - ±35 mV × 6.556 = ±0.229 V;
  - 750 ms ÷ 8 = 93.75 ms;
  - 0.5 °C × 1.8 = 0.9 °F.
- **Not re-checked in this pass:** the ESP32-C3 datasheet items (GPIO5 RTC pad, ADC1_CH4, ±35 mV
  at 12 dB), the ESP-IDF GPIO hold rules, the Pololu and Mean Well figures, and the DS18B20
  datasheet. They stand on the review's reading and on the V4.1 review.

---

## 3. Held items the source now settles

These were held as "not verified". The 2026.10.2 source answers four of them. None changes
V4.2; they change what a later decision rests on.

- **Item 4, publish dedup. ESPHome does not drop unchanged values.**
  - `Sensor::publish_state` → `internal_send_state_to_frontend` has no equality test
    (`components/sensor/sensor.cpp`).
  - `APIServer::on_sensor_update` sends every publish of a non-internal sensor to every
    subscribed client (`api_server.cpp`, `API_DISPATCH_UPDATE`).
  - The only merge is in `DeferredBatch::add_item` (`api_connection.h`): a second publish of the
    same entity, while one is still queued in the unsent batch, is merged with it.
  - So the ~140/min upper bound is the real network count.
  - Whether HA records identical states was not checked here.
- **Item 5, NVS writes. They are coalesced, and bounded per key.**
  - A `restore_value: yes` global is compared every 1 s (`RestoringGlobalsComponent`,
    `PollingComponent(1000)`, `memcmp`). A change is queued with `save()`.
  - `ESP32PreferenceBackend::save` (`components/esp32/preferences.cpp`) only updates a RAM list,
    `s_pending_save`, and replaces any pending entry for the same key.
  - NVS is written only when `global_preferences->sync()` runs:
    - every `flash_write_interval`, default 60 s (`components/preferences`; this file sets no
      `preferences:` block);
    - and in `on_shutdown`. `deep_sleep` calls `App.run_safe_shutdown_hooks()`, so this
      includes every sleep entry.
  - At sync, `is_changed_` skips any key whose bytes match NVS.
  - The integration sensors' `restore: true` uses the same path (`publish_and_save_` →
    `pref_.save`).
  - **Bound:** at most one NVS write per key per 60 s while its value keeps changing, plus one per
    shutdown or sleep entry. `last_outage_min_v`, updated about every 5 s on discharge, costs at
    most 1 write/min, not 12/min [D]. The survival-wake trio costs at most one write each per
    wake.
  - Scope: 33 `restore_value: yes` globals and 4 `restore: true` integration sensors [S: grep].
    The NVS partition is 0x70000 = 448 KiB [M: generated `partitions.csv`].
  - A flash-life figure would need the NVS entry sizes and the flash's erase-cycle rating, which
    were not read. Not quantified.
- **Item 6, does `sample()` honour `samples:`? Yes. The item stands.**
  - `ADCSensor::sample()` → `sample_fixed_attenuation_()` loops `sample_count_` times over
    `adc_oneshot_read` (`components/adc/adc_sensor_esp32.cpp`).
  - At 8 samples, the 1 s supervisor plus the 5 s sensor make (1 + 0.2) calls/s × 8 = 9.6
    conversions/s [D].
  - The time per conversion was not measured.
- **Item 7, burst read of 06h + 02h. Not possible; two transfers is the minimum.**
  - SBOS656C §8.5.3.3: a read returns the register at the pointer, MSB then LSB.
  - "To change the register pointer for a read operation, a new value must be written to the
    register pointer."
  - The datasheet describes no auto-increment.

Still held, needing a bench measurement or the owner's decision: items 1, 2, 3, 8 and 9.
Item 10 stays a firmware heuristic; its arithmetic is confirmed in §2.5.

---

## 4. Owner actions

1. **Do not delete `ota_password` from `secrets.yaml`.** The deployed Rev 1 monitor and the
   top-off charger still use it.
2. In HA, the Rev 4 device's model will read `esp32-c3`. Nothing in this repo keys on it; the HA
   host's own configuration is not in this repo and was not checked.
3. The bench procedure now names V4.2. V4.2 changes no expected line except the boot line's
   version.

---

## 5. The review as received (2026-11-15)

Reproduced unchanged except that the owner's name is written as "the owner", as elsewhere in this
repo. The file it names, `ups-monitor-rev4-v4.2.yaml`, is `ups-monitor-rev4.yaml` here; git keeps
the versions. §1–§4 above supersede it where they differ: O1's secrets advice, O3, and O5's
account of 8.8 ms.

> # UPS Monitor Rev 4 — firmware V4.2 optimization review
>
> Date: 2026-11-15. Base: V4.1 (2026-11-15), file `ups-monitor-rev4-v4.2.yaml`.
> Constraint, as asked: optimization **only through component specifications
> and current ESPHome documentation** (ESPHome 2026.10.2 / ESP-IDF 5.5.6).
> No interval, threshold, debounce or cadence was retuned on judgement, and no
> behaviour was changed on a bench guess.
>
> ## What changed in V4.2 (all in the file, marked REV 4.2 [O1]–[O5])
>
> | # | Change | Grounding | Effect |
> |---|---|---|---|
> | O1 | OTA `password:` → `encryption:` (reuses the API key) | ESPHome OTA docs: plain-text OTA fallback is removed in 2027.3.0; a password wastes ~3.5 KB flash and 60 B RAM. V4.1 was never flashed, so no staged migration is needed — first flash of V4.2 is already encrypted. | Future-proofing + ~3.5 KB flash. After flashing, remove the now-unused `ota_password` from secrets.yaml. |
> | O2 | `esp32: board: seeed_xiao_esp32c3` → `variant: esp32c3` | ESPHome esp32 docs: board "is no longer recommended, `variant` should be used instead"; at least one of board/variant must be set. Pins in this file are addressed by GPIO number, so no pin-alias change. | Doc-compliant; no behaviour change. |
> | O3 | `sdkconfig_options: COMPILER_OPTIMIZATION_SIZE: "y"` | Used in official ESP32-C3 device examples (e.g. Shelly H&T Gen3). | Compile option only. Size saving on this config is **unverified** — the build log will show it. |
> | O4 | Deleted dead `lvd_voltage` substitution and the commented-out INA260 power channel (F07) | Code audit: `lvd_voltage` is unreferenced since F10; the power block was commented YAML. | Zero runtime effect; file is 19 lines shorter. History lives in git. |
> | O5 | Comment correction: AVG=4 refresh is **4.96 ms**, not ~8.8 ms | ESPHome writes INA260 config 0x0307 (AVG=4, VBUSCT 1.1 ms, ISHCT 140 µs); TI INA260 SBOS656C Table 6: 4 × (1.1 ms + 0.14 ms) = 4.96 ms. The 8.8 ms figure matched the POR config 0x6127 (both CTs 1.1 ms). | Comment only. The 30 ms onset sample spacing is still ≥ 6× the refresh, so its independence argument still holds. |
>
> Validation done: YAML parses (Python yaml, `!secret` handled); project
> version is 4.2; no remaining `board: seeed`, `ota_password` in code, or
> "V4.1 boot" string (the two remaining "8.8 ms" mentions are the O5
> explanation itself). **ESPHome `config` validation passed on ESPHome
> 2026.10.2 (exit 0, "Configuration is valid!")** using a clean venv install
> and dummy secrets in /tmp — no warnings. Validation caught one real error
> in the first draft: `sdkconfig_options` is not valid directly under `esp32:`,
> it must sit under `framework:` — fixed in the delivered file, and the
> re-run passed. Compile was not run (that downloads the ESP-IDF toolchain);
> config validation does not prove it compiles, and the firmware is still
> **not bench-tested and not flashed**.
>
> ## What was checked and found already correct (no change)
>
> - **INA260 F07 confirmed:** with `power:` omitted, ESPHome 2026.10.2
>   `ina260.cpp update()` never reads register 0x03. The one-transfer-per-second
>   saving is real and already banked in V4.1.
> - **INA260 failed read → return, no publish:** values freeze at last-good,
>   matching the firmware's stale-data reasoning. AVG/conversion time are **not
>   YAML-configurable** — AVG=4 is fixed in the driver, so no AVG retune is
>   possible from the config.
> - **F02 CVRF gate:** datasheet-exact (TI SBOS656C §8.3.3, §8.6.5). Reading
>   Mask/Enable 0x06 clears CVRF, so one read per poll is the correct idiom.
>   Note: in continuous mode a conversion completes every ~5 ms, so at a 1 s
>   supervisor cadence CVRF is set on essentially every healthy poll — it is a
>   stall/power-down detector, not a per-sample freshness discriminator.
> - **GPIO5 hold:** `gpio_hold_en` + `gpio_deep_sleep_hold_en` is exactly what
>   ESP-IDF requires on ESP32-C3; GPIO5 is an RTC pad. Correct as written.
> - **PSU ADC on GPIO4 = ADC1_CH4:** the calibrated, Wi-Fi-safe ADC (ESP32-C3
>   datasheet §4.2.2.1). 12 dB attenuation, 8 samples, C7 100 nF match the
>   datasheet's own ADC test conditions. ±35 mV at ATTEN3 is ±0.23 V at the bus
>   (×6.556) — ample margin under the 7.0 V mains threshold.
> - **DS18B20 at 30 s / 12-bit:** 40× the 750 ms conversion time. Dropping to
>   9-bit would cut conversion 8× (750 → 93.75 ms) but its 0.5 °C step is
>   0.9 °F, which breaks the firmware's 0.1 °F display resolution — blocked.
> - **I2C 400 kHz:** joint ceiling of ESP32-C3 fast mode and INA260 fast mode.
>   Cannot go faster without the INA260 high-speed master-code sequence, which
>   ESPHome's I2C driver does not expose.
> - **Logger INFO + baud_rate 0, Wi-Fi `power_save_mode: none`, deep-sleep
>   timer-only wake, `scan: false`:** all documented and valid as written.
> - **20 ms survival settle, 30 ms onset spacing, 1 s INA260 cadence:** all
>   ≥ 4× the 4.96 ms AVG=4 refresh.
> - **D24V7F3 has no enable pin**, so the 3.3 V rail cannot be power-gated in
>   survival sleep; its quiescent is < 10 µA. The S13V25F12 modem shed (EN low)
>   is the only way to stop its 10–35 mA no-load quiescent — already the design.
>
> ## Held — NOT changed, because spec/doc alone cannot justify them
>
> These are the big-ticket items. Each needs a bench measurement (or a
> decision from the owner), so they are listed here, not silently applied:
>
> 1. **Onset detector 100 ms → 500 ms–1 s** (20 raw I2C transfers/s, the
>    dominant I2C/CPU-tick cost). Needs bench: no step missed at 1 s, Onset
>    Capture Quality Good still goes true, measured awake current at both
>    cadences. The step is sustained (minutes), not a 100 ms transient, so 1 s
>    *should* be harmless — that is an inference, not a spec fact.
> 2. **Survival wake 120 s → 300–600 s.** Each wake is a full boot (~1–3 s
>    awake); at 120 s that is ~1–2.5% awake duty, which likely dominates the
>    sleep budget over the 5 µA chip floor. Needs bench: mAh per wake. Also
>    needs an ESPHome-doc check on whether Wi-Fi can be kept from associating
>    on a timer wake.
> 3. **Wi-Fi `power_save_mode: none` → light/modem.** Largest awake-current
>    term, but deliberate (reliability > power). Needs bench + latency check.
> 4. **Publish traffic (~140/min upper bound, ~32 sensors on 60 s clocks).**
>    Whether unchanged values are actually transmitted depends on ESPHome
>    publish dedup, which was **not verified** in this pass — do not claim the
>    saving until it is. Event-driven `update_interval: never` + publish-on-
>    change is the documented pattern, but retrofitting it to ~32 sensors
>    risks a sensor that never publishes; it is a per-sensor change, not a
>    blanket one.
> 5. **NVS / restore globals.** Four integration sensors with `restore: true`
>    and several `restore_value: yes` globals are written on hot paths
>    (e.g. `last_outage_min_v` ~every 5 s during a discharge; the survival
>    wake trio on every 120 s wake). The ESPHome docs warn `restore` "can wear
>    out your flash", but whether a global assignment writes NVS immediately
>    or is coalesced/flushed at shutdown was **not verified** against the
>    2026.10.2 source — the flash-write count cannot be quantified yet.
> 6. **Supervisor ADC:** `psu_adc.sample()` every 1 s on top of the 5 s
>    published sensor (8 samples each, if `samples:` applies to `sample()`).
>    Whether `ADCSensor::sample()` honours `samples:` in 2026.10.2 was **not
>    verified** — if it is a single conversion, this item evaporates.
> 7. **Shed-path 2 transfers/poll (0x06 CVRF + 0x02).** Required as coded;
>    no burst read covers both (registers are not adjacent). Datasheet
>    confirmation of "no burst" was not completed.
> 8. **Runtime Remaining in hours *and* minutes** (two sensors, one number),
>    **10 Hz mean/SD diagnostic** (24 publishes/min, no behavioural consumer
>    — but the noise question it answers is still open), **Apparent Ri 1 s
>    interval re-reading 5 s values** (its 45 s gate timing was validated by
>    replay at 1 s ticks). All small; the Ri cadence change needs the replay
>    re-run, the diagnostic needs the owner to say the noise question is answered.
> 9. **HDR-60-12 decay / mains debounce:** hold-up is 12 ms @ 115 VAC at full
>    load — that is *not* the decay time to the 7.0 V threshold, and no decay
>    curve exists in the spec. The 10 s debounce and 60 s plausibility delay
>    cannot be derived from the datasheet; they must be bench-measured
>    (open item 6). Unchanged.
> 10. **0xFFFF guard on current reads:** 0xFFFF as a *bus voltage* is
>     impossible (bit 15 is always 0, TI §8.6.3), but as a *current* it is
>     −1.25 mA, a legal near-zero value. The guard is a firmware heuristic,
>     not a datasheet rule — flagged, not changed.
>
> ## Sources
>
> - ESPHome 2026.10.2 docs: esphome.io/components/sensor/ina260,
>   /sensor/adc, /i2c, /deep_sleep, /sensor/dallas_temp,
>   /sensor/integration, /components/sensor (filters), /logger, /wifi,
>   /ota, /esp32; api-docs.esphome.io (ina260.cpp source).
> - TI INA260 SBOS656C Rev C (Dec 2016).
> - Maxim/Analog DS18B20 Rev 6 (2019).
> - Espressif ESP32-C3 Datasheet v2.5; ESP-IDF v5.4 GPIO docs.
> - Pololu D24V7F3 #5592 and S13V25F12 #4984 product pages.
> - Mean Well HDR-60-SPEC.
> - CodeRabbit review of PR #5 (2026-11-15) was noted but is out of scope
>   here: this pass optimizes V4.1 as written; the CodeRabbit findings
>   (outage-marker sentinel, decay comparison, modem-on time, shed-alarm
>   freshness) are triage items for the PR, not optimizations, and were not
>   folded in.
>
> ## Status
>
> - V4.2 file written, YAML-validated, and **ESPHome 2026.10.2 `config`
>   validation passed (exit 0, "Configuration is valid!")**. Compile was not
>   run. **V4.2 is not bench-tested and not flashed** — same status as V4.1.
>   Nothing in this pass touches the repo or the board.
