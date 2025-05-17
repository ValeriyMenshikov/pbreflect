# Contributing Guide

Thank you for your interest in the pbreflect project! This document contains information on how to contribute to the project.

## Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/ValeriyMenshikov/pbreflect.git
   cd pbreflect
   ```

2. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install project dependencies:
   ```bash
   poetry install
   ```

4. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Code Style

The project follows PEP 8 standards and uses the following tools for code style checking:

- Ruff - for linting
- Black - for code formatting
- isort - for import sorting
- mypy - for type checking

Before submitting changes, make sure the code meets the standards:

```bash
# Check code style
poetry run ruff check .

# Format code
poetry run black .

# Sort imports
poetry run isort .

# Type checking
poetry run mypy .
```

## Testing

Run tests to ensure your changes don't break existing functionality:

```bash
poetry run pytest
```

## Contribution Process

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make the necessary changes and add tests if needed.

3. Ensure all tests pass and the code meets style standards.

4. Create a commit with a descriptive message:
   ```bash
   git commit -m "Add feature X that solves problem Y"
   ```

5. Push changes to your fork of the repository:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request to the main repository.

## Project Structure

The project consists of two main modules:

1. `protorecover` - for recovering .proto files from running gRPC servers
   - `GrpcReflectionClient` - for interacting with the gRPC reflection service
   - `ProtoFileBuilder` - for creating .proto files from descriptors
   - `RecoverService` - for managing the recovery process

2. `pbgen` - for generating client code based on .proto files
   - Code generators for creating client libraries
   - Patchers for modifying generated code

## Documentation

When making changes, please update the relevant documentation:

- Docstrings for new functions and classes
- README.md for API or functionality changes
- CHANGELOG.md for significant changes

## Reporting Issues

If you find a bug or have a suggestion for improvement, please create an Issue in the project repository.

Thank you for your contribution to the project!
