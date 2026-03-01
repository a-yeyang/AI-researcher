from gpt_researcher.retrievers.unpaywall.unpaywall import UnpaywallResolver


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_unpaywall_resolver_resolve_doi(monkeypatch):
    payload = {
        "title": "Test Paper",
        "doi": "10.1000/test",
        "year": 2024,
        "journal_name": "IEEE X",
        "is_oa": True,
        "oa_status": "gold",
        "best_oa_location": {
            "url_for_pdf": "https://example.com/test.pdf",
            "url": "https://example.com/test",
        },
    }

    def _mock_get(*args, **kwargs):
        return _MockResponse(payload)

    monkeypatch.setenv("UNPAYWALL_EMAIL", "test@example.com")
    monkeypatch.setattr("gpt_researcher.retrievers.unpaywall.unpaywall.requests.get", _mock_get)

    resolver = UnpaywallResolver(query="")
    result = resolver.resolve_doi("10.1000/test")

    assert result is not None
    assert result["doi"] == "10.1000/test"
    assert result["oa_pdf_url"] == "https://example.com/test.pdf"
    assert result["is_open_access"] is True
