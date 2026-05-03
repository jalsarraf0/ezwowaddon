"""Tests for github API client."""

from __future__ import annotations

import pathlib

import responses

from ezwow.core import github as gh


@responses.activate
def test_branch_head_sha_success(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/shagu/pfQuest/branches/master",
        json={"commit": {"sha": "abc123"}},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("shagu/pfQuest", "master") == "abc123"


@responses.activate
def test_branch_head_sha_uses_cache_on_etag(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        json={"commit": {"sha": "first"}},
        status=200,
        headers={"ETag": "et1"},
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        status=304,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("x/y", "master") == "first"
    assert client.branch_head_sha("x/y", "master") == "first"


@responses.activate
def test_branch_head_sha_returns_none_on_404(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/missing/repo/branches/master",
        status=404,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("missing/repo", "master") is None


@responses.activate
def test_latest_release_tag(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/releases/latest",
        json={"tag_name": "v1.2.3", "assets": []},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.latest_release_tag("x/y") == "v1.2.3"


@responses.activate
def test_token_added_when_configured(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        json={"commit": {"sha": "z"}},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path, token="secrettoken")
    client.branch_head_sha("x/y", "master")
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.headers["Authorization"] == "Bearer secrettoken"
