# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os
import pytest

import assets


@pytest.fixture
def repo():
    from github import Github

    gh = Github(os.getenv("GITHUB_TOKEN_ASSETS") or None)
    return gh.get_repo("elastic/package-assets")


@pytest.fixture
def package():
    return "endpoint/8.3.0"


@pytest.fixture
def invalid_package():
    return "invalid/a.b.c"


@pytest.fixture
def entries(package, repo):
    return assets.get_remote_assets(package, repo)


def test_get_remote_assets(package, repo):
    entries = assets.get_remote_assets(package, repo)
    assert len(list(entries)) == 60


def test_get_remote_assets_invalid(invalid_package, repo):
    with pytest.raises(ValueError) as exc:
        _ = list(assets.get_remote_assets(invalid_package, repo))
    assert str(exc.value) == f"Package not found: {invalid_package}"


def test_download_assets(entries):
    contents = assets.download_assets(entries)
    assert len(list(contents)) == 60
