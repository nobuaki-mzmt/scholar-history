# Citation forecast

Latest observation: **1,056 citations** on 2026-10-30.

## Model comparison

| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linear | 145.3 | 609.3 | 718 | 802 | 887 | 972 | 1057 |
| Quadratic | 28.3 | 289.4 | 1043 | 1274 | 1528 | 1804 | 2103 |
| Exponential | 313.7 | 2935.9 | 2331 | 3901 | 6538 | 10942 | 18313 |
| Shifted power law | 9.4 | 13.1 | 1093 | 1435 | 1856 | 2367 | 2980 |

**Recommended simple extrapolation: Shifted power law.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.

As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of **2026: 1109**, **2027: 1436**, **2028: 1765**, **2029: 2093**, **2030: 2421**.

## Milestones under the recommended model

| Milestone | Approximate crossing |
|---|---|
| 1,100 | 2027-01-09 |
| 1,200 | 2027-05-03 |
| 1,500 | 2028-03-02 |
| 2,000 | 2029-04-21 |
| 2,500 | 2030-03-27 |
| 3,000 | 2031-01-11 |

## Interpretation

- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.
- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.
- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.
- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.

![Citation forecast](citation_forecast.png)
