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

import assets
import packages


def get_stack_version():
    es_url = os.getenv("ELASTIC_PACKAGE_ELASTICSEARCH_HOST")
    es_user = os.getenv("ELASTIC_PACKAGE_ELASTICSEARCH_USERNAME")
    es_pass = os.getenv("ELASTIC_PACKAGE_ELASTICSEARCH_PASSWORD")

    if not es_url or not es_user or not es_pass:
        return None

    res = requests.get(es_url, auth=(es_user, es_pass), verify=False)
    res.raise_for_status()
    return res.json()["version"]["number"]


def make_plan(bases):
    local_assets = {}
    for base, package, version in assets.walk():
        if not bases or base in bases:
            meta = assets.get_meta(base, package, version)
            if meta is not None:
                local_assets.setdefault(base, {}).setdefault(package, {}).setdefault(version, meta)

    remote_assets = {}
    for base in local_assets:
        base_dir = os.path.join(packages.packages_dir, base, "packages")
        if os.path.exists(base_dir):
            for package in local_assets[base]:
                package_dir = os.path.join(base_dir, package)
                if os.path.exists(package_dir):
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

            yield (base, package, all_versions, only_local, only_remote)


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
@click.option("--pedantic", is_flag=True, help="Fail if something is wrong with local assets")
def meta(ctx, pedantic):
    """ Print the meta info of all the stored assets """
    for base, package, version in assets.walk():
        meta = assets.get_meta(base, package, version)
        if meta is None:
            if pedantic:
                click.echo(f"Missing or empty meta: assets/{base}/{package}/{version}/meta.yml", err=True)
                ctx.exit(1)
            continue
        asset = dict(base=base, package=package, version=version, meta=meta)
        click.echo(json.dumps(asset))


@cli.command()
@click.option("--bases", help="Comma separated list of base(s) - es: staging,snapshot")
def plan(bases):
    """ Print the update plan in a diff-like format """

    if bases:
        bases = [b.strip() for b in bases.split(",")]

    for (base, package, all_versions, only_local, only_remote) in make_plan(bases):
        if only_local or only_remote:
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


@cli.command()
@click.pass_context
@click.option("--bases", help="Comma separated list of base(s) - es: staging,snapshot")
def update(ctx, bases):
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

    if bases:
        bases = [b.strip() for b in bases.split(",")]

    for (base, package, all_versions, only_local, only_remote) in make_plan(bases):
        for version in sorted(only_remote, key=semver.VersionInfo.parse):
            package_dir = os.path.join(packages.packages_dir, base, "packages", package, version)
            click.echo(f"install package from {package_dir}")
            args = ["elastic-package", "install", package]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=package_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            asset_dir = os.path.join(assets.assets_dir, base, package, version)
            click.echo(f"export assets to {asset_dir}")
            args = ["elastic-package", "dump", "installed-objects", "--package", package, "--output", asset_dir]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=assets.assets_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            click.echo("copy manifest")
            args = ["cp", "-v", os.path.join(package_dir, "manifest.yml"), asset_dir]
            p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=asset_dir)
            if p.returncode:
                click.echo(p.stdout, err=True)
                click.echo(f"Subprocess returned {p.returncode}", err=True)
                continue
            click.echo(p.stdout)

            click.echo("write meta")
            with open(os.path.join(asset_dir, "meta.yml"), "w+") as f:
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
            args = ["git", "commit", "-n", "-m", f"Add assets: {package} {version} ({base}, {stack_version})"]
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

        os.makedirs(os.path.dirname(filename), exist_ok=True)
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
