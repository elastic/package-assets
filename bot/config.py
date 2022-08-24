# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import yaml
import semver


def flatten(tracked_packages):
    if type(tracked_packages) is not list:
        tracked_packages = [tracked_packages]

    flattened = {}
    for tracked_package in tracked_packages:
        if type(tracked_package) is str:
            tracked_package = {tracked_package: None}
        for name, package in tracked_package.items():
            flattened[name] = package or {}

    return flattened


def validate(config):
    tracked_packages = flatten(config.get("tracked-packages", {}))
    config["tracked-packages"] = tracked_packages

    for name, package in tracked_packages.items():
        branches = package.get("branches", None)
        if not branches:
            package["branches"] = ["production", "staging", "snapshot"]
        elif type(branches) == str:
            package["branches"] = [x.strip() for x in branches.split(",")]

        minimum_version = package.get("minimum-version", None)
        if minimum_version:
            v = (str(minimum_version).split(".") + [0, 0, 0])[:3]
            package["minimum-version"] = semver.VersionInfo(*v)

    return config


def load(filename):
    with open(filename) as f:
        return validate(yaml.safe_load(f))
