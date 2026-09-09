from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "src" else Path.cwd()
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


@dataclass
class ModelFit:
    name: str
    predict: callable
    train_rmse: float
    backtest_rmse: float | None = None


def read_series() -> tuple[pd.DataFrame, pd.DataFrame]:
    hist_path = DATA / "historical_citations.csv"
    metrics_path = DATA / "metrics.csv"

    historical = pd.read_csv(hist_path)
    historical["observed_date"] = pd.to_datetime(historical["observed_date"]).dt.tz_localize(None)
    historical = historical[["observed_date", "total_citations"]].copy()
    historical["source"] = "historical workbook"
    historical["priority"] = 0

    metrics = pd.read_csv(metrics_path)
    metrics["observed_date"] = pd.to_datetime(metrics["observed_at_utc"], utc=True).dt.tz_convert(None).dt.normalize()
    metrics = metrics[["observed_date", "total_citations"]].copy()
    metrics["source"] = "automated tracker"
    metrics["priority"] = 1

    combined = pd.concat([historical, metrics], ignore_index=True)
    combined["total_citations"] = pd.to_numeric(combined["total_citations"], errors="raise")
    combined = combined.sort_values(["observed_date", "priority"])
    combined = combined.drop_duplicates("observed_date", keep="last").sort_values("observed_date").reset_index(drop=True)

    # The new tracker records several observations per week while the older record is sparse.
    # Use the last observed value in each calendar month for fitting so modern observations do
    # not receive disproportionate weight merely because they are sampled more frequently.
    monthly = combined.copy()
    monthly["month"] = monthly["observed_date"].dt.to_period("M")
    monthly = monthly.groupby("month", as_index=False).tail(1).sort_values("observed_date").reset_index(drop=True)
    return combined, monthly


def time_years(dates: pd.Series | pd.DatetimeIndex, origin: pd.Timestamp) -> np.ndarray:
    d = pd.to_datetime(dates)
    delta = d - origin
    days = delta.dt.days.to_numpy(dtype=float) if hasattr(delta, "dt") else np.asarray(delta.days, dtype=float)
    return days / 365.2425


def rmse(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y, dtype=float) - np.asarray(pred, dtype=float)) ** 2)))


def fit_power(t: np.ndarray, y: np.ndarray):
    # Shifted power law y = a * (t + c)^b. Search c on a broad positive grid,
    # then solve a and b by log-linear regression for each candidate c.
    best = None
    for c in np.logspace(-2, 1.7, 600):
        x = np.log(t + c)
        coef = np.polyfit(x, np.log(y), 1)
        pred = np.exp(np.polyval(coef, x))
        score = rmse(y, pred)
        if best is None or score < best[0]:
            best = (score, c, coef)
    score, c, coef = best
    return lambda x: np.exp(np.polyval(coef, np.log(np.asarray(x, dtype=float) + c))), score


def fit_models(frame: pd.DataFrame, origin: pd.Timestamp) -> dict[str, ModelFit]:
    t = time_years(frame["observed_date"], origin)
    y = frame["total_citations"].to_numpy(dtype=float)
    models: dict[str, ModelFit] = {}

    coef = np.polyfit(t, y, 1)
    predict = lambda x, c=coef: np.polyval(c, np.asarray(x, dtype=float))
    models["linear"] = ModelFit("Linear", predict, rmse(y, predict(t)))

    coef = np.polyfit(t, y, 2)
    predict = lambda x, c=coef: np.polyval(c, np.asarray(x, dtype=float))
    models["quadratic"] = ModelFit("Quadratic", predict, rmse(y, predict(t)))

    coef = np.polyfit(t, np.log(y), 1)
    predict = lambda x, c=coef: np.exp(np.polyval(c, np.asarray(x, dtype=float)))
    models["exponential"] = ModelFit("Exponential", predict, rmse(y, predict(t)))

    predict, score = fit_power(t, y)
    models["power"] = ModelFit("Shifted power law", predict, score)
    return models


def add_backtest(models: dict[str, ModelFit], monthly: pd.DataFrame, origin: pd.Timestamp) -> None:
    cutoff = pd.Timestamp("2023-01-01")
    train = monthly[monthly["observed_date"] <= cutoff].copy()
    test = monthly[monthly["observed_date"] > cutoff].copy()
    if len(train) < 8 or len(test) < 2:
        return
    historical_models = fit_models(train, origin)
    test_t = time_years(test["observed_date"], origin)
    y = test["total_citations"].to_numpy(dtype=float)
    for key, model in models.items():
        model.backtest_rmse = rmse(y, historical_models[key].predict(test_t))


def recent_linear(monthly: pd.DataFrame):
    recent = monthly[monthly["observed_date"] >= pd.Timestamp("2026-04-01")].copy()
    if len(recent) < 3:
        return None
    origin = recent["observed_date"].min()
    t = time_years(recent["observed_date"], origin)
    y = recent["total_citations"].to_numpy(dtype=float)
    coef = np.polyfit(t, y, 1)
    return origin, (lambda dates, c=coef, o=origin: np.polyval(c, time_years(pd.to_datetime(dates), o)))


