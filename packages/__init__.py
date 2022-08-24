# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os
from pathlib import Path

packages_dir = Path(__file__).parent


def walk():
    for branch in ("production", "staging", "snapshot"):
        for asset_branch, packages, _ in os.walk(packages_dir / branch / "packages"):
            for package in packages:
                for _, versions, _ in os.walk(Path(asset_branch) / package):
                    for version in versions:
                        yield branch, package, version
                    break
            break


def get_manifest(branch, package, version):
    import yaml

    meta_filename = packages_dir / branch / "packages" / package / version / "manifest.yml"
    if meta_filename.exists():
        with open(meta_filename) as f:
            return yaml.safe_load(f)
