#!/usr/bin/env bash
set -e

# SystemForge AI Release Tagging Script
# Reads versions from frontend/package.json and backend/pyproject.toml
# and creates a git tag if they match (or warns if they differ).

echo "🚀 SystemForge Release Script"

# Read frontend version
FRONTEND_VERSION=$(grep '"version"' frontend/package.json | sed -E 's/.*"version": "(.*)",/\1/')
echo "Frontend version: $FRONTEND_VERSION"

# Read backend version
BACKEND_VERSION=$(grep '^version' backend/pyproject.toml | sed -E 's/version = "(.*)"/\1/')
echo "Backend version: $BACKEND_VERSION"

if [ "$FRONTEND_VERSION" != "$BACKEND_VERSION" ]; then
    echo "⚠️ Warning: Frontend ($FRONTEND_VERSION) and Backend ($BACKEND_VERSION) versions do not match!"
    echo "Please align them before creating a release."
    exit 1
fi

VERSION="v$FRONTEND_VERSION"

if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "❌ Tag $VERSION already exists."
    exit 1
fi

echo "Creating tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"

echo "✅ Tag $VERSION created successfully."
echo "Run 'git push origin $VERSION' to trigger the release workflow."
