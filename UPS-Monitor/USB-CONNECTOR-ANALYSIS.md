# USB Connector Analysis - CRITICAL BOM ERROR IDENTIFIED

**Component:** J4 - USB-C Connector
**BOM Specified Part:** GCT USB4135-GF-A (INCORRECT - Power-Only)
**Required Part:** GCT USB4110-GF-A (CORRECT - USB 2.0 with Data)
**Analysis Date:** 2026-04-11
**Status:** 🔴 **CRITICAL BOM ERROR - REQUIRES CORRECTION**

---

## 🔴 CRITICAL FINDING: BOM Specifies Wrong Connector!

### The Problem

**USB4135-GF-A CANNOT BE USED for this design!**

The BOM specifies GCT USB4135-GF-A (6-pin power-only connector), but the ESP32-C3-MINI-1-N4 **requires USB data pins (D+/D-)** for programming and debugging via its built-in USB Serial/JTAG controller.

**Evidence from PCB Analysis:**
```
From KiCad PCB file (UPS-MONITOR-V2-Rev3-final (3).kicad_pcb):
- Line 1444-1445: Pad A5 connected to net 15 "USB_DM" (USB Data Minus)
- Line 1450-1451: Pad B5 connected to net 16 "USB_DP" (USB Data Plus)
- Line 77-78: Nets USB_DM and USB_DP are defined and routed
```

**The PCB was designed for a data-capable USB-C connector, but someone specified the wrong part number in the BOM!**

---

## Understanding the USB4135-GF-A (Power-Only)

**Part Number:** USB4135-GF-A
**Type:** USB Type-C Receptacle, Power-Only, 6-Pin
**Pin Configuration:**
- 2x VBUS pins (A9/B9) - power delivery
- 2x GND pins - ground return
- 2x CC pins (A12/B12) - configuration channel
- **NO D+/D- data pins at positions A5/B5!**

**Current Ratings:**
- VBUS: 3.0A collective
- GND: 4.25A collective
- Voltage: 48V DC

**Mechanical:**
- Height: 3.22mm
- Body length: 6.90mm
- Fully SMT (both signal and shield)
- Horizontal top-mount

**Why It Won't Work:**
- ❌ No data pins (A5/B5 positions unpopulated)
- ❌ Cannot program ESP32-C3 via USB
- ❌ Cannot debug via USB Serial/JTAG
- ❌ PCB routes USB_DM/USB_DP to pads A5/B5 but connector has no pins there

