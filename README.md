# Google Scholar citation history

This repository records periodic snapshots of [Nobuaki Mizumoto's Google Scholar profile](https://scholar.google.co.jp/citations?user=bALkDW4AAAAJ&hl=en) and identifies which publications gained or lost citations between observations.

Google Scholar shows the current state of its index but does not provide a downloadable history of past totals or per-publication citation counts. This project creates that missing history with a scheduled GitHub Action.

## Outputs

- [`data/metrics.csv`](data/metrics.csv): total citations, h-index, i10-index, recent-window metrics, and publication count for every successful observation
- [`data/publications.csv`](data/publications.csv): a complete per-publication snapshot for every observation
- [`data/changes.csv`](data/changes.csv): only publications whose citation count or profile presence changed
- [`reports/latest.md`](reports/latest.md): the latest metrics, detected changes, and most-cited publications
- [`reports/citation_history.png`](reports/citation_history.png): total citations through time
- [`reports/top_publications.png`](reports/top_publications.png): most-cited publications in the latest snapshot

## Schedule

The workflow runs Monday, Wednesday, and Friday at 12:17 UTC. It can also be run manually from **Actions → Update Google Scholar history → Run workflow**.

Each successful run retrieves all pages of the public profile, extracts profile metrics and stable publication identifiers, compares the result with the preceding snapshot, appends the observation and changes, regenerates the reports, and commits the updated files.

## Failure safeguards

Google Scholar has no public API and sometimes blocks automated traffic. The collector therefore uses low-frequency requests, retries temporary failures, detects block pages, rejects duplicate identifiers, and refuses a profile that is suspiciously incomplete relative to the preceding snapshot. A failed Action leaves the last valid history unchanged.

## Local use

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
python src/collect.py
python src/report.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuration

[`config.json`](config.json) contains the Scholar profile ID, public profile URL, request interval, page size, and incomplete-profile safety threshold.

A negative change means Google Scholar reported a lower count for that publication at the later observation. It may reflect de-duplication, record merging, removal of an indexed document, or a temporary indexing difference.

## License

MIT
