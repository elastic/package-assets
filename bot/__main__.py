# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import os
import json
import yaml
import click
import semver
import subprocess
import requests
from pathlib import Path

import assets
import packages

config = {}


def get_stack_version():
    es_url = os.getenv("ELASTIC_PACKAGE_ELASTICSEARCH_HOST")
    es_user = os.getenv("ELASTIC_PACKAGE_ELASTICSEARCH_USERNAME")
    es_pass = os.getenv("ELASTIC_PACKAGE_ELASTICSEARCH_PASSWORD")

    if not es_url or not es_user or not es_pass:
        return None

    res = requests.get(es_url, auth=(es_user, es_pass), verify=False)
    res.raise_for_status()
    return res.json()["version"]["number"]


def make_plan(branches):
    tracked_packages = config.get("tracked-packages", {})

    local_assets = {}
    for branch, package, version in assets.walk():
        meta = assets.get_meta(branch, package, version)
        if meta is not None:
            local_assets.setdefault(package, {}).setdefault(branch, {}).setdefault(version, meta)

    remote_assets = {}
    for package in tracked_packages:
        for branch in tracked_packages[package]["branches"]:
            package_dir = packages.packages_dir / branch / "packages" / package
            if package_dir.exists():
                for version in os.listdir(package_dir):
                    meta = packages.get_manifest(branch, package, version)
                    if meta is not None:
                        remote_assets.setdefault(package, {}).setdefault(branch, {}).setdefault(version, meta)

    for package in remote_assets:
        for branch in remote_assets[package]:
            local_versions = set(local_assets.get(package, {}).get(branch, {}))
            remote_versions = set(remote_assets[package][branch])

            min_version = tracked_packages[package].get("minimum-version", 0)
            if min_version:
                remote_versions = {v for v in remote_versions if v >= min_version or v in local_versions}

            all_versions = local_versions | remote_versions
            only_local = local_versions - remote_versions
            only_remote = remote_versions - local_versions

            yield (package, branch, all_versions, only_local, only_remote)


@click.group()
@click.pass_context
@click.option("--config", "conf_file", default="config.yaml", show_default=True, help="Path to the configuration file.")
def cli(ctx, conf_file):
    from .config import load

    try:
        global config
        if Path(conf_file).exists():
            config = load(conf_file)
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
@click.option("--pedantic", is_flag=True, help="Fail if something is wrong with local assets")
def meta(ctx, pedantic):
    """ Print the meta info of all the stored assets """
    for branch, package, version in assets.walk():
        meta = assets.get_meta(branch, package, version)
        if meta is None:
            if pedantic:
                click.echo(f"Missing or empty meta: assets/{branch}/{package}/{version}/meta.yml", err=True)
                ctx.exit(1)
            continue
        asset = dict(branch=branch, package=package, version=version, meta=meta)
        click.echo(json.dumps(asset))


@cli.command()
@click.option("--branches", help="Comma separated list of branches - es: staging,snapshot")
def plan(branches):
    """ Print the update plan in a diff-like format """

    if branches:
        branches = [b.strip() for b in branches.split(",")]

    for (package, branch, all_versions, only_local, only_remote) in make_plan(branches):
        if only_local or only_remote:
            click.echo(f"--- remote/{package}/{branch}")
            click.echo(f"+++ local/{package}/{branch}")
            click.echo(f"@@ -1,{len(only_remote)} +1,{len(only_local)} @@")

            for version in sorted(all_versions, key=semver.VersionInfo.parse):
                if version in only_remote:
                    click.echo(f"-{version}")
                elif version in only_local:
                    click.echo(f"+{version}")
                else:
                    click.echo(f" {version}")


@cli.command()
@click.pass_context
@click.option("--branches", help="Comma separated list of branches - es: staging,snapshot")
def update(ctx, branches):
    """ Perform the assets updates """

    stack_version = get_stack_version()
    if not stack_version:
        click.echo("Forgot to 'eval \"$(elastic-package stack shellinit)\"' in your shell?", err=True)
        ctx.exit(1)

    meta = {
        "stack": {
            "version": stack_version,
        },
    }

    if branches:
        branches = [b.strip() for b in branches.split(",")]

    for (package, branch, all_versions, only_local, only_remote) in make_plan(branches):
        for version in sorted(only_remote, key=semver.VersionInfo.parse):
            package_dir = packages.packages_dir / branch / "packages" / package / version
            click.echo(f"install package from {package_dir}")
            args = ["elastic-package", "install", package]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=package_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            asset_dir = assets.assets_dir / branch / package / version
            click.echo(f"export assets to {asset_dir}")
            args = ["elastic-package", "dump", "installed-objects", "--package", package, "--output", asset_dir]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=assets.assets_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            click.echo("copy manifest")
            args = ["cp", "-v", package_dir / "manifest.yml", asset_dir]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=asset_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            click.echo("write meta")
            with open(asset_dir / "meta.yml", "w+") as f:
                yaml.dump(meta, f)

            click.echo(f"git: add {asset_dir}...")
            args = ["git", "add", "*"]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=asset_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            click.echo(f"git: commit {asset_dir}...")
            args = ["git", "commit", "-n", "-m", f"Add assets: {package} {version} ({branch}, {stack_version})"]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=asset_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)


@cli.command()
@click.pass_context
@click.argument("PACKAGE")
@click.argument("OUTPUT_DIR")
def download(ctx, package, output_dir):
    """ Download the assets of a given package

    PACKAGE whose assets are to be downloaded - es: endpoint/8.2.3
    OUTPUT_DIR directory where the assets are downloaded to
    """

    from github import Github

    github = Github(os.getenv("GITHUB_TOKEN_ASSETS") or None)
    repo = github.get_repo("elastic/package-assets")
    entries = assets.get_remote_assets(package, repo)

    count = 0
    for entry, content in assets.download_assets(entries):
        filename = entry.path.replace(package, output_dir)

        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "wb") as f:
            f.write(content)

        count += 1

    if count:
        click.echo(f"Saved {count} assets")
    else:
        click.echo(f"Not found: {package}", err=True)
        ctx.exit(1)


if __name__ == "__main__":
    cli(prog_name="bot")
