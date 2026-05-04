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


@responses.activate
def test_default_branch_returns_value(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y",
        json={"default_branch": "main"},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.default_branch("x/y") == "main"


@responses.activate
def test_default_branch_returns_none_on_404(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/missing/repo",
        status=404,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.default_branch("missing/repo") is None


@responses.activate
def test_default_branch_returns_none_when_field_missing(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y",
        json={"name": "y"},  # no default_branch field
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.default_branch("x/y") is None


@responses.activate
def test_get_falls_back_to_cache_on_network_error(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        json={"commit": {"sha": "cached-sha"}},
        status=200,
        headers={"ETag": "et"},
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("x/y", "master") == "cached-sha"

    # Now next call raises ConnectionError — should fall back to cache
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        body=ConnectionError("offline"),
    )
    assert client.branch_head_sha("x/y", "master") == "cached-sha"


@responses.activate
def test_get_returns_none_on_network_error_with_no_cache(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        body=ConnectionError("offline"),
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("x/y", "master") is None


@responses.activate
def test_get_returns_none_on_non_json_200(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        body="this is not json",
        status=200,
        content_type="application/json",
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("x/y", "master") is None


@responses.activate
def test_get_handles_5xx_by_returning_cache_or_none(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        status=500,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("x/y", "master") is None


@responses.activate
def test_latest_release_tag_returns_none_on_404(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/missing/repo/releases/latest",
        status=404,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.latest_release_tag("missing/repo") is None


@responses.activate
def test_latest_release_assets_returns_empty_on_404(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/missing/repo/releases/latest",
        status=404,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.latest_release_assets("missing/repo") == []


@responses.activate
def test_latest_release_assets_returns_assets_list(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/releases/latest",
        json={"tag_name": "v1", "assets": [{"name": "a.zip"}]},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.latest_release_assets("x/y") == [{"name": "a.zip"}]


def test_corrupt_cache_file_treated_as_miss(tmp_path: pathlib.Path):
    """A corrupt cache file shouldn't crash the client — just treat it as a miss."""
    client = gh.GitHubClient(cache_dir=tmp_path)
    cache_file = client._cache_path("branch:x/y:master")
    cache_file.write_text("{not json")
    assert client._read_cache("branch:x/y:master") is None


def test_cache_file_missing_required_keys_treated_as_miss(tmp_path: pathlib.Path):
    client = gh.GitHubClient(cache_dir=tmp_path)
    cache_file = client._cache_path("branch:x/y:master")
    cache_file.write_text('{"foo": "bar"}')  # valid JSON, missing etag/body
    assert client._read_cache("branch:x/y:master") is None
