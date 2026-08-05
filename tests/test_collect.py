import unittest

from bs4 import BeautifulSoup

from src.collect import blocked_page, changes_from_snapshots, parse_metrics, parse_publications, parse_serpapi_metrics, parse_serpapi_publications

HTML = """
<div id="gsc_prf_in">Test Scholar</div>
<table id="gsc_rsb_st"><thead><tr><th></th><th>All</th><th>Since 2021</th></tr></thead><tbody>
<tr><td>Citations</td><td>1,234</td><td>900</td></tr>
<tr><td>h-index</td><td>20</td><td>18</td></tr>
<tr><td>i10-index</td><td>30</td><td>28</td></tr>
</tbody></table>
<tr class="gsc_a_tr"><td><a class="gsc_a_at" href="/citations?citation_for_view=bALkDW4AAAAJ:abc123">A paper title</a><div class="gs_gray">A Author</div><div class="gs_gray">Journal</div></td><td><a class="gsc_a_ac">42*</a></td><td class="gsc_a_y"><span>2024</span></td></tr>
"""

SERPAPI = {
    "author": {"name": "Test Scholar"},
    "cited_by": {
        "table": [
            {"citations": {"all": 1234, "since_2021": 900}},
            {"h_index": {"all": 20, "since_2021": 18}},
            {"i10_index": {"all": 30, "since_2021": 28}},
        ]
    },
    "articles": [
        {
            "title": "A paper title",
            "citation_id": "bALkDW4AAAAJ:abc123",
            "authors": "A Author",
            "publication": "Journal",
            "year": "2024",
            "cited_by": {"value": 42},
        }
    ],
}


class ParserTests(unittest.TestCase):
    def test_metrics_and_publications(self):
        soup = BeautifulSoup(HTML, "html.parser")
        metrics = parse_metrics(soup)
        publications = parse_publications(soup)
        self.assertEqual(metrics["total_citations"], 1234)
        self.assertEqual(metrics["recent_since_year"], "2021")
        self.assertEqual(publications[0]["paper_id"], "abc123")
        self.assertEqual(publications[0]["citations"], 42)

    def test_serpapi_metrics_and_publications(self):
        metrics = parse_serpapi_metrics(SERPAPI)
        publications = parse_serpapi_publications(SERPAPI)
        self.assertEqual(metrics["total_citations"], 1234)
        self.assertEqual(metrics["recent_since_year"], "2021")
        self.assertEqual(publications[0]["paper_id"], "abc123")
        self.assertEqual(publications[0]["citations"], 42)

    def test_change_detection(self):
        previous = {"abc": {"paper_id": "abc", "title": "Paper", "citations": "10"}}
        current = {"abc": {"paper_id": "abc", "title": "Paper", "citations": 7}}
        changes = changes_from_snapshots(previous, current, "2026-08-05T00:00:00Z")
        self.assertEqual(changes[0]["delta"], -3)
        self.assertEqual(changes[0]["change_type"], "citation_decrease")

    def test_block_detection(self):
        self.assertTrue(blocked_page("Our systems have detected unusual traffic"))
        self.assertFalse(blocked_page(HTML))


if __name__ == "__main__":
    unittest.main()
