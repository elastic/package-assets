# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os
import json

assets_dir = os.path.dirname(__file__)


def walk():
    for base in ("release", "staging", "snapshot", "git"):
        for asset_base, packages, _ in os.walk(os.path.join(assets_dir, base)):
            for package in packages:
                for _, versions, _ in os.walk(os.path.join(asset_base, package)):
                    for version in versions:
                        yield base, package, version
                    break
            break


def get_meta(base, package, version):
    meta_filename = os.path.join(assets_dir, base, package, version, "meta.json")
    if os.path.exists(meta_filename):
        with open(meta_filename) as f:
            return json.load(f)
