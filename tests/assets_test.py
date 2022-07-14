# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os
import pytest

import assets


@pytest.fixture
def tmpdir():
    from tempfile import mkdtemp
    from shutil import rmtree

    d = mkdtemp()
    yield d
    rmtree(d)


@pytest.fixture
def repo():
    from github import Github

    gh = Github(os.getenv("GITHUB_TOKEN_ASSETS") or None)
    return gh.get_repo("elastic/package-assets")


@pytest.fixture
def package():
    return "endpoint/8.3.0"


@pytest.fixture
def entries(package, repo):
    return assets.get_remote_assets(package, repo)


def test_get_remote_assets(package, repo):
    entries = assets.get_remote_assets(package, repo)
    assert len(list(entries)) == 60


def test_download_assets(package, entries, tmpdir):
    count = assets.download_assets(package, entries, tmpdir)
    assert count == 60
