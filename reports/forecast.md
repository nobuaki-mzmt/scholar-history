# Citation forecast

Latest observation: **1,024 citations** on 2026-10-07.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 143.9 | 602.8 | 714 | 799 | 883 | 967 | 1051 |
| Quadratic | 27.6 | 284.2 | 1039 | 1269 | 1521 | 1796 | 2093 |
| Exponential | 311.5 | 2904.0 | 2333 | 3906 | 6547 | 10958 | 18343 |
| Shifted power law | 9.1 | 11.4 | 1092 | 1433 | 1854 | 2364 | 2977 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1101**, **2027: 1417**, **2028: 1734**, **2029: 2050**, **2030: 2366**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-10 |
| 1,200 | 2027-05-05 |
| 1,500 | 2028-03-04 |
| 2,000 | 2029-04-22 |
| 2,500 | 2030-03-28 |
| 3,000 | 2031-01-13 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
