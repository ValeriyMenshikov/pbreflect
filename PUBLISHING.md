# Package Publishing Instructions

This document contains instructions for preparing and publishing the pbreflect package to PyPI.

## Preparation for Release

1. Update the package version in the following files:
   - `pyproject.toml`
   - `pbreflect/__init__.py`

2. Update CHANGELOG.md, adding information about the new version and changes.

3. Make sure all tests pass:
   ```bash
   poetry run pytest
   ```

4. Check code style:
   ```bash
   poetry run ruff check .
   poetry run mypy .
   ```

## Building the Package

1. Build the package using Poetry:
   ```bash
   poetry build
   ```

   This will create distribution files in the `dist/` directory.

## Publishing to PyPI

1. For publishing to TestPyPI (recommended for testing):
   ```bash
   poetry publish -r testpypi
   ```

2. For publishing to the main PyPI repository:
   ```bash
   poetry publish
   ```

   Or, if you want to build and publish in one command:
   ```bash
   poetry publish --build
   ```

## Creating a Git Tag

After successful publication, create a tag in Git:

```bash
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1
```

## Verifying Installation

Verify that the package installs successfully:

```bash
# Create a virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install the package
pip install pbreflect

# Verify that the package works
pbreflect --version
```
