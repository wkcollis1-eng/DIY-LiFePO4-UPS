# UPS Monitor V2 Rev3 - Component Sourcing Guide

## Overview

This document provides detailed sourcing information and alternative component options for the UPS Monitor V2 Rev3 design. The goal is to maintain the original board design while providing flexibility for component procurement, particularly for PCB assembly services in China (e.g., PCBWay, JLCPCB).

**Document Version:** 1.0
**PCB Revision:** Rev3
**Last Updated:** 2026-04-11

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

### 1. WAGO 2060-452 Terminal Blocks (J1, J2) - **HIGH PRIORITY**

**Original Specification:**
- Manufacturer: WAGO
- Part Number: 2060-452
- Type: 2-position SMD lever nut
- Pitch: 5.08mm (assumed)
- Application: J1 = Battery Input (12V), J2 = Load Output (12V)

**Issue:**
- WAGO lever nuts are European specialty components
- Limited availability in Asia
- Higher cost when imported
- Lead time concerns

**Recommended Alternatives:**

| Alternative | Manufacturer | LCSC Part# | Notes |
|------------|--------------|------------|-------|
| **KF2EDGR-5.08-2P** | Ningbo Kangnex | C73760 | Spring-cage screw terminal, widely available |
| **DG128-5.08-02P** | DIBO | C429946 | Screw terminal, good availability |

**Action Required:**
1. ⚠️ Verify WAGO 2060-452 footprint pitch (need to check datasheet)
2. ⚠️ Confirm alternative terminals have compatible pad layout
3. Test mechanical fit before committing to alternatives
4. Consider cost/benefit: WAGO premium vs. standard screw terminals

**Trade-offs:**
- **WAGO Advantages:** Tool-free connection, user-friendly, premium feel
- **Alternative Advantages:** Lower cost, better availability, proven reliability
- **Risk:** Footprint mismatch - requires verification before ordering

---

### 2. WSLT2512R0100FEA Current Shunt (R_SHUNT) - **MEDIUM PRIORITY**

**Original Specification:**
- Manufacturer: Vishay
- Part Number: WSLT2512R0100FEA
- Value: 10mΩ ±1%
- Package: WSK2512 (6332 metric)
- Type: TRUE 4-terminal Kelvin connection
- Power: 1W rated

**Issue:**
- Premium component with specific footprint
- May have availability/lead time in China

**Recommended Alternatives:**

| Alternative | Manufacturer | LCSC Part# | Notes |
|------------|--------------|------------|-------|
| **WSLP2512R0100FEA** | Vishay | C436034 | Vishay alternative series, same footprint |
| **LR2512-01R010F4** | Milliohm | C436125 | Generic 4-terminal 10mΩ shunt |
| **WSL25120R010FEA** | Vishay | C131682 | 2-terminal version - **requires footprint verification** |

**Action Required:**
1. Verify footprint compatibility for 4-terminal vs 2-terminal options
2. Confirm power dissipation requirements (original = 1W)
3. Consider accuracy requirements (INA228 accuracy depends on shunt tolerance)

**Trade-offs:**
- **4-terminal (Kelvin):** Better accuracy, eliminates trace resistance errors
- **2-terminal:** Simpler, more available, may introduce small measurement error
- **Recommendation:** Keep 4-terminal for measurement accuracy

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
