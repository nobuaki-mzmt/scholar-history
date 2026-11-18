# Citation forecast

Latest observation: **1,069 citations** on 2026-11-18.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 152.3 | 623.2 | 755 | 845 | 935 | 1026 | 1116 |
| Quadratic | 28.8 | 298.6 | 1052 | 1286 | 1544 | 1824 | 2126 |
| Exponential | 303.8 | 3043.2 | 2165 | 3584 | 5942 | 9838 | 16287 |
| Shifted power law | 9.4 | 12.9 | 1094 | 1436 | 1858 | 2369 | 2983 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1108**, **2027: 1435**, **2028: 1763**, **2029: 2091**, **2030: 2418**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-08 |
| 1,200 | 2027-05-02 |
| 1,500 | 2028-03-01 |
| 2,000 | 2029-04-19 |
| 2,500 | 2030-03-25 |
| 3,000 | 2031-01-10 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
