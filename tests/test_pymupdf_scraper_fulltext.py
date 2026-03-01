from types import SimpleNamespace

from gpt_researcher.scraper.pymupdf.pymupdf import PyMuPDFScraper


class _MockLoader:
    def __init__(self, path):
        self.path = path

    def load(self):
        return [
            SimpleNamespace(page_content="Page one content", metadata={"title": "Mock Paper"}),
            SimpleNamespace(page_content="Page two content", metadata={"title": "Mock Paper"}),
        ]


def test_pymupdf_scraper_returns_multi_page_content(monkeypatch):
    monkeypatch.setattr("gpt_researcher.scraper.pymupdf.pymupdf.PyMuPDFLoader", _MockLoader)

    scraper = PyMuPDFScraper("dummy.pdf")
    content, images, title = scraper.scrape()

    assert "Page one content" in content
    assert "Page two content" in content
    assert "[Page 1]" in content
    assert "[Page 2]" in content
    assert images == []
    assert title == "Mock Paper"
