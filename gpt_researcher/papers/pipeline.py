"""Academic paper research pipeline."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from ..actions.retriever import get_retriever
from .cache import PaperCache
from .models import AcademicPipelineResult, PaperRecord
from .tools import (
    CitationGraphAnalyzer,
    CommDomainQueryPlanner,
    FullTextFetcher,
    LongPaperSummarizer,
    PaperDedupRanker,
    PaperParser,
)

logger = logging.getLogger(__name__)


class AcademicResearchPipeline:
    """Run OA-oriented academic retrieval + summarization."""

    def __init__(self, researcher):
        self.researcher = researcher
        self.config = self._normalize_config(getattr(researcher, "academic_config", {}) or {})
        self.cache = PaperCache(ttl_seconds=self.config["cache_ttl_seconds"])
        self.query_planner = CommDomainQueryPlanner()
        self.ranker = PaperDedupRanker()
        self.fetcher = FullTextFetcher(cache=self.cache)
        self.parser = PaperParser()
        self.summarizer = LongPaperSummarizer(researcher)
        self.citation_analyzer = CitationGraphAnalyzer()
        self.crossref_cls = get_retriever("crossref")
        self.unpaywall_cls = get_retriever("unpaywall")

    @staticmethod
    def _normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
        sources = raw.get("sources") or ["arxiv", "semantic_scholar", "openalex", "core"]
        if isinstance(sources, str):
            sources = [s.strip() for s in sources.split(",") if s.strip()]
        return {
            "sources": sources,
            "year_from": int(raw["year_from"]) if raw.get("year_from") else None,
            "year_to": int(raw["year_to"]) if raw.get("year_to") else None,
            "oa_only": bool(raw.get("oa_only", True)),
            "max_papers": int(raw.get("max_papers", 12)),
            "summarize_long_paper": bool(raw.get("summarize_long_paper", True)),
            "max_summary_papers": int(raw.get("max_summary_papers", 3)),
            "cache_ttl_seconds": int(raw.get("cache_ttl_seconds", 7 * 24 * 3600)),
        }

    async def run(self, query: str) -> AcademicPipelineResult:
        queries = self.query_planner.plan(query=query, max_queries=4)
        if self.researcher.verbose:
            from ..actions.utils import stream_output
            await stream_output(
                "logs",
                "academic_planning",
                f"Using academic mode with queries: {queries}",
                self.researcher.websocket,
            )

        records = await self._retrieve_records(queries)
        if not records:
            return AcademicPipelineResult(context="", papers=[], summaries=[])

        records = self.ranker.deduplicate(records)
        records = await self._enrich_records(records)
        records = self._filter_records(records)
        records = self.ranker.rank(records, query=query, max_papers=self.config["max_papers"])
        records = self.citation_analyzer.analyze(records)

        summaries = []
        if self.config["summarize_long_paper"]:
            summaries = await self._summarize_long_papers(records, query=query)

        context = self._build_context(records=records, summaries=summaries)
        return AcademicPipelineResult(context=context, papers=records, summaries=summaries)

    async def _retrieve_records(self, queries: list[str]) -> list[PaperRecord]:
        tasks = []
        for source in self.config["sources"]:
            for query in queries:
                tasks.append(self._search_source(source=source, query=query))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_records: list[PaperRecord] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Academic source search failed: %s", result)
                continue
            all_records.extend(result)
        return all_records

    async def _search_source(self, source: str, query: str) -> list[PaperRecord]:
        retriever_cls = get_retriever(source)
        if retriever_cls is None:
            logger.warning("Academic source '%s' is not registered", source)
            return []

        try:
            retriever = retriever_cls(query=query, query_domains=self.researcher.query_domains)
        except TypeError:
            retriever = retriever_cls(query=query)

        raw_results = await asyncio.to_thread(
            retriever.search,
            self.researcher.cfg.max_search_results_per_query * 2
        )
        if not raw_results:
            return []
        return [self._normalize_record(source=source, data=item) for item in raw_results]

    async def _enrich_records(self, records: list[PaperRecord]) -> list[PaperRecord]:
        if not records:
            return records

        crossref = self.crossref_cls(query="") if self.crossref_cls else None
        unpaywall = self.unpaywall_cls(query="") if self.unpaywall_cls else None

        async def enrich_one(record: PaperRecord) -> PaperRecord:
            if record.doi and crossref and hasattr(crossref, "enrich_by_doi"):
                try:
                    enriched = await asyncio.to_thread(crossref.enrich_by_doi, record.doi)
                    if enriched:
                        record.title = record.title or enriched.get("title", "")
                        record.venue = record.venue or enriched.get("venue")
                        record.year = record.year or enriched.get("year")
                        record.url = record.url or enriched.get("url", "")
                except Exception:
                    pass

            if record.doi and not record.oa_pdf_url and unpaywall and hasattr(unpaywall, "resolve_doi"):
                try:
                    resolved = await asyncio.to_thread(unpaywall.resolve_doi, record.doi)
                    if resolved:
                        record.oa_pdf_url = resolved.get("oa_pdf_url") or record.oa_pdf_url
                        record.is_open_access = bool(resolved.get("is_open_access") or record.is_open_access)
                        record.url = record.url or resolved.get("href", "")
                except Exception:
                    pass
            return record

        return list(await asyncio.gather(*[enrich_one(r) for r in records]))

    def _normalize_record(self, source: str, data: dict[str, Any]) -> PaperRecord:
        title = str(data.get("title", "")).strip()
        abstract = str(data.get("body") or data.get("abstract") or "").strip()
        url = str(data.get("href") or data.get("url") or "").strip()
        doi = data.get("doi")
        if not doi:
            doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", url)
            doi = doi_match.group(0) if doi_match else None

        year = data.get("year")
        try:
            year = int(year) if year is not None else None
        except (TypeError, ValueError):
            year = None

        oa_pdf_url = data.get("oa_pdf_url") or data.get("pdf_url")
        is_oa = bool(data.get("is_open_access") or oa_pdf_url)

        return PaperRecord(
            title=title,
            abstract=abstract,
            url=url,
            source=source,
            doi=doi,
            year=year,
            venue=data.get("venue"),
            oa_pdf_url=oa_pdf_url,
            is_open_access=is_oa,
            citation_count=data.get("citation_count"),
            raw=data,
        )

    def _filter_records(self, records: list[PaperRecord]) -> list[PaperRecord]:
        filtered: list[PaperRecord] = []
        year_from = self.config["year_from"]
        year_to = self.config["year_to"]
        for r in records:
            if year_from and r.year and r.year < year_from:
                continue
            if year_to and r.year and r.year > year_to:
                continue
            if self.config["oa_only"] and not (r.is_open_access or r.oa_pdf_url):
                continue
            filtered.append(r)
        return filtered

    async def _summarize_long_papers(self, records: list[PaperRecord], query: str):
        summaries = []
        max_summary = min(self.config["max_summary_papers"], len(records))

        for record in records[:max_summary]:
            if not (record.oa_pdf_url or record.url):
                continue
            cache_key = f"{record.doi or ''}|{record.oa_pdf_url or record.url}"
            cached_summary = self.cache.get_json("summary", cache_key)
            if cached_summary:
                summaries.append(self.summarizer.from_cache_payload(cached_summary))
                continue

            fulltext = await asyncio.to_thread(self.fetcher.fetch, record)
            if not fulltext:
                continue
            fulltext = self.parser.parse(fulltext)
            summary = await self.summarizer.summarize(fulltext, query=query)
            if not summary:
                continue
            self.cache.set_json("summary", cache_key, self.summarizer.to_cache_payload(summary))
            summaries.append(summary)

        return summaries

    def _build_context(self, records: list[PaperRecord], summaries: list) -> str:
        lines = []
        for i, record in enumerate(records, start=1):
            lines.append(
                f"[Paper {i}] {record.title}\n"
                f"Source: {record.source}\n"
                f"Year: {record.year or 'N/A'}\n"
                f"Venue: {record.venue or 'N/A'}\n"
                f"DOI: {record.doi or 'N/A'}\n"
                f"URL: {record.oa_pdf_url or record.url}\n"
                f"Abstract: {record.abstract or 'N/A'}\n"
            )

        for j, summary in enumerate(summaries, start=1):
            lines.append(
                f"[Long Paper Summary {j}] {summary.title}\n"
                f"Source URL: {summary.source_url}\n"
                f"Global Summary:\n{summary.global_summary}\n\n"
                f"Query-focused Summary:\n{summary.query_focused_summary}\n"
            )

        return "\n---\n".join(lines)
