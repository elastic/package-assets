# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os

assets_dir = os.path.dirname(__file__)
bases = ("production", "staging", "snapshot")


def walk():
    """
    Traverse all the local assets.

    :return: generator yielding (base, package, version) of all the local assets
    """

    for base in bases:
        for asset_base, packages, _ in os.walk(os.path.join(assets_dir, base)):
            for package in packages:
                for _, versions, _ in os.walk(os.path.join(asset_base, package)):
                    for version in versions:
                        yield base, package, version
                    break
            break


def get_meta(base, package, version):
    """
    Get the meta-data of a local asset.

    :param base: one among 'production', 'staging', 'snapshot'
    :param package: package name, ex. 'endpoint'
    :param version: package version, ex. '8.3.0'
    :return: dictionary containing the meta-data
    """

    import yaml

    meta_filename = os.path.join(assets_dir, base, package, version, "meta.yml")
    if os.path.exists(meta_filename):
        with open(meta_filename) as f:
            return yaml.safe_load(f)


def get_remote_assets(package, repo):
    """
    Retrieve the list of a package's remote assets.

    :param package: name and version of the package, ex. 'endpoint/8.3.0'
    :param repo: repository object searched for the assets
    :return: generator yielding the remote assets entries
    """

    from github import GithubException

    for branch in bases:
        try:
            contents = repo.get_contents(package, ref=branch)
        except GithubException:
            continue

        while contents:
            content = contents.pop(0)
            if content.type == "dir":
                contents += repo.get_contents(content.path, ref=branch)
            else:
                yield content
        break


def download_assets(package, entries, outdir):
    """
    Download the assets of a package.

    :param package: name and version of the package, ex. 'endpoint/8.3.0'
    :param entries: assets entries as generated by :py:func:`.get_assets`
    :param outdir: directory where the assets are saved to
    :return: number of assets downloaded
    """

    from requests_futures.sessions import FuturesSession
    from concurrent.futures import as_completed

    session = FuturesSession()
    futures = []

    for entry in entries:
        future = session.get(entry.download_url)
        future.entry = entry
        futures.append(future)

    for future in as_completed(futures):
        res = future.result()
        res.raise_for_status()

        filename = future.entry.path.replace(package, outdir)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(res.content)

    session.close()
    return len(futures)
