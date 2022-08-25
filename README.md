## Purpose

This repository contains assets, the objects dumped from the Stack as they are created when the package of an integration is there installed.

The assets update happens in an automated fashion driven by Github Actions CI.

## Repository branches

There are a few branches:

`main`  
where the automation code resides  

`production`  
`staging`  
`snapshot`  
where the assets reside, according to their release status

## Repository layout

### Assets

The automation expects the asset branches to be available in the `assets/` subdir. Ex. if production assets need update, `assets/production` is expected to be present.

The CI flow manages the preparation of the `assets/` subdir but the casual user needs to explicitly take care of it (ex. using `git worktree add assets/production production`).

### Packages

Packages reside in the external repository [package-storage](https://github.com/elastic/package-storage), in the respective `production`, `staging`, and `snapshot` branches. The automation expects them in the `package/` subdir, similarily to the assets.

The CI flow manages the preparation of the `packages/` subdir but the casual user needs to explicitly take care of it (ex. using `git clone -b production https://github.com/elastic/package-storage packages/production`).

### Bot

The update automation is located in the `bot/` subdir.

The [config.yaml](./config.yaml) file specifies what packages, versions and branches are tracked.

As example, the following configuation tracks the endpoint package on all the `production`, `staging`, and `snapshot` branches but ignores versions earlier than 8.x. Zoom package is only tracked on the `production` and `staging` branches but all the versions are included.

```
tracked-packages:
  - endpoint:
      minimum-version: 8
  - zoom:
      branches:
       - production
       - staging
```

The bot adds new package versions as they are made available but never removes any. Ex: shifting endpoint's `minimum-version` to 9 will not delete any of the already dumped 8.x versions, it will simply ignore any new release until a 9.x is published.

Therefore assets removal can only happen with `git rm <package>/<version>` in the appropriate branch or from the GitHub UI.

## Manual invocation

The automation has a few dependencies, you can install them as follows:

```shell
$ python3 -m pip install -r requirements.txt
...
```

Check that everything is set:

```shell
$ python3 -m bot
Usage: bot [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  download  Download the assets of a given package
  meta      Print the meta info of all the stored assets
  plan      Print the update plan in a diff-like format
  update    Perform the assets updates
```


