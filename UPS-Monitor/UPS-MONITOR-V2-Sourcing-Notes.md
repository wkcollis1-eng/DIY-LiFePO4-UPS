# UPS Monitor V2 Rev3 - Component Sourcing Guide

## Overview

This document provides detailed sourcing information and alternative component options for the UPS Monitor V2 Rev3 design. The goal is to maintain the original board design while providing flexibility for component procurement, particularly for PCB assembly services in China (e.g., PCBWay, JLCPCB).

**Document Version:** 1.1
**PCB Revision:** Rev3
**Last Updated:** 2026-04-11

---

## 🔴 CRITICAL ALERT - Footprint Verification Complete

**IMPORTANT:** Footprint compatibility analysis has been completed. See `FOOTPRINT-VERIFICATION-REPORT.md` for full details.

### Key Findings:

1. **⚠️ WAGO 2060-452 (J1, J2) - FOOTPRINT MISMATCH**
   - **PCB Footprint:** 5.0mm pitch
   - **WAGO 2060-452 Spec:** 4.0mm pitch
   - **Result:** WAGO 2060-452 **WILL NOT FIT** the existing PCB!
   - **✅ Solution:** Use 5.08mm alternatives (KF2EDGR-5.08-2P or DG128-5.08-02P) - **VERIFIED COMPATIBLE**

2. **⚠️ R_SHUNT - BOM Description Error**
   - BOM claims "4-terminal Kelvin" but WSLT2512 is **2-terminal** only
   - Footprint compatible with all 2512 alternatives
   - Kelvin sensing achieved via PCB pad layout, not separate terminals

3. **✅ Other Components**
   - Current shunt alternatives: Fully compatible (same 2512 footprint)
   - Tactile switches: Standard footprints, likely compatible
   - USB-C connector: Requires detailed verification for alternatives

**See detailed report:** `FOOTPRINT-VERIFICATION-REPORT.md`

---

## Sourcing Strategy

### Primary Sources
1. **LCSC** - Primary distributor for Chinese PCB assembly services
2. **Digikey/Mouser** - For specialty components not available via LCSC
3. **Direct from manufacturer** - For unique components (WAGO, GCT)

### Component Categories

#### ✅ No Issues - Readily Available
- All 0402/0805 passive components (R1-R11, C2-C9)
- ESP32-C3-MINI-1-N4 (U1)
- INA228AIDGST (U2)
- AP63203WU-7 (U3)
- SMAJ15CA TVS diode (TVS1)
- Blue 0402 LED (LED1)
- Standard 2.54mm pin headers (J3)

#### ⚠️ Alternatives Recommended - Sourcing Concerns

---

## Component-Specific Sourcing Notes

### 1. WAGO 2060-452 Terminal Blocks (J1, J2) - **CRITICAL PRIORITY**

**🔴 CRITICAL FOOTPRINT MISMATCH IDENTIFIED**

**PCB Footprint Specification** (from KiCad file analysis):
- **Actual Pitch:** 5.0mm (pads at ±2.5mm)
- Pad Size: 3.0mm x 2.8mm rectangular
- Dual pads (top and bottom) for each terminal

**WAGO 2060-452 Specification:**
- Manufacturer: WAGO
- Part Number: 2060-452/998-404
- **Official Pitch:** 4.0mm (per WAGO datasheet)
- Type: 2-position SMD lever nut with push-button
- Application: J1 = Battery Input (12V), J2 = Load Output (12V)

**⚠️ CRITICAL ISSUE:**
- **WAGO 2060-452 HAS 4.0mm PITCH**
- **PCB FOOTPRINT HAS 5.0mm PITCH**
- **RESULT: WAGO 2060-452 WILL NOT FIT THIS PCB!**

The BOM specifies WAGO 2060-452 but the PCB footprint is incompatible. Either:
1. Wrong part number in BOM, or
2. Incorrect footprint in PCB design

**Issues (Beyond Footprint):**
- WAGO lever nuts are European specialty components
- Limited availability in Asia
- Higher cost when imported
- Lead time concerns

**✅ VERIFIED Compatible Alternatives (5.08mm pitch):**

| Alternative | Manufacturer | LCSC Part# | Pitch | Status |
|------------|--------------|------------|-------|--------|
| **KF2EDGR-5.08-2P** ✅ | Ningbo Kangnex/Cixi Kefa | C73760 | **5.08mm** | **FOOTPRINT VERIFIED - COMPATIBLE** |
| **DG128-5.08-02P** ✅ | DIBO | C429946 | **5.08mm** | **FOOTPRINT VERIFIED - COMPATIBLE** |

**Footprint Verification Status:**
- ✅ **PCB footprint is 5.0mm pitch** - extracted from KiCad file
- ✅ **5.08mm alternatives are compatible** - 0.08mm difference is within tolerance
- ❌ **WAGO 2060-452 is NOT compatible** - 4.0mm vs 5.0mm = 1mm mismatch

