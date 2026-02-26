# Safety

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
- Do not charge with a voltage above 14.4V — the PSU is set to 13.3V and the OVP ceiling is 13.8V minimum

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
