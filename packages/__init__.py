# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os

packages_dir = os.path.dirname(__file__)


def walk():
    for base in ("production", "staging", "snapshot"):
        for asset_base, packages, _ in os.walk(os.path.join(packages_dir, base, "packages")):
            for package in packages:
                for _, versions, _ in os.walk(os.path.join(asset_base, package)):
                    for version in versions:
                        yield base, package, version
                    break
            break


def get_manifest(base, package, version):
    import yaml

    meta_filename = os.path.join(packages_dir, base, "packages", package, version, "manifest.yml")
    if os.path.exists(meta_filename):
        with open(meta_filename) as f:
            return yaml.safe_load(f)
