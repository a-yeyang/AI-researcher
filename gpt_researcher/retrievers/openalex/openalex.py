"""OpenAlex retriever."""

from __future__ import annotations

from typing import Any

import requests


class OpenAlexSearch:
    """Search papers from OpenAlex Works API."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, query: str, query_domains=None):
        self.query = query

    def search(self, max_results: int = 20) -> list[dict[str, Any]]:
        params = {
            "search": self.query,
            "per-page": max_results,
            "mailto": "support@gpt-researcher.local",
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return []

        results = []
        for item in payload.get("results", []):
            doi = item.get("doi")
            if doi and doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")
            primary_location = item.get("primary_location") or {}
            source = (primary_location.get("source") or {}).get("display_name")
            oa_url = primary_location.get("pdf_url")
            results.append(
                {
                    "title": item.get("title", ""),
                    "href": item.get("id", ""),
                    "body": item.get("abstract_inverted_index", {}) and self._collapse_abstract(item.get("abstract_inverted_index", {})) or "",
                    "doi": doi,
                    "year": item.get("publication_year"),
                    "venue": source,
                    "is_open_access": bool(oa_url),
                    "oa_pdf_url": oa_url,
                    "citation_count": item.get("cited_by_count"),
                }
            )
        return results

    @staticmethod
    def _collapse_abstract(inverted_index: dict[str, list[int]]) -> str:
        positions: dict[int, str] = {}
        for word, indexes in inverted_index.items():
            for idx in indexes:
                positions[idx] = word
        return " ".join(positions[i] for i in sorted(positions))
