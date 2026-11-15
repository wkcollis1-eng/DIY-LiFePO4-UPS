# UPS Monitor Rev 4 firmware: review of V4.0, and V4.1

Date: 2026-11-15. Reviewed: `ups-monitor-rev4.yaml` V4.0 (commit b1980f4) against
`ups-monitor-rev4-design.md` revision 9, section 8 (canonical). Toolchain: ESPHome
2026.10.2, which builds with ESP-IDF 5.5.6 and riscv32-esp-elf 14.2.0, on an ESP32-C3.

Evidence tags follow the design doc:
- [M] measured;
- [D] derived;
- [I] inferred;
- [S] a source read for this review: a datasheet, or the ESPHome 2026.10.2 / ESP-IDF 5.5.6
  source. File and line are given where it matters.

Line numbers are V4.1's unless marked V4.0.

**Nothing in this report has run on hardware.**

---

## 1. Executive summary

**Verdict: V4.1 is ready for the bench, not for service.**
- It compiles clean on 2026.10.2: 0 errors, and 0 `-Wall -Wextra` warnings.
- Its two safety lambdas, the supervisor and the -150 decision, pass host-side behavioural
  tests run on their generated C++.
- It has never run on a C3, and every REV 4 threshold is still a placeholder.

**No P0 found.** Four candidate P0s were checked against source and cleared:
1. `gpio_hold_en(GPIO_NUM_5)` does latch the pad.
2. `gpio_deep_sleep_hold_en()` does not freeze I2C after a wake.
3. Setup does not wait for WiFi, so -150 runs with no AP.
4. GPIO5 resets high-Z with no pull.

**Three P1s are fixed:**
- **F01:** a reboot early in an outage counted a second outage and zeroed the Ah/Wh.
- **F02:** shed reads were not proven fresh, as section 8 requires.
- **F03:** a non-timer reboot during survival re-shed on one sample, against section 5.

**Top three risks.** None can be closed in firmware:
1. **Open item 7.** Does the GPIO5 latch survive the ROM boot? Can the pad be read back
   while held? The source shows the app keeps the hold; the ROM is not in source.
2. **Open items 6 and 14.** The HDR decay and the new pack's shed and rest voltages are
   unmeasured. A shed pack resting at or above 13.0 V cycles the modem on battery
   (deviation 1). V4.1 adds the instrument for it, and an optional gate that is off by
   default.
3. **Open items 15 to 17.** The shed, latch, release and Q1/Q2 path have never run. A stuck
   HIGH hides behind Q2 until the next outage.

---

## 2. Findings

Severity: P0 critical, P1 major, P2 minor, P3 nit. F01 to F11 are applied in V4.1; each
change is tagged `REV 4.1 [Fnn]` in the YAML. F12 to F19 are documented only.

