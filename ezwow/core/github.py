"""Lightweight GitHub API client with ETag conditional caching."""

from __future__ import annotations

import json
import logging
import pathlib
from dataclasses import dataclass
from typing import Any

import requests

API_ROOT = "https://api.github.com"
TIMEOUT = 10
log = logging.getLogger(__name__)

JsonDict = dict[str, Any]


@dataclass
class _CacheEntry:
    etag: str
    body: JsonDict


class GitHubClient:
    def __init__(self, *, cache_dir: pathlib.Path, token: str | None = None) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token = token
        self.session = requests.Session()

    def _headers(self, etag: str | None) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if etag:
            headers["If-None-Match"] = etag
        return headers

    def _cache_path(self, key: str) -> pathlib.Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, key: str) -> _CacheEntry | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _CacheEntry(etag=data["etag"], body=data["body"])
        except (json.JSONDecodeError, KeyError):
            return None

    def _write_cache(self, key: str, entry: _CacheEntry) -> None:
        path = self._cache_path(key)
        path.write_text(
            json.dumps({"etag": entry.etag, "body": entry.body}),
            encoding="utf-8",
        )

    def _get_with_cache(self, key: str, url: str) -> JsonDict | None:
        cached = self._read_cache(key)
        try:
            resp = self.session.get(
                url,
                headers=self._headers(cached.etag if cached else None),
                timeout=TIMEOUT,
            )
        except (requests.RequestException, OSError) as exc:
            log.warning("github GET %s failed: %s", url, exc)
            return cached.body if cached else None
        if resp.status_code == 304 and cached:
            return cached.body
        if resp.status_code == 200:
            try:
                body: JsonDict = resp.json()
            except ValueError:
                log.warning("github returned non-JSON for %s", url)
                return None
            etag = resp.headers.get("ETag", "")
            self._write_cache(key, _CacheEntry(etag=etag, body=body))
            return body
        if resp.status_code == 404:
            return None
        log.warning("github GET %s returned %d", url, resp.status_code)
        return cached.body if cached else None

    def branch_head_sha(self, repo: str, branch: str) -> str | None:
        url = f"{API_ROOT}/repos/{repo}/branches/{branch}"
        body = self._get_with_cache(f"branch:{repo}:{branch}", url)
        if not body:
            return None
        commit = body.get("commit", {})
        sha = commit.get("sha") if isinstance(commit, dict) else None
        return sha if isinstance(sha, str) else None

    def latest_release_tag(self, repo: str) -> str | None:
        url = f"{API_ROOT}/repos/{repo}/releases/latest"
        body = self._get_with_cache(f"release:{repo}", url)
        if not body:
            return None
        tag = body.get("tag_name")
        return tag if isinstance(tag, str) else None

    def latest_release_assets(self, repo: str) -> list[JsonDict]:
        url = f"{API_ROOT}/repos/{repo}/releases/latest"
        body = self._get_with_cache(f"release:{repo}", url)
        if not body:
            return []
        assets = body.get("assets", [])
        return assets if isinstance(assets, list) else []
