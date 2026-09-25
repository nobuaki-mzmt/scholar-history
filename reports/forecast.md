# Citation forecast

Latest observation: **1,013 citations** on 2026-09-25.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 135.5 | 590.2 | 672 | 750 | 829 | 907 | 985 |
| Quadratic | 27.2 | 276.3 | 1028 | 1255 | 1505 | 1776 | 2069 |
| Exponential | 320.5 | 2799.5 | 2552 | 4328 | 7350 | 12464 | 21137 |
| Shifted power law | 9.2 | 12.8 | 1086 | 1424 | 1841 | 2344 | 2949 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1105**, **2027: 1428**, **2028: 1752**, **2029: 2075**, **2030: 2398**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-17 |
| 1,200 | 2027-05-12 |
| 1,500 | 2028-03-13 |
| 2,000 | 2029-05-04 |
| 2,500 | 2030-04-11 |
| 3,000 | 2031-01-28 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
