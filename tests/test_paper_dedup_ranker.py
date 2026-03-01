from gpt_researcher.papers.models import PaperRecord
from gpt_researcher.papers.tools import PaperDedupRanker


def test_paper_dedup_ranker_deduplicate_by_doi():
    ranker = PaperDedupRanker()
    records = [
        PaperRecord(
            title="A",
            abstract="first",
            url="https://doi.org/10.1000/x",
            source="crossref",
            doi="10.1000/x",
        ),
        PaperRecord(
            title="A duplicate",
            abstract="better abstract",
            url="https://example.com/paper",
            source="openalex",
            doi="10.1000/x",
            oa_pdf_url="https://example.com/paper.pdf",
            is_open_access=True,
        ),
        PaperRecord(
            title="B",
            abstract="other",
            url="https://arxiv.org/abs/1234.5678",
            source="arxiv",
        ),
    ]

    deduped = ranker.deduplicate(records)
    assert len(deduped) == 2
    assert any(r.doi == "10.1000/x" and r.oa_pdf_url for r in deduped)


def test_paper_dedup_ranker_rank():
    ranker = PaperDedupRanker()
    records = [
        PaperRecord(
            title="Massive MIMO beamforming for 6G",
            abstract="Includes channel estimation and RIS",
            url="u1",
            source="openalex",
            year=2025,
            is_open_access=True,
        ),
        PaperRecord(
            title="General machine learning paper",
            abstract="No communication terms",
            url="u2",
            source="openalex",
            year=2019,
        ),
    ]
    ranked = ranker.rank(records, query="6G massive MIMO beamforming", max_papers=2)
    assert ranked[0].title.startswith("Massive MIMO")
