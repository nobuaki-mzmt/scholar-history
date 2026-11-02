# Citation forecast

Latest observation: **1,064 citations** on 2026-11-02.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 152.3 | 622.5 | 755 | 845 | 935 | 1025 | 1115 |
| Quadratic | 29.0 | 298.8 | 1053 | 1287 | 1545 | 1825 | 2128 |
| Exponential | 302.5 | 3020.5 | 2170 | 3594 | 5960 | 9870 | 16346 |
| Shifted power law | 9.6 | 14.4 | 1099 | 1445 | 1871 | 2388 | 3010 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1112**, **2027: 1447**, **2028: 1782**, **2029: 2117**, **2030: 2451**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-02 |
| 1,200 | 2027-04-25 |
| 1,500 | 2028-02-21 |
| 2,000 | 2029-04-08 |
| 2,500 | 2030-03-12 |
| 3,000 | 2030-12-26 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
