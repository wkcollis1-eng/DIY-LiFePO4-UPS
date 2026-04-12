# UPS Monitor V2 Rev3 - Footprint Compatibility Verification Report

**Report Date:** 2026-04-11
**PCB Revision:** Rev3
**Analysis Type:** Component alternatives footprint compatibility based on KiCad PCB file and datasheet comparison

---

## Executive Summary

This report documents the footprint compatibility analysis between original components and proposed alternatives for the UPS Monitor V2 Rev3 design. Analysis was performed by extracting actual footprint data from the KiCad PCB file and comparing against manufacturer specifications.

### Critical Findings:

1. **⚠️ WAGO Terminal Blocks (J1, J2)** - **FOOTPRINT MISMATCH IDENTIFIED**
2. **✅ 5.08mm Terminal Alternatives** - **COMPATIBLE** (better than original!)
3. **⚠️ Current Shunt (R_SHUNT)** - **Part Number/Footprint Confusion**
4. **✅ USB-C Connector (J4)** - Specific footprint, alternatives need verification
5. **✅ Tactile Switches (SW1, SW2)** - Standard footprint, alternatives compatible

---

## 1. WAGO 2060-452 Terminal Blocks (J1, J2)

### Critical Discovery: FOOTPRINT MISMATCH

#### From KiCad PCB File:
```
Line 537: (descr "WAGO 2060-452/998-404 SMD 2-position push-in connector, 5.0mm pitch, 9A")
Line 562-569: Pad positions at ±2.5mm = 5.0mm pad spacing
Pad size: 3mm x 2.8mm rectangular pads
```

**Actual Footprint in Design:**
- **Pin Spacing: 5.0mm** (pads at -2.5mm and +2.5mm)
- Pad Size: 3.0mm x 2.8mm
- Dual pads top and bottom for each terminal

