"""Crossref API retriever and enricher."""

from __future__ import annotations

from typing import Any

import requests


class CrossrefSearch:
    """Search and enrich paper metadata via Crossref."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, query: str, query_domains=None):
        self.query = query

    def search(self, max_results: int = 20) -> list[dict[str, Any]]:
        params = {"query": self.query, "rows": max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            items = response.json().get("message", {}).get("items", [])
        except requests.RequestException:
            return []

        results = []
        for item in items:
            doi = item.get("DOI")
            title_list = item.get("title") or []
            abstract = item.get("abstract") or ""
            published = (item.get("issued") or {}).get("date-parts", [[]])[0]
            year = published[0] if published else None
            url = item.get("URL") or (doi and f"https://doi.org/{doi}") or ""
            venue = (item.get("container-title") or [""])[0]
            results.append(
                {
                    "title": title_list[0] if title_list else "",
                    "href": url,
                    "body": abstract,
                    "doi": doi,
                    "year": year,
                    "venue": venue,
                    "is_open_access": False,
                }
            )
        return results

    def enrich_by_doi(self, doi: str) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.BASE_URL}/{doi}", timeout=20)
            response.raise_for_status()
            item = response.json().get("message", {})
        except requests.RequestException:
            return {}

        title_list = item.get("title") or []
        published = (item.get("issued") or {}).get("date-parts", [[]])[0]
        year = published[0] if published else None
        return {
            "title": title_list[0] if title_list else "",
            "doi": item.get("DOI"),
            "venue": (item.get("container-title") or [""])[0],
            "year": year,
            "url": item.get("URL"),
        }
