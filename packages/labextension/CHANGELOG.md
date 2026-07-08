# Changelog

All notable changes to **Grader Labextension** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- entries -->

## [Unreleased]

## [0.12.4] - 2026-07-07

### Added
- Monorepo structure combining grader-service and grader-labextension
- UV workspace for unified dependency management
- Integration test suite
- Unified GitHub Actions workflows
- Root documentation files (README.md, DEVELOPMENT.md, CONTRIBUTING.md)

### Changed
- Moved service to `packages/service/`
- Moved labextension to `packages/labextension/`
- Updated CI/CD for monorepo structure

### Fixed
- Slash in assignment name leads to export error by @florian-jaeger, TU-Wien-dataLAB/grader-labextension#115

## [0.12.3] - 2025-06-01

Previous labextension changelog entries are available in the git history before the monorepo migration.
