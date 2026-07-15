# Changelog

All notable changes to **Grader Service** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- entries -->

## [Unreleased]

## [0.12.5] - 2026-07-15

### Fixed
- The 0.12.4 wheel omitted `grader_service.api.models` and eight other runtime subpackages (`autograding.kube`, `convert.converters`, `convert.gradebook`, `convert.nbgraderformat`, `convert.preprocessors`, `handlers.git`, `migrate.versions`, `scripts`), causing the `db-migration` init container to fail with `ModuleNotFoundError: No module named 'grader_service.api.models'`; restored setuptools auto-discovery (equivalent to the previous `find_packages`) which the `setup.py` -> `pyproject.toml` migration had replaced with a stale explicit package list (#381)

## [0.12.4] - 2026-07-07

### Added
- Tests for the Celery autograding tasks (#370)

### Changed
- Restructured into a monorepo: the service now lives under `packages/service/`, with unified dependency management via a UV workspace and consolidated GitHub Actions workflows (#373)
- `BaseHandler.template_namespace` now builds the base URL with `urljoin` instead of `os.path.join` (#369)
- Test suite: added a `slow` pytest marker and excluded tests from the coverage report (#369)

### Removed
- Deprecated `KubeAutogradeExecutor` configuration (`image_config_path`, `resolve_image_name`, `resolve_node_selector`, and the `_get_image`/`_get_image_name` helpers), deprecated since v0.7; the `node_selector` parameter of `make_pod` was removed as well (#369)
- Unused `add` Celery task (#370)
- Dead code in `grader_service/utils.py` (e.g. `random_port`, `make_ssl_context`, `exponential_backoff`, `wait_for_server`, `print_ps_info`, `url_escape_path`, `get_accepted_mimetype`, and the `token_authenticated`/`admin_only`/`metrics_authentication` decorators) (#369)

### Fixed
- Autograding no longer fails when a missing grade cell has to be re-added but no grade or solution cells were submitted; the cell is now inserted at the start of the notebook (#368)
- Typo `INSTRUCTOR_SUBMISSION_COMMIT_CASH` → `INSTRUCTOR_SUBMISSION_COMMIT_HASH` (#369)
- SQLAlchemy deprecation warning in the `4a88dacd888f_add_ondelete_cascade` migration (use `inspect()` instead of `Inspector.from_engine`) (#369)

## [0.12.0] - 2025-06-01

Previous service changelog entries are available in the git history before the monorepo migration.
