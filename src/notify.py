from pathlib import Path
import os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
THRESHOLD = 3

def main():
    metrics = pd.read_csv(DATA / "metrics.csv")
    if len(metrics) < 2:
        notify = False
        delta = 0
        latest = None
    else:
        metrics = metrics.sort_values("observed_at_utc")
        previous = metrics.iloc[-2]
        latest = metrics.iloc[-1]
        delta = int(latest["total_citations"]) - int(previous["total_citations"])
        notify = abs(delta) > THRESHOLD

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"notify={'true' if notify else 'false'}\n")
            handle.write(f"delta={delta}\n")

    if not notify or latest is None:
        return

    changes = pd.read_csv(DATA / "changes.csv")
    current = changes[changes["observed_at_utc"] == latest["observed_at_utc"]].copy()

    sign = "+" if delta > 0 else ""
    title = f"Google Scholar change: {sign}{delta} citations"
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"title={title}\n")

    lines = [
        f"# Google Scholar citation change",
        "",
        f"Total citations changed from **{int(previous['total_citations'])}** to **{int(latest['total_citations'])}** ({sign}{delta}).",
        "",
        f"Observed at `{latest['observed_at_utc']}`.",
        "",
        "## Publication-level changes",
        "",
    ]

    if current.empty:
        lines.append("No publication-level changes were recorded for this snapshot.")
    else:
        lines.extend([
            "| Publication | Previous | Current | Change |",
            "|---|---:|---:|---:|",
        ])
        for _, row in current.sort_values("delta", ascending=False).iterrows():
            paper_title = str(row["title"]).replace("|", "\\|")
            prev = "" if pd.isna(row["previous_citations"]) else int(row["previous_citations"])
            cur = "" if pd.isna(row["current_citations"]) else int(row["current_citations"])
            d = int(row["delta"])
            lines.append(f"| {paper_title} | {prev} | {cur} | {d:+d} |")

    lines.extend([
        "",
        "[Latest report](../blob/main/reports/latest.md) · [Complete change history](../blob/main/data/changes.csv)",
    ])

    Path("/tmp/citation-notification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
