# Google Scholar citation history

This repository records periodic snapshots of [Nobuaki Mizumoto's Google Scholar profile](https://scholar.google.co.jp/citations?user=bALkDW4AAAAJ&hl=en), identifies which publications gained or lost citations between observations, and combines the automated record with an older hand-maintained citation history for simple growth modeling and forecasts.

Google Scholar shows the current state of its index but does not provide a downloadable history of past totals or per-publication citation counts. This project creates that missing history with a scheduled GitHub Action.

## Historical archive

The repository preserves the original hand-maintained workbook at [`data/archive/GoogleScholarCitations.xlsx`](data/archive/GoogleScholarCitations.xlsx). A normalized citation-total series extracted from that workbook is stored as [`data/historical_citations.csv`](data/historical_citations.csv).

The historical series begins in 2013 and includes irregular observations through June 2026. It is not rewritten by the automated collector; instead, new Google Scholar snapshots continue in `data/metrics.csv`.

## Forecast analysis

[`src/forecast.py`](src/forecast.py) merges the historical citation totals with the automated tracker and refits simple growth models after every successful collection. Because the modern tracker records several observations per week while the old record is sparse, model fitting uses at most the last observation in each calendar month so recent data do not receive disproportionate weight merely because they are sampled more often.

The script compares:

- linear growth;
- quadratic growth;
- exponential growth; and
- a shifted power-law curve, which allows accelerating but sub-exponential growth.

For a simple retrospective check, each model is also fit using only data through 2023-01-01 and then evaluated against the later 2026 observations. This is not a formal forecasting study, but it is useful for detecting obviously over-aggressive extrapolation. A recent linear trend using observations from April 2026 onward is reported as a short-term sanity check.

Forecast outputs are:

- [`reports/forecast.md`](reports/forecast.md): model comparison, milestone estimates, and interpretation;
- [`reports/forecast_models.csv`](reports/forecast_models.csv): model errors and year-end forecasts; and
- [`reports/citation_forecast.png`](reports/citation_forecast.png): historical observations and forecast curves.

Forecasts are descriptive scenarios, not calibrated prediction intervals. Publication timing, changes in research visibility, field-specific citation dynamics, and Google Scholar indexing revisions can all move the trajectory substantially.

## One-time setup

Google Scholar blocks requests from shared GitHub-hosted runner IP addresses. Scheduled runs therefore use the [SerpApi Google Scholar Author API](https://serpapi.com/google-scholar-author-api).

1. Create a SerpApi account.
2. Copy the private API key from the SerpApi account page.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Select **New repository secret**.
5. Set the name to `SERPAPI_KEY` and paste the API key as the value.
6. Open **Actions → Update Google Scholar history → Run workflow**.

The API key is stored as an encrypted GitHub Actions secret and is not written to the repository or logs.

## Automated outputs

- [`data/metrics.csv`](data/metrics.csv): total citations, h-index, i10-index, recent-window metrics, and publication count for every successful observation
- [`data/publications.csv`](data/publications.csv): a complete per-publication snapshot for every observation
- [`data/changes.csv`](data/changes.csv): only publications whose citation count or profile presence changed
- [`reports/latest.md`](reports/latest.md): the latest metrics and detected changes
- [`reports/citation_history.png`](reports/citation_history.png): historical + automated total-citation history
- [`reports/top_publications.png`](reports/top_publications.png): most-cited publications in the latest snapshot

## Schedule

The workflow runs Monday, Wednesday, and Friday at 12:17 UTC. It can also be run manually from **Actions → Update Google Scholar history → Run workflow**.

Each successful run retrieves the public profile, appends the new observation and publication-level changes, regenerates the historical reports and forecasts, and commits updated `data/` and `reports/` files.

## Failure safeguards

The collector retries temporary failures, rejects duplicate identifiers, and refuses a profile that is suspiciously incomplete relative to the preceding snapshot. A failed Action leaves the last valid history unchanged.

The scheduled workflow uses SerpApi. When run locally without a `SERPAPI_KEY`, the collector attempts a direct request to Google Scholar instead. Direct requests may still be blocked depending on the network.

## Local use

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
python src/collect.py
python src/report.py
python src/forecast.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

To use SerpApi locally, set the environment variable first:

```powershell
$env:SERPAPI_KEY="your_private_key"
python src/collect.py
```

## Configuration

[`config.json`](config.json) contains the Scholar profile ID, public profile URL, provider selection, page size, request interval, and incomplete-profile safety threshold.

A negative citation change means Google Scholar reported a lower count for that publication at the later observation. It may reflect de-duplication, record merging, removal of an indexed document, or a temporary indexing difference.

## License

MIT
