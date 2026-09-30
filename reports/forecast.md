# Citation forecast

Latest observation: **1,017 citations** on 2026-09-30.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 135.7 | 591.1 | 673 | 751 | 829 | 907 | 986 |
| Quadratic | 27.3 | 276.9 | 1029 | 1256 | 1506 | 1777 | 2070 |
| Exponential | 321.1 | 2808.7 | 2550 | 4324 | 7344 | 12453 | 21116 |
| Shifted power law | 9.2 | 12.8 | 1092 | 1433 | 1854 | 2364 | 2976 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1105**, **2027: 1426**, **2028: 1749**, **2029: 2070**, **2030: 2392**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-10 |
| 1,200 | 2027-05-05 |
| 1,500 | 2028-03-04 |
| 2,000 | 2029-04-22 |
| 2,500 | 2030-03-29 |
| 3,000 | 2031-01-13 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
