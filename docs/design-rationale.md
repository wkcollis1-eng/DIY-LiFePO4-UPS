# Design Rationale

---

## Why Build Instead of Buy?

A $75 APC BE600M1 exists and works out of the box. Over 10 years this DIY build costs approximately $200 more than that option. The build makes sense only if specific limitations of commercial SLA-based UPS units matter to you:

| Limitation | Commercial SLA UPS | This Design |
|---|---|---|
| Battery lifespan | 2–3 years (SLA, 100% SoC float) | 5–10 years (LiFePO4, 13.3V float) |
| Runtime @ 18W | 2–2.5 hours | 6.5 hours |
| Switchover time | 4–10ms | <1ms (MOSFET ideal diode) |
| Output voltage | Regulated (with DC-DC losses) | Direct battery feed, 11.71–13.16V |
| Monitoring | None or proprietary | Native Home Assistant integration |
| Load visibility | None | Voltage, temperature, SoC, runtime |

This design was also a constrained engineering exercise — the builder already operates a 12V 500Ah (~6kWh) LiFePO4 system for whole-home backup and applied existing domain knowledge to a small dedicated UPS.

---

## Float Charging Strategy

LiFePO4 cells have a natural open-circuit resting voltage of approximately 13.3–13.4V at 100% SoC. Setting the PSU to 13.3V means the battery reaches equilibrium and essentially stops accepting charge current — the system operates in a continuous partial float rather than a forced absorption cycle.

Traditional UPS float voltage of 13.8–14.0V forces continuous absorption current into the cells, accelerating calendar aging. The 13.3V strategy trades a small capacity reserve (the battery sits at approximately 95–98% rather than 100%) for significantly reduced cell stress.

Expected battery lifespan: 5–10 years in residential continuous-float service — 2–3× better than SLA-based commercial UPS alternatives.

**PSU trimmer setting:** The LRS-100-12 output voltage is adjustable from 10.2–13.8V via an onboard trimmer pot. The pot is set to 13.3V and lacquered to prevent mechanical drift. Aging drift in a climate-controlled installation is analytically negligible (estimated 3–5 mV/year), well within the 500mV headroom before the OVP threshold at 13.8V.

---

## Direct Battery Feed — No DC-DC Converter

The original design specified a Mean Well DDR-60G-12 DC-DC converter to regulate a fixed 12.0V output across the full battery discharge range. After analysis, this was dropped:

- Both connected devices (HA Green, XB7) accept 12V nominal with an inferred ±10% tolerance, per IEC 62368-1 / UL 62368-1 design practice for 12V DC input rails.
- The system's device terminal voltage envelope is 11.71–13.16V — within that inferred tolerance throughout the entire battery discharge cycle.
- Adding a DC-DC converter would introduce ~3–5W of conversion losses, reduce runtime, add a failure point, and add ~$30 to cost with no meaningful benefit given the voltage envelope analysis.
- The Victron BP-65 MOSFET LVD (11.8V cutoff) prevents the battery from discharging below the point where device operation would be uncertain.

Neither Nabu Casa nor Comcast publish explicit minimum/maximum input voltage specifications for these products beyond the nominal 12V rating. The ±10% tolerance inference is an engineering judgment, not a manufacturer guarantee.

---

## Why Victron BatteryProtect BP-65 vs. Relay Module?

The original design specified a Noyito relay module for low-voltage disconnect. The Victron BP-65 was substituted after comparative analysis:

- MOSFET switching: no relay contact arcing, no mechanical wear, essentially unlimited cycle life
- IP67 potted electronics: immune to moisture and condensation
- Programmable thresholds via Bluetooth (VictronConnect app) — no physical jumpers
- 90-second hold-off before disconnect prevents false trips on transient voltage sag
- 30-second reconnect delay prevents rapid cycling after AC restoration
- 5-year warranty
- Setting 7: 11.8V cutoff / 12.8V reconnect — well-matched to LiFePO4 discharge curve

The added cost (~$25 over a relay module) is justified by the reliability and programmability requirements of an always-on residential UPS.
