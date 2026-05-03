"""Verify every catalog URL resolves with HTTP HEAD <400."""

from __future__ import annotations

import json
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "addons.json"


def main() -> int:
    raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    failures: list[tuple[str, str, int]] = []

    for addon in raw.get("addons", []):
        url = (
            f"https://github.com/{addon['github']}/archive/"
            f"refs/heads/{addon.get('branch', 'master')}.zip"
        )
        try:
            resp = requests.head(url, allow_redirects=True, timeout=15)
        except requests.RequestException as exc:
            failures.append((addon["id"], url, -1))
            print(f"FAIL {addon['id']:30s} {url}  ({exc})")
            continue
        if resp.status_code >= 400:
            failures.append((addon["id"], url, resp.status_code))
            print(f"FAIL {addon['id']:30s} {url}  HTTP {resp.status_code}")
        else:
            print(f"OK   {addon['id']:30s} {url}")

    if failures:
        print(f"\n{len(failures)} broken URLs", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
