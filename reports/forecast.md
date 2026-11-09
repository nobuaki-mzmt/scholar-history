# Citation forecast

Latest observation: **1,067 citations** on 2026-11-09.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 152.4 | 623.0 | 755 | 845 | 935 | 1025 | 1116 |
| Quadratic | 28.9 | 298.9 | 1053 | 1287 | 1545 | 1825 | 2127 |
| Exponential | 303.1 | 3030.1 | 2168 | 3590 | 5953 | 9857 | 16322 |
| Shifted power law | 9.5 | 13.9 | 1099 | 1444 | 1870 | 2387 | 3009 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1111**, **2027: 1443**, **2028: 1776**, **2029: 2108**, **2030: 2440**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-02 |
| 1,200 | 2027-04-26 |
| 1,500 | 2028-02-22 |
| 2,000 | 2029-04-09 |
| 2,500 | 2030-03-13 |
| 3,000 | 2030-12-27 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
