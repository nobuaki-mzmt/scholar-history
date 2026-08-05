import argparse
import csv
import json
import os
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


def parse_serpapi_metrics(payload):
    table = payload.get("cited_by", {}).get("table", [])
    entries = {}
    recent_since_year = ""
    for row in table:
        for label in ("citations", "h_index", "i10_index"):
            values = row.get(label)
            if not isinstance(values, dict):
                continue
            recent_keys = [key for key in values if key != "all"]
            recent_key = recent_keys[0] if recent_keys else ""
            match = re.fullmatch(r"since_(\d{4})", recent_key)
            if match:
                recent_since_year = match.group(1)
            entries[label] = (integer(values.get("all")), integer(values.get(recent_key)))
    missing = [label for label in ("citations", "h_index", "i10_index") if label not in entries]
    if missing:
        raise ScholarError(f"Missing SerpApi metrics: {', '.join(missing)}")
    return {
        "total_citations": entries["citations"][0],
        "recent_citations": entries["citations"][1],
        "h_index": entries["h_index"][0],
        "recent_h_index": entries["h_index"][1],
        "i10_index": entries["i10_index"][0],
        "recent_i10_index": entries["i10_index"][1],
        "recent_since_year": recent_since_year,
    }


def parse_serpapi_publications(payload):
    publications = []
    for article in payload.get("articles", []):
        citation_id = str(article.get("citation_id", ""))
        paper_id = citation_id.split(":", 1)[1] if ":" in citation_id else citation_id
        if not paper_id:
            raise ScholarError("A SerpApi publication did not contain a stable Scholar identifier")
        publications.append({
            "paper_id": paper_id,
            "title": str(article.get("title", "")).strip(),
            "authors": str(article.get("authors", "")).strip(),
            "venue": str(article.get("publication", "")).strip(),
            "year": integer(article.get("year")) or "",
            "citations": integer((article.get("cited_by") or {}).get("value")),
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


def request_serpapi(session, params, attempts=3):
    last_error = None
    for attempt in range(attempts):
        try:
            response = session.get("https://serpapi.com/search.json", params=params, timeout=90)
            try:
                payload = response.json()
            except requests.JSONDecodeError:
                payload = {}
            if response.status_code == 200 and not payload.get("error"):
                status = payload.get("search_metadata", {}).get("status")
                if status in (None, "Success"):
                    return payload
            message = payload.get("error") or f"HTTP {response.status_code}"
            last_error = ScholarError(f"SerpApi request failed: {message}")
        except requests.RequestException as error:
            last_error = ScholarError(f"SerpApi request failed: {error}")
        if attempt + 1 < attempts:
            time.sleep(5 * (attempt + 1))
    raise last_error


def validate_publications(publications):
    if not publications:
        raise ScholarError("No publications were found")
    if len({paper["paper_id"] for paper in publications}) != len(publications):
        raise ScholarError("Duplicate Scholar paper identifiers were returned")


def fetch_direct_profile(config):
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
    validate_publications(publications)
    return profile_name, metrics, publications, "google_scholar_direct"


def fetch_serpapi_profile(config, api_key):
    session = requests.Session()
    page_size = min(int(config.get("page_size", 100)), 100)
    publications = []
    metrics = None
    profile_name = ""
    for page_number in range(20):
        payload = request_serpapi(session, {
            "engine": "google_scholar_author",
            "author_id": config["profile_id"],
            "hl": config.get("language", "en"),
            "start": page_number * page_size,
            "num": page_size,
            "api_key": api_key,
        })
        if page_number == 0:
            profile_name = str(payload.get("author", {}).get("name", "")).strip()
            if not profile_name:
                raise ScholarError("SerpApi did not return the Scholar profile name")
            metrics = parse_serpapi_metrics(payload)
        page_publications = parse_serpapi_publications(payload)
        publications.extend(page_publications)
        if len(page_publications) < page_size:
            break
    else:
        raise ScholarError("SerpApi pagination exceeded the safety limit")
    validate_publications(publications)
    return profile_name, metrics, publications, "serpapi"


def fetch_profile(config):
    provider = str(config.get("provider", "auto")).lower()
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if provider not in ("auto", "direct", "serpapi"):
        raise ScholarError(f"Unsupported provider: {provider}")
    if provider == "serpapi" or api_key:
        if not api_key:
            raise ScholarError("SERPAPI_KEY is required when provider is serpapi")
        return fetch_serpapi_profile(config, api_key)
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        raise ScholarError("SERPAPI_KEY is not configured. Add it as a GitHub Actions repository secret before running this workflow")
    return fetch_direct_profile(config)


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
    profile_name, metrics, publications, data_source = fetch_profile(config)
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
    status = {"observed_at_utc": observed_at, "profile_name": profile_name, "profile_url": config["profile_url"], "data_source": data_source, "publication_count": len(publications), **metrics}
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
    print(f"Recorded {status['total_citations']} citations across {status['publication_count']} publications from {status['data_source']}; detected {len(changes)} changes")


if __name__ == "__main__":
    main()
