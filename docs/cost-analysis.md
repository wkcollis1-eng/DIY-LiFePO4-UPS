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
| **Runtime @ 14.5W DC load** | ~7.8 hours | 2–2.5 hours |
| **Battery lifespan** | 10–20 years | 2–3 years |
| **Home Assistant integration** | Native (voltage, temp, SoC, runtime) | None or proprietary software |

Build this if you want seamless switchover, extended runtime, or native HA monitoring. Don't build this expecting significant cost savings.

---

## Annual Operating Cost

| Option | Wall Draw | Annual kWh | Annual Cost |
|---|---|---|---|
| Bare wall warts (OEM adapters, no UPS) | 16.0W measured | 140 kWh | ~$41/yr |
| This DIY UPS (DC load through HDR-60-12 at ~81% efficiency) | ~17.9W | 157 kWh | ~$46/yr |
| APC BE600M1 (SLA, Line-Interactive) | ~20W estimated | 175 kWh | ~$52/yr |
| APC BX1500M | ~25W estimated | 219 kWh | ~$64/yr |

> Wall wart baseline measured via Kill-a-Watt: 2.538 kWh over 158.8 hours (6 days 14h 50min) = 16.0W average, confirmed stable across three independent combined measurement windows. XB7 OEM adapter DoE Level VI (≥88% efficiency, model NBC56B120460VU). The DIY UPS adds only ~$5/yr vs running devices on bare wall warts — UPS capability is essentially free to operate compared to doing nothing. Commercial alternatives cost $6–18/yr more to run.

---

## 10-Year Lifecycle Cost Comparison

| Metric | This DIY UPS | Bare Wall Warts | APC BE600M1 | APC BX1500M |
|---|---|---|---|---|
| Initial Cost | $224 | $0 | $85 | $180 |
| Battery Replacement (10yr) | $30 (1×) | — | $60–90 (2–3×) | $100–150 (2–3×) |
| Annual Electricity | $46/yr ($460) | $41/yr ($410) | $52/yr ($520) | $64/yr ($640) |
| **10-Year Grand Total** | **~$714** | **~$410** | **~$665–695** | **~$920–970** |

The DIY UPS costs ~$304 more over 10 years than running bare wall warts — this is the cost of UPS capability. It costs roughly the same as the APC BE600M1 over 10 years while delivering 3× more runtime (7.8h vs 2–3h), 10× faster switchover, and 5× longer battery life.
