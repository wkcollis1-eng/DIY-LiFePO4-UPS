# Safety

> **Currency note (2026-10-16).** This document is part of the original design set. It describes the build as of March 2026, when a Home Assistant Green ran directly on the 12 V bus and a Shelly Plus Uni ADC did the monitoring. Since then the ESPHome INA260 monitor (April 2026, now on the UPS-Monitor-THT Rev 1 board) has become the measurement of record, the HA Green has been retired, and the HA host is an ASRock N100DC that has run from this UPS through an 18 V boost since 2026-08-29 ([BOOST-DS-r1](../UPS-Monitor/boost-subsystem-design.md)). The load on battery is now 2.089 A / 26.80 W steady [M, 2026-08-29 outage, n = 156, [08-31 report](../reports/UPS_Report_2026-08-31_Boost_Integration.md)]. On 2026-09-15 the pack delivered 2.5331 Ah / 31.821 Wh from onset to LVD [M, [09-15 report](../reports/UPS_Report_2026-09-15_Full_Discharge_Survival_Test.md)], a capacity shortfall that is still under investigation. The [README](../README.md) describes the system as it runs now.
>
> *In this document:* Its heat-dissipation estimate is at the HA Green load and leaves out the boost. [BOOST-DS-r1](../UPS-Monitor/boost-subsystem-design.md) adds rules for the boost, including the energization order to follow whenever the battery or the host's barrel jack is disconnected or reconnected (OP-1).

---

## Electrical Safety

> **WARNING: This project involves 120VAC mains power. Lethal voltages are present inside the enclosure when AC is connected. Do not open the enclosure or touch internal wiring with AC power connected.**

- Disconnect AC power before touching any internal wiring
- Install F2 (battery positive fuse) FIRST before connecting battery to any circuit
- Verify all connections with a multimeter before initial power-up
- Never bypass fuses — they protect against fire and equipment damage
- Plug AC cord directly into wall outlet; do not use extension cords or power strips

The enclosure contains both 120VAC (PSU input side) and 12V DC (battery and load side). The two are physically segregated within the enclosure — PSU on the left, DC components on the right. AC and DC cable glands exit on opposite sides of the bottom face. Do not route AC and DC wiring in parallel bundles.

---

## Battery Safety (LiFePO4)

LiFePO4 is the safest lithium chemistry — thermal runaway threshold above 270°C, non-flammable under normal conditions. However, a shorted 10Ah cell can deliver very high instantaneous current.

- F2 (10A, battery positive) must be the first connection made when installing the battery
- Never short the battery terminals
- The battery's built-in BMS provides cell-level over-voltage, under-voltage, and 10A overcurrent protection
- Do not charge with a voltage above 14.4V — the PSU is set to 13.3V and the BMS OVP ceiling is 14.4–14.6V

> **Correction (2026-10-16).** The "BMS OVP ceiling" in the last bullet is the **charge voltage** printed on the Cyclenbatt label [owner, 2026-09-21], not the BMS over-voltage cutoff. Neither the label nor any document in this repo gives the cutoff, so its value is unknown; a BMS normally trips above the charge range it is rated for [I; falsifier: a Cyclenbatt document that puts the cutoff inside 14.4–14.6 V]. The planned top-off procedure charges the pack to 14.6 V on a Dylannet P20 and then holds it at 14.40 V, both inside the label's range ([top-off design](../Top-Off-Charger/top-off-charger-design.md), RQ-10); the 14.4 V limit above predates that plan.

---

## Fire Safety

Overall fire risk is low: ~10W total heat dissipation at typical load, ABS flame-retardant enclosure (self-extinguishing), LiFePO4 chemistry, and multiple over-voltage protection layers.

Warning signs requiring immediate power-off and investigation:

- Battery swelling or bulging
- Unusual chemical or burning odor
- Enclosure surface temperature above normal (warm to the touch is expected; hot is not)
- Discoloration of wiring or components visible through the enclosure lid

---

## Installation Notes

- Indoor, climate-controlled installation only. This design is rated IP65 but is not intended for outdoor or high-humidity environments.
- The enclosure should not be installed in direct sunlight or near heat sources. Rated operating range for all components is −30°C to +70°C; the 63–75°F (17–24°C) residential environment is well within spec.
- Do not install above the battery — cable gland entry is at the bottom of the enclosure.
- The Victron BP-65 manual specifies installation within 50cm of the battery. The enclosure layout satisfies this requirement.
