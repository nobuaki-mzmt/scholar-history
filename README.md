# Google Scholar citation history

Tracks [Nobuaki Mizumoto's Google Scholar profile](https://scholar.google.co.jp/citations?user=bALkDW4AAAAJ&hl=en) over time, including total citations, publication-level changes, and simple citation-growth forecasts.

## Useful links

- [`data/changes.csv`](data/changes.csv): publications whose citation count or profile presence changed
- [`reports/latest.md`](reports/latest.md): latest metrics and detected changes
- [`data/metrics.csv`](data/metrics.csv): citation, h-index, and i10-index history
- [`reports/forecast.md`](reports/forecast.md): model comparison and citation forecast
- [`reports/citation_history.png`](reports/citation_history.png): long-term citation history

## How it works

A GitHub Action runs Monday, Wednesday, and Friday and can also be run manually from **Actions → Update Google Scholar history → Run workflow**.

Each successful run:

1. retrieves the current Google Scholar profile;
2. records profile-level and per-publication citation counts;
3. identifies gains, losses, additions, and removals;
4. updates plots and forecasts; and
5. commits the new data automatically.

## Data

- [`data/publications.csv`](data/publications.csv): complete per-publication snapshots
- [`data/historical_citations.csv`](data/historical_citations.csv): older hand-recorded citation totals
- [`data/archive/GoogleScholarCitations.xlsx`](data/archive/GoogleScholarCitations.xlsx): original historical workbook

The historical record begins in 2013. Automated tracking continues in `data/metrics.csv`.

## Forecasts

[`src/forecast.py`](src/forecast.py) combines the historical and automated records and compares simple linear, quadratic, exponential, and shifted power-law models.

Outputs:

- [`reports/forecast.md`](reports/forecast.md)
- [`reports/forecast_models.csv`](reports/forecast_models.csv)
- [`reports/citation_forecast.png`](reports/citation_forecast.png)

These are descriptive extrapolations, not calibrated predictions.

## Collection

Scheduled GitHub runs use the SerpApi Google Scholar Author API because Google Scholar often blocks shared GitHub-hosted runner IP addresses. The API key is stored as the repository secret `SERPAPI_KEY`.

The collector includes safeguards against incomplete or blocked responses; failed runs leave the last valid history unchanged.

## Local use

```bash
pip install -r requirements.txt
python -m unittest discover -s tests
python src/collect.py
python src/report.py
python src/forecast.py
```

## License

MIT
