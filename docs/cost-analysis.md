# Cost Analysis

---

## Actual Build Cost

| Category | Cost | % of Total |
|---|---|---|
| Main Power Components (PSU, Battery, BP-65, Ideal Diode) | $89.60 | 41.7% |
| Monitoring & Control (Shelly, DS18B20) | $22.13 | 10.3% |
| Protection & Wiring | $44.98 | 21.0% |
| Enclosure & Hardware | $34.25 | 16.0% |
| Tools | $13.57 | 6.3% |
| Pololu Shipping | $6.45 | 3.0% |
| Amazon Cash Back (5%) | −$9.75 | — |
| Sales Tax | $13.40 | 6.2% |
| **TOTAL** | **$214.62** | 100% |

> Tools ($13.57) are one-time costs not specific to this project. Excluding tools, effective build cost is ~$201.

---

## 10-Year Lifecycle Cost Comparison

| Metric | This DIY UPS | APC BE600M1 | APC BX1500M |
|---|---|---|---|
| Initial Cost | $215 | $75 | $210 |
| Battery Replacement (10yr) | $30 (1×) | $75–100 (3–4×) | $120–160 (3–4×) |
| Annual Electricity | $58/yr ($580) | $52/yr ($520) | $53/yr ($530) |
| **10-Year Grand Total** | **~$825** | **~$670–695** | **~$860–900** |

The DIY build costs approximately $130–155 more over 10 years than the cheapest commercial option (APC BE600M1) and is broadly comparable to the APC BX1500M over the same period.

---

## Annual Operating Cost

Device and monitoring load: ~18W (HA Green 3W + XB7 14.7W measured + Shelly 1W + BP-65 parasitic 0.018W).

At PSU efficiency of ~81% at light load, wall draw is approximately 22–23W.

Annual electricity: ~200 kWh/yr at $0.29/kWh (CT average) ≈ **$58/year**.

> XB7 modem power validated via 3-day Kill-a-Watt measurement: 1.066 kWh consumed over 72.44 hours = 14.7W average, 20.3W peak. Combined system baseline measurement planned after HA Green baseline is complete.
