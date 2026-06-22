# Release Process

SystemForge AI follows semantic versioning.

## Versioning

- `MAJOR`: breaking API, auth, storage, or export contract changes.
- `MINOR`: backward-compatible features.
- `PATCH`: fixes, documentation improvements, dependency updates.

## Release Checklist

Before tagging a release:

- [ ] `docker compose config --quiet`
- [ ] `docker compose build --no-cache`
- [ ] Backend lint passes.
- [ ] Backend tests pass.
- [ ] Frontend install, lint, typecheck, tests, and build pass.
- [ ] E2E smoke test passes.
- [ ] `npm audit --audit-level=high` has no high/critical findings or documented exceptions.
- [ ] Backend dependency audit has no high/critical findings or documented exceptions.
- [ ] Helm chart lint and Kubernetes schema validation pass.
- [ ] Changelog is updated.
- [ ] README quick start has been tested from a clean checkout.

## GitHub Release

1. Update `CHANGELOG.md`.
2. Create a tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. The release workflow builds and publishes both container images.
4. Attach release notes with:
   - Highlights
   - Breaking changes
   - Migration notes
   - Security notes
   - Known limitations

## Artifact Strategy

Target release artifacts:

- GitHub Release notes.
- Signed backend container image.
- Signed frontend container image.
- Versioned Helm chart package.
- Source SBOM, image SBOM/provenance, and SHA-256 checksums.

Container images are signed keylessly with Sigstore Cosign through GitHub OIDC. Consumers should verify the issuer and repository identity before deployment.
