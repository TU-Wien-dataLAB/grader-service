# Release Guide

This document describes the release process for the Grader Platform monorepo.
The two packages Grader Service and Grader Labextension are
versioned and released independently. Each package owns its `CHANGELOG.md`, and
[tbump](https://github.com/your-tools/tbump) is the single tool used to bump
versions and create git tags. tbump is configured in each package's
`pyproject.toml`.

## Versioning Strategy

The monorepo uses **independent versioning** for each package, so they can be
released on their own cycles:

| Package | Version Tag Pattern | PyPI Package |
|---------|---------------------|--------------|
| Grader Service | `grader-service-X.Y.Z` | `grader-service` |
| Grader Labextension | `grader-labextension-X.Y.Z` | `grader-labextension` |
| Helm Chart | `grader-service-chart-X.Y.Z` | (OCI chart, no PyPI) |

The Helm chart version is **independent** of the service version. The chart
`version:` tracks chart (templates/values) changes and is bumped by the chart
tbump config. The chart `appVersion` tracks the service version and is bumped by
the service tbump (so it advances whenever a service release is cut, staging it
for the next chart release). A service release does **not** publish a chart; cut
a chart release to publish a chart (with whatever `appVersion` is currently in
the repo).

## Prerequisites

- Git access to push commits and tags to `main`
- `PYPI_API_TOKEN` secret configured in the GitHub repository
- Docker registry credentials (for publishing Docker images)
- tbump installed, it is a root dev dependency, so `uv sync` installs it

## Semantic Versioning

Both packages follow Semantic Versioning:

- **MAJOR** version for major changes that break backwards compatibility
- **MINOR** version for incompatible feature additions
- **PATCH** version for backwards-compatible bug fixes

Example: `0.12.0` → `0.12.1` (patch), `0.13.0` (minor), `1.0.0` (major)

## Release Process

The workflow is the same for both packages. Run tbump from inside the package
directory (it finds the nearest `pyproject.toml` with a `[tool.tbump]` section
by searching upward from the current working directory). tbump accepts either
an explicit version (`tbump 0.13.0`) or a bump rule (`tbump minor`,
`tbump patch`, `tbump major`).

### Service

1. Update `packages/service/CHANGELOG.md`: rename `## [Unreleased]` to
   `## [X.Y.Z] - YYYY-MM-DD` (today's date) and add a fresh empty
   `## [Unreleased]` section above it. Commit the changelog change:
   ```bash
   git add packages/service/CHANGELOG.md
   git commit -m "docs(service): changelog for X.Y.Z"
   ```

2. Bump the version, create the tag, and push with tbump:
   ```bash
   cd packages/service
   tbump X.Y.Z   # or: tbump minor | tbump patch | tbump major
   ```
   tbump patches the version files, creates a commit `Bump service to X.Y.Z`,
   creates the tag `grader-service-X.Y.Z`, and pushes both the current branch
   and the tag to the remote. Use `--no-push` to skip pushing (for example,
   when releasing from a branch you intend to merge via a pull request).

3. Create a GitHub Release from the tag, using the changelog entry as the
   release notes:
   ```bash
   gh release create grader-service-X.Y.Z \
       --title "grader-service-X.Y.Z" \
       --notes-file packages/service/CHANGELOG.md
   ```
   Publishing the release triggers the CI workflow.

### Labextension

1. Update `packages/labextension/CHANGELOG.md`: rename `## [Unreleased]` to
   `## [X.Y.Z] - YYYY-MM-DD` (today's date) and add a fresh empty
   `## [Unreleased]` section above it. Commit the changelog change:
   ```bash
   git add packages/labextension/CHANGELOG.md
   git commit -m "docs(labextension): changelog for X.Y.Z"
   ```

2. Bump the version, create the tag, and push with tbump:
   ```bash
   cd packages/labextension
   tbump X.Y.Z   # or: tbump minor | tbump patch | tbump major
   ```
   tbump patches the version files, creates a commit
   `Bump labextension to X.Y.Z`, creates the tag `grader-labextension-X.Y.Z`,
   and pushes both the current branch and the tag to the remote. Use `--no-push`
   to skip pushing (for example, when releasing from a branch you intend to
   merge via a pull request).

3. Create a GitHub Release from the tag, using the changelog entry as the
   release notes:
   ```bash
   gh release create grader-labextension-X.Y.Z \
       --title "grader-labextension-X.Y.Z" \
       --notes-file packages/labextension/CHANGELOG.md
   ```
   Publishing the release triggers the CI workflow.

### Helm Chart (chart-only release)

A chart-only release ships Helm chart changes (templates, `values.yaml`) without
cutting a new service wheel or Docker image. The chart `version` is independent
of the service version; `appVersion` is whatever the last service release set it
to (the service tbump advances `appVersion`, the chart tbump does not).

1. Bump the chart version, create the tag, and push with the chart tbump config
   (run from the `packages/service/charts` directory so tbump auto-discovers
   `tbump.toml`):
   ```bash
   cd packages/service/charts
   tbump X.Y.Z   # or: tbump minor | tbump patch | tbump major
   ```
   tbump patches `version:` in both `Chart.yaml` files (and the all-in-one
   subchart dependency, which shares the version), creates a commit
   `Bump chart to X.Y.Z`, creates the tag `grader-service-chart-X.Y.Z`, and
   pushes both the current branch and the tag to the remote. Use `--no-push` to
   skip pushing (for example, when releasing from a branch you intend to merge via
   a pull request).

2. Create a GitHub Release from the tag (there is no separate chart changelog;
   use the release body to describe the chart change):
   ```bash
   gh release create grader-service-chart-X.Y.Z \
       --title "grader-service-chart-X.Y.Z" \
       --notes "Describe the chart change here"
   ```
   Publishing the release triggers the `publish-helm` CI job, which packages
   `packages/service/charts/grader-service` and pushes it to the OCI registry.
   No service build, test, Docker, or PyPI jobs run for a chart release.

## What tbump Does

tbump reads the `[tool.tbump]` section from the package's `pyproject.toml`,
bumps every `[[tool.tbump.file]]` entry, creates a commit using
`message_template`, and creates an annotated tag using `tag_template`. It is
run from inside the package directory.

**Service** (`packages/service/pyproject.toml`) bumps:
- `pyproject.toml` -> `version = "..."`
- `grader_service/_version.py` -> `__version__ = "..."`
- `charts/grader-service/Chart.yaml` -> `appVersion`
- `charts/grader-service-all-in-one/Chart.yaml` -> `appVersion`

Commit message: `Bump service to {new_version}`
Tag: `grader-service-{new_version}`

**Helm Chart** (`packages/service/charts/tbump.toml`) bumps:
- `charts/grader-service/Chart.yaml` -> `version`
- `charts/grader-service-all-in-one/Chart.yaml` -> `version` (and the all-in-one
  `grader-service` subchart dependency, which shares the version)

Commit message: `Bump chart to {new_version}`
Tag: `grader-service-chart-{new_version}`

Run the chart tbump from `packages/service/charts` (or with
`tbump --cwd packages/service/charts`) so it auto-discovers `tbump.toml`. The
chart `appVersion` is **not** bumped here; it tracks the service version via the
service tbump.

**Labextension** (`packages/labextension/pyproject.toml`) bumps:
- `package.json` &mdash; `"version": "..."`
- `binder/environment.yml` &mdash; `grader-labextension==...`

The labextension version is dynamic (read from `package.json` via
`hatch-nodejs-version`), so there is no static version in the labextension
`pyproject.toml`.

Commit message: `Bump labextension to {new_version}`
Tag: `grader-labextension-{new_version}`

By default tbump commits, tags, **and pushes** &mdash; it pushes the current
branch and the tag atomically to the upstream remote. Useful flags:

- `tbump --dry-run X.Y.Z` &mdash; preview the changes without committing, tagging,
  or pushing.
- `tbump --only-patch X.Y.Z` &mdash; patch the version files without committing,
  tagging, or pushing (useful for inspecting the diff first).
- `tbump --no-push X.Y.Z` &mdash; commit and tag, but do not push.
- `tbump --no-tag-push X.Y.Z` &mdash; commit, tag, and push the branch, but do not
  push the tag.

## Automated Release Workflow

Once the GitHub Release is published, the `release` `published` event triggers
the `Main CI` workflow. Publishing is gated on the build **and** test jobs
passing.

**Service** (tag `grader-service-X.Y.Z`):
1. `build-service` &mdash; builds the wheel, runs ruff check & format check
2. `test-service` &mdash; runs ruff + pytest with coverage
3. `docker-service` &mdash; builds and pushes the Docker image, tagged with the
   release version (runs after `build-service` and `test-service` succeed)
4. `publish-service` &mdash; publishes the wheel to PyPI (runs after
   `docker-service` succeeds)

A service release does **not** publish a chart. The service tbump advances the
chart `appVersion` in the repo, which is picked up by the next chart release.

**Helm Chart** (tag `grader-service-chart-X.Y.Z`):
1. `publish-helm` &mdash; packages `packages/service/charts/grader-service` and
   pushes it to the OCI registry

No service build, test, Docker, or PyPI jobs run for a chart release.

**Labextension** (tag `grader-labextension-X.Y.Z`):
1. `build-labextension` &mdash; builds TypeScript + Python wheel, runs ruff
2. `test-labextension` &mdash; runs Python and JavaScript tests
3. `docker-labextension` &mdash; builds and pushes the Docker image, tagged with
   the release version (runs after `build-labextension` and `test-labextension`
   succeed)
4. `publish-labextension` &mdash; publishes the wheel to PyPI (runs after
   `docker-labextension` succeeds)

> Docker images are built on pushes to `main`, on pull requests, and on
> releases (tagged with the release version) via the `docker-service` and
> `docker-labextension` jobs. The publish jobs run only after the matching
> docker job succeeds.

## Verify Release

**Check GitHub Actions:**
- Go to the repository Actions tab and verify all workflows completed
  successfully.

**Verify PyPI:**
```bash
# Service
pip install grader-service==X.Y.Z

# Labextension
pip install grader-labextension==X.Y.Z
```

**Verify Helm Chart (Service only):**
```bash
helm search repo grader-service --versions
```

## Changelog Maintenance

Each package maintains its own changelog following the
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

- `packages/service/CHANGELOG.md`
- `packages/labextension/CHANGELOG.md`

Each changelog has an `## [Unreleased]` section at the top. The workflow:

1. During development, add entries under `## [Unreleased]` as you make changes.
2. At release time, rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` and
   add a fresh empty `## [Unreleased]` section above it.
3. Commit the changelog change, then run tbump.

Keep a Changelog categories:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

## Release Checklist

### Pre-Release
- [ ] All tests pass (`make test-all`)
- [ ] All linters pass (`make lint-all`)
- [ ] Documentation is up to date
- [ ] The package's `CHANGELOG.md` is updated (rename `[Unreleased]` to
      `[X.Y.Z] - YYYY-MM-DD`, add a fresh `[Unreleased]`)

### Release
- [ ] Commit the changelog change
- [ ] Run tbump from the package directory (bumps versions, commits, tags, and
      pushes the branch + tag by default)
- [ ] Create a GitHub Release from the tag (triggers CI)
- [ ] Monitor GitHub Actions workflows

### Post-Release
- [ ] Verify the wheel is available on PyPI
- [ ] Verify the Docker image is available
- [ ] Verify the Helm chart is available (Service only)
- [ ] Test installation from PyPI

## Emergency Hotfix Release

For urgent bug fixes:

1. Create a hotfix branch from the release tag:
   ```bash
   git checkout -b hotfix/grader-service-X.Y.Z grader-service-X.Y.Z
   ```

2. Apply the fix and update the changelog (rename `## [Unreleased]` to the
   hotfix version `## [X.Y.(Z+1)] - YYYY-MM-DD`, add a fresh
   `## [Unreleased]`), then commit the fix and changelog:
   ```bash
   git commit -m "Hotfix: description of fix"
   ```

3. Bump the patch version, create the tag, and push with tbump:
   ```bash
   cd packages/service   # or packages/labextension
   tbump patch
   ```
   tbump commits, tags, and pushes by default.

4. Create a GitHub Release from the tag (triggers CI).

## Troubleshooting

### Workflow Fails

1. Check the workflow logs for specific errors
2. Verify all tests pass locally (`make test-all`)
3. Check that `PYPI_API_TOKEN` and Docker registry credentials are set in GitHub
   Secrets
4. Re-run failed jobs if it was a transient error

### PyPI Publish Fails

1. Verify the `PYPI_API_TOKEN` secret is set
2. Check that the package name doesn't conflict
3. Ensure the version number is unique (not already published)
4. Manually publish as a fallback:
   ```bash
   cd packages/service   # or packages/labextension
   uv build
   uv publish
   ```

### Docker Build Fails

1. Check Docker registry credentials
2. Verify Dockerfile paths are correct
3. Test the build locally:
   ```bash
   docker build -f packages/service/Dockerfile .
   ```

### Tag Already Exists

If tbump fails because the tag already exists, delete and recreate it:
```bash
git tag -d grader-service-X.Y.Z
git push origin :refs/tags/grader-service-X.Y.Z
# fix the issue, then re-run tbump
```
