import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


class ScholarError(RuntimeError):
    pass


def integer(value):
    cleaned = re.sub(r"[^0-9-]", "", str(value or ""))
    return int(cleaned) if cleaned else 0


def blocked_page(html, url=""):
    text = html.lower()
    markers = (
        "unusual traffic",
        "our systems have detected",
        "not a robot",
        "recaptcha",
        "enable javascript and cookies to continue",
    )
    return "/sorry/" in url or any(marker in text for marker in markers)


def parse_metrics(soup):
    table = soup.select_one("#gsc_rsb_st")
    if table is None:
        raise ScholarError("Google Scholar metrics table was not found")
    recent_since_year = ""
    for cell in table.select("thead th"):
        match = re.search(r"Since\s+(\d{4})", cell.get_text(" ", strip=True), re.I)
        if match:
            recent_since_year = match.group(1)
    rows = {}
    for row in table.select("tbody tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        if len(cells) >= 3:
            rows[cells[0].lower()] = (integer(cells[1]), integer(cells[2]))
    required = ("citations", "h-index", "i10-index")
    missing = [label for label in required if label not in rows]
    if missing:
        raise ScholarError(f"Missing Google Scholar metrics: {', '.join(missing)}")
    return {
        "total_citations": rows["citations"][0],
        "recent_citations": rows["citations"][1],
        "h_index": rows["h-index"][0],
        "recent_h_index": rows["h-index"][1],
        "i10_index": rows["i10-index"][0],
        "recent_i10_index": rows["i10-index"][1],
        "recent_since_year": recent_since_year,
    }


def paper_id_from_href(href):
    value = parse_qs(urlparse(href).query).get("citation_for_view", [""])[0]
    return value.split(":", 1)[1] if ":" in value else value


def parse_publications(soup):
    publications = []
    for row in soup.select("tr.gsc_a_tr"):
        title_element = row.select_one(".gsc_a_at")
        if title_element is None:
            continue
        gray = row.select(".gs_gray")
        citation_element = row.select_one(".gsc_a_ac")
        year_element = row.select_one(".gsc_a_y span")
        paper_id = paper_id_from_href(title_element.get("href", ""))
        if not paper_id:
            raise ScholarError("A publication did not contain a stable Scholar identifier")
        publications.append({
            "paper_id": paper_id,
            "title": title_element.get_text(" ", strip=True),
            "authors": gray[0].get_text(" ", strip=True) if len(gray) > 0 else "",
            "venue": gray[1].get_text(" ", strip=True) if len(gray) > 1 else "",
            "year": integer(year_element.get_text(" ", strip=True)) if year_element else "",
            "citations": integer(citation_element.get_text(" ", strip=True)) if citation_element else 0,
        })
    return publications


def request_page(session, url, params, attempts=3):
    last_error = None
    for attempt in range(attempts):
        try:
            response = session.get(url, params=params, timeout=45)
            if response.status_code == 200 and not blocked_page(response.text, response.url):
                return response.text
            last_error = ScholarError(
                "Google Scholar returned a traffic block page"
                if response.status_code == 200
                else f"Google Scholar returned HTTP {response.status_code}"
            )
        except requests.RequestException as error:
            last_error = ScholarError(f"Google Scholar request failed: {error}")
        if attempt + 1 < attempts:
            time.sleep(10 * (attempt + 1))
    raise last_error


def fetch_profile(config):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })
    page_size = int(config.get("page_size", 100))
    delay = float(config.get("request_delay_seconds", 2))
    publications = []
    metrics = None
    profile_name = ""
    for page_number in range(20):
        html = request_page(session, "https://scholar.google.com/citations", {
            "user": config["profile_id"],
            "hl": config.get("language", "en"),
            "view_op": "list_works",
            "sortby": "pubdate",
            "cstart": page_number * page_size,
            "pagesize": page_size,
        })
        soup = BeautifulSoup(html, "html.parser")
        if page_number == 0:
            name_element = soup.select_one("#gsc_prf_in")
            if name_element is None:
                raise ScholarError("Google Scholar profile name was not found")
            profile_name = name_element.get_text(" ", strip=True)
            metrics = parse_metrics(soup)
        page_publications = parse_publications(soup)
        publications.extend(page_publications)
        if len(page_publications) < page_size:
            break
        time.sleep(delay)
    else:
        raise ScholarError("Profile pagination exceeded the safety limit")
    if not publications:
        raise ScholarError("No publications were found")
    if len({paper["paper_id"] for paper in publications}) != len(publications):
        raise ScholarError("Duplicate Scholar paper identifiers were returned")
    return profile_name, metrics, publications


