# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os
import json
import click
import semver

import assets
import packages


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
@click.option("--pedantic", is_flag=True, help="Fail if something is wrong with local assets")
def meta(ctx, pedantic):
    for base, package, version in assets.walk():
        meta = assets.get_manifest(base, package, version)
        if meta is None:
            if pedantic:
                click.echo(f"Missing {base}/{package}/{version}/manifest.yml", err=True)
                ctx.exit(1)
            continue
        asset = dict(base=base, package=package, version=version, meta=meta)
        click.echo(json.dumps(asset))


@cli.command()
def diff():
    local_assets = {}
    for base, package, version in assets.walk():
        meta = assets.get_manifest(base, package, version)
        if meta is not None:
            local_assets.setdefault(base, {}).setdefault(package, {}).setdefault(version, meta)

    remote_assets = {}
    for base in local_assets:
        base_dir = os.path.join(packages.packages_dir, base, "packages")
        if not os.path.exists(base_dir):
            continue
        for package in local_assets[base]:
            package_dir = os.path.join(base_dir, package)
            if not os.path.exists(package_dir):
                continue
            versions = remote_assets.setdefault(base, {}).setdefault(package, {})
            for version in os.listdir(package_dir):
                versions[version] = packages.get_manifest(base, package, version)

    for base in remote_assets:
        for package in remote_assets[base]:
            local_versions = set(local_assets[base][package])
            remote_versions = set(remote_assets[base][package])
            both_versions = local_versions & remote_versions

            min_version = min(both_versions, key=semver.VersionInfo.parse)
            remote_versions = {v for v in remote_versions if semver.compare(v, min_version) >= 0}

            all_versions = local_versions | remote_versions
            only_local = local_versions - remote_versions
            only_remote = remote_versions - local_versions

            click.echo(f"--- remote/{base}/{package}")
            click.echo(f"+++ local/{base}/{package}")
            click.echo(f"@@ -1,{len(only_remote)} +1,{len(only_local)} @@")

            for version in sorted(all_versions, key=semver.VersionInfo.parse):
                if version in only_remote:
                    click.echo(f"-{version}")
                elif version in only_local:
                    click.echo(f"+{version}")
                else:
                    click.echo(f" {version}")


if __name__ == "__main__":
    cli(prog_name="bot")
