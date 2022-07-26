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
def path():
    return os.path.join(os.path.dirname(__file__), "..", "assets", "production")


@pytest.fixture
def package():
    return "endpoint/8.3.0"


@pytest.fixture
def invalid_package():
    return "invalid/a.b.c"


@pytest.fixture
def entries(package, repo):
    return assets.get_remote_assets(package, repo)


@pytest.fixture
def package_paths_list(package):
    return [
        f"{package}/component_templates/.fleet_agent_id_verification-1.json",
        f"{package}/component_templates/.fleet_globals-1.json",
        f"{package}/component_templates/.logs-endpoint.action.responses@custom.json",
        f"{package}/component_templates/.logs-endpoint.action.responses@package.json",
        f"{package}/component_templates/.logs-endpoint.actions@custom.json",
        f"{package}/component_templates/.logs-endpoint.actions@package.json",
        f"{package}/component_templates/.logs-endpoint.diagnostic.collection@custom.json",
        f"{package}/component_templates/.logs-endpoint.diagnostic.collection@package.json",
        f"{package}/component_templates/logs-endpoint.alerts@custom.json",
        f"{package}/component_templates/logs-endpoint.alerts@package.json",
        f"{package}/component_templates/logs-endpoint.events.file@custom.json",
        f"{package}/component_templates/logs-endpoint.events.file@package.json",
        f"{package}/component_templates/logs-endpoint.events.library@custom.json",
        f"{package}/component_templates/logs-endpoint.events.library@package.json",
        f"{package}/component_templates/logs-endpoint.events.network@custom.json",
        f"{package}/component_templates/logs-endpoint.events.network@package.json",
        f"{package}/component_templates/logs-endpoint.events.process@custom.json",
        f"{package}/component_templates/logs-endpoint.events.process@package.json",
        f"{package}/component_templates/logs-endpoint.events.registry@custom.json",
        f"{package}/component_templates/logs-endpoint.events.registry@package.json",
        f"{package}/component_templates/logs-endpoint.events.security@custom.json",
        f"{package}/component_templates/logs-endpoint.events.security@package.json",
        f"{package}/component_templates/metrics-endpoint.metadata@custom.json",
        f"{package}/component_templates/metrics-endpoint.metadata@package.json",
        f"{package}/component_templates/metrics-endpoint.metrics@custom.json",
        f"{package}/component_templates/metrics-endpoint.metrics@package.json",
        f"{package}/component_templates/metrics-endpoint.policy@custom.json",
        f"{package}/component_templates/metrics-endpoint.policy@package.json",
        f"{package}/ilm_policies/logs-endpoint.collection-diagnostic.json",
        f"{package}/ilm_policies/logs.json",
        f"{package}/ilm_policies/metrics.json",
        f"{package}/index_templates/.logs-endpoint.action.responses.json",
        f"{package}/index_templates/.logs-endpoint.actions.json",
        f"{package}/index_templates/.logs-endpoint.diagnostic.collection.json",
        f"{package}/index_templates/logs-endpoint.alerts.json",
        f"{package}/index_templates/logs-endpoint.events.file.json",
        f"{package}/index_templates/logs-endpoint.events.library.json",
        f"{package}/index_templates/logs-endpoint.events.network.json",
        f"{package}/index_templates/logs-endpoint.events.process.json",
        f"{package}/index_templates/logs-endpoint.events.registry.json",
        f"{package}/index_templates/logs-endpoint.events.security.json",
        f"{package}/index_templates/metrics-endpoint.metadata.json",
        f"{package}/index_templates/metrics-endpoint.metrics.json",
        f"{package}/index_templates/metrics-endpoint.policy.json",
        f"{package}/ingest_pipelines/.fleet_final_pipeline-1.json",
        f"{package}/ingest_pipelines/logs-endpoint.action.responses-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.actions-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.alerts-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.diagnostic.collection-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.events.file-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.events.library-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.events.network-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.events.process-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.events.registry-8.3.0.json",
        f"{package}/ingest_pipelines/logs-endpoint.events.security-8.3.0.json",
        f"{package}/ingest_pipelines/metrics-endpoint.metadata-8.3.0.json",
        f"{package}/ingest_pipelines/metrics-endpoint.metrics-8.3.0.json",
        f"{package}/ingest_pipelines/metrics-endpoint.policy-8.3.0.json",
        f"{package}/manifest.yml",
        f"{package}/meta.yml",
    ]


def test_get_local_assets(package, path, package_paths_list):
    contents = assets.get_local_assets(package, path)
    paths = sorted(c[0] for c in contents)
    assert paths == package_paths_list


def test_get_local_assets_invalid(invalid_package, path):
    with pytest.raises(ValueError) as exc:
        _ = list(assets.get_local_assets(invalid_package, path))
    assert str(exc.value) == f"Package not found: {invalid_package}"


def test_get_remote_assets(package, repo):
    entries = assets.get_remote_assets(package, repo)
    assert len(list(entries)) == 60


def test_get_remote_assets_invalid(invalid_package, repo):
    with pytest.raises(ValueError) as exc:
        _ = list(assets.get_remote_assets(invalid_package, repo))
    assert str(exc.value) == f"Package not found: {invalid_package}"


def test_download_assets(entries, package_paths_list):
    contents = assets.download_assets(entries)
    paths = sorted(c[0] for c in contents)
    assert paths == package_paths_list
