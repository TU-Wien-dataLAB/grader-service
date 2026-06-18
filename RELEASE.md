# Release Guide

This document describes the release process for the Grader Platform monorepo.

## Versioning Strategy

The monorepo uses **separate versioning** for each package:

| Package | Version Tag Pattern | PyPI Package |
|---------|-------------------|--------------|
| Grader Service | `grader-service-X.Y.Z` | `grader-service` |
| Grader Labextension | `grader-labextension-X.Y.Z` | `grader-labextension` |

This allows independent release cycles for each component.

## Prerequisites

- Git access to push tags
- PyPI API token (stored as `PYPI_API_TOKEN` secret)
- Docker registry credentials (for service releases)

## Semantic Versioning

Both packages follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible changes
- **MINOR** version for backwards-compatible features
- **PATCH** version for backwards-compatible bug fixes

Example: `0.12.0` → `0.12.1` (patch), `0.13.0` (minor), `1.0.0` (major)

## Release Process

### 1. Prepare the Release

**For Service:**
```bash
cd packages/service
# Update version in pyproject.toml
# Update CHANGELOG.md with release notes
git add pyproject.toml CHANGELOG.md
git commit -m "Release grader-service-X.Y.Z"
```

**For Labextension:**
```bash
cd packages/labextension
# Update version in pyproject.toml and package.json
# Update CHANGELOG.md with release notes
git add pyproject.toml package.json CHANGELOG.md
git commit -m "Release grader-labextension-X.Y.Z"
```

### 2. Create and Push Tag

**Service Release:**
```bash
git tag grader-service-X.Y.Z
git push origin grader-service-X.Y.Z
```

**Labextension Release:**
```bash
git tag grader-labextension-X.Y.Z
git push origin grader-labextension-X.Y.Z
```

### 3. Automated Release Workflow

Once the tag is pushed, GitHub Actions automatically:

**For Service:**
1. Runs `build-service` workflow (build, lint)
2. Runs `test-service` workflow (tests)
3. Creates Docker image (`docker-service`)
4. Publishes to PyPI (`publish-service`)
5. Publishes Helm chart (`publish-helm`)

**For Labextension:**
1. Runs `build-labextension` workflow (build Python + TypeScript)
2. Runs `test-labextension` workflow (Python + JS tests)
3. Publishes to PyPI (`publish-labextension`)

### 4. Verify Release

**Check GitHub Actions:**
- Go to repository Actions tab
- Verify all workflows completed successfully

**Verify PyPI:**
```bash
# Service
pip install grader-service==X.Y.Z

# Labextension
pip install grader-labextension==X.Y.Z
```

**Verify Docker Image (Service only):**
```bash
docker pull <registry>/<org>/grader-service:<tag>
```

**Verify Helm Chart (Service only):**
```bash
helm search repo grader-service --versions
```

## Creating a GitHub Release

After the tag is pushed and workflows complete:

1. Go to GitHub Releases page
2. Click "Draft a new release"
3. Select the tag you just pushed
4. Copy changelog entries for this version
5. Click "Publish release"

This triggers the `release` event that runs the publish workflows.

## Release Checklist

### Pre-Release
- [ ] All tests pass locally (`make test-all`)
- [ ] All linters pass (`make lint-all`)
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated with release notes
- [ ] Version numbers are updated in `pyproject.toml`
- [ ] For labextension: `package.json` version is updated

### Release
- [ ] Commit version changes
- [ ] Create and push git tag
- [ ] Monitor GitHub Actions workflows
- [ ] Verify PyPI package is available
- [ ] Create GitHub release with changelog

### Post-Release
- [ ] Verify Docker image is available (service)
- [ ] Verify Helm chart is available (service)
- [ ] Test installation from PyPI
- [ ] Update documentation if needed

## Emergency Hotfix Release

For urgent bug fixes:

1. Create hotfix branch from release tag:
   ```bash
   git checkout -b hotfix/grader-service-X.Y.Z <tag>
   ```

2. Apply fix and update patch version:
   ```bash
   # Update version to X.Y.(Z+1)
   git commit -m "Hotfix: description of fix"
   ```

3. Create hotfix tag:
   ```bash
   git tag grader-service-X.Y.(Z+1)
   git push origin grader-service-X.Y.(Z+1)
   ```

## Version Management Tools

### Using tbump (Recommended)

Install tbump:
```bash
pip install tbump
```

**Service:**
```bash
cd packages/service
tbump minor  # or patch, major
git push origin main --tags
```

**Labextension:**
```bash
cd packages/labextension
tbump minor  # or patch, major
git push origin main --tags
```

### Manual Version Update

Edit `pyproject.toml` directly:

**Service (`packages/service/pyproject.toml`):**
```toml
[project]
name = "grader-service"
version = "X.Y.Z"
```

**Labextension (`packages/labextension/pyproject.toml`):**
```toml
[project]
name = "grader-labextension"
version = "X.Y.Z"
```

Also update `packages/labextension/package.json`:
```json
{
  "name": "grader-labextension",
  "version": "X.Y.Z"
}
```

## Troubleshooting

### Workflow Fails

1. Check the workflow logs for specific errors
2. Verify all tests pass locally
3. Check PyPI credentials in GitHub Secrets
4. Re-run failed jobs if transient error

### PyPI Publish Fails

1. Verify `PYPI_API_TOKEN` secret is set
2. Check package name doesn't conflict
3. Ensure version number is unique (not already published)
4. Manually publish as fallback:
   ```bash
   cd packages/service  # or labextension
   uv build
   uv publish
   ```

### Docker Build Fails (Service)

1. Check Docker registry credentials
2. Verify Dockerfile paths are correct
3. Test build locally:
   ```bash
   docker build -f packages/service/Dockerfile .
   ```

### Tag Already Exists

Delete and recreate tag:
```bash
git tag -d grader-service-X.Y.Z
git push origin :refs/tags/grader-service-X.Y.Z
git tag grader-service-X.Y.Z
git push origin grader-service-X.Y.Z
```

## Release Schedule

- **Minor releases**: Every 2-4 weeks with new features
- **Patch releases**: As needed for bug fixes
- **Major releases**: As needed for breaking changes

## Changelog Maintenance

Update the relevant CHANGELOG.md for each package:

**Service:** `packages/service/CHANGELOG.md`
**Labextension:** `packages/labextension/CHANGELOG.md`

Format follows [Keep a Changelog](https://keepachangelog.com/):

```markdown
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