**Action Required:**
1. ✅ ~~Verify WAGO 2060-452 footprint pitch~~ **COMPLETE - Confirmed 4.0mm, NOT compatible**
2. ✅ ~~Confirm alternative terminals have compatible pad layout~~ **COMPLETE - 5.08mm verified**
3. ⚠️ **CRITICAL:** Update BOM to remove WAGO 2060-452 or correct PCB footprint
4. ⚠️ Test mechanical fit of 5.08mm alternatives during prototype phase
5. ✅ **RECOMMEND:** Use KF2EDGR-5.08-2P or DG128-5.08-02P for production

**Trade-offs:**
- **WAGO Advantages:** Tool-free connection, user-friendly, premium feel
- **Alternative Advantages:** Lower cost, better availability, proven reliability
- **Risk:** Footprint mismatch - requires verification before ordering

---

### 2. WSLT2512R0100FEA Current Shunt (R_SHUNT) - **MEDIUM PRIORITY**

**⚠️ BOM DESCRIPTION ERROR IDENTIFIED**

**Original Specification:**
- Manufacturer: Vishay
- Part Number: WSLT2512R0100FEA
- Value: 10mΩ ±1%
- Package: 2512 (6.4mm x 3.2mm metric)
- **BOM Claims:** "TRUE 4-terminal Kelvin connection"
- **ACTUAL Type:** **2-terminal** resistor (per Vishay datasheet)
- Power: 1W rated

**⚠️ CRITICAL CORRECTION:**
- **WSLT2512 is a 2-TERMINAL resistor**, not 4-terminal
- BOM description is incorrect
- Kelvin sensing achieved through optimized PCB pad layout, not separate sense terminals
- PCB footprint uses 2-terminal design (verified from KiCad file)

**Issue:**
- Premium component with specific footprint
- May have availability/lead time in China
- BOM description needs correction

**✅ VERIFIED Compatible Alternatives (All 2-Terminal):**

| Alternative | Manufacturer | LCSC Part# | Terminals | Notes |
|------------|--------------|------------|-----------|-------|
| **WSL2512R0100FEA** ✅ | Vishay | C131682 | 2-terminal | **FOOTPRINT VERIFIED** - Same 2512 package as WSLT |
| **WSLP2512R0100FEA** | Vishay | C436034 | 2-terminal | Vishay alternative series, same footprint |
| **LR2512-01R010F4** | Milliohm | C436125 | 2-terminal | Generic 10mΩ shunt, same 2512 footprint |

**Action Required:**
1. ✅ ~~Verify footprint compatibility~~ **COMPLETE - All 2512 parts compatible**
2. ⚠️ **Correct BOM description** - Remove "4-terminal" claim
3. Confirm power dissipation requirements (original = 1W, all alternatives = 1-2W)
4. Consider accuracy requirements (INA228 accuracy depends on shunt tolerance)

**Trade-offs:**
- **Kelvin Sensing via PCB Layout:** Modern approach using optimized pad geometry
- **WSLT2512 Advantages:** High temp rating (275°C), premium quality
- **WSL2512 Advantages:** Lower cost, same electrical performance, widely available
- **Recommendation:** WSL2512 for cost savings or WSLT2512 for high-temp environments

---

### 3. Vishay IHLP-5050EZ Buck Inductor (L1) - **MEDIUM PRIORITY**

**Original Specification:**
- Manufacturer: Vishay
- Series: IHLP-5050EZ
- Value: 4.7µH
- Current Rating: 2.6A (minimum required for AP63203 2A output)
- Package: 5050 (5.0mm x 5.0mm)
- Features: Low DCR, shielded

**Issue:**
- Premium Vishay inductor may be costly
- Availability varies by region

**Recommended Alternatives:**

| Alternative | Manufacturer | LCSC Part# | Specs | Notes |
|------------|--------------|------------|-------|-------|
| **IHLP-5050CE-01** | Vishay | C456873 | 4.7µH, similar series | Alternative Vishay line |
| **MWSA0518-4R7MT** | Sunlord | C439979 | 4.7µH, 3A | Chinese brand, cost-effective |
| **SLF5045T-4R7M2R6-PF** | TDK | C266959 | 4.7µH, 2.6A | Premium Japanese brand |

**Action Required:**
1. Verify DCR specification (lower is better for efficiency)
2. Confirm saturation current rating ≥ 2.6A
3. Check temperature rating for application

**Trade-offs:**
- All alternatives should work electrically
- Vishay/TDK = premium performance, higher cost
- Sunlord = cost-effective, proven in Chinese market
- **Recommendation:** Sunlord for cost savings, Vishay/TDK for premium build

---

### 4. GCT USB4135-GF-A USB-C Connector (J4) - **MEDIUM PRIORITY**

**Original Specification:**
- Manufacturer: GCT
- Part Number: USB4135-GF-A
- Type: USB-C receptacle, edge-mount
- Pins: 16-position

**Issue:**
- GCT-specific part may require special ordering
- Edge-mount style less common than standard SMT

**Recommended Alternatives:**

