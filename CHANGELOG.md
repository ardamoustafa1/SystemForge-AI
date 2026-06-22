# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Extensively reorganized README (architecture, service manifest, full env reference, runbook, hardening checklist).
- Added `CONTRIBUTING.md`.
- Added badges, ADR index, and changelog policy to README.
- Added star-focused GitHub README showcase: product positioning, screenshots, quick demo, architecture, showcase, release and contributor links.
- Added local Docker demo seed script (`backend/scripts/seed_demo.py`).
- Added Docker Compose demo seed service (`backend-demo-seed`).
- Added demo credentials and showcase design seed env variables to `.env.example`.
- Added `docs/ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md`, `docs/SHOWCASE_EXAMPLES.md`, `docs/RELEASE_PROCESS.md`, `docs/GOOD_FIRST_ISSUES.md`, `docs/MAINTAINER_GUIDE.md`.
- Added logo and product screenshot assets for README visuals.
- Added verified dashboard and architecture review screenshots from the Docker demo.
- Added concrete Docker Compose, Terraform, Kubernetes, and architecture showcase files under `examples/`.
- Added Cosign keyless signature, SBOM/provenance, Helm package, and checksum generation to the release workflow.

### Changed
- Refactored README information architecture into a professional documentation format.
- Updated `docs/QUICK_START.md` with the seeded demo flow.
- Converted `docs/LOAD_TEST_REPORT.md` into a release-quality benchmark evidence format.
- Updated `ROADMAP.md` to reflect a realistic release gate status.
- Updated frontend API access to work through a same-origin `/api` proxy.
- Migrated frontend Docker setup to a deterministic `npm ci` flow on Node 22 Alpine.

### Fixed
- Fixed broken/missing logo and demo image references in README.
- Fixed API key metadata schema drift with a new Alembic migration.
- Removed metrics middleware that caused all requests to drop to 500 due to a FastAPI router incompatibility.
- Adapted Docker backend test fixtures to the current schema; all 64 tests now pass.

### Security
- Added a production hardening checklist to the documentation.
- Secured the Prometheus metrics endpoint with a token.
- Reduced frontend dependency audit results to 0 vulnerabilities.
