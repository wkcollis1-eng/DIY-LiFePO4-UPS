# Design Specification

This document formalizes the engineering requirements, design decisions, and verification methods for the DIY LiFePO4 UPS system.

---

## 1. Requirements

### 1.1 Functional Requirements

| ID | Requirement | Priority | Rationale |
|---|---|---|---|
| FR-1 | Provide uninterrupted 12V DC power to Home Assistant Green and Xfinity XB7 modem during grid outages | Must | Primary system purpose |
| FR-2 | Switchover time shall be <1ms | Must | Prevent modem reboot on power transition |
| FR-3 | Runtime shall exceed 6 hours at typical load | Should | Outlast majority of residential outages |
| FR-4 | Battery shall automatically charge when grid power is available | Must | Hands-free operation |
| FR-5 | System shall report battery voltage and temperature to Home Assistant | Should | Enable monitoring and automated shutdown |
| FR-6 | System shall disconnect loads before battery damage occurs | Must | Protect battery from deep discharge |

### 1.2 Electrical Requirements

| ID | Requirement | Specification | Rationale |
|---|---|---|---|
| ER-1 | Output voltage range | 11.74–13.26V at device terminals | Within inferred ±10% tolerance of 12V nominal devices |
| ER-2 | Typical load capacity | ≥15W continuous | Combined device load is 13.8W typical |
| ER-3 | Peak load capacity | ≥20W for 5 seconds | Accommodate simultaneous device peak (18.67W) |
| ER-4 | Low-voltage disconnect | 11.8V ± 0.1V | Prevent battery damage while maximizing runtime |
| ER-5 | Reconnect threshold | 12.8V ± 0.1V | Ensure adequate charge before reconnecting loads |
| ER-6 | Float voltage | 13.3V ± 0.1V | Match LiFePO4 resting voltage to minimize calendar aging |

### 1.3 Safety Requirements

| ID | Requirement | Implementation | Rationale |
|---|---|---|---|
| SR-1 | Battery circuit shall have primary fuse protection | F2: 10A fast-blow at battery positive | Protect against short circuit |
| SR-2 | Each load circuit shall have individual fuse protection | F3: 2A (HA Green), F4: 5A (XB7) | Isolate faults to single load |
| SR-3 | Battery shall have BMS with OVP/UVP/OCP | Cyclenbatt built-in 10A BMS | Secondary protection layer |
| SR-4 | System shall prevent reverse current to PSU | MOSFET ideal diode | Protect PSU from battery backfeed |
| SR-5 | Enclosure shall be IP65 rated | LeMotech ABS junction box | Dust/water ingress protection |

### 1.4 Reliability Requirements

| ID | Requirement | Target | Rationale |
|---|---|---|---|
| RR-1 | Battery lifespan | ≥7 years | Exceed commercial UPS 2–3 year SLA lifespan |
| RR-2 | PSU MTBF | >500,000 hours | Industrial-grade reliability |
| RR-3 | System availability | >99.9% | Critical home infrastructure |

---

## 2. Design Decisions

### 2.1 Architecture Selection

**Decision:** DC-buffer topology with direct battery feed (no DC-DC converter)

**Alternatives Considered:**
1. Line-interactive UPS topology (commercial approach)
2. DC-buffer with regulated DC-DC output

**Selection Rationale:**
- Eliminates 4–10ms switchover delay inherent in line-interactive designs
- Avoids 2.8W continuous DC-DC conversion losses
- Device terminal voltage (11.74–13.26V) remains within inferred tolerance
- Reduces component count and failure points

**Trade-offs Accepted:**
- Output voltage tracks battery state rather than fixed regulation
- Relies on device tolerance of ±10% (inferred, not manufacturer-guaranteed)

### 2.2 Float Charging Strategy

**Decision:** Fixed 13.3V float voltage matching LiFePO4 resting voltage

**Alternatives Considered:**
1. Traditional 13.8–14.0V absorption charging
2. Active charge controller with CV/CC stages

**Selection Rationale:**
- 13.3V matches natural LiFePO4 resting voltage at 100% SoC
- Near-zero current flow at equilibrium minimizes calendar aging
- Eliminates charge controller cost and complexity
- PSU trimmer adjustment provides adequate precision (±0.1V)

**Trade-offs Accepted:**
- No active charge current limiting (unnecessary at equilibrium)
- PSU must maintain calibration over time (lacquered trimmer, 3–5 mV/year drift)

### 2.3 Low-Voltage Disconnect

**Decision:** Victron BatteryProtect BP-65 (MOSFET-based, programmable)

**Alternatives Considered:**
1. Relay-based LVD module (Noyito)
2. Software-only shutdown via Home Assistant

**Selection Rationale:**
- MOSFET switching: 0.006V drop vs 0.130V relay contact drop
- 1.5mA quiescent vs 730mW relay coil power
- 90-second hold-off prevents false trips on transient sag
- 30-second reconnect delay prevents rapid cycling
- Programmable via Bluetooth (VictronConnect app)
- IP67 potted electronics, no calibration drift

**Trade-offs Accepted:**
- Higher cost (~$25 premium over relay module)
- Requires Bluetooth app for configuration changes

### 2.4 Monitoring Integration