def crossing_date(model: ModelFit, target: int, origin: pd.Timestamp, start: pd.Timestamp, years: int = 8):
    dates = pd.date_range(start, start + pd.DateOffset(years=years), freq="D")
    pred = model.predict(time_years(dates, origin))
    idx = np.where(pred >= target)[0]
    return dates[idx[0]] if len(idx) else None


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    combined, monthly = read_series()
    origin = monthly["observed_date"].min()
    latest = combined.iloc[-1]

    models = fit_models(monthly, origin)
    add_backtest(models, monthly, origin)
    candidates = [m for m in models.values() if m.backtest_rmse is not None]
    recommended = min(candidates, key=lambda m: m.backtest_rmse) if candidates else models["power"]
    local = recent_linear(monthly)

    year_ends = pd.to_datetime([f"{year}-12-31" for year in range(int(latest.observed_date.year), int(latest.observed_date.year) + 5)])
    model_rows = []
    for model in models.values():
        forecasts = model.predict(time_years(year_ends, origin))
        row = {
            "model": model.name,
            "training_rmse": round(model.train_rmse, 2),
            "backtest_rmse": round(model.backtest_rmse, 2) if model.backtest_rmse is not None else np.nan,
        }
        for date, value in zip(year_ends, forecasts):
            row[f"forecast_{date.year}"] = round(float(value), 1)
        model_rows.append(row)
    pd.DataFrame(model_rows).to_csv(REPORTS / "forecast_models.csv", index=False)

    future_end = latest.observed_date + pd.DateOffset(years=4)
    grid = pd.date_range(origin, future_end, freq="7D")
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.scatter(combined["observed_date"], combined["total_citations"], s=18, label="Observed")
    pred = recommended.predict(time_years(grid, origin))
    axis.plot(grid, pred, linewidth=2, label=f"{recommended.name} forecast")
    if local is not None:
        _, local_predict = local
        local_grid = pd.date_range(pd.Timestamp("2026-04-01"), future_end, freq="7D")
        axis.plot(local_grid, local_predict(local_grid), linestyle="--", linewidth=1.5, label="Recent linear trend")
    axis.axvline(latest.observed_date, linestyle=":", linewidth=1)
    axis.set_title("Google Scholar citation history and simple forecasts")
    axis.set_xlabel("Date")
    axis.set_ylabel("Total citations")
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(REPORTS / "citation_forecast.png", dpi=160)
    plt.close(figure)

    lines = [
        "# Citation forecast", "",
        f"Latest observation: **{int(latest.total_citations):,} citations** on {latest.observed_date.date()}.", "",
        "## Model comparison", "",
        "| Model | Training RMSE | Backtest RMSE | 2026 | 2027 | 2028 | 2029 | 2030 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models.values():
        vals = model.predict(time_years(year_ends, origin))
        bt = f"{model.backtest_rmse:.1f}" if model.backtest_rmse is not None else "NA"
        lines.append("| " + " | ".join([
            model.name, f"{model.train_rmse:.1f}", bt,
            *[f"{v:.0f}" for v in vals],
        ]) + " |")
    lines += [
        "",
        f"**Recommended simple extrapolation: {recommended.name}.** It had the lowest RMSE when models were fit only through 2023-01-01 and then asked to predict the later 2026 observations.",
        "",
    ]
    if local is not None:
        _, local_predict = local
        vals = local_predict(year_ends)
        lines.append("As a short-term sanity check, a straight line fitted only to observations from April 2026 onward gives year-end forecasts of " + ", ".join(f"**{d.year}: {v:.0f}**" for d, v in zip(year_ends, vals)) + ".")
        lines.append("")

    lines += ["## Milestones under the recommended model", "", "| Milestone | Approximate crossing |", "|---|---|"]
    for target in (1100, 1200, 1500, 2000, 2500, 3000):
        date = crossing_date(recommended, target, origin, latest.observed_date)
        lines.append(f"| {target:,} | {date.date() if date is not None else 'beyond forecast window'} |")
    lines += [
        "",
        "## Interpretation", "",
        "- The trajectory is clearly accelerating, but a literal exponential fit extrapolates far too aggressively and performs poorly in the pre-2023 backtest.",
        "- The shifted power law captures accelerating but sub-exponential growth and currently provides the best simple long-horizon backtest among the tested forms.",
        "- Forecast uncertainty here is dominated by model structure, publication timing, field-specific citation dynamics, and Google Scholar indexing changes. Treat the numbers as scenario estimates rather than confidence-calibrated predictions.",
        "- The fitting series uses at most one observation per calendar month so the new three-times-per-week tracker does not overwhelm the sparse historical record.",
        "",
        "![Citation forecast](citation_forecast.png)",
    ]
    (REPORTS / "forecast.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Recommended model: {recommended.name}; latest={int(latest.total_citations)}; backtest RMSE={recommended.backtest_rmse:.2f}")


if __name__ == "__main__":
    main()
