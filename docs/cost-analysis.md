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

## 10-Year Lifecycle Cost Comparison

| Metric | This DIY UPS | APC BE600M1 | APC BX1500M |
|---|---|---|---|
| Initial Cost | $225 | $85 | $180 |
| Battery Replacement (10yr) | $30 (1×) | $60–90 (2–3×) | $100–150 (2–3×) |
| Annual Electricity | $41/yr ($410) | $51/yr ($510) | $64/yr ($640) |
| **10-Year Grand Total** | **~$665** | **~$655–685** | **~$920–970** |
| **Savings** | — | $0 | $255–$305 |

While more expensive up-front, the DIY UPS with HDR-60-12 costs the same over 10 years vs the cheapest commercial option (BE600M1) and $255–$305 less than the BX1500M — while delivering more runtime and 10× faster switchover.

| Metric | This DIY UPS | APC BE600M1 | APC BX1500M | Bare Wall Warts |
|---|---|---|---|---|
| Runtime | 8.2 hours | ~2–3 hours | ~5–7 hours | N/A |
| Switchover Speed | <1ms | ~5–10ms | ~5–10ms | N/A |
| Annual Consumption | 139.8 kWh | 175 kWh | 219 kWh | ~136 kWh |

---

## Annual Operating Cost

Device and monitoring load: 13.68W measured DC. HDR-60-12 efficiency ~87% at 22% load: 15.39W wall draw.

- Annual consumption: 139.8 kWh
- Annual cost at $0.29/kWh: **$40.54**

Bare wall warts consume ~136 kWh/yr at $39.44. UPS overhead: essentially break-even. Commercial alternatives consume 175–219 kWh/yr ($51–64/yr), saving $10–20/yr vs this design.

**Calculation Details:** AC draw = DC load / eff. (87% from datasheet at low load). kWh/yr = W × 8760 / 1000. Cost = kWh × rate.