**Decision:** Shelly Plus Uni with ADC voltage sensing and DS18B20 temperature probe

**Alternatives Considered:**
1. INA219 current/voltage sensor via I2C
2. Victron SmartShunt with VE.Direct
3. No monitoring (manual checks only)

**Selection Rationale:**
- Native Home Assistant integration via WiFi
- ADC sufficient for voltage-based SoC estimation on LiFePO4 flat discharge curve
- DS18B20 provides temperature monitoring for thermal alerts
- Lower cost than Victron SmartShunt
- No additional hardware interface required

**Trade-offs Accepted:**
- Voltage-based SoC less accurate than coulomb counting
- Requires WiFi connectivity (acceptable for home network device)

---

## 3. Verification Matrix

### 3.1 Requirement Verification

| Req ID | Verification Method | Acceptance Criteria | Status |
|---|---|---|---|
| FR-1 | Functional test | Both devices operate continuously during simulated outage | Pending |
| FR-2 | Oscilloscope measurement | Switchover transient <1ms, no voltage dropout below 11.5V | Pending |
| FR-3 | Timed discharge test | Runtime ≥6 hours at measured typical load | Pending (calculated: 8.2h) |
| FR-4 | Current measurement | Charge current tapers to <50mA at float equilibrium | Pending |
| FR-5 | HA dashboard verification | Voltage and temperature readings update every 30 seconds | Pending |
| FR-6 | Discharge test | BP-65 disconnects loads at 11.8V ± 0.1V | Pending |
| ER-1 | Multimeter measurement | Measure device terminal voltage at float and LVD threshold | Pending |
| ER-2 | Load test | System stable at 15W continuous for 1 hour | Pending |
| ER-3 | Peak load test | System stable at 20W for 5 seconds, no fuse trip | Pending |
| ER-4 | Discharge test | BP-65 Setting 7 verified, disconnect at 11.8V | Pending |
| ER-5 | Charge recovery test | BP-65 reconnects after battery reaches 12.8V | Pending |
| ER-6 | Multimeter measurement | PSU output verified at 13.3V ± 0.1V | Pending |
| SR-1 | Visual inspection | F2 installed at battery positive terminal | Pending |
| SR-2 | Visual inspection | F3 and F4 installed on respective load circuits | Pending |
| SR-3 | Datasheet review | Cyclenbatt BMS specs confirmed | Complete |
| SR-4 | Functional test | No current flow from battery to PSU when AC present | Pending |
| SR-5 | Visual inspection | Enclosure sealed, cable glands installed | Pending |
| RR-1 | Analysis | Float strategy analysis supports 7–10 year estimate | Complete |
| RR-2 | Datasheet review | HDR-60-12 MTBF: 927,600 hours | Complete |

### 3.2 Calculated Performance (Pre-Build)

| Parameter | Calculated Value | Method |
|---|---|---|
| Typical load | 13.8W DC | Kill-a-Watt measurement × 82.5% efficiency |
| Peak load | 18.67W DC | Kill-a-Watt peak measurement × 82.5% efficiency |
| Runtime at typical load | 8.2 hours | 112.5Wh usable ÷ 13.8W |
| Minimum device voltage | 11.74V | 11.8V LVD − 0.063V wiring drop |
| Maximum device voltage | 13.26V | 13.3V float − 0.041V wiring drop |
| Annual electricity cost | ~$41/year | 15.7W wall draw × 8,760h × $0.30/kWh |

### 3.3 Post-Build Validation Checklist

- [ ] Verify PSU output voltage: 13.3V ± 0.1V
- [ ] Verify battery float voltage equilibrium (charge current <50mA)
- [ ] Verify device terminal voltage at float: expected ~13.26V
- [ ] Verify BP-65 Setting 7 programmed (11.8V cutoff / 12.8V reconnect)
- [ ] Simulate AC outage: verify <1ms switchover (oscilloscope or device continuity)
- [ ] Discharge test: verify BP-65 disconnects at 11.8V
- [ ] Verify device terminal voltage at LVD: expected ~11.74V
- [ ] Reconnect test: verify BP-65 reconnects after 12.8V reached
- [ ] Temperature sensor calibration: compare DS18B20 to reference thermometer
- [ ] Home Assistant integration: verify voltage and temperature display
- [ ] Full runtime test: discharge from float to LVD, record actual runtime
- [ ] Enclosure thermal test: verify internal temperature <50°C at steady state

---

## 4. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Device voltage tolerance narrower than inferred ±10% | Low | High | Verify operation at 11.74V and 13.26V before permanent installation |
| PSU trimmer drift exceeds analysis | Low | Medium | Lacquer trimmer; annual voltage verification |
| Battery capacity degradation faster than expected | Low | Medium | Monitor via Shelly ADC; replace if runtime drops below 4 hours |
| Thermal runaway in enclosed battery | Very Low | High | DS18B20 monitoring; 40°C HA alert; passive ventilation |
| Inrush current trips F4 fuse | Low | Low | BP-65 soft-start; 5A fuse I²t margin adequate for capacitive inrush |
| WiFi connectivity loss prevents monitoring | Medium | Low | BP-65 provides hardware LVD independent of monitoring |

---

## 5. Document History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-03 | Initial release |
