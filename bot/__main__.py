# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import json
import click

import assets
from .epr import get_epr


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
@click.option("--pedantic", is_flag=True, help="Fail if something is wrong with local assets")
def meta(ctx, pedantic):
    for base, package, version in assets.walk():
        meta = assets.get_meta(base, package, version)
        if meta is None:
            if pedantic:
                click.echo(f"Missing {base}/{package}/{version}/meta.json", err=True)
                ctx.exit(1)
            continue
        asset = dict(base=base, package=package, version=version, meta=meta)
        click.echo(json.dumps(asset))


@cli.command()
def diff():
    local_assets = {}
    for base, package, version in assets.walk():
        meta = assets.get_meta(base, package, version)
        if meta is not None:
            local_assets.setdefault(base, {}).setdefault(package, {}).setdefault(version, meta)

    remote_assets = {}
    for base in local_assets:
        for package in local_assets[base]:
            versions = remote_assets.setdefault(base, {}).setdefault(package, {})
            if base == "release":
                for x in get_epr().search(package, True):
                    versions[x["version"]] = x

    for base in local_assets:
        for package in local_assets[base]:
            local_versions = set(local_assets[base][package])
            remote_versions = set(remote_assets[base][package])

            all_versions = local_versions | remote_versions
            only_local = local_versions - remote_versions
            only_remote = remote_versions - local_versions

            click.echo(f"--- remote/{base}/{package}")
            click.echo(f"+++ local/{base}/{package}")
            click.echo(f"@@ -1,{len(only_remote)} +1,{len(only_local)} @@")

            for version in sorted(all_versions):
                if version in only_remote:
                    click.echo(f"-{version}")
                elif version in only_local:
                    click.echo(f"+{version}")
                else:
                    click.echo(f" {version}")


if __name__ == "__main__":
    cli(prog_name="bot")