| ID | Sev | Location | Problem, with evidence | Why it matters | Fix (status) | Bench test |
|---|---|---|---|---|---|---|
| F01 | P1 | on_boot -100, L800–830 | **The -100 re-anchor tests the bus, but on_battery now comes from PSU sense.**<br>• V4.0 re-anchored on `v < ${on_battery_threshold_v} && i < -0.05f`, the V1.x definition of "on battery".<br>• REV 4's `on_battery` is `g_mains_state == 0` (L3143).<br>• Trace of a reboot on battery with the bus ≥ 13.15 V: -100 skips, so `outage_start_uptime` stays 0. on_press at about 19–20 s then passes every guard, does `total_outage_count++`, and resets `ah_/wh_delivered_outage`.<br>• A bus above 13.15 V on battery is plausible at the 13.6 V float [I: design doc 8]. | It re-opens the V1.12 item-7 bug: a wrong outage count and lost Ah/Wh. That is the record item 14 uses for capacity and runtime. | **Applied.** `wait_until` the supervisor's first mains decision (60 s timeout), then test `g_mains_state == 0 && i < -0.05f`. | 9 |
| F02 | P1 | supervisor step 2, L1931–1962 | **Shed reads are not proven fresh.**<br>• Section 8 requires a valid reading to be "fresh from this poll". V4.0's own comment admits "'valid' does not prove the conversion is new (CVRF is not read)".<br>• The `write_read` return code is ignored.<br>• In power-down "the data from the last conversion remain available" [S: SBOS656C §8.3.3]. | A frozen or powered-down INA260 can count toward N. Design doc 8.1 says the rule is met; it was not. | **Applied.**<br>• Read 06h first and require CVRF (bit 3) [S: SBOS656C §8.6.5].<br>• Require `i2c::ERROR_OK` on both transfers.<br>• New substitution `shed_require_cvrf: "true"`.<br>• New counter "Shed Path Stale Reads". | 5 |
| F03 | P1 | -150, L879–900 | **A non-timer reboot during survival re-sheds on one sample.**<br>• On a non-timer boot with NVS `survival_mode_active` set, 900 drives LOW. -150 then re-sleeps with the pad latched HIGH on one PSU sample and at most three bus reads.<br>• Design doc §5: "ESP reboots during a latched shed … the modem comes back on … sheds again after about 20 s of valid readings". Hard invariant 3 says the same. | It re-sheds without the supervisor's debounce, against the canonical failure-mode table. | **Applied.** New exit reason 4, "Reset during survival". The supervisor re-earns the shed. Cost is 16–28 mAh per such reset [D, §3.2]. | 10 |
| F04 | P2 | binary_sensor L3582 | **No clean alarm for a broken Q1 path.** Only "Modem Shed" ON signals it, and its ON edge can also go out just before a working shed drops the AP [I]. | A broken Q1 path runs the modem to the BMS cutoff with no unambiguous alert. | **Applied.** "Modem Shed Ineffective": shed latched, AND fresh block I below `survival_entry_current_lo`, held for `plausibility_alert_delay`. Alert only. | 8 |
| F05 | P2 | supervisor L1896–1919; onset detector L2253 | **No firmware instrument for open item 6, the HDR decay.** | The decay sets what `mains_debounce_polls` and `plausibility_alert_delay` must exceed, and how wide deviation 4's band is. | **Applied.** "PSU Decay To Threshold" (s): from the onset detector's load step to the first PSU poll below `mains_present_v`. Resolution about 1.2 s. | 2 |
| F06 | P2 | -150, L1027–1060 | **Exit reason 5 rests on an unmeasured assumption.**<br>• It assumes `survival_exit_v` sits above the shed pack's rest voltage, which is unmeasured (deviation 1).<br>• The exit test reads no current, and its log is never seen (no network). | A rest at or above 13.0 V turns the modem on, on battery; it re-sheds, and the cycle repeats. | **Applied.**<br>• Read 01h at every exit test and keep it in NVS ("Survival Exit Test Current").<br>• Optional gate `survival_exit5_require_charge`, default `false` = V4.0 behaviour. | 7 |
| F07 | P3 | ina260 platform, L2407–2429 | **The INA260 power channel is unused.** It is internal, with `throttle_average: 5s`, and nothing reads `ina260_power` (grep: defined only). | One I2C read and one scheduler interval per second, consumed by nothing. | **Applied.** Commented out, keeping its history. The 2026.10.2 platform skips 03h when no power sensor is set [S: ina260.cpp:111–119]. | regression: Battery Power still publishes |
| F08 | P2 | onset detector L2215–2230; capture scripts L3909, L3954 | **Failed I2C reads can feed garbage into the capture paths.**<br>• `uint8_t b[2];` is uninitialised and reused for the 02h and 01h reads, and the `ErrorCode` is ignored.<br>• If the 01h read fails without writing `b[]`, then `iraw = vraw`. A 13.5 V bus (raw 10800) then reads as 10800 × 1.25 mA = +13.5 A [D]. | It corrupts the float hold and the 10 Hz statistics. Two in a row trip a recharge capture, and onset R has no plausibility band. | **Applied.** Buffers pre-zeroed, `ERROR_OK` checked, the failed sample skipped. The success path is unchanged. | regression: first outage's ONSET/RECHARGE lines |
| F09 | P3 | many | **Comments disagree with the code or the source.**<br>• "NaN" ADC handling: `sample()` never returns NaN [S: adc_sensor_esp32.cpp:160–205; `aggr_{0}`].<br>• "gpio_config logs one INFO line": it is `ESP_LOGD`, and `CONFIG_LOG_DEFAULT_LEVEL=1` [S].<br>• On battery / fully charged exclusivity.<br>• The reason-code list.<br>• Plausibility delay sizing.<br>• TB2/R8/R1 (item 28).<br>• `%u` with a `uint32_t` (`-Wformat`). | Comment-vs-code drift is the class of error that produced V1.13's AVG=1/AVG=4 mistake. | **Applied.** REV 4.1 notes beside the originals, no history rewritten, plus one cast. | — |
| F10 | P3 | LVD Imminent, L3329 | **LVD Imminent still uses `lvd_voltage`**, the BP-65's Setting 7. There is no BP-65. | It goes stale once `shed_voltage` is re-derived. | **Applied.** Now `${shed_voltage} + 0.10f`: 11.90 V either way today. | — |
| F11 | P3 | substitutions L467 | **Inherited pack values are not marked as placeholders.** 4.18 Ah capacity, the phases, the 13.30 V float and others came from the old pack. The new pack's nameplate is 10 Ah [S: design doc 1.6]. | Runtime Remaining probably reads low [I]; the phase and alarm thresholds are unvalidated. | **Applied.** A TODO block naming the measurement for each. Values unchanged (invariant 8). | 11 |
| F12 | P2 | onset detector | **No back-off on I2C failure.**<br>• Each transfer can block up to 100 ms [S: i2c_bus_esp_idf.cpp:187, `i2c_master_execute_defined_operations(..., 100)`].<br>• On a stuck bus the detector alone asks for 2 × 100 ms per 100 ms tick. | The loop saturates and the API/WiFi starve. GPIO5 handling still runs, late. It fails toward modem on (no valid read). | **Not applied** (validated path; not safety-critical). Proposal: skip the detector for 5 s after a failed poll. | optional: hold SDA low |
| F13 | P3 | -150 L1039 | **The confirm read v2 has no plausibility test.** A raw2 of 0xFFFF reads 81.9 V, which is ≥ 13.0 V. It needs a plausible v1 ≥ 13.0 AND a garbage v2. | It fails toward exit, modem on. | **Not applied** (inherited V1.8 exit; invariant 7). Proposal: the same 5–16 V test on raw2. | — |
| F14 | P2 | survival design | **Nothing reacts to a lost hold.** A lost hold powers the modem through every sleep while the ESP keeps sleeping. "Shed Hold Lost Count" counts it. | During "survival", the pack drains at modem load: 1.13–1.82 A at 11.8 V [S: doc 1.7]. | **Not applied:** it depends on item 7. Proposal: after K consecutive lost-hold wakes, stop sleeping and hold HIGH while awake, at the board's ~35 mA [S: doc 1.7]. | 4 decides |
| F15 | P3 | api L1242 | **Stale rationale.** `reboot_timeout: 30min` is justified by the BP-65 LVD and HA Green; neither is on this system. | If HA is unreachable for 30 min, the board reboots. Each reboot re-earns any shed, about 20 s of modem load. | **Not applied** (owner's call). | — |
| F16 | P3 | -150 L1112 | **A misleading re-sleep log.** "V=… < 13.0V, mains absent" is also printed when v1 ≥ 13.0 and the confirm, or the F06 gate, refused the exit. | Misleading forensics. The WARN printed just before it is right. | **Not applied** (cosmetic). | — |
| F17 | P3 | ESPHome `adc` | **A failed ADC floods the log.** Each failed conversion logs a WARN inside `ADCSensor`: 8 per sample, at 1 Hz from the supervisor plus every 5 s from the sensor [S]. | A log flood on an ADC fault. | **Not fixable in YAML** without dropping samples. | — |
| F18 | P3 | On Battery | **A wire-off state hides the next outage from the counters.** With PSU_SENSE off on mains, On Battery is already ON. A real outage then produces no on_press edge, so it is not counted and the Ah/Wh are not reset. Shed and survival are unaffected. | Accounting only; "PSU Sense Lost" alerts on the state. | **Not applied.** | 6 observes it |
| F19 | P3 | design doc 8.1, 5, 7 | **The design doc no longer matches V4.1.** Freshness is now implemented, and reason 4, the new entities and the two new substitutions are missing. | Section 8 is canonical. | **Not applied.** The doc is the owner's; the edits are listed in §6. | — |

---

## 3. Deep dives

### 3.1 GPIO5 hold through deep sleep (open item 7)

**What the ESP-IDF 5.5.6 source shows for the ESP32-C3:**
1. **`gpio_hold_en(GPIO_NUM_5)` is the call that holds the pad.**
   - The wrapper (gpio.c:744–762) finds `rtc_gpio_is_valid_gpio(5)` false, because the C3
     has no RTCIO unit (`SOC_RTCIO_PIN_COUNT 0`; rtc_io.c:29–35).
   - `GPIO_HOLD_MASK[5]` is `BIT(5)` (soc/esp32c3/gpio_periph.c:42).
   - So the call reaches `gpio_ll_hold_en`, which for GPIO0–5 does
     `REG_SET_BIT(RTC_CNTL_PAD_HOLD_REG, BIT(5))` (hal/esp32c3/gpio_ll.h:445–451). That is
     an RTC-domain latch. **That bit holds GPIO5.**
2. **`gpio_deep_sleep_hold_en()` is for the digital pads, not GPIO5.**
   - It sets `RTC_CNTL_DG_PAD_AUTOHOLD_EN` (gpio_ll.h:398–402). That concerns the digital
     pads, GPIO6–21 (`SOC_GPIO_VALID_DIGITAL_IO_PAD_MASK 0x3FFFC0`).
   - Its effect here: at deep-sleep entry, `esp_sleep_isolate_digital_gpio()`
     (sleep_modes.c:896, sleep_gpio.c:134–184) isolates every digital pad that is not
     individually held. I2C, 1-Wire and the spare pins go input-off, output-off, no pulls.
   - After wake "the digital GPIO state can be changed freely" (gpio.h:443–445), so I2C works
     at -150.
   - V4.1 keeps the call (invariant 4). It is belt-and-braces for GPIO5 and lowers the
     sleep floor.
3. **App startup does not release GPIO5's hold.**
   - On `RESET_REASON_CORE_DEEP_SLEEP`, cpu_start.c:826–829 calls
     `esp_deep_sleep_wakeup_io_reset()`.
   - That releases holds only on GPIO0–5 pads enabled as deep-sleep **wake** pins
     (sleep_gpio.c:207–221).
   - This firmware has no `wakeup_pin`, so nothing in app startup releases GPIO5.
4. **Light-sleep GPIO switching does not interfere.** `gpio_sleep_mode_config_apply()` is on
   the light-sleep branch only (sleep_modes.c:753–755). ESPHome's `deep_sleep_()` touches
   only its wake pin, and there is none (deep_sleep_esp32.cpp:109–180).
5. **The reset state is safe.** GPIO5/MTDI resets to state "1": input enabled, high-Z, no
   pull [S: ESP32-C3 datasheet v1.2, Table 6]. R3 therefore holds Q1 off until 900 runs.
   Only MTCK/GPIO6 (SDA) gets the pad-JTAG pull-up.
6. **`modem_off_set` order is right:** level, then `gpio_config(INPUT_OUTPUT, no pulls)`,
   then level again, then the hold calls. That is the order section 8's `gpio_hold_dis` note
   asks for. Avoiding `gpio_reset_pin` is justified: it enables the pull-up (gpio.c:467–468).

**Still open (item 7):**
- **The ROM.** The ROM bootloader is binary. Whether it writes `RTC_CNTL_PAD_HOLD_REG` on a
  deep-sleep reset cannot be read from source. It should not [I].
- **Readback while held.** The hold latches the pad's input enable as configured
  (INPUT_OUTPUT). ESP-IDF says that in input mode "the input read value can still reflect the
  changes" (gpio.h:388–391). For a pad held across a power-down of the digital domain, that
  is unproven.
- **The -150 readback cannot tell "hold lost" from "held pad unreadable".** Bench test 4
  separates the two with a scope.

**If the hold is lost (F14):**
- The modem runs through each 120 s sleep, and the pad is re-driven HIGH for each awake
  window.
- The counter rises once per wake, but the pack drains at modem load.
- Don't fix this blind: test 4 decides whether the hold works.

### 3.2 The -150 survival decision

**Order after V4.1.** Every non-re-sleep path ends in the release lambda: GPIO5 LOW, holds
released.

| Step | Condition | Result |
|---|---|---|
| 0 | `survival_mode_active` false | Body skipped; release, modem on |
| 1 | **[F03]** wake cause ≠ TIMER | Exit reason 4, release. -160 then decides the watchdog |
| 2 | Timer wake | Read GPIO5 as input. LOW: Shed Hold Lost Count +1 |
| 3 | PSU sample | `psu1`. A failed ADC reads about 0 V = absent; NaN cannot occur [F09] |
| 4 | Bus 02h, plus up to 2 re-reads 20 ms apart | Implausible (raw 0/FFFF, ≤ 5 V, ≥ 16 V): exit reason 2 |
| 5 | v1 < 13.0 V | Record first/min/last wake V |
| 6 | Cycles ≥ 10,800 | Exit reason 3 |
| 7 | `mains1 \|\| v1 ≥ 13.0` | 50 ms, then read v2, **i2 [F06]** and psu2:<br>• `rec_psu`: reason 1;<br>• `rec_v`, plus the optional charge gate: reason 5;<br>• otherwise WARN and re-sleep |
| 8 | Re-sleep | cycle++, INA260 power-down (0x6120), 100 ms, `modem_off_set(true, true)`, `deep_sleep.enter` (manual = true) |

**Invariants:**
- **2 holds:** 900 skips timer wakes, and -150 reads the PSU and then the bus before any pad
  write.
- **3 holds now (F03).**
- **4 and 5 hold:** every exit runs the release lambda.
- **6 holds:** GPIO3 is untouched.

**F03 cost:**
- After a non-timer reset the modem is on until:
  - the mains debounce (poll 10);
  - plus 10 valid reads (the first is at poll 10, so the shed falls at poll 19);
  - plus survival's 30 s `delayed_on`;
  - plus up to one 5 s block.
- That is ≈ 19 + 30 + (0 to 5) ≈ 50 to 55 s [D].
- At 1.13 to 1.82 A [S: design doc 1.7, at 11.8 V]:
  - 1.13 A × 50 s ÷ 3600 = 0.016 Ah;
  - 1.82 A × 55 s ÷ 3600 = 0.028 Ah.
- So 16 to 28 mAh per reset [D]. Resets during survival need a crash, a brown-out or a person.

**Max-cycles backstop:**
- 10,800 × 120 s = 1,296,000 s = 15.0 days [D].
- After a reason-3 exit the supervisor re-earns the shed, and survival re-arms with the count
  reset.
- So the backstop is about one minute of modem load every 15 days, not a permanent exit
  [D: code].

**Awake time per re-sleep wake.** The fixed delays are 20 + (0 to 40) + 100 ms. Add 50 ms
when the exit test runs, plus setup and teardown [D]. F06 adds one I2C read, about 0.1 ms,
only inside the exit test.

**Deviation 1 and the F06 gate:**
- A pack that charges (mains back, PSU_SENSE off) reads amps positive at the exit test.
- A resting pack reads the board's own draw, tens of mA negative.
- That separates the two cases without the unmeasured rest voltage.
- The gate is off until test 7 has shown the exit-test current of a real wire-off recovery.
- "Survival Exit Test Current" records the answer in the field either way.

**Host test of the generated lambda (9/9 pass):**
- reason 4 with no I2C;
- re-sleep on a depleted pack;
- reason 1 with 3.5 A stored;
- reason 5 on a charging pack, gate on;
- a resting pack at 13.05 V: reason 5 with the gate off, re-sleep with it on;
- reason 2 on a 0 V read;
- the hold-lost counter.

### 3.3 The supervisor (1 s)

**Timing** [D: code; scheduler.cpp:107–111 gives the interval's random first offset, 0 to
500 ms]:

| Event | Poll | Time after setup |
|---|---|---|
| Mains state set | 10 | 9.0–9.5 s |
| Shed reads start | 10 (same poll) | 9.0–9.5 s |
| 10th valid read: the shed | 19 | 18.0–18.5 s, the doc's "about 20 s" |
| `on_battery` ON (state + 10 s) | — | 19.0–19.5 s |
| Survival arm | — | about 50–55 s |
| Old -100 check | — | 6 s |
| V4.1 -100 check | — | 9.0–9.5 s, about 10 s before on_press |

**Within a poll:** mains, then shed, then pad.
- The pad level is written every poll.
- While the latch is clear, `gpio_hold_dis` runs every poll, as section 8 requires.
- The pad is then read back. Two mismatches raise "MODEM_OFF Readback Fault" and re-run the
  setup once.

**Races checked:**
- **Survival arm.** The arm sets the flag, then waits 100 ms, then writes the pad. The
  supervisor returns at once on the flag.
- **Interleaving.** ESPHome's loop is single-threaded, and no lambda yields, so nothing can
  interleave inside one.
- **-100 against on_press:** F01, above.
- **The onset detector against the supervisor on I2C:** sequential.
- **The 5 s trackers and the 60 s slope:** they read `.state` only.

**I2C transfers per second** [D]:

| State | V4.0 | V4.1 | Why |
|---|---|---|---|
| On mains | 23 (onset 20 + platform 3) | 22 | F07 −1 |
| On battery, before the shed | 24 | 24 | F02 +1, F07 −1 |
| Shed latched | 23 | 22 | F07 −1 |

**CVRF (F02):**
- It "is set after all conversions, averaging, and multiplications are complete" and clears on
  a 06h read [S: SBOS656C §8.3.3, §8.6.5].
- One averaging cycle takes 4 × (1.1 + 0.14) ms = 4.96 ms. This comes from decoding 0x0307
  [S: SBOS656C Table 5]: AVG = 001 (4), VBUSCT = 100 (1.1 ms), ISHCT = 000 (140 µs),
  MODE = 111 (continuous).
- Nothing else reads 06h: not the platform (ina260.cpp:86–120), not -150, not -160, not the
  onset detector.
- **Assumption [I]:** CVRF sets on every averaging cycle in continuous mode. The text gives no
  mode restriction.
- **Falsifier:** "Shed Path Stale Reads" counts during test 5. If it does, set
  `shed_require_cvrf: "false"` and report it.

**Host test of the generated lambda (21/21 pass):**
- the debounce edges at polls 9 and 10;
- the decay publish (1.7 s);
- no shed at 9 reads, a shed at 10;
- the latch held while the bus recovers, with no INA reads while latched;
- release only on the 10th mains poll;
- a stale CVRF read resets N and counts;
- a NACK on 02h or 06h resets N, and a 06h NACK is not counted as stale;
- a 0 V read resets N;
- `survival_mode_active` touches nothing;
- a mains glitch publishes nothing.

### 3.4 INA260 pairing and registers

**Pairing holds by construction on 2026.10.2.** `update()` (ina260.cpp:86–120) reads 02h
and publishes V, reads 01h and publishes I, then reads 03h. It returns at the first failed
read. So an I publish implies a V publish in the same update, and the paired-block
accumulator's premise holds. F07 removes only the trailing 03h read. Re-read this function
at every ESPHome upgrade, as the V1.20 comment says.

**Setup** (ina260.cpp:36–60):
1. Write 0x8000 (reset), then wait 2 ms.
2. Check the IDs, 0x5449 / 0x2270.
3. Write 0x0307.

Any failure calls `mark_failed`. The states then stay NaN, and "INA260 Healthy" goes OFF.
Configuration ownership is unchanged: the platform writes 00h, and this firmware writes it
only for the inherited power-down.

**0x6120 decodes as power-down** [D: SBOS656C Table 5]: AVG 000, VBUSCT 100, ISHCT 100,
MODE 000. Bits 14 to 12 read 110, as in the POR value 0x6127.

**Register formats and plausibility** [S: SBOS656C §8.6.2–3]:
- 01h is signed, 1.25 mA LSB; 02h is 1.25 mV LSB; both MSB first.
- Bit 15 of 02h is always 0, so 0xFFFF is never a real reading.
- The 5 to 16 V window rejects anything at or above 0x8000 (40.96 V) anyway.

**Unchanged:** the stale watchdog (15 s; unsigned subtraction, safe across the millis
rollover) and the unpaired-reads count.

### 3.5 PSU sense

**Divider:**
- The pin sees 18 ÷ (100 + 18) = 0.15254 of PSU_SENSE. At 13.6 V that is 2.0746 V
  [D: R6/R7, design doc 4.5].
- The nominal ratio is 118 ÷ 18 = 6.5556.
- At 12 dB the calibrated range is 0 to 2500 mV [S: doc 4.5, citing the C3 datasheet]. That
  is 16.39 V full scale [D: 2.5 × 6.5556].

**Threshold:**
- 7.0 V sits between the 0.10 V backfeed [M per doc] and 13.6 V. The midpoint is 6.85 V [D].
- Q2's override threshold is 0.55 to 0.6 V × 122/22 = 3.05 to 3.33 V [D: doc 4.4].
- Deviation 4 is the band from there up to 7.0 V.

**ADC** [S: adc_sensor_esp32.cpp:160–205; adc_sensor_common.cpp:20–58]:
- Each `sample()` averages 8 one-shot reads.
- Failed reads are skipped. If all fail, the result is raw 0, about 0 V. NaN never occurs.
- If calibration fails, the driver falls back to raw × 3.3/4095, which is the wrong scale at
  12 dB. A DMM calibration absorbs that only if the fallback is already active when you
  calibrate [I].

**Debounce:** 10 polls, the same in both directions. Release needs 10 consecutive "present"
polls.

**Plausibility timing (F09 note):**
- "PSU Running Bus Not Fed" sees the outage's discharge at every outage start while mains is
  still debounced present.
- So it needs `plausibility_alert_delay` > t_decay(7.0 V) + `mains_debounce_polls` s [D].
- "Modem Shed Ineffective" uses the same delay.

### 3.6 Open items 6, 7, 14 and 15 after V4.1

- **Item 6, the HDR decay:** unmeasured. F05 adds a field instrument; test 2 measures the
  curve.
- **Item 7, GPIO5 through deep sleep:**
  - The source narrows it: the app does not drop the hold, and I2C works after wake.
  - Still open: the ROM, and readback while held. Test 4.
- **Item 14, the first discharge:** unmeasured.
  - F11 names the measurement for every inherited value.
  - F06 records the datum that decides deviation 1.
  - Test 11.
- **Item 15, the shed logic:**
  - It now meets section 8's valid-reading rule, including freshness (F02).
  - 21 host checks pass. Untested on hardware: tests 5 and 8.

---

## 4. The V4.1 YAML

- **Full file:** `UPS-Monitor-Rev4/ups-monitor-rev4.yaml`, committed with this report.
- **Unified diff against V4.0:** Appendix A, 684 lines.
- **Size:** 3675 → 3997 lines. 39 lines were changed or removed, every one intended
  (blast-radius check, §7).
- **History kept:**
  - No changelog entry and no history comment was rewritten.
  - Each correction is a `REV 4.1 [Fnn]` note beside the original.
  - The removed power channel is commented out, with its V1.16 comment intact.

---

## 5. Bench test plan

**Before any test:**
- **Logs.** `logger: baud_rate: 0`, so logs come over the network only: `esphome logs
  ups-monitor-rev4.yaml` or the HA device log.
- **Bench AP.** During a shed the XB7's AP is gone. Run the bench with a dummy load on the
  modem terminal, about 12 Ω 25 W [D: 12 V ÷ 1 A; 12 W]. Give the bench a separate AP with
  the same SSID and password, so the API outlives the shed.
- **First flash.**
  - V4.1 has never been on the device, so the first flash is over USB.
  - Do it with the XIAO out of its socket, or with BUS unpowered. The board feeds the XIAO's
    3V3 from U3, and USB would set the XIAO's own regulator against it [I].
  - OTA after that.
- **Equipment:**
  - a bench supply on BUS, 10 to 14 V and 3 A;
  - the HDR-60-12 or a second supply on PSU_SENSE;
  - a 2-channel scope and a DMM.

Each test below gives its setup, steps, expected result, pass/fail and the line or entity
that proves it.

**1. First power and divider calibration** (open item 28; `psu_divider_ratio`)
- **Setup:** PSU at 13.6 V on PSU_SENSE; the DMM on TB2 pad 4 (PSU_SENSE) to pad 3 (GND).
- **Steps:**
  1. Read the DMM and "PSU Sense Voltage" after 1 min.
  2. Set `psu_divider_ratio = 6.556 × V_DMM ÷ V_reported` and re-flash.
  3. Repeat at a second voltage, for example 12.0 V, if the supply allows.
- **Pass:** after the change, the reading agrees with the DMM within 0.05 V at 13.6 V [I:
  design doc 4.5 expects tens of mV calibrated].
- **Also:** U4's output at its VOUT joint lies within 11.52 to 12.48 V (item 13).

**2. HDR-60-12 output decay** (open item 6; F05)
- **Setup:** the real HDR-60-12 and the pack, both connected; the scope on PSU_SENSE (ch1)
  and on the bus at the INA260 VIN+ (ch2).
- **Steps:**
  1. Switch AC off at the PSU's input.
  2. Capture t from the AC switch to PSU_SENSE = 7.0 V (`mains_present_v`), to 3.3 V and to
     3.0 V (Q2's band).
  3. Repeat 3 times.
- **Expected:** the log shows `PSU sense … V < 7.0 V, … s after the INA260 load step (HDR
  decay, open item 6)`, and "PSU Decay To Threshold" agrees with the scope's 7.0 V time
  within about 1.2 s.
- **Then set**, as placeholders replaced by measurement:
  - `mains_debounce_polls` above the decay, per section 8;
  - `plausibility_alert_delay` above t_decay(7.0 V) + `mains_debounce_polls` s, with margin
    (owner's choice).
- **Pass:** "PSU Running Bus Not Fed" stays OFF through every AC cut.

**3. GPIO5 at boot** (item 28: the 900 lambda runs before anything touches GPIO5)
- **Setup:** BUS at 12.5 V from the bench supply, PSU_SENSE at 0 V; scope on GPIO5 and on
  MODEM_EN (U4 pad 1).
- **Steps:** power up, then press Restart in HA, then do an OTA. Scope each with a single
  trigger.
- **Pass:** GPIO5 is never HIGH and MODEM_EN never falls below about 2 V, on all three.
- **Proof:** the scope traces; the log shows `Boot wake cause = … (cold/reset)`.

**4. GPIO5 hold through deep sleep and the ROM boot** (open item 7)
- **Setup:** as test 3, with a ≥ 0.5 A load on the modem terminal. Then lower BUS to 11.7 V
  to force a shed, which survival entry follows. The scope triggers on the ESP's wake, for
  example the 3V3 current or the INA260 SDA activity.
- **Steps:** let 5 wakes pass (10 min).
- **Expected:** GPIO5 HIGH and MODEM_EN ≤ 0.2 V continuously, through every sleep and every
  ROM boot; "Shed Hold Lost Count" unchanged.
- **How to read a failure:**
  - GPIO5 HIGH on the scope but the count rises: the held pad does not read back. Fix the
    readback, not the hold.
  - GPIO5 LOW on the scope: the hold is lost. Then F14 applies.
- **Proof:** the scope; "Shed Hold Lost Count" after exit; the wake logs, if a bench AP keeps
  the ESP connected during its windows.

**5. Shed, latch and release** (items 15 and 16; F02)
- **Setup:** BUS from the bench supply at 12.5 V; PSU_SENSE at 0 V. Add a 0.5 A resistor
  directly on BUS, which keeps I below −0.30 A, so survival entry cannot follow and the
  latch can be watched awake.
- **Steps:**
  1. Wait 10 s: "Mains Present" OFF.
  2. Dip BUS to 11.75 V for 5 s, then back to 12.5 V.
  3. Hold BUS at 11.75 V.
  4. Raise BUS to 12.5 V.
  5. Apply 13.6 V to PSU_SENSE.
- **Expected:**
  - After step 2: no shed (N resets).
  - After step 3: `MODEM SHED #1 | V=… <= 11.80 V on 10 valid reads` about 10 s later; GPIO5
    HIGH on the scope.
  - After step 4: the latch holds; GPIO5 stays HIGH.
  - After step 5: `MODEM RESTORED | mains present … (debounced)` after 10 polls; GPIO5 LOW.
- **Pass:**
  - "Shed Path Stale Reads" = 0 throughout;
  - "MODEM_OFF Readback Fault" OFF throughout;
  - "Modem Shed Count" +1.
- **Optional negative test, bench build only:** a template button that writes 0x6120 to 00h.
  Stale reads should count, and no shed should happen while stale.

**6. PSU_SENSE wire off** (items 18 and 25; F18)
- **Setup:** normal service, PSU on, pack at float.
- **Steps:** pull the PSU_SENSE lead at TB2 pad 4; wait 2 min; refit it.
- **Expected:**
  - "Mains Present" OFF after 10 s.
  - "On Battery" ON after about 20 s. This is known and misleading (F18).
  - "PSU Sense Lost" ON after 60 s.
  - No `MODEM SHED`, because the bus is at float.
  - No survival entry.
- **Pass:** the modem stays on throughout, and every entity recovers after the lead is
  refitted.

**7. Survival entry and exit, and the section 8 commissioning test** (item 17; F06)
- **Setup:** the real pack, PSU and modem. Force a shed by lowering the threshold
  temporarily, for example `shed_voltage: "12.9"` in a bench build. Do not discharge the new
  pack to 11.8 V before test 11.
- **Steps (section 8):**
  1. Force the shed on battery (AC off at the PSU).
  2. Let survival sleep start: `SURVIVAL SLEEP ENTRY (modem shed)` in the log.
  3. Restore AC and wait two wake periods (240 s).
  4. Cut AC again.
- **Pass:** after step 3, "Survival Exit Reason" = Recovery and "Survival Exit Test Current"
  is positive (charging). After step 4 the modem stays on. That proves the hold was released.
- **Wire-off variant:** repeat with PSU_SENSE pulled before step 3.
  - Expect "Recovery, PSU sense absent" (reason 5) once the bus reads ≥ 13.0 V twice.
  - Record "Survival Exit Test Current" (amps positive).
  - This is the evidence to set `survival_exit5_require_charge: "true"`.

**8. Q1 failure** (F04)
- **Setup:** as test 5, without the BUS resistor. Defeat Q1, for example by jumpering its
  base to its emitter, or by lifting R2.
- **Steps:** force the shed (BUS 11.75 V, PSU_SENSE 0 V).
- **Expected:**
  - `MODEM SHED #…`, and the modem stays on;
  - "Modem Shed" ON, and "Modem Shed Ineffective" ON after 60 s;
  - no survival entry;
  - "MODEM_OFF Readback Fault" OFF, since the pad reads HIGH as commanded.
- **Pass:** all four. Restore Q1 afterwards and repeat test 5.

**9. Mid-outage reboot** (F01)
- **Setup:** real pack, freshly floated; AC off at the PSU. The bus should still be above
  13.15 V. Check "Battery Voltage".
- **Steps:** about 2 min into the outage, press "Restart".
- **Expected:** `Booted during outage -- counters PRESERVED from NVS (… Ah)` about 10 s after
  boot, and `on_press suppressed — already in an outage` about 10 s later.
- **Pass:** "Total Outages" unchanged and "Ah Delivered (This Outage)" not reset. V4.0 would
  have failed both.

**10. Reset during survival** (F03)
- **Setup:** as test 7, in survival sleep.
- **Steps:** press the XIAO's reset button between two wakes.
- **Expected:**
  - `SURVIVAL EXIT (RESET DURING SURVIVAL, wake cause 0)`; "Survival Exit Reason" = Reset
    during survival.
  - The modem comes on at once.
  - `MODEM SHED` again about 19 s later, and `SURVIVAL SLEEP ENTRY` about 30 s after that.
- **Pass:** the modem is on from the reset until the new shed. Expect about 50 to 55 s
  (§3.2).

**11. First discharge of the pack** (item 14; F11)
- **Setup:** real pack, full float; AC off; the modem as the load; HA recording at 5 s.
- **Steps:** run to the shed at the placeholder 11.8 V, then let survival run 1 h before
  restoring AC.
- **Record:**
  - Ah and Wh at the `MODEM SHED` line, which sets `validated_capacity_ah`;
  - the V curve, for the phase boundaries and the slope thresholds;
  - the XB7's peaks near the shed, which set `shed_valid_reads_n`;
  - "Survival First / Min / Last Wake Voltage", which shows whether the rest voltage stays
    below 13.0 V (deviation 1);
  - the first recharge's peak against the 5.0 A label (item 19).
- **Pass:** every F11 value has a measurement to replace it.

---

## 6. What V4.1 does not change, and why

**Values, unchanged because they are unmeasured (invariant 8):**
- every REV 4 placeholder: the divider ratio, `mains_present_v`, `mains_debounce_polls`,
  `shed_voltage`, `shed_valid_reads_n`, the plausible range, `psu_not_feeding_i_a`,
  `plausibility_alert_delay` and `survival_exit_v`;
- every value inherited from the previous pack (F11): capacity, phases, slope thresholds,
  float and warning/critical. F11 names the measurement for each.

**Logic, unchanged because it is validated (invariant 7):**
- the survival entry window and its 30 s `delayed_on`;
- the 120 s interval, the 10,800-cycle backstop and the 60 s `run_duration` watchdog;
- the on_battery filters (10 s / 60 s), the on_press and on_release guards, and the Ah/Wh
  integration. F01 changes only the -100 condition, a REV 4 inconsistency;
- the paired-block accumulator, the Apparent Ri gate, and the onset/recharge capture
  arithmetic. F08 touches only failed-read handling.

**Other:**
- **GPIO3** stays a passive Alert monitor (invariant 6).
- **F12 to F18:** the reasons are in the table. The two that touch inherited exits (F13) and
  the survival design (F14) need the owner and the bench.
- **The `api` and `wifi` reboot timeouts, and the OTA password warning** ESPHome prints:
  these are the owner's.
- **The design doc** (F19) is the owner's. Section 8.1 should record:
  - freshness by CVRF and the two new substitutions;
  - exit reason 4 and the new section 5 behaviour;
  - the four new entities;
  - the reason-5 gate as the candidate fix for deviation 1;
  - item 28's comment corrections, now done;
  - section 7's firmware row (V4.1, compile result).

---

## 7. Verification

**Done in this session:**
- `esphome config` on 2026.10.2: valid.
- **Real compile, ESP-IDF 5.5.6 toolchain:**
  - exit 0, "Successfully compiled program", 0 errors;
  - `main.cpp.obj` rebuilt (its mtime advanced on each run);
  - RAM 116,034 → 116,354 B; flash 984,492 → 986,962 B.
- **`-Wall -Wextra -fsyntax-only` on `main.cpp`,** with the build's own flags and its
  precompiled header removed so each version compiles against its own headers:
  - V4.0: 1 warning, the inherited `%u` with a `uint32_t`.
  - V4.1: 0 warnings.
- **Host behavioural tests,** run on the lambdas extracted verbatim from the generated
  `main.cpp`:
  - supervisor: 21 of 21;
  - -150: 9 of 9.
  - The only edit was the reason-5 gate's `false` literal, made a variable so that both
    settings could be tested.
- **Blast radius:**
  - 39 lines changed or removed, every one intended;
  - LF endings only; `restore_value: yes` 32 → 33;
  - 10 GPIO5 code sites before and after (`modem_off_set`, the supervisor, -150);
  - no component `pin: GPIO5`.
- **Source facts read for this review:**
  - ESPHome: setup priorities (`component.h`), globals at HARDWARE (`globals_component.h`),
    the ina260 driver, `ADCSensor::sample`, the I2C API, the script `execute`,
    `begin_sleep`/`prevent`, the scheduler offset, NVS sync, and `can_proceed`.
  - ESP-IDF: the GPIO hold, autohold, isolation and wakeup-IO reset, plus `sdkconfig` (log
    level 1, brown-out on, task WDT 5 s, NVS partition 0x70000).
  - Datasheets: TI SBOS656C §8.3.3, §8.6.1–8.6.5; ESP32-C3 datasheet v1.2, Table 6.

**Not verified, needs hardware:**
- open items 6, 7, 13, 14, 15–17 and 28;
- CVRF behaviour in continuous mode [I];
- readback of a held pad;
- the ROM's treatment of the RTC pad hold;
- the sleep floor (43–83 µA [S: firmware header]);
- on-device timing;
- whether "Modem Shed"'s ON edge reaches HA at a working shed [I].

**Sandbox only:** the build used dummy `secrets.yaml` values in a scratch directory. This
firmware has no `build_path`, and the committed YAML has only the edits above.

---

## Appendix A: unified diff, V4.0 → V4.1

```diff
diff --git a/UPS-Monitor-Rev4/ups-monitor-rev4.yaml b/UPS-Monitor-Rev4/ups-monitor-rev4.yaml
index 63d484d..00453ee 100644
--- a/UPS-Monitor-Rev4/ups-monitor-rev4.yaml
+++ b/UPS-Monitor-Rev4/ups-monitor-rev4.yaml
@@ -1,5 +1,5 @@
 # ============================================================================
-# UPS Monitor REV 4 BOARD — firmware V4.0 (2026-11-09) — NOT YET BENCH-TESTED
+# UPS Monitor REV 4 BOARD — firmware V4.1 (2026-11-15) — NOT YET BENCH-TESTED
 # ============================================================================
 # Derived from UPS-Monitor/ups-monitor.yaml V1.20 (the deployed Rev 1 firmware,
 # which is unchanged). Requirements: UPS-Monitor-Rev4/ups-monitor-rev4-design.md
@@ -36,6 +36,43 @@
 #       running but bus not fed, PSU sense lost. Counters: Modem Shed Count,
 #       Shed Hold Lost Count (the field instrument for design-doc open item 7).
 #
+# What V4.1 changes against V4.0 (review of 2026-11-15; search "REV 4.1 [F" for
+# every site; report: UPS-Monitor-Rev4/ups-monitor-rev4-v4.1-review.md):
+#   [F01] Priority -100 re-anchors a mid-outage reboot on the debounced PSU-sense
+#         mains state, the signal on_battery uses. V4.0 still tested the bus
+#         against 13.15 V, so a reboot early in an outage, with the bus above
+#         13.15 V, counted a new outage and zeroed the restored Ah/Wh.
+#   [F02] A shed read is valid only if the INA260 reports a NEW conversion
+#         (Mask/Enable CVRF) and both I2C transfers return OK. Design doc section
+#         8 asks for "fresh from this poll"; V4.0 could not tell a frozen register.
+#         New: substitution shed_require_cvrf, counter "Shed Path Stale Reads".
+#   [F03] A NON-timer boot with the survival flag set leaves survival sleep (new
+#         exit reason 4) instead of re-shedding on one sample; the supervisor
+#         re-earns the shed, as design doc section 5 says a reboot during a shed
+#         does.
+#   [F04] "Modem Shed Ineffective": shed latched while the modem's load is still
+#         on the bus (Q1 path broken). Alert only.
+#   [F05] "PSU Decay To Threshold": seconds from the INA260 load step to the first
+#         PSU-sense poll below mains_present_v. Field instrument for open item 6.
+#   [F06] Pack current read at every survival exit test, logged and kept in NVS
+#         ("Survival Exit Test Current"). Optional gate, OFF by default
+#         (survival_exit5_require_charge), that makes exit reason 5 also need a
+#         charging pack: design doc 8.1 deviation 1 without the unmeasured rest V.
+#   [F07] The unused INA260 power-register channel is removed: one I2C read and
+#         one throttle_average scheduler item per second, consumed by nothing.
+#   [F08] Onset detector and both capture scripts: buffers pre-zeroed and I2C
+#         results checked. A failed current read after a good voltage read reused
+#         the voltage bytes as the current (13.5 V read back as +13.5 A).
+#   [F09] Comments corrected where V4.0 no longer matched the code or the
+#         ESPHome 2026.10.2 / ESP-IDF 5.5.6 source (ADC never returns NaN;
+#         gpio_config does not log at INFO; which call holds GPIO5; reason codes;
+#         on_battery / fully-charged exclusivity; plausibility delay sizing).
+#   [F10] LVD Imminent tests 100 mV above shed_voltage (was the BP-65's
+#         lvd_voltage). Same 11.90 V today; stays in step when the shed moves.
+#   [F11] Every value inherited from the previous pack is listed with a TODO and
+#         the measurement that replaces it. No substitution value from V4.0 was
+#         changed. F01, F02 and F03 change behaviour; the rest add or annotate.
+#
 # PLACEHOLDERS - not measured, set in the "REV 4" substitutions block: the divider
 # ratio, the mains threshold, the mains debounce (the HDR output decay is
 # unmeasured, open item 6), N and the plausible range (item 15), and every pack
@@ -91,6 +128,12 @@
 #                             NOT shared with deep_sleep. Recovery is timer-wake (§-150)
 #                             and the run_duration watchdog, neither of which uses GPIO3.
 #   GPIO20 (D7) — now SPARE (was the breadboard ALERT pin; left unconnected on PCB)
+#   REV 4.1 [F09]: on the Rev 4 board (2026-11-12 save) TB2 is a 4-pole screw
+#   terminal: pad 1 +3V3, pad 2 DQ, pad 3 GND, pad 4 PSU_SENSE (design doc 3, item 1;
+#   meter it before connecting). R8 4.7k has a footprint but is DNP: the sensor in
+#   service carries its own pull-up (item 27).
+#   REV 4.1 [F09]: on Rev 4 the ALERT pull-up is R1 10k (design doc 4.6), not R2.
+#   GPIO4 = PSU_ADC and GPIO5 = MODEM_OFF (design doc 4.7) are in the REV 4 notes.
 #
 # Power: TB1 (BATTERY +/-) → F1 (5x20 mm 1A slow-blow) → C4 47uF / C5 0.1uF →
 #        D24V7F3 VIN; VOUT (3.3 V) → 3V3 rail (XIAO 3V3, INA VCC) with C1 10uF +
@@ -421,6 +464,28 @@ substitutions:
   friendly_name: "UPS Monitor Rev 4"
   device_description: "12V LiFePO4 modem UPS, Rev 4 board — INA260 + DS18B20 + PSU sense + modem shed"

+  # --- REV 4.1 [F11] — values inherited from the PREVIOUS pack / Rev 1 system --
+  # TODO(open item 14): none of these was measured on the Cyclenbatt 10 Ah pack at
+  # the 13.6 V float. Each stays as it is until this pack's first coulomb-counted
+  # discharge to the shed, logged at 5 s, gives its replacement:
+  #   validated_capacity_ah 4.18   -> Ah Delivered (This Outage) at the MODEM SHED
+  #                                   line. Nameplate is 10 Ah [S], so Runtime
+  #                                   Remaining probably reads low until then [I].
+  #   float_voltage 13.30          -> only seeds g_onset_float_v; set to the bus at
+  #                                   float on this PSU (13.571-13.587 V [D]).
+  #   on_battery_threshold_v 13.15 -> after [F01], used only by the voltage gate of
+  #                                   Battery Fully Charged; check it against the
+  #                                   measured float.
+  #   settling/plateau/knee_min_v  -> phase boundaries on that discharge's V curve.
+  #   knee/cliff_slope_threshold   -> the EMA slope in that discharge's knee/cliff.
+  #   warning/critical_voltage     -> no host to shut down (design doc 8): alerts.
+  #   onset_float_v_min 13.15      -> the at-rest gate of the onset capture.
+  #   survival_entry_current_lo/hi -> the board's post-shed draw (about -35 mA [D])
+  #                                   and its WiFi peaks, from the shed test log.
+  #   survival_exit_v 13.0         -> the shed pack's resting voltage over 1 h.
+  #   shed_voltage 11.80           -> that discharge, and the XB7's lowest input.
+  # The Ri literals (20-300 mOhm band, -0.8 A arm, 0.20 A rest) sit in lambdas.
+
   # --- Battery & system parameters (INA260 coulomb-counted, May 2026) -------
   validated_capacity_ah:    "4.18"   # Ah usable at 13.3V float, 14.9W load.
                                      # V1.17: load is now 26.8 W [M 2026-08-29];
@@ -446,6 +511,8 @@ substitutions:
   warning_voltage:          "12.40"  # HA first-warning notification
   critical_voltage:         "12.20"  # Software-controlled HA Green shutdown
   lvd_voltage:              "11.80"  # BP-65 hardware disconnect (Setting 7)
+                                     # REV 4.1 [F10]: no longer referenced; no BP-65
+                                     # here. LVD Imminent now uses shed_voltage.

   # --- Discharge phase boundary voltages (May 2026 characterisation) --------
   settling_min_v:           "13.00"  # Above → settling  (OCV relaxation, ~5 min)
@@ -609,6 +676,22 @@ substitutions:
                                      # lowest typical draw, 0.98 A / 2 [D, doc 1.7].
   plausibility_alert_delay: "60s"    # both plausibility alerts must hold this long.
                                      # Must also exceed the HDR decay (open item 6).
+                                     # REV 4.1 [F09]: precisely, the decay to
+                                     # mains_present_v PLUS mains_debounce_polls s:
+                                     # "PSU Running Bus Not Fed" sees the outage's
+                                     # discharge while mains is still debounced
+                                     # present. Same bound for Modem Shed Ineffective.
+  # REV 4.1 [F02]: true = a shed read also needs CVRF (INA260 Mask/Enable bit 3)
+  # set, i.e. a conversion finished since the previous poll. false = V4.0
+  # behaviour. Either way stale reads are counted ("Shed Path Stale Reads"). Bench:
+  # that counter stays 0 through the shed test (review bench plan, test 5).
+  shed_require_cvrf:        "true"
+  # REV 4.1 [F06]: true = exit reason 5 (bus >= survival_exit_v twice, PSU sense
+  # absent) also needs the pack CHARGING: I >= ac_return_current_a at the exit
+  # test. false = V4.0 behaviour (default). Turn on once the bench has shown the
+  # exit-test current of a wire-off recovery (review bench test 7), and before
+  # service if a shed pack is seen resting at or above survival_exit_v (item 14).
+  survival_exit5_require_charge: "false"

 # ============================================================================
 esphome:
@@ -617,7 +700,7 @@ esphome:
   comment: ${device_description}
   project:
     name: "wkcollis1.ups-monitor-rev4"
-    version: "4.0"
+    version: "4.1"
   on_boot:
     # ── Priority 900: REV 4 — GPIO5 / MODEM_OFF, decided on the wake cause ──
     # Runs before everything else in this file, including the NVS globals
@@ -717,14 +800,29 @@ esphome:
     - priority: -100
       then:
         - delay: 6s
+        # REV 4.1 [F01] — wait for the supervisor's first debounced mains decision
+        # (about mains_debounce_polls s after boot), then test the SAME signal
+        # on_battery uses. V4.0 kept the V1.x bus test, v < on_battery_threshold_v,
+        # but REV 4's on_battery comes from PSU sense: at the 13.6 V float a pack
+        # early in an outage can hold the bus above 13.15 V [I: design doc 8]. A
+        # reboot then skipped this re-anchor, on_press found outage_start_uptime
+        # == 0, counted a NEW outage and zeroed the restored Ah/Wh: the V1.12
+        # item-7 bug, re-opened. on_press fires on_battery's delayed_on (10 s)
+        # after g_mains_state reaches 0, so this still runs first.
+        - wait_until:
+            condition:
+              lambda: 'return id(g_mains_state) >= 0 || id(survival_mode_active);'
+            timeout: 60s
         - if:
             condition:
               lambda: |-
                 float v = id(ina260_voltage).state;
                 float i = id(ina260_current).state;
+                // REV 4.1 [F01]: debounced mains ABSENT replaces the V1.x
+                // v < ${on_battery_threshold_v}. v is still required to be valid.
                 return !id(survival_mode_active) &&
                        !isnan(v) && !isnan(i) &&
-                       v < ${on_battery_threshold_v} && i < -0.05f;
+                       id(g_mains_state) == 0 && i < -0.05f;
             then:
               - lambda: |-
                   // Re-anchor timing only if not already set this outage.
@@ -743,6 +841,8 @@ esphome:
     # Skipped entirely on normal boots — zero overhead in normal operation.
     #
     # Decision logic (fail toward EXIT, never toward re-sleep):
+    #   0. REV 4.1 [F03]: a NON-timer boot with the flag set exits at once
+    #      (reason 4, modem on); the supervisor must re-earn the shed.
     #   1. 20 ms settle (V1.13: the SOLE freshness wait — the ina260 platform's
     #      setup() reset + 0x0307 config ran at priority 600; a fresh AVG=4
     #      conversion needs ~5 ms), then register 0x02 read (1.25 mV LSB,
@@ -776,6 +876,27 @@ esphome:
             id(survival_should_sleep) = false;
             if (!id(survival_mode_active)) return;

+            // REV 4.1 [F03] — a NON-timer boot (power-on, brown-out, panic, task
+            // WDT, esp_restart) with the NVS survival flag still set. Priority 900
+            // has already driven GPIO5 LOW (modem on). V4.0 went on to re-sleep with
+            // the pad latched HIGH on ONE PSU sample and at most three bus reads:
+            // a re-shed without the supervisor, against design doc section 5 ("ESP
+            // reboots during a latched shed ... the modem comes back on ... sheds
+            // again after about 20 s of valid readings") and the RAM-only latch.
+            // Now: leave survival (reason 4), modem on, and let the supervisor
+            // re-earn the shed from live readings; survival re-arms through its
+            // normal entry if the pack is still low. Cost per such reset: about
+            // mains_debounce_polls + shed_valid_reads_n + 30 s of modem load.
+            if (esp_sleep_get_wakeup_cause() != ESP_SLEEP_WAKEUP_TIMER) {
+              id(survival_mode_active) = false;
+              id(outage_was_survival)  = false;   // as reason 2: don't strand the marker
+              id(survival_exit_reason) = 4;       // REV 4.1: 4 = reset during survival
+              ESP_LOGW("ups.survival",
+                "SURVIVAL EXIT (RESET DURING SURVIVAL, wake cause %d) | modem on; the shed must be re-earned",
+                (int) esp_sleep_get_wakeup_cause());
+              return;
+            }
+
             // V1.13: 20 ms freshness wait — now the SOLE pre-decision settle (the
             // priority-600 mode-restore + its 10 ms delay were removed; the platform
             // is the single configurator, AVG=4). A fresh AVG=4 averaged bus-voltage
@@ -807,6 +928,10 @@ esphome:
             //     ratio is applied here. NaN (a failed read) counts as mains ABSENT.
             float psu1 = id(psu_adc).sample() * ${psu_divider_ratio}f;
             bool mains1 = !isnan(psu1) && psu1 >= ${mains_present_v}f;
+            // REV 4.1 [F09]: in ESPHome 2026.10.2 ADCSensor::sample() never returns
+            // NaN on ESP32: failed conversions are skipped and an all-failed read
+            // returns raw 0 (Aggregator aggr_{0}), about 0 V = mains ABSENT. Same
+            // direction as the NaN rule above; the isnan() stays as a belt.

             // V1.9: register 0x02 (Bus Voltage) read via the I2CDevice helper.
             // write_read issues write-pointer -> repeated-START -> read as ONE
@@ -899,9 +1024,28 @@ esphome:
                 id(ina_raw).write_read(&vreg, 1, vd2, 2);   // vreg still in scope
                 uint16_t raw2 = ((uint16_t)vd2[0] << 8) | vd2[1];
                 float v2 = raw2 * 0.00125f;
+                // REV 4.1 [F06] — pack current at the exit test (0x01, signed, 1.25 mA
+                // LSB [S: SBOS656C]). A pack that is CHARGING (mains back, PSU_SENSE
+                // wire off) reads amps positive; a shed pack that only rests above
+                // survival_exit_v (design doc 8.1 deviation 1, open item 14) reads
+                // the board's own draw, tens of mA negative. Kept in NVS for every
+                // exit test, because this log line is never seen (no network).
+                uint8_t ireg = 0x01; uint8_t ib2[2] = {0, 0};
+                bool i2_ok = (id(ina_raw).write_read(&ireg, 1, ib2, 2) == i2c::ERROR_OK);
+                float i2 = i2_ok ? (int16_t)(((uint16_t)ib2[0] << 8) | ib2[1]) * 0.00125f : NAN;
+                id(survival_exit_test_i) = i2;
                 float psu2 = id(psu_adc).sample() * ${psu_divider_ratio}f;
                 bool rec_psu = mains1 && !isnan(psu2) && psu2 >= ${mains_present_v}f;
                 bool rec_v   = (v1 >= ${survival_exit_v}f) && (v2 >= ${survival_exit_v}f);
+                // REV 4.1 [F06]: optional (survival_exit5_require_charge, default
+                // false = V4.0): reason 5 also needs I >= ac_return_current_a.
+                if (${survival_exit5_require_charge} && !rec_psu && rec_v &&
+                    !(!isnan(i2) && i2 >= ${ac_return_current_a}f)) {
+                  ESP_LOGW("ups.survival",
+                    "Reason-5 exit refused: bus %.3f / %.3f V >= ${survival_exit_v} V but I=%.4f A is not charging (resting pack?)",
+                    v1, v2, i2);
+                  rec_v = false;
+                }
                 if (rec_psu || rec_v) {
                     id(survival_mode_active) = false;
                     id(survival_exit_reason) = 1;   // V1.14: 1 = genuine recovery (V >= 13.0 x2)
@@ -937,9 +1081,9 @@ esphome:
                         id(last_outage_start_v), id(last_outage_min_v));
                     }
                     ESP_LOGI("ups.survival",
-                      "SURVIVAL EXIT (%s) | V1=%.3fV V2=%.3fV | PSU %.2fV / %.2fV | recovery — normal boot, modem released",
+                      "SURVIVAL EXIT (%s) | V1=%.3fV V2=%.3fV | PSU %.2fV / %.2fV | I=%.4fA | recovery — normal boot, modem released",
                       rec_psu ? "mains on PSU sense" : "bus voltage only, PSU sense absent",
-                      v1, v2, psu1, psu2);
+                      v1, v2, psu1, psu2, i2);   // REV 4.1 [F06]: + I
                     // V1.20: say out loud that no recharge-step Ri will be captured
                     // for this outage, instead of leaving the sensor silently stale.
                     // This is CORRECT behaviour, not a defect to fix: the BP-65 cut the
@@ -957,8 +1101,8 @@ esphome:
                     return;
                 }
                 ESP_LOGW("ups.survival",
-                  "Exit re-read failed: V1=%.3f V2=%.3f PSU %.2f / %.2f — re-sleeping",
-                  v1, v2, psu1, psu2);
+                  "Exit re-read failed: V1=%.3f V2=%.3f PSU %.2f / %.2f I=%.4f — re-sleeping",
+                  v1, v2, psu1, psu2, i2);   // REV 4.1 [F06]: + I
             }

             // Below exit threshold (or glitch re-read) — re-enter sleep.
@@ -1081,7 +1225,7 @@ esphome:
       then:
         - logger.log:
             level: INFO
-            format: "UPS Monitor Rev 4 V4.0 boot complete -- INA260 @ 0x40 (platform-configured, AVG=4, paired 5 s V/I blocks), DS18B20 on GPIO10, PSU sense on GPIO4, modem shed on GPIO5 (hold through survival sleep), timer-wake + run_duration watchdog + stale-data watchdog + onset/recharge Ri capture (one-shot) + settled-step Apparent Ri (windowed gate)"
+            format: "UPS Monitor Rev 4 V4.1 boot complete -- INA260 @ 0x40 (platform-configured, AVG=4, paired 5 s V/I blocks), DS18B20 on GPIO10, PSU sense on GPIO4, modem shed on GPIO5 (hold through survival sleep), timer-wake + run_duration watchdog + stale-data watchdog + onset/recharge Ri capture (one-shot) + settled-step Apparent Ri (windowed gate)"

 esp32:
   board: seeed_xiao_esp32c3
@@ -1254,6 +1398,10 @@ i2c_device:
 # 1-Wire bus
 # DQ = GPIO10 (XIAO D10) → DS18B20 DQ on TB2 (3-pin JST-XH: 3V3 / DQ / GND)
 # DS18B20 module has built-in 4.7 kΩ pull-up — no external resistor required.
+# REV 4.1 [F09]: on the Rev 4 board (2026-11-12 save) TB2 is a 4-pole screw
+# terminal: pad 1 +3V3, pad 2 DQ, pad 3 GND, pad 4 PSU_SENSE (design doc 3, item 1;
+# meter it before connecting). R8 4.7k has a footprint but is DNP: the sensor in
+# service carries its own pull-up (item 27).
 # ----------------------------------------------------------------------------
 one_wire:
   - platform: gpio
@@ -1413,6 +1561,25 @@ globals:
     type: int
     initial_value: '0'
     restore_value: yes
+  # REV 4.1 [F02]: supervisor shed-path reads that found CVRF clear (no conversion
+  # since the previous poll). RAM only: a diagnostic, not worth an NVS write.
+  - id: g_shed_stale_reads
+    type: int
+    initial_value: '0'
+    restore_value: no
+  # REV 4.1 [F05]: millis() of the first INA260 load step after rest (onset
+  # detector); 0 = none pending. Consumed by the supervisor's first low PSU poll.
+  - id: g_step_ms
+    type: uint32_t
+    initial_value: '0'
+    restore_value: no
+  # REV 4.1 [F06]: pack current (A, signed) at the last survival exit test. NVS:
+  # the exit runs with no network, so its log line is not seen. Written only at an
+  # exit test (rare). NAN until the first one; reset at survival entry.
+  - id: survival_exit_test_i
+    type: float
+    initial_value: 'NAN'
+    restore_value: yes

   # --- V1.14: INA260 stale-data watchdog (transient) -------------------------
   # Updated from the bus-voltage on_raw_value (1 Hz — fires ONLY when the
@@ -1568,6 +1735,9 @@ globals:
   # distinguishable only in logs that cannot be streamed mid-outage (baud_rate 0;
   # the AP is dead). 0 = none this episode, 1 = recovery (V >= 13.0 x2),
   # 2 = fail-safe (implausible read), 3 = max-cycle backstop. Reset to 0 at arm.
+  # REV 4.1 [F09]: REV 4 redefined 1 (PSU sense confirmed mains, twice) and added
+  # 5 (bus >= survival_exit_v twice, PSU sense absent); [F03] adds 4 (reset during
+  # survival: a non-timer boot with the flag set).
   - id: survival_exit_reason
     type: int
     initial_value: '0'
@@ -1694,6 +1864,9 @@ interval:
   #             modem load is gone); only debounced mains clears it.
   #             LIMIT: "valid" does not prove the conversion is new (CVRF is not
   #             read). A chip that answers with a frozen register would pass.
+  #             REV 4.1 [F02]: closed. CVRF (06h bit 3) is read before every shed
+  #             read; clear = INVALID (shed_require_cvrf), and I2C errors are
+  #             checked, not only the pre-zeroed buffer.
   #   3. PAD    the commanded level is written every poll; when it is LOW the
   #             hold is released every poll as well. Then the pad is read back
   #             (it is configured INPUT_OUTPUT). Two consecutive mismatches raise
@@ -1711,6 +1884,8 @@ interval:

           // 1. MAINS — direct sample, volts at the pin x divider ratio.
           float psu = id(psu_adc).sample() * ${psu_divider_ratio}f;
+          // REV 4.1 [F09]: sample() never returns NaN on ESPHome 2026.10.2 (see
+          // -150); a failed ADC reads about 0 V, which counts as absent the same way.
           if (!isnan(psu) && psu >= ${mains_present_v}f) {
             id(g_mains_lo_n) = 0;
             if (id(g_mains_hi_n) < 30000) id(g_mains_hi_n) += 1;
@@ -1718,6 +1893,28 @@ interval:
             id(g_mains_hi_n) = 0;
             if (id(g_mains_lo_n) < 30000) id(g_mains_lo_n) += 1;
           }
+          // REV 4.1 [F05] — open item 6 field instrument. The first poll below the
+          // threshold while mains is still debounced PRESENT is when the HDR output
+          // has decayed through mains_present_v. Timed from the INA260 load step the
+          // onset detector saw (g_step_ms): the ideal diode hands the bus to the
+          // pack once the PSU output sags below it [I]. Resolution is the 1 s poll
+          // plus the 0.2 s step debounce, so a decay under ~1.2 s is only bounded.
+          // Measurement only: nothing below reads it.
+          if (id(g_mains_state) == 1 && id(g_mains_lo_n) == 1) {
+            uint32_t now_ms = millis();
+            if (id(g_step_ms) != 0 && (now_ms - id(g_step_ms)) < 600000u) {
+              float s = (now_ms - id(g_step_ms)) / 1000.0f;
+              id(psu_decay_s).publish_state(s);
+              ESP_LOGI("ups.mains",
+                "PSU sense %.2f V < ${mains_present_v} V, %.1f s after the INA260 load step (HDR decay, open item 6)",
+                psu, s);
+            } else {
+              ESP_LOGI("ups.mains",
+                "PSU sense %.2f V < ${mains_present_v} V, no INA260 load step in the last 600 s (glitch, decay < step debounce, or decay > 600 s)",
+                psu);
+            }
+            id(g_step_ms) = 0;
+          }
           if (id(g_mains_hi_n) >= ${mains_debounce_polls}) id(g_mains_state) = 1;
           if (id(g_mains_lo_n) >= ${mains_debounce_polls}) id(g_mains_state) = 0;

@@ -1731,11 +1928,32 @@ interval:
               ESP_LOGW("ups.shed", "MODEM RESTORED | mains present, PSU sense %.2f V (debounced)", psu);
             }
           } else if (id(g_mains_state) == 0 && !id(shed_latched)) {
+            // REV 4.1 [F02] — FRESH, per design doc section 8 ("fresh from this
+            // poll"). Mask/Enable (06h) bit 3, CVRF, "is set after all conversions,
+            // averaging, and multiplications are complete" and clears when 06h is
+            // read [S: TI SBOS656C, 8.6.5]. Nothing else reads 06h: not this file,
+            // not the ina260 platform (2026.10.2 source, update() reads 02h/01h/03h
+            // only). So CVRF = 1 means an AVG=4 conversion (~5 ms) finished since
+            // the previous poll. A powered-down or stalled chip still answers with
+            // its last result [S: SBOS656C 8.3.3, "the data from the last
+            // conversion remain available"], and now reads INVALID. Both transfers
+            // must also return i2c::ERROR_OK (V4.0 relied on the zeroed buffer).
+            uint8_t mreg = 0x06; uint8_t mb[2] = {0, 0};      // Mask/Enable (06h)
+            bool i2c_ok = (id(ina_raw).write_read(&mreg, 1, mb, 2) == i2c::ERROR_OK);
+            bool cvrf   = (mb[1] & 0x08) != 0;                // bit 3, low byte
             uint8_t reg = 0x02; uint8_t b[2] = {0, 0};
-            id(ina_raw).write_read(&reg, 1, b, 2);              // Bus Voltage (0x02)
+            i2c_ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK) && i2c_ok;  // Bus Voltage (0x02)
             uint16_t vraw = ((uint16_t)b[0] << 8) | b[1];
             float v = vraw * 0.00125f;
-            bool valid = (vraw != 0x0000 && vraw != 0xFFFF &&
+            if (i2c_ok && !cvrf && id(g_shed_stale_reads) < 1000000000) {
+              id(g_shed_stale_reads) += 1;
+              if (id(g_shed_stale_reads) % 60 == 1)
+                ESP_LOGW("ups.shed",
+                  "Shed read STALE: INA260 CVRF clear, no conversion since the last poll | V=%.3f | count %d%s",
+                  v, id(g_shed_stale_reads), ${shed_require_cvrf} ? " | read rejected" : " | gate off, read used");
+            }
+            bool valid = (i2c_ok && (cvrf || !${shed_require_cvrf}) &&
+                          vraw != 0x0000 && vraw != 0xFFFF &&
                           v > ${shed_plausible_v_min}f && v < ${shed_plausible_v_max}f);
             if (valid && v <= ${shed_voltage}f) id(g_shed_low_n) += 1;
             else                                id(g_shed_low_n) = 0;
@@ -1994,11 +2212,19 @@ interval:
           if (id(g_onset_capturing))    return;     // capture owns the bus

           // Raw INA260 read -- same explicit-byte pattern as the survival path.
-          uint8_t reg; uint8_t b[2];
-          reg = 0x02; id(ina_raw).write_read(&reg, 1, b, 2);   // Bus Voltage (0x02)
+          // REV 4.1 [F08] — buffer pre-zeroed and both I2C results checked. Through
+          // V4.0, b[] was uninitialised and reused, and the result was ignored: a
+          // failed CURRENT read after a good voltage read left the voltage bytes in
+          // b[], so 13.5 V came back as +13.5 A (raw 10800 x 1.25 mA) [D]. A
+          // failed poll is now skipped, like the 0x0000 guard below. Success-path
+          // behaviour is unchanged.
+          uint8_t reg; uint8_t b[2] = {0, 0};
+          reg = 0x02; bool ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK);  // Bus Voltage (0x02)
           uint16_t vraw = ((uint16_t)b[0] << 8) | b[1];
-          reg = 0x01; id(ina_raw).write_read(&reg, 1, b, 2);   // Current (0x01)
+          b[0] = 0; b[1] = 0;
+          reg = 0x01; ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK) && ok;  // Current (0x01)
           int16_t  iraw = (int16_t)(((uint16_t)b[0] << 8) | b[1]);
+          if (!ok) return;                                     // REV 4.1 [F08]
           if (vraw == 0x0000 || vraw == 0xFFFF) return;        // bad-read / pre-first-conv guard
           float v = vraw * 0.00125f;                           // V, 1.25 mV LSB
           float i = iraw * 0.00125f;                           // A, 1.25 mA LSB, +chg/-dis
@@ -2037,6 +2263,7 @@ interval:
               if (id(g_onset_armed)) {
                 id(g_onset_armed)         = false;
                 id(g_onset_capturing)     = true;
+                id(g_step_ms)             = millis();   // REV 4.1 [F05]: rest->load instant
                 id(onset_capture).execute();
               }
               return;
@@ -2177,22 +2404,28 @@ sensor:
             // still unpaired means that update's current read failed.
             if (id(g_v_pending)) id(ina_unpaired_reads)++;
             id(g_v_pending) = true;
-    power:
-      # V1.16: renamed + internal. The INA260 POWER register computes an
-      # UNSIGNED product per internal conversion; near zero current it reports
-      # the rectified noise floor (0.07-0.40 W observed on this unit at float)
-      # instead of the true ~0.01 W. Same silicon-family behavior characterized
-      # on the bank monitor's INA228 (2026-07-17). "Battery Power" is now the
-      # signed V x I template below — same name, so HA entity id continuity holds.
-      name: "INA260 Power Register"
-      id: ina260_power
-      internal: true
-      unit_of_measurement: "W"
-      accuracy_decimals: 3
-      device_class: power
-      state_class: measurement
-      filters:
-        - throttle_average: 5s
+    # REV 4.1 [F07] — the power channel below is REMOVED (commented out, kept for
+    # its history). It was internal and nothing read ina260_power: Battery Power is
+    # the signed V x I template. Without it the platform's update() reads 02h and
+    # 01h only (2026.10.2 ina260.cpp skips 03h when power_sensor_ is null): one I2C
+    # transfer and one throttle_average scheduler interval fewer per second. The
+    # V-then-I order, and so the paired-block accumulator, is unchanged.
+    # power:
+    #   # V1.16: renamed + internal. The INA260 POWER register computes an
+    #   # UNSIGNED product per internal conversion; near zero current it reports
+    #   # the rectified noise floor (0.07-0.40 W observed on this unit at float)
+    #   # instead of the true ~0.01 W. Same silicon-family behavior characterized
+    #   # on the bank monitor's INA228 (2026-07-17). "Battery Power" is now the
+    #   # signed V x I template below — same name, so HA entity id continuity holds.
+    #   name: "INA260 Power Register"
+    #   id: ina260_power
+    #   internal: true
+    #   unit_of_measurement: "W"
+    #   accuracy_decimals: 3
+    #   device_class: power
+    #   state_class: measurement
+    #   filters:
+    #     - throttle_average: 5s

   # V1.20 — the HA-facing Battery Voltage / Battery Current. Published ONLY by the
   # paired-block accumulator on ina260_current_raw above; never polled.
@@ -2615,6 +2848,43 @@ sensor:
     lambda: 'return id(shed_hold_lost_count);'
     update_interval: 60s

+  # REV 4.1 [F02] — supervisor shed-path reads with CVRF clear. Expected 0. Any
+  # count means the INA260 answered without a new conversion: a power-down left
+  # behind, a stalled chip, or an unexpected 06h reader. RAM: resets on reboot.
+  - platform: template
+    name: "Shed Path Stale Reads"
+    id: shed_path_stale_reads_sensor
+    accuracy_decimals: 0
+    icon: "mdi:counter"
+    state_class: total_increasing
+    entity_category: diagnostic
+    lambda: 'return (float) id(g_shed_stale_reads);'
+    update_interval: 60s
+
+  # REV 4.1 [F05] — open item 6: seconds from the INA260 load step to the first
+  # PSU-sense poll below mains_present_v. Published once per outage start.
+  - platform: template
+    name: "PSU Decay To Threshold"
+    id: psu_decay_s
+    unit_of_measurement: "s"
+    accuracy_decimals: 1
+    icon: "mdi:timer-sand"
+    entity_category: diagnostic
+    update_interval: never
+
+  # REV 4.1 [F06] — pack current at the last survival exit test (NVS). Amps
+  # positive = charging (mains was back); tens of mA negative = a resting pack
+  # that crossed survival_exit_v (design doc 8.1 deviation 1). NAN until the first.
+  - platform: template
+    name: "Survival Exit Test Current"
+    id: survival_exit_test_i_sensor
+    unit_of_measurement: "A"
+    accuracy_decimals: 3
+    device_class: current
+    entity_category: diagnostic
+    lambda: 'return id(survival_exit_test_i);'
+    update_interval: 60s
+
   # --------------------------------------------------------------------------
   # V1.14 — Survival-event capture sensors (doc S9.2, S13).
   # Populated only after a survival episode; NaN/zero-guarded until then.
@@ -2836,6 +3106,7 @@ text_sensor:
         case 3:  return std::string("Max cycles");    // 15-day backstop
         // REV 4: 1 = PSU sense confirmed mains; 5 = bus >= exit x2 with PSU
         // sense still reading absent (check the PSU_SENSE wire).
+        case 4:  return std::string("Reset during survival");  // REV 4.1 [F03]
         case 5:  return std::string("Recovery, PSU sense absent");
         default: return std::string("None");          // no episode / armed
       }
@@ -2919,10 +3190,13 @@ binary_sensor:
             // double-increment total_outage_count, undoing the -100 preservation.
             // TIMING COUPLING: relies on -100 (delay 6 s) running before this on_press
             // (on_battery delayed_on 10 s) on a reboot — keep delayed_on > the -100 delay.
+            // REV 4.1 [F01]: -100 now waits for the supervisor's first mains decision
+            // and runs in the loop that sets g_mains_state = 0; on_battery's
+            // delayed_on still puts this on_press 10 s after it.
             if (id(outage_start_uptime) != 0) {
               ESP_LOGW("ups",
                 "on_press suppressed — already in an outage (start=%u); counters preserved",
-                id(outage_start_uptime));
+                (unsigned) id(outage_start_uptime));   // REV 4.1 [F09]: uint32_t is long on riscv32 (-Wformat)
               return;
             }
             id(outage_start_uptime)  = (uint32_t)id(device_uptime).state;
@@ -3052,7 +3326,10 @@ binary_sensor:
     device_class: problem
     lambda: |-
       // Within 100 mV of BP-65 hardware disconnect (11.80 V, Setting 7)
-      return id(ina260_voltage).state < (${lvd_voltage} + 0.10f) &&
+      // REV 4.1 [F10]: no BP-65 here; the disconnect is this node's own shed, so
+      // test 100 mV above shed_voltage (11.90 V, as before). It is the last alert
+      // HA can see: a working shed takes the network with it.
+      return id(ina260_voltage).state < (${shed_voltage} + 0.10f) &&
              id(ina260_current).state < -0.10f;

   # --------------------------------------------------------------------------
@@ -3128,6 +3405,7 @@ binary_sensor:
   # line is held high in hardware; the internal INPUT_PULLUP below is redundant
   # (kept as belt-and-suspenders, harmless). Adafruit #4226 has no pull-up of its
   # own — R2 supplies it.
+  # REV 4.1 [F09]: on the Rev 4 board this pull-up is R1 10k (design doc 4.6).
   #
   # V1.11 — GPIO3 is now a SINGLE-OWNER passive input. Event-wake is backed out, so
   # this pin is no longer the deep_sleep wakeup_pin and allow_other_uses is REMOVED
@@ -3231,6 +3509,9 @@ binary_sensor:
       // 13.179-13.193 V [M, n=5] -- load bursts at float, not a charge change.
       // The VOLTAGE half stays strict, so exclusivity with on_battery (V below
       // the same threshold) still holds by construction.
+      // REV 4.1 [F09]: no longer true. REV 4's on_battery comes from PSU sense,
+      // not from this threshold, so both can be ON at once: for example with the
+      // PSU_SENSE wire off on mains, which "PSU Sense Lost" reports.
       if (!(id(ina260_voltage).state > ${on_battery_threshold_v}f)) return false;
       float i_lim = id(battery_fully_charged).state ? ${fully_charged_hold_i_a}f : 0.10f;
       return fabs(id(ina260_current).state) < i_lim;
@@ -3290,6 +3571,25 @@ binary_sensor:
     icon: "mdi:router-network-wireless"
     lambda: 'return id(shed_latched);'

+  # REV 4.1 [F04] — the Q1-path alarm. "Modem Shed" ON reaches HA only if the
+  # network outlives the shed, but its ON edge can also race out in the moment
+  # before a WORKING shed drops the AP, so it is a noisy alert source. This one
+  # needs the shed latched AND the modem's load still on the bus (fresh block
+  # current below survival_entry_current_lo, the bound that also blocks survival
+  # entry) for plausibility_alert_delay: Q1/R2 open, EN not wired to U4, or Q2
+  # stuck on. Alert only; it does not drive GPIO5.
+  - platform: template
+    name: "Modem Shed Ineffective"
+    id: modem_shed_ineffective
+    device_class: problem
+    lambda: |-
+      if (!id(shed_latched) || id(last_ina_publish_ms) == 0 ||
+          (millis() - id(last_ina_publish_ms)) > 15000u) return false;
+      float i = id(ina260_current).state;
+      return !isnan(i) && i < ${survival_entry_current_lo}f;
+    filters:
+      - delayed_on: ${plausibility_alert_delay}
+
   # Pad read back differs from the commanded level on 2 consecutive polls. This
   # includes MODEM_OFF HIGH with mains present (open item 16).
   - platform: template
@@ -3428,6 +3728,7 @@ binary_sensor:
             id(survival_min_wake_v)   = 0.0f;
             id(survival_last_wake_v)  = 0.0f;
             id(survival_exit_reason)  = 0;
+            id(survival_exit_test_i)  = NAN;   // REV 4.1 [F06]: fresh per episode
             id(last_outage_ah)       = id(ah_delivered_outage).state;
             id(last_outage_wh)       = id(wh_delivered_outage).state;
             id(last_recharge_peak_a) = id(recharge_peak_a);
@@ -3538,6 +3839,7 @@ button:
           id(survival_min_wake_v)      = 0.0f;
           id(survival_last_wake_v)     = 0.0f;
           id(survival_exit_reason)     = 0;
+          id(survival_exit_test_i)     = NAN;   // REV 4.1 [F06]
           ESP_LOGI("ups", "Last outage data cleared manually");


@@ -3563,6 +3865,22 @@ script:
   # turn the modem off. gpio_config() logs one INFO line per call, which is why
   # the supervisor calls this only on a change.
   # Synchronous (no delay), so execute() has finished when it returns.
+  # REV 4.1 [F09]: gpio_config() logs at ESP_LOGD (ESP-IDF 5.5.6 gpio.c) and this
+  # build sets CONFIG_LOG_DEFAULT_LEVEL=1 (errors only), so it logs nothing here.
+  # Calling it only on a change is still right: fewer pad reconfigurations.
+  # REV 4.1 [F09] — which call holds GPIO5 (ESP-IDF 5.5.6 source, ESP32-C3):
+  # GPIO0-5 are VDD3P3_RTC pads; the digital ones are GPIO6-21
+  # (SOC_GPIO_VALID_DIGITAL_IO_PAD_MASK 0x3FFFC0). gpio_hold_en(GPIO_NUM_5) ->
+  # gpio_ll_hold_en sets bit 5 of RTC_CNTL_PAD_HOLD_REG, an RTC-domain latch: that
+  # bit is what holds this pad. gpio_deep_sleep_hold_en() sets the digital pads'
+  # autohold only, and makes deep-sleep entry isolate every digital pad that is not
+  # individually held (sleep_gpio.c, esp_sleep_isolate_digital_gpio): I2C, 1-Wire
+  # and the spare pins sit input-off, output-off, no pulls, through the sleep.
+  # After wake "the digital GPIO state can be changed freely" (gpio.h), so I2C
+  # works at -150. Both calls stay (design doc 8; hard invariant 4). On a timer
+  # wake cpu_start.c releases holds only on GPIO0-5 pads enabled as deep-sleep
+  # WAKE pins (esp_deep_sleep_wakeup_io_reset); GPIO5 is not one, so the app does
+  # not drop this hold. What the ROM does to it is not in source: open item 7.
   # --------------------------------------------------------------------------
   - id: modem_off_set
     mode: single
@@ -3597,12 +3915,14 @@ script:
           count: ${onset_sample_count}
           then:
             - lambda: |-
-                uint8_t reg; uint8_t b[2];
-                reg = 0x02; id(ina_raw).write_read(&reg, 1, b, 2);
+                // REV 4.1 [F08] — pre-zeroed, results checked (see the detector).
+                uint8_t reg; uint8_t b[2] = {0, 0};
+                reg = 0x02; bool ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK);
                 uint16_t vraw = ((uint16_t)b[0] << 8) | b[1];
-                reg = 0x01; id(ina_raw).write_read(&reg, 1, b, 2);
+                b[0] = 0; b[1] = 0;
+                reg = 0x01; ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK) && ok;
                 int16_t  iraw = (int16_t)(((uint16_t)b[0] << 8) | b[1]);
-                if (vraw != 0x0000 && vraw != 0xFFFF) {
+                if (ok && vraw != 0x0000 && vraw != 0xFFFF) {
                   id(g_cap_vsum) += vraw * 0.00125f;
                   id(g_cap_isum) += fabs(iraw * 0.00125f);   // discharge magnitude
                   id(g_cap_n)++;
@@ -3640,12 +3960,14 @@ script:
           count: ${onset_sample_count}
           then:
             - lambda: |-
-                uint8_t reg; uint8_t b[2];
-                reg = 0x02; id(ina_raw).write_read(&reg, 1, b, 2);
+                // REV 4.1 [F08] — pre-zeroed, results checked (see the detector).
+                uint8_t reg; uint8_t b[2] = {0, 0};
+                reg = 0x02; bool ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK);
                 uint16_t vraw = ((uint16_t)b[0] << 8) | b[1];
-                reg = 0x01; id(ina_raw).write_read(&reg, 1, b, 2);
+                b[0] = 0; b[1] = 0;
+                reg = 0x01; ok = (id(ina_raw).write_read(&reg, 1, b, 2) == i2c::ERROR_OK) && ok;
                 int16_t  iraw = (int16_t)(((uint16_t)b[0] << 8) | b[1]);
-                if (vraw != 0x0000 && vraw != 0xFFFF) {
+                if (ok && vraw != 0x0000 && vraw != 0xFFFF) {
                   id(g_cap_vsum) += vraw * 0.00125f;
                   id(g_cap_isum) += iraw * 0.00125f;           // SIGNED (charge +)
                   id(g_cap_n)++;
```