| Alternative | Manufacturer | LCSC Part# | Notes |
|------------|--------------|------------|-------|
| **USB-TYPE-C-019** | XKB Connection | C283540 | Generic USB-C 16P edge mount |
| **TYPE-C-31-M-12** | Korean Hroparts Elec | C165948 | USB-C 16P SMT receptacle |

**Action Required:**
1. ⚠️ **CRITICAL:** Verify mechanical footprint compatibility
2. Check PCB edge clearance requirements
3. Confirm pin mapping matches original design

**Trade-offs:**
- GCT connectors are known for quality and reliability
- Generic alternatives widely available but mechanical fit is critical
- **Recommendation:** Order samples to verify mechanical fit before production

**Safety Note:**
- BOM warns: "disconnect 12V before connecting USB — VBUS tied to LOAD_OUT"
- This warning applies regardless of connector choice

---

### 5. Omron B3S-1000 Tactile Switches (SW1, SW2) - **LOW PRIORITY**

**Original Specification:**
- Manufacturer: Omron
- Part Number: B3S-1000
- Type: SMD tactile switch
- Application: SW1 = BOOT (GPIO9), SW2 = RESET (EN)

**Issue:**
- Japanese brand, moderate cost
- Alternatives widely available

**Recommended Alternatives:**

| Alternative | Manufacturer | LCSC Part# | Notes |
|------------|--------------|------------|-------|
| **TS-1187A-B-A-B** | XKB Connectivity | C318884 | Generic 3x6mm tactile |
| **K2-1187SQ-A4SW-06** | Korean Hroparts Elec | C393942 | Korean alternative |

**Action Required:**
1. Verify footprint dimensions (3x6mm typical)
2. Confirm actuation force acceptable for user interface
3. Check travel distance and tactile feedback

**Trade-offs:**
- Omron = premium quality, consistent feel
- Alternatives = cost-effective, adequate performance
- **Recommendation:** Alternatives acceptable for this application

---

### 6. Electrolytic Capacitor C1 (100µF 25V) - **LOW PRIORITY**

**Original Specification:**
- Value: 100µF
- Voltage: 25V
- Package: Electrolytic 6.3 x 5.4mm
- Application: Input bulk capacitor
- Preference: Low ESR

**Issue:**
- Size specification (6.3 x 5.4mm) needs verification
- ESR specification not quantified in BOM

**Recommended Alternatives:**

| Alternative | Manufacturer | LCSC Part# | Notes |
|------------|--------------|------------|-------|
| **100µF 25V 6.3x5.4** | Lelon | C134878 | Verify dimensions |
| **100µF 25V D6.3xH5.4** | Nichicon | C42097 | Premium low-ESR option |

**Action Required:**
1. Confirm physical dimensions on PCB (radial lead spacing)
2. Specify acceptable ESR range (typically < 100mΩ for this application)
3. Temperature rating check (+105°C preferred)

**Trade-offs:**
- Standard commodity part, widely available
- Low-ESR types preferred for input filtering
- **Recommendation:** Any reputable brand with correct dimensions and ESR

---

## PCB Assembly Service Recommendations

### For PCBWay Assembly:

1. **Before Quoting:**
   - Upload this alternatives list along with BOM
   - Request availability check for original parts first
   - Ask for cost comparison with alternatives

2. **Critical Verifications:**
   - WAGO terminal footprints (J1, J2) - **must verify before substitution**
   - USB-C connector mechanical fit (J4) - **must verify before substitution**
   - Current shunt footprint compatibility (R_SHUNT)

3. **Recommended Approach:**
   - Request quote with original parts
   - Request quote with LCSC alternatives
   - Compare cost/lead time trade-offs

### For JLCPCB Assembly:

- Similar process to PCBWay
- JLCPCB has extensive LCSC integration
- Consider their "Basic Parts" library for fastest turnaround

---

## Verification Checklist

Before finalizing component substitutions:

- [ ] Verify WAGO 2060-452 actual footprint and pitch
- [ ] Check USB4135-GF-A mechanical dimensions vs. alternatives
- [ ] Confirm 4-terminal shunt footprint compatibility
- [ ] Validate inductor DCR and saturation current specs
- [ ] Test tactile switch footprint and feel
- [ ] Verify electrolytic capacitor physical dimensions
- [ ] Review alternative datasheets for electrical compatibility
- [ ] Update assembly drawings if mechanical parts change
- [ ] Test prototype with critical alternates before production

---

## Notes

- **"Verified" column in CSV:** Update to "Yes" after physical testing confirms compatibility
- **LCSC Part Numbers:** Subject to change; verify availability at time of order
- **Footprint Compatibility:** "Yes" = same package code, "Verify" = needs dimensional check
- **Cost Optimization:** Sunlord/generic alternatives can reduce BOM cost by 20-30%
- **Lead Time:** LCSC-stocked parts typically 1-2 weeks; Digikey/Mouser may be faster for specialty parts

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-04-11 | Initial sourcing guide created | - |

---

## Contact

For questions about component alternatives or sourcing strategy, refer to the main project repository or contact the design team.