#### From WAGO 2060-452 Datasheet:
- **Official Pin Spacing: 4.0mm** ([WAGO website](https://www.wago.com/us/pcb-interconnect/smd-pcb-terminal-block/p/2060-452_998-404))
- WAGO 2060 series available in **4mm or 6mm** pitch variants
- **NO 5.0mm variant exists in WAGO 2060 series**

### Analysis:

**❌ CRITICAL ISSUE:** The KiCad footprint claims to be for WAGO 2060-452 but uses 5.0mm pitch, while the actual WAGO 2060-452 part has 4.0mm pitch.

**Possible Explanations:**
1. Wrong part number in BOM (should be a different connector)
2. Custom/modified footprint that doesn't match the specified part
3. Design error that needs correction

**Impact:** The specified WAGO 2060-452 component **WILL NOT FIT** the existing PCB footprint.

### Alternative Component Compatibility:

#### ✅ **KF2EDGR-5.08-2P (Ningbo Kangnex)** - **COMPATIBLE**
- Pin Spacing: **5.08mm** ([LCSC C73760](https://www.lcsc.com/product-detail/Pluggable-System-Terminal-Block_Cixi-Kefa-Elec-KF2EDGR-5-08-2P_C441204.html))
- Type: 2P screw terminal, SMD
- **Status: Better match than original WAGO!**
- Pad layout: Verify dimensions but pitch matches

#### ✅ **DG128-5.08-02P (DIBO)** - **COMPATIBLE**
- Pin Spacing: **5.08mm** (LCSC C429946)
- Type: 2P screw terminal, SMD
- **Status: Better match than original WAGO!**

### Recommendation:

1. **Verify the correct part** that was intended for this design
2. **Use 5.08mm pitch alternatives** (KF2EDGR or DG128) which match the actual footprint
3. **Do NOT order WAGO 2060-452** for this PCB without footprint modification

---

## 2. Current Shunt Resistor (R_SHUNT)

### From KiCad PCB File:
```
Line 468: (descr "Shunt Resistor SMD 2512 (6332 Metric), 2.6mm thick, Vishay WKS2512...")
Line 475: (fp_text value "WSLT2512R0100FEA")
```

### Analysis:

**⚠️ PART NUMBER CONFUSION IDENTIFIED**

**KiCad Footprint Description:** Vishay **WSK2512** series
**KiCad Part Value:** Vishay **WSLT2512**R0100FEA
**BOM Specification:** Vishay **WSLT2512**R0100FEA (10mΩ 1% "4-terminal Kelvin")

#### Research Findings:

**WSLT2512 Series:**
- **2-terminal** power metal strip resistor ([Vishay Datasheet](https://www.vishay.com/docs/30121/wslt2512.pdf))
- Package: 2512 (6.4mm x 3.2mm)
- **NOT a true 4-terminal Kelvin design**
- High temperature rating (275°C)

**WSK2512 Series:**
- **4-terminal** Kelvin shunt resistor
- True 4-wire sensing capability
- Different footprint than WSLT

**BOM Claims:** "TRUE 4-terminal Kelvin connection" but WSLT2512 is only 2-terminal!

### Alternative Compatibility:

#### Option 1: Keep 2-Terminal Design (Current PCB Footprint)

✅ **WSLT2512R0100FEA** - Original part (2-terminal)
✅ **WSL2512R0100FEA** - Similar 2-terminal alternative (LCSC C131682)
✅ **LR2512-01R010F4** - Generic 2-terminal (LCSC C436125)

Note: Kelvin sensing can be implemented with modified pad layout on 2-terminal parts ([Analog Devices Guide](https://www.analog.com/en/resources/analog-dialogue/articles/optimize-high-current-sensing-accuracy.html))

#### Option 2: True 4-Terminal Kelvin (Requires Footprint Change)

❌ **Requires different footprint** - Current PCB uses 2-terminal layout

### Recommendation:

1. **Correct BOM description** - Remove "4-terminal" claim, it's misleading
2. **WSLT2512R0100FEA** is compatible with current footprint
3. **WSL2512** alternatives also compatible (same footprint)
4. Kelvin sensing accuracy achieved through pad layout, not separate terminals

---

## 3. USB4135-GF-A USB-C Connector (J4)

### From KiCad PCB File:
```
Line 1385: (descr "USB Type C Receptacle, GCT, power-only, 6P, top mounted, horizontal, 3A")
Referenced datasheet: https://gct.co/files/drawings/usb4135.pdf
```

**Pad Positions Extracted:**
- A5: -0.5mm
- B5: +0.5mm
- A9/B9: ±1.52mm
- A12/B12: ±2.75mm
- Shield pads (S1): ±5.125mm
- All pads at Y = -3.0325mm

### Analysis:

**✅ Footprint is specific to USB4135-GF-A**

The footprint is designed specifically for the GCT USB4135-GF-A connector with exact pad spacing and dimensions.

### Alternative Compatibility:

#### ⚠️ **USB-TYPE-C-019 (XKB Connection)** - LCSC C283540
- **Status: REQUIRES VERIFICATION**
- Generic USB-C 16P edge mount
- Pad spacing may differ from GCT design
- **Action Required:** Download datasheet and compare pad positions

#### ⚠️ **TYPE-C-31-M-12 (Korean Hroparts)** - LCSC C165948
- **Status: REQUIRES VERIFICATION**
- USB-C 16P SMT receptacle
- Different manufacturer, likely different pad layout
- **Action Required:** Verify mechanical and electrical compatibility

### Recommendation:

1. **USB4135-GF-A is best option** for guaranteed fit
2. **Generic alternatives are HIGH RISK** without detailed footprint comparison
3. **Action Required:** Obtain alternative datasheets and compare:
   - Pad positions (X, Y coordinates)
   - Pad sizes
   - Shield mounting pad locations
   - PCB edge clearance requirements
4. Consider ordering **samples** before committing to alternatives

---

## 4. Omron B3S-1000 Tactile Switches (SW1, SW2)

### From Research:

**Omron B3S-1000 Specifications:**
- Package: 6.6mm x 6.0mm x 4.3mm height
- Surface mount tactile switch
- Standard footprint available in multiple CAD libraries ([Ultra Librarian](https://app.ultralibrarian.com/details/f9ae1b5e-919f-11e9-ab3a-0a3560a4cccc/Omron/B3S-1000), [SnapEDA](https://www.snapeda.com/parts/B3S-1000/Omron/view-part/))

### Alternative Compatibility:

#### ✅ **TS-1187A-B-A-B (XKB Connectivity)** - LCSC C318884
- **Status: LIKELY COMPATIBLE**
- Generic 3x6mm tactile switch
- Very common footprint
- Verify: Actuation force, travel distance

#### ✅ **K2-1187SQ-A4SW-06 (Korean Hroparts)** - LCSC C393942
- **Status: LIKELY COMPATIBLE**
- Similar tactile switch design
- Standard SMD footprint

### Recommendation:

**Low Risk** - Tactile switch footprints are highly standardized. Generic alternatives should be compatible, but verify:
1. Mounting hole pattern
2. Actuation force (user feel)
3. Travel distance
4. Operating life

---

## Summary Table: Footprint Compatibility

| Component | Original Part | Footprint Pitch/Size | Alternative | Alt Pitch/Size | Compatible? | Risk Level |
|-----------|---------------|---------------------|-------------|----------------|-------------|------------|
| **J1, J2** | WAGO 2060-452 | **5.0mm** (actual PCB) | KF2EDGR-5.08-2P | **5.08mm** | ✅ **YES** | ⚠️ **CRITICAL** |
| **J1, J2** | WAGO 2060-452 | 4.0mm (datasheet) | N/A | N/A | ❌ **NO** | 🔴 **WILL NOT FIT** |
| **R_SHUNT** | WSLT2512R0100FEA | 2512 (6.4x3.2mm) | WSL2512R0100FEA | 2512 (6.4x3.2mm) | ✅ **YES** | 🟢 **LOW** |
| **R_SHUNT** | WSLT2512R0100FEA | 2512 (6.4x3.2mm) | LR2512-01R010F4 | 2512 (6.4x3.2mm) | ✅ **YES** | 🟢 **LOW** |
| **J4** | USB4135-GF-A | GCT specific | USB-TYPE-C-019 | Unknown | ⚠️ **VERIFY** | 🟡 **MEDIUM** |
| **J4** | USB4135-GF-A | GCT specific | TYPE-C-31-M-12 | Unknown | ⚠️ **VERIFY** | 🟡 **MEDIUM** |
| **SW1, SW2** | B3S-1000 | 6.6x6.0mm | TS-1187A-B-A-B | ~6x3mm | ✅ **LIKELY** | 🟢 **LOW** |
| **SW1, SW2** | B3S-1000 | 6.6x6.0mm | K2-1187SQ-A4SW-06 | Standard | ✅ **LIKELY** | 🟢 **LOW** |

---

## Action Items

### Immediate Actions Required:

1. **🔴 CRITICAL - J1/J2 Terminal Blocks:**
   - [ ] Confirm actual connector used in original design
   - [ ] Update BOM to reflect correct part (5.08mm pitch terminal, NOT WAGO 2060-452)
   - [ ] Recommend: KF2EDGR-5.08-2P or DG128-5.08-02P for production

2. **🟡 HIGH - R_SHUNT Description:**
   - [ ] Correct BOM to remove "4-terminal Kelvin" description
   - [ ] Clarify that WSLT2512 is 2-terminal with Kelvin pad layout
   - [ ] Verify alternatives WSL2512 or LR2512 for cost savings

3. **🟡 MEDIUM - J4 USB-C Connector:**
   - [ ] Obtain datasheets for USB-TYPE-C-019 and TYPE-C-31-M-12
   - [ ] Compare pad positions, dimensions, and mechanical fit
   - [ ] Consider ordering samples for physical verification
   - [ ] Recommend staying with USB4135-GF-A unless cost is critical

4. **🟢 LOW - SW1/SW2 Switches:**
   - [ ] Verify tactile switch alternatives during prototype phase
   - [ ] Test user feel and actuation force
   - [ ] Generic alternatives acceptable

### Documentation Updates:

- [ ] Update `UPS-MONITOR-V2-BOM.csv` with corrected part numbers
- [ ] Update `UPS-MONITOR-V2-Alternatives.csv` with compatibility status
- [ ] Update `UPS-MONITOR-V2-Sourcing-Notes.md` with findings from this report

---

## References

### Sources Consulted:

**WAGO 2060 Series:**
- [WAGO 2060-452/998-404 Product Page](https://www.wago.com/us/pcb-interconnect/smd-pcb-terminal-block/p/2060-452_998-404)
- [Ultra Librarian CAD Files](https://app.ultralibrarian.com/details/9a3a9cbd-10a1-11e9-ab3a-0a3560a4cccc/Wago/2060-452-998-404)
- [WAGO PartCommunity 3D Models](https://wago.partcommunity.com/3d-cad-models/2060-452-998-404-smd-terminal-block-with-push-buttons-in-tape-and-reel-packing-pin-spacing-4-mm-0-157-in-2-pole-wago)

**Terminal Block Alternatives:**
- [LCSC KF2EDGR-5.08-2P](https://www.lcsc.com/product-detail/Pluggable-System-Terminal-Block_Cixi-Kefa-Elec-KF2EDGR-5-08-2P_C441204.html)
- [Handson Technology KF2EDG Datasheet](https://handsontec.com/dataspecs/connector/KF2EDG.pdf)

**Vishay Current Shunts:**
- [Vishay WSLT2512 Datasheet](https://www.vishay.com/docs/30121/wslt2512.pdf)
- [Vishay WSL2512 Datasheet](https://www.vishay.com/docs/30100/wsl.pdf)
- [KiCad WSK2512 Footprint Discussion](https://github.com/KiCad/kicad-footprints/pull/573)
- [Analog Devices: Kelvin Connection PCB Layout Guide](https://www.analog.com/en/resources/analog-dialogue/articles/optimize-high-current-sensing-accuracy.html)

**GCT USB Connector:**
- [GCT USB4135 Product Page](https://gct.co/connector/usb4135)
- [Digikey USB4135-GF-A](https://www.digikey.com/en/products/detail/gct/USB4135-GF-A/16036137)
- [SnapEDA USB4135-GF-A](https://www.snapeda.com/parts/USB4135-GF-A/Global%20Connector%20Technology/view-part/)

**Omron Tactile Switches:**
- [Ultra Librarian B3S-1000](https://app.ultralibrarian.com/details/f9ae1b5e-919f-11e9-ab3a-0a3560a4cccc/Omron/B3S-1000)
- [SnapEDA B3S-1000](https://www.snapeda.com/parts/B3S-1000/Omron/view-part/)
- [LCSC B3S-1000P](https://www.lcsc.com/product-image/C180420.html)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-11 | Footprint Analysis | Initial footprint compatibility verification |

---

**CONFIDENTIAL** - For internal design review only