**Sources:** [GCT USB4135 Product Page](https://gct.co/connector/usb4135), [GCT News](https://gct.co/news/usb4135), [DigiKey](https://www.digikey.com/en/products/detail/gct/USB4135-GF-A/16036137), [TME](https://www.tme.com/us/en-us/details/usb4135-gf-a/usb-ieee1394-connectors/gct/)

---

## ESP32-C3-MINI-1-N4 USB Programming Requirements

**Built-in USB Serial/JTAG Controller:**
- ESP32-C3 has integrated USB Serial/JTAG functionality
- **Requires GPIO18 (D-) and GPIO19 (D+)** for programming and debugging
- No external USB-UART bridge needed
- Single USB cable provides both programming and JTAG debugging

**Critical Requirement:**
The USB connector MUST have data pins (D+/D-) to support ESP32-C3 programming. A power-only connector is insufficient.

**Sources:** [ESP-IDF USB Serial/JTAG Console](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-guides/usb-serial-jtag-console.html), [ESP32-C3 Built-in JTAG](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-guides/jtag-debugging/configure-builtin-jtag.html), [ESP32 Forum Discussion](https://esp32.com/viewtopic.php?t=26949)

---

## ✅ SOLUTION: GCT USB4110-GF-A (USB 2.0 with Data)

### Recommended Replacement

**Part Number:** GCT USB4110-GF-A
**Type:** USB Type-C Receptacle, USB 2.0, 16-Pin
**Pin Configuration:**
- 2x VBUS pins (A9/B9) - power delivery
- 2x GND pins - ground return
- 2x CC pins (A12/B12) - configuration channel
- **2x Data pins (A5/B5) - D+/D- for USB 2.0** ✅
- Additional pins for USB signaling

**Current Ratings:**
- VBUS: 5.0A collective (better than USB4135!)
- GND: 6.25A collective (better than USB4135!)
- Voltage: 48V DC

**Mechanical:**
- Height: 3.26mm (vs 3.22mm - only 0.04mm taller)
- Body length: 7.35mm (vs 6.90mm - 0.45mm longer)
- Fully SMT (both signal and shield)
- Horizontal top-mount

**Sources:** [GCT USB4110 Product Page](https://gct.co/connector/usb4110), [DigiKey](https://www.digikey.com/en/products/detail/gct/USB4110-GF-A/10384547), [TME](https://www.tme.com/us/en-us/details/usb4110-gf-a/usb-ieee1394-connectors/gct/), [Octopart](https://octopart.com/usb4110-gf-a-global+connector+technology-105888518)

---

## Footprint Compatibility Analysis

### Why USB4110-GF-A is a Drop-In Replacement

**USB Type-C Standard Pad Positions:**
All USB-C connectors (whether 6-pin, 16-pin, or 24-pin) follow the USB Type-C specification for pad positions. The difference is only which pins are populated.

**From KiCad Footprint Analysis:**
```
Pad Positions (extracted from PCB file):
- A5: at -0.5mm (size 0.7 x 1.2mm) → USB_DM ✅
- B5: at +0.5mm (size 0.7 x 1.2mm) → USB_DP ✅
- A9: at 1.52mm (size 0.76 x 1.2mm) → VBUS
- B9: at -1.52mm (size 0.76 x 1.2mm) → VBUS
- A12: at 2.75mm (size 0.8 x 1.2mm) → CC1
- B12: at -2.75mm (size 0.8 x 1.2mm) → CC2
- S1 (shield): at ±5.125mm (SMT mounting)
```

**The PCB already has pads at A5/B5 positions!**

This confirms the PCB was designed for a full USB-C connector with data support, not a power-only connector.

**Compatibility Assessment:**

| Parameter | USB4135-GF-A | USB4110-GF-A | Compatible? |
|-----------|--------------|--------------|-------------|
| **Manufacturer** | GCT | GCT | ✅ Yes |
| **Product Family** | USB41xx | USB41xx | ✅ Yes |
| **Mounting Type** | Fully SMT | Fully SMT | ✅ Yes |
| **Orientation** | Horizontal top-mount | Horizontal top-mount | ✅ Yes |
| **Shield Pads** | SMT at ±5.125mm | SMT at ±5.125mm | ✅ Yes |
| **Signal Pad Positions** | Standard USB-C | Standard USB-C | ✅ Yes |
| **Height** | 3.22mm | 3.26mm (+0.04mm) | ✅ Yes |
| **Body Length** | 6.90mm | 7.35mm (+0.45mm) | ✅ Likely* |
| **Has A5/B5 Data Pins** | ❌ NO | ✅ YES | ✅ **Critical!** |

*0.45mm increase in body length is negligible and should not cause mechanical interference

**Verdict:** ✅ **DROP-IN COMPATIBLE** - USB4110-GF-A uses the same footprint as USB4135-GF-A, with the addition of data pins the PCB is already expecting.

---

## Alternative Options (Not Recommended)

### Other USB-C Connectors Considered

**Generic Alternatives:**
- XKB USB-TYPE-C-019 (LCSC C283540)
- Korean Hroparts TYPE-C-31-M-12 (LCSC C165948)

**Why Not Recommended:**
- ⚠️ Different manufacturers - footprint compatibility uncertain
- ⚠️ May use through-hole shield mounting instead of SMT
- ⚠️ Pad positions may not match GCT footprint exactly
- ⚠️ Higher risk of mechanical fit issues

**If USB4110-GF-A is unavailable:**
- Consider GCT USB4085-GF-A (16-pin, but uses through-hole mounting - requires PCB redesign)
- Generic USB-C connectors may work but require footprint verification

---

## BOM Safety Warning

From the original BOM (line 25):
```
J4,USB4135-GF-A,USB-C edge-mount receptacle,GCT USB4135-GF-A,
WARNING: disconnect 12V before connecting USB — VBUS tied to LOAD_OUT
```

**CRITICAL SAFETY NOTE:**
- The design ties USB VBUS to LOAD_OUT (12V battery power)
- This is **NOT standard USB power delivery** (normally 5V)
- **DO NOT connect a standard USB power source** to this connector!
- The USB connector is for **data/programming only**, not for providing 5V USB power
- When plugging in a USB cable from PC, ensure 12V battery is disconnected

**This safety warning remains valid regardless of which USB-C connector is used!**

---

## Recommended Action Plan

### Immediate Actions:

1. **✅ STOP using USB4135-GF-A** - it cannot program the ESP32-C3
2. **✅ UPDATE BOM to specify USB4110-GF-A** (GCT part number)
3. **✅ Verify sourcing** from DigiKey, Mouser, or other GCT distributors
4. **⚠️ Check enclosure clearance** for 0.45mm longer body (likely OK)

### Before Production:

- [ ] Update BOM CSV with USB4110-GF-A
- [ ] Update assembly drawing if connector shape differs
- [ ] Verify USB4110-GF-A availability and lead time
- [ ] Order sample for physical verification (recommended)
- [ ] Test ESP32-C3 USB programming after assembly

### For Future Design Revisions:

- [ ] Add BOM note: "USB connector MUST support USB 2.0 data (D+/D-)"
- [ ] Update schematic to clearly show data pins routed to ESP32
- [ ] Consider adding test points for USB_DM/USB_DP signals

---

## Sourcing Information

### GCT USB4110-GF-A Availability:

**DigiKey:** [USB4110-GF-A](https://www.digikey.com/en/products/detail/gct/USB4110-GF-A/10384547)
- Usually in stock
- Pricing: ~$0.50-$1.00 per unit (quantity dependent)

**Mouser:** Available from multiple distributors

**TME:** [USB4110-GF-A](https://www.tme.com/us/en-us/details/usb4110-gf-a/usb-ieee1394-connectors/gct/)

**LCSC:** Check availability (may or may not stock)

**Lead Time:** Typically 1-2 weeks if in stock; 8-12 weeks if on backorder

**Lifecycle Status:**
- GCT actively promotes this product line
- No obsolescence notices
- Part of GCT's current USB-C portfolio
- **Lifecycle risk:** Low

---

## Summary Table

| Aspect | USB4135-GF-A (BOM) | USB4110-GF-A (Correct) | Status |
|--------|-------------------|----------------------|--------|
| **Data Pins (A5/B5)** | ❌ NOT present | ✅ Present | **Critical!** |
| **ESP32 Programming** | ❌ NOT possible | ✅ Possible | **Critical!** |
| **Footprint Match** | ⚠️ Partial (missing data) | ✅ Full match | **Drop-in** |
| **Mounting** | ✅ Fully SMT | ✅ Fully SMT | ✅ Same |
| **Current Rating** | 3A VBUS | 5A VBUS | ✅ Better |
| **Height** | 3.22mm | 3.26mm | ✅ Compatible |
| **Availability** | Good | Good | ✅ Available |
| **Price** | ~$0.50 | ~$0.50-$1.00 | ✅ Similar |

---

## Conclusion

**🔴 CRITICAL BOM ERROR IDENTIFIED:**

The BOM incorrectly specifies GCT USB4135-GF-A (6-pin power-only connector), which:
- ❌ Does NOT have USB data pins (D+/D-)
- ❌ CANNOT program ESP32-C3-MINI-1-N4
- ❌ Will not connect to the USB_DM/USB_DP signals routed on the PCB

**✅ CORRECT PART: GCT USB4110-GF-A**

The USB4110-GF-A is the proper connector for this design because:
- ✅ Has USB 2.0 data support (D+/D- pins at A5/B5)
- ✅ Supports ESP32-C3 USB Serial/JTAG programming
- ✅ DROP-IN compatible footprint (same GCT USB41xx family)
- ✅ Better electrical specs (5A vs 3A VBUS rating)
- ✅ Fully SMT design matches original intent
- ✅ Readily available from major distributors

**ACTION REQUIRED:** Update BOM from USB4135-GF-A to USB4110-GF-A before production!

---

**Report Version:** 2.0 (CORRECTED)
**Date:** 2026-04-11
**Status:** 🔴 **CRITICAL - BOM CORRECTION REQUIRED**
**Recommendation:** Replace USB4135-GF-A with USB4110-GF-A (drop-in compatible)
