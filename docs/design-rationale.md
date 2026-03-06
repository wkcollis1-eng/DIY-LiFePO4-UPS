# Design Rationale

---

## Why Build Instead of Buy?

Commercial UPS units rely on Sealed Lead Acid (SLA) batteries with a 2–3 year lifespan, aggressive 100% SoC float charging that accelerates degradation, minimal monitoring, and 4–10ms switchover times that can cause modem reboots. Commercial units often use Line-Interactive topology which is where that 4–10ms delay comes from, whereas this design is effectively an Always-On/DC-Buffer topology.

This design addresses each limitation:

| Limitation | Commercial SLA UPS | This Design |
|---|---|---|
| Battery lifespan | 2–3 years (SLA, 100% SoC float) | 7–10 years (LiFePO4, 13.3V float) |
| Runtime @ 13.39W measured | 2–2.5 hours | 8.2 hours |
| Switchover time | 4–10ms | <1ms (MOSFET ideal diode) |
| Output voltage | Regulated (with DC-DC losses) | Direct battery feed, 11.73–13.26V |
| Monitoring | None or proprietary | Native Home Assistant integration |
| Load visibility | None | Voltage, temperature, SoC, runtime |
| Annual Electricity Cost | ~$51/yr | ~$41/yr |

> **Honest context:** A $85 APC BE600M1 would do the same job out of the box. This build saves roughly $25 over 10 years vs that option (based on battery replacements and electricity usage). The engineering rationale — longer battery life, faster switchover, direct HA integration, no DC-DC converter voltage regulation. Build this if those tradeoffs matter to you.

---

## Float Charging Strategy

LiFePO4 cells have a natural open-circuit resting voltage of approximately 13.3–13.4V at 100% SoC. By setting the PSU to 13.3V, the system reaches a natural equilibrium: the battery charges to 13.3V and current delivery tapers to near-zero because there is no longer a voltage differential to drive it. The PSU runs continuously at a fixed voltage, delivering only what load current the connected devices draw.

Traditional UPS float voltage of 13.8–14.0V forces continuous absorption current and accelerates calendar aging. This design's 13.3V float matches the battery's resting voltage, minimizing forced absorption while retaining full capacity for outage response.

Expected battery lifespan: 7–10 years in residential continuous-float service — 2–3× better than SLA-based commercial UPS alternatives. LiFePO4 degrades primarily through high-voltage calendar aging (time above ~3.65V/cell) and high-temperature storage. This design avoids both.

**PSU trimmer setting:** The HDR-60-12 output voltage is adjustable from 10.2–13.8V via an onboard trimmer pot. The pot is set to 13.3V and lacquered to prevent mechanical drift. Aging drift in a climate-controlled installation is analytically negligible (estimated 3–5 mV/year), well within the 1.1V headroom before the BMS OVP threshold at 14.4–14.6V.

---

## Direct Battery Feed — No DC-DC Converter

The original design specified a Mean Well DDR-60G-12 DC-DC converter to regulate a fixed 12.0V output across the full battery discharge range. After analysis, this was dropped:

- Both connected devices (HA Green, XB7) accept 12V nominal with an inferred ±10% tolerance, per IEC 62368-1 / UL 62368-1 design practice for 12V DC input rails.
- The system's device terminal voltage envelope is 11.73–13.26V — within that inferred tolerance throughout the entire battery discharge cycle.
- Adding a DC-DC converter would introduce ~2.8W of continuous conversion losses, reduce runtime, add a failure point, and add ~$34 to cost with no meaningful benefit given the voltage envelope analysis.
- The Victron BP-65 MOSFET LVD (11.8V cutoff) prevents the battery from discharging below the point where device operation would be uncertain.
- Efficiency is maximized by utilizing the wide input tolerance of modern switching power supplies, eliminating the need for a secondary DC-DC conversion stage.

Neither Nabu Casa nor Comcast publish explicit minimum/maximum input voltage specifications for these products beyond the nominal 12V rating. The ±10% tolerance inference is an engineering judgment, not a manufacturer guarantee.

---

## Why Victron BatteryProtect BP-65 vs. Relay Module?

The original design specified a Noyito relay module for low-voltage disconnect. The Victron BP-65 was substituted after comparative analysis:

- MOSFET switching: no arcing, 0.006V drop vs 0.130V for relay contacts
- 1.5mA quiescent vs 730mW for Noyito relay coil
- IP67 potted electronics, no calibration drift
- Programmable thresholds via Bluetooth (VictronConnect app) — no physical jumpers
- 90-second hold-off before disconnect prevents false trips on transient voltage sag
- 30-second reconnect delay prevents rapid cycling after AC restoration
- 5-year warranty
- Setting 7: 11.8V cutoff / 12.8V reconnect — well-matched to LiFePO4 discharge curve

The added cost (~$25 over a relay module) is offset by eliminating the DDR-60G-12 DC-DC converter and is justified by the reliability and programmability requirements of an always-on residential UPS.
