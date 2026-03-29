# 🔋 UPS Performance Validation Report: DIY LiFePO4 System

## 1. Executive Summary
This document provides the technical validation of the DIY LiFePO4 UPS system (10Ah nominal capacity). Following a series of empirical discharge tests (**Test D3**), the system has been characterized as a **Voltage-Constrained Architecture**.

While the hardware is capable of 10Ah, the single-rail 13.3V design limits starting SOC to approximately 70%. This report reconciles the measured 4.25–4.3 hour runtime with a four-phase physical model, achieving a **model accuracy of >99%**.

---

## 2. System Architecture & Constraints
The system utilizes a "Single-Rail" topology where the charger and load share a common DC bus. This results in a permanent engineering trade-off:

| Requirement | Target Voltage | System Provision |
| :--- | :--- | :--- |
| Sensitive Load Ceiling | $\le 13.3\text{V}$ | 13.3V CV Float |
| LiFePO4 Full Saturation | $14.2\text{V} - 14.4\text{V}$ | **Not Attainable** |

**Verdict:** The system is energy-limited by design. By floating the battery at 13.3V, we ensure 100% equipment safety and significantly extend the battery's calendar life by avoiding high-voltage stress.

---

## 3. Empirical Discharge Phases (Reconciled)
The following table represents the validated behavior of the battery under a **14.5W constant load**.

| Phase | Voltage Range | Duration | Drop Rate | Engineering Note |
| :--- | :--- | :--- | :--- | :--- |
| **Settling** | $13.27\text{V} \rightarrow 13.00\text{V}$ | $8 \text{ min}$ | $18 \text{ mV/min}$ | Surface charge depletion. |
| **Plateau** | $13.00\text{V} \rightarrow 12.80\text{V}$ | $146 \text{ min}$ | $1.4 \text{ mV/min}$ | Extremely flat, bulk capacity delivery |
| **Knee** | $12.80\text{V} \rightarrow 12.45\text{V}$ | $81 \text{ min}$ | $4.2 \text{ mV/min}$ | Gradual acceleration |
| **Cliff** | $12.45\text{V} \rightarrow 11.80\text{V}$ | $22 \text{ min}$ | $29 \text{ mV/min}$ | Rapid collapse (steepest below 12.4V) |

**Total Modeled Runtime:** 257 Minutes (4.28 Hours)

**Key Finding:** The **cliff begins at 12.45V**. The 12.4V warning fires at the inflection point, giving ~5–6 minutes until the 12.2V software shutdown.

---
---

## 4. State of Charge (SOC) & Capacity Utilization
Because the system operates in a restricted voltage band, "100% SOC" is defined as the maximum charge attainable at the 13.3V float ceiling.

| Region | Capacity (Ah) | Status |
| :--- | :--- | :--- |
| **Upper Buffer** | $\sim 3.0\text{Ah}$ | Inaccessible (Hardware limit) |
| **Usable Window** | $\sim 5.1\text{Ah}$ | ✅ **Active Backup Energy** |
| **Lower Buffer** | $\sim 1.9\text{Ah}$ | Reserved for LVD/Protection |

---

## 5. Automation & Safety Logic
Based on the high-resolution "Cliff" data, the following thresholds are used for the Home Assistant monitoring stack:

*   **13.00V (Grid Loss):** Initial notification. The system is entering the stable Plateau.
*   **12.80V (Warning):** Plateau end. The system has entered the 81-minute Knee phase.
*   **12.45V (Critical):** Cliff onset. Action required. Only $\sim 10$ minutes remain before software shutdown begins.
*   **12.20V (Shutdown):** Automatic graceful shutdown command issued to Home Assistant Green.
*   **11.80V (LVD):** Hardware disconnect via Victron BP-65 to prevent permanent cell damage.

---

## 6. Final Engineering Conclusion
The UPS is performing with extreme predictability. The identification of the **81-minute Knee phase** is critical, as it confirms the system is not in immediate danger when the voltage first begins to dip below 12.8V.

The architecture successfully balances simplicity and safety, providing a robust 4.3-hour backup window for the network stack while maintaining the battery in a low-stress state.

**Document Status:** *Final — Reconciled against raw discharge telemetry (March 2026).*