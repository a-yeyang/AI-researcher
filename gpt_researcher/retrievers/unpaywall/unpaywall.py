"""Unpaywall resolver for OA paper links."""

from __future__ import annotations

import os
from typing import Any

import requests


class UnpaywallResolver:
    """Resolve DOI to OA metadata using Unpaywall API."""

    BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self, query: str, query_domains=None):
        self.query = query
        self.email = os.getenv("UNPAYWALL_EMAIL") or os.getenv("CROSSREF_EMAIL")

    def search(self, max_results: int = 5) -> list[dict[str, Any]]:
        # Unpaywall is DOI-centric; interpret query as DOI for compatibility.
        if not self.query:
            return []
        resolved = self.resolve_doi(self.query)
        if not resolved:
            return []
        return [resolved]

    def resolve_doi(self, doi: str) -> dict[str, Any] | None:
        if not doi or not self.email:
            return None
        try:
            response = requests.get(
                f"{self.BASE_URL}/{doi}",
                params={"email": self.email},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return None

        best_location = payload.get("best_oa_location") or {}
        oa_url = best_location.get("url_for_pdf") or best_location.get("url")
        return {
            "title": payload.get("title", ""),
            "href": oa_url or payload.get("doi_url", ""),
            "body": payload.get("abstract") or "",
            "doi": payload.get("doi"),
            "year": payload.get("year"),
            "venue": payload.get("journal_name"),
            "is_open_access": bool(payload.get("is_oa")),
            "oa_pdf_url": oa_url,
            "oa_status": payload.get("oa_status"),
            "best_oa_location": best_location,
        }
