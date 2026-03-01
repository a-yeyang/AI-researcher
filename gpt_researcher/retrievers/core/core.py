"""CORE API retriever."""

from __future__ import annotations

import os
from typing import Any

import requests


class CoreSearch:
    """Search OA papers via CORE API."""

    BASE_URL = "https://api.core.ac.uk/v3/search/works"

    def __init__(self, query: str, query_domains=None):
        self.query = query
        self.api_key = os.getenv("CORE_API_KEY")

    def search(self, max_results: int = 20) -> list[dict[str, Any]]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        params = {"q": self.query, "limit": max_results}

        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return []

        items = payload.get("results") or payload.get("data") or []
        results = []
        for item in items:
            results.append(
                {
                    "title": item.get("title", ""),
                    "href": item.get("downloadUrl") or item.get("url") or "",
                    "body": item.get("abstract") or item.get("fullText") or "",
                    "doi": item.get("doi"),
                    "year": item.get("yearPublished"),
                    "venue": item.get("publisher"),
                    "is_open_access": bool(item.get("downloadUrl")),
                    "oa_pdf_url": item.get("downloadUrl"),
                    "citation_count": item.get("citationCount"),
                }
            )
        return results
