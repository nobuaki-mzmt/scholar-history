from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


def read_csv(path):
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def placeholder(path, title):
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.text(0.5, 0.5, "No observations recorded yet", ha="center", va="center", transform=axis.transAxes)
    axis.set_title(title)
    axis.set_axis_off()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    metrics = read_csv(DATA / "metrics.csv")
    publications = read_csv(DATA / "publications.csv")
    changes = read_csv(DATA / "changes.csv")

    citation_path = REPORTS / "citation_history.png"
    if metrics.empty:
        placeholder(citation_path, "Google Scholar citation history")
    else:
        frame = metrics.copy()
        frame["observed_at_utc"] = pd.to_datetime(frame["observed_at_utc"], utc=True)
        frame = frame.sort_values("observed_at_utc")
        figure, axis = plt.subplots(figsize=(9, 5))
        axis.plot(frame["observed_at_utc"], frame["total_citations"], marker="o")
        axis.set_title("Google Scholar citation history")
        axis.set_xlabel("Observation date")
        axis.set_ylabel("Total citations")
        axis.grid(True, alpha=0.25)
        figure.autofmt_xdate()
        figure.tight_layout()
        figure.savefig(citation_path, dpi=160)
        plt.close(figure)

    top_path = REPORTS / "top_publications.png"
    if publications.empty:
        placeholder(top_path, "Most-cited publications")
    else:
        latest_time = publications["observed_at_utc"].max()
        latest = publications[publications["observed_at_utc"] == latest_time].copy()
        latest["citations"] = pd.to_numeric(latest["citations"], errors="coerce").fillna(0)
        latest = latest.nlargest(10, "citations").sort_values("citations")
        labels = [title if len(title) <= 65 else title[:62] + "..." for title in latest["title"]]
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.barh(labels, latest["citations"])
        axis.set_title("Most-cited publications at the latest observation")
        axis.set_xlabel("Citations")
        figure.tight_layout()
        figure.savefig(top_path, dpi=160, bbox_inches="tight")
        plt.close(figure)

    lines = ["# Latest Google Scholar snapshot", ""]
    if metrics.empty:
        lines.append("No successful observations have been recorded yet.")
    else:
        latest = metrics.sort_values("observed_at_utc").iloc[-1]
        lines.extend([
            f"Observed at `{latest['observed_at_utc']}`.", "",
            "| Metric | All | Recent window |", "|---|---:|---:|",
            f"| Citations | {int(latest['total_citations'])} | {int(latest['recent_citations'])} |",
            f"| h-index | {int(latest['h_index'])} | {int(latest['recent_h_index'])} |",
            f"| i10-index | {int(latest['i10_index'])} | {int(latest['recent_i10_index'])} |",
            f"| Publications tracked | {int(latest['publication_count'])} |  |", "",
            "## Changes in this observation", ""
        ])
        current = changes[changes["observed_at_utc"] == latest["observed_at_utc"]].copy() if not changes.empty else pd.DataFrame()
        if current.empty:
            lines.append("No per-publication changes were detected relative to the preceding observation.")
        else:
            lines.extend(["| Publication | Previous | Current | Change | Type |", "|---|---:|---:|---:|---|"])
            for _, row in current.sort_values("delta", ascending=False).iterrows():
                title = str(row["title"]).replace("|", "\\|")
                lines.append(f"| {title} | {row['previous_citations']} | {row['current_citations']} | {int(row['delta']):+d} | {row['change_type']} |")
    (REPORTS / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