def read_rows(path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def latest_snapshot(path):
    rows = read_rows(path)
    if not rows:
        return {}
    latest_time = max(row["observed_at_utc"] for row in rows)
    return {row["paper_id"]: row for row in rows if row["observed_at_utc"] == latest_time}


def append_rows(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def changes_from_snapshots(previous, current, observed_at):
    changes = []
    for paper_id in sorted(set(previous) | set(current)):
        old = previous.get(paper_id)
        new = current.get(paper_id)
        if old is None:
            changes.append({"observed_at_utc": observed_at, "paper_id": paper_id, "title": new["title"], "previous_citations": "", "current_citations": new["citations"], "delta": new["citations"], "change_type": "new_publication"})
        elif new is None:
            changes.append({"observed_at_utc": observed_at, "paper_id": paper_id, "title": old["title"], "previous_citations": old["citations"], "current_citations": "", "delta": -integer(old["citations"]), "change_type": "missing_publication"})
        else:
            delta = integer(new["citations"]) - integer(old["citations"])
            if delta:
                changes.append({"observed_at_utc": observed_at, "paper_id": paper_id, "title": new["title"], "previous_citations": integer(old["citations"]), "current_citations": integer(new["citations"]), "delta": delta, "change_type": "citation_increase" if delta > 0 else "citation_decrease"})
    return changes


def collect(config_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    root = config_path.parent
    publication_path = root / "data" / "publications.csv"
    previous = latest_snapshot(publication_path)
    profile_name, metrics, publications = fetch_profile(config)
    if previous and len(publications) < len(previous) * float(config.get("minimum_previous_fraction", 0.8)):
        raise ScholarError(f"Scholar returned only {len(publications)} publications after {len(previous)} previously; no data were written")
    observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    current = {paper["paper_id"]: paper for paper in publications}
    changes = changes_from_snapshots(previous, current, observed_at) if previous else []
    metric_fields = ["observed_at_utc", "profile_name", "total_citations", "recent_citations", "h_index", "recent_h_index", "i10_index", "recent_i10_index", "recent_since_year", "publication_count"]
    publication_fields = ["observed_at_utc", "paper_id", "title", "authors", "venue", "year", "citations"]
    change_fields = ["observed_at_utc", "paper_id", "title", "previous_citations", "current_citations", "delta", "change_type"]
    metric_row = {"observed_at_utc": observed_at, "profile_name": profile_name, **metrics, "publication_count": len(publications)}
    append_rows(root / "data" / "metrics.csv", metric_fields, [metric_row])
    append_rows(publication_path, publication_fields, [{"observed_at_utc": observed_at, **paper} for paper in publications])
    if changes:
        append_rows(root / "data" / "changes.csv", change_fields, changes)
    status = {"observed_at_utc": observed_at, "profile_name": profile_name, "profile_url": config["profile_url"], "publication_count": len(publications), **metrics}
    (root / "data" / "last_success.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return status, changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    args = parser.parse_args()
    try:
        status, changes = collect(args.config.resolve())
    except ScholarError as error:
        print(f"Collection failed safely: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Recorded {status['total_citations']} citations across {status['publication_count']} publications; detected {len(changes)} changes")


if __name__ == "__main__":
    main()
