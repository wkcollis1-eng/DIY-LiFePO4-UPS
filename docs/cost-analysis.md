# Cost Analysis

---

## Actual Build Cost

| Category | Cost | % of Total |
|---|---|---|
| Main Power Components (PSU, Battery, BP-65, Ideal Diode) | $100.63 | 45.0% |
| Monitoring & Control (Shelly, DS18B20) | $23.47 | 10.5% |
| Protection & Wiring | $44.94 | 19.7% |
| Enclosure & Hardware | $32.83 | 14.6% |
| Tools | $12.73 | 5.7% |
| Pololu Shipping | $6.45 | 2.9% |
| Amazon Cash Back (5%) | −$10.21 | — |
| Sales Tax | $13.98 | 6.2% |
| **TOTAL** | **$223.88** | 100% |

> Tools ($12.73) are one-time costs not specific to this project. Excluding tools, effective build cost is ~$211.

---

## Why Build This?

This project costs more up-front than a commercial UPS. The value proposition is **not** cost savings — it's technical capability:

| Capability | This DIY UPS | Commercial SLA UPS |
|---|---|---|
| **Switchover time** | <1ms (imperceptible) | 4–10ms (can cause modem reboots) |
| **Runtime @ ~14W load** | ~8.2 hours | 2–2.5 hours |
| **Home Assistant integration** | Native (voltage, temp, SoC, runtime) | None or proprietary software |
| **Battery lifespan** | 7–10 years | 2–3 years |

Build this if you want seamless switchover, extended runtime, or native HA monitoring. Don't build this expecting significant cost savings.

---

## 10-Year Lifecycle Cost Comparison

For transparency, here's how the economics compare over a 10-year period:

| Metric | This DIY UPS | APC BE600M1 | APC BX1500M |
|---|---|---|---|
| Initial Cost | $224 | $85 | $180 |
| Battery Replacement (10yr) | ~$30 (1×) | $60–90 (2–3×) | $100–150 (2–3×) |
| Annual Electricity | $40/yr ($400) | $51/yr ($510) | $64/yr ($640) |
| **10-Year Total** | **~$654** | **~$655–685** | **~$920–970** |

**Bottom line:** Over 10 years, this DIY build costs roughly the same as the cheapest commercial option (BE600M1). The economics are essentially break-even — don't build this expecting significant savings or expecting to lose money.

The real value is the 3× longer runtime, instant switchover, and HA integration — not cost savings.

---

## Annual Operating Cost

| Parameter | Value | Calculation |
|---|---|---|
| DC load (measured) | 13.68W | HA Green + XB7 + Shelly + BP-65 |
| PSU efficiency @ 22% load | ~87% | HDR-60-12 datasheet |
| AC wall draw | 15.7W | 13.68W ÷ 0.87 |
| Annual consumption | 138 kWh | 15.7W × 8760h ÷ 1000 |
| Annual cost @ $0.29/kWh | ~$40 | 138 kWh × $0.29 |

For comparison, commercial UPS units consume 175–220 kWh/yr due to lower efficiency and transformer losses, costing $51–64/yr. The ~$10–20/yr electricity savings is real but modest.
