# Cost Analysis

---

## Actual Build Cost

| Category | Cost | % of Total |
|---|---|---|
| Main Power Components (PSU, Battery, BP-65, Ideal Diode) | $96.10 | 38.3% |
| Monitoring & Control (Shelly, DS18B20) | $24.98 | 9.9% |
| Protection & Wiring | $46.34 | 18.3% |
| Enclosure & Hardware | $33.22 | 13.1% |
| Tools | $13.57 | 5.4% |
| Pololu Shipping | $6.45 | 2.6% |
| Amazon Cash Back (5%) | −$10.73 | — |
| Sales Tax | $14.63 | 5.6% |
| **TOTAL** | **$234.37** | 100% |

> Tools ($13.57) are one-time costs not specific to this project. Excluding tools, effective build cost is ~$221.

---

## 10-Year Lifecycle Cost Comparison

| Metric | This DIY UPS | APC BE600M1 | APC BX1500M |
|---|---|---|---|
| Initial Cost | $234 | $75 | $210 |
| Battery Replacement (10yr) | $30 (1×) | $75–100 (3–4×) | $120–160 (3–4×) |
| Annual Electricity | $58/yr ($580) | $52/yr ($520) | $53/yr ($530) |
| **10-Year Grand Total** | **~$850** | **~$670–695** | **~$860–900** |

The DIY build costs approximately $155–180 more over 10 years than the cheapest commercial option (APC BE600M1) and is broadly comparable to the APC BX1500M over the same period.

---

## Annual Operating Cost

Device and monitoring load: ~18W (HA Green 3W + XB7 ~14W + Shelly 1W + BP-65 parasitic 0.018W).

At PSU efficiency of ~81% at light load, wall draw is approximately 22–23W.

Annual electricity: ~200 kWh/yr at $0.29/kWh (CT average) ≈ **$58/year**.

> The 18W figure will be updated from 7-day Kill-a-Watt measurements. Preliminary 47-minute XB7 sample showed 13.9W average vs. the 15W document estimate. Combined system baseline measurement is planned after individual device baselines are complete.
