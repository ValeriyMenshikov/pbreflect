# PBReflect

[![PyPI version](https://img.shields.io/pypi/v/pbreflect.svg)](https://pypi.org/project/pbreflect)
[![Python versions](https://img.shields.io/pypi/pyversions/pbreflect.svg)](https://pypi.python.org/pypi/pbreflect)
[![Tests](https://img.shields.io/github/actions/workflow/status/ValeriyMenshikov/pbreflect/python-test.yml?branch=main&label=tests)](https://github.com/ValeriyMenshikov/pbreflect/actions/workflows/python-test.yml)
[![Coverage](https://img.shields.io/coverallsCoverage/github/ValeriyMenshikov/pbreflect.svg)](https://coveralls.io/github/ValeriyMenshikov/pbreflect)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/ValeriyMenshikov/pbreflect/python-publish.yml?branch=main&label=publish)](https://github.com/ValeriyMenshikov/pbreflect/actions/workflows/python-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/ValeriyMenshikov/pbreflect/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/pbreflect.svg)](https://pypistats.org/packages/pbreflect)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://github.com/python/mypy)

PBReflect is a powerful tool for recovering Protocol Buffer (protobuf) definitions from gRPC services using the reflection API. It allows developers to generate `.proto` files from running gRPC servers without having access to the original source code.

## Features

- **Automatic Discovery**: Automatically discovers all services and messages exposed by a gRPC server
- **Proto Generation**: Generates complete `.proto` files with proper package structure
- **TLS Support**: Supports secure connections with custom certificates
- **Dependency Resolution**: Correctly handles dependencies between proto files
- **Simple CLI**: Easy-to-use command-line interface
- **Client Generation**: Generate Python client libraries from `.proto` files with multiple generator strategies
- **Custom Templates**: Support for custom code generation templates
- **All-in-One Command**: Generate client code directly from a gRPC server in a single step
- **Test Stub Generation**: Automatically generate pytest test stubs and conftest fixtures for all gRPC services
- **Custom Test Templates**: Support for custom test stub templates, independent from client code templates

## Installation

```bash
# Install using pip
pip install pbreflect

# Or using uv
uv add pbreflect
```

## Quick Start

### Direct Client Generation from Server

PBReflect provides an all-in-one command to generate client code directly from a gRPC server:

```bash
# Generate client code directly from a gRPC server
pbreflect reflect -h localhost:50051 -o ./clients
```

This command:
1. Connects to the gRPC server
2. Retrieves proto definitions using reflection
3. Generates client code in one step
4. Automatically cleans up temporary proto files

You can customize the generation with various options:

```bash
# Generate custom client code directly from a server
pbreflect reflect -h localhost:50051 -o ./clients --gen-type pbreflect --template-dir ./my-templates
```

For secure connections, you can use TLS certificates:

```bash
# With TLS support
pbreflect reflect -h secure.example.com:443 -o ./clients \
  --root-cert ./certs/ca.pem \
  --private-key ./certs/client.key \
  --cert-chain ./certs/client.pem
```

### Recovering Proto Files Only

If you only need to recover proto files from a gRPC server:

```bash
# Basic usage
pbreflect get-protos -h localhost:50051 -o ./protos
```

This will connect to the gRPC server at `localhost:50051`, retrieve all available proto definitions, and save them to the `./protos` directory.

#### Using TLS/SSL

For secure connections, you can use TLS certificates:

```bash
# With root certificate only
pbreflect get-protos -h secure.example.com:443 -o ./protos --root-cert ./certs/ca.pem

# With full client authentication
pbreflect get-protos -h secure.example.com:443 -o ./protos \
  --root-cert ./certs/ca.pem \
  --private-key ./certs/client.key \
  --cert-chain ./certs/client.pem
```

### Client Code Generation from Proto Files

If you already have proto files and want to generate client code:

```bash
# Generate client code from proto files
pbreflect generate --proto-dir ./protos --output-dir ./generated --gen-type pbreflect
```

#### Generator Strategies

PBReflect supports multiple code generation strategies:

- **default**: Standard protoc Python output
- **mypy**: Standard output with mypy type annotations
- **betterproto**: Uses betterproto generator for more Pythonic API
- **pbreflect**: Custom generator with enhanced gRPC client support

Example:

```bash
# Generate code using the betterproto strategy
pbreflect generate --proto-dir ./protos --output-dir ./generated --gen-type betterproto
```

#### Custom Templates

For the `pbreflect` generator strategy, you can specify a custom templates directory:

```bash
# Generate code using custom templates
pbreflect generate --proto-dir ./protos --output-dir ./generated --gen-type pbreflect --template-dir ./my-templates
```

This allows you to customize the generated code according to your needs.

### Custom Templates Reference

PBReflect uses [Jinja2](https://jinja.palletsprojects.com/) templates for code generation. You can create custom templates by placing `.jinja2` files in a directory and passing it via `--template-dir` (for client code) or `--tests-template-dir` (for test stubs).

#### Client Templates (`--template-dir`)

The client generator uses a single template file:

| Template File | Description |
|---|---|
| `client.jinja2` | Generates typed gRPC client wrapper classes for each service |

**Variables available in `client.jinja2`:**

| Variable | Type | Description |
|---|---|---|
| `package` | `str` | Proto package name (e.g. `my.api.v1`) |
| `async_mode` | `bool` | Whether to generate async (`grpc.aio`) or sync clients |
| `imports` | `list[str]` | List of Python import statements for messages and dependencies |
| `services` | `list[dict]` | List of service descriptors (see below) |
| `messages` | `list[dict]` | List of message descriptors (see below) |
| `enums` | `list[dict]` | List of enum descriptors (see below) |

**Service dict fields:**

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Service name as defined in proto (e.g. `UserService`) |
| `full_name` | `str` | Fully qualified name including package (e.g. `my.api.v1.UserService`) |
| `methods` | `list[dict]` | List of method descriptors (see below) |

**Method dict fields:**

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Method name in snake_case (e.g. `get_user`) |
| `original_name` | `str` | Original method name from proto (e.g. `GetUser`) |
| `input_type` | `str` | Input message type (e.g. `GetUserRequest` or `empty_pb2.Empty`) |
| `output_type` | `str` | Output message type (e.g. `GetUserResponse`) |
| `is_server_streaming` | `bool` | Whether the method uses server-side streaming |
| `is_client_streaming` | `bool` | Whether the method uses client-side streaming |

**Message dict fields:**

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Message name (e.g. `User`) |
| `fields` | `list[dict]` | List of field descriptors |
| `nested_types` | `list[dict]` | Nested message types (same structure as message dict) |
| `nested_enums` | `list[dict]` | Nested enum types (same structure as enum dict) |
| `fields[].name` | `str` | Field name |
| `fields[].number` | `int` | Field number |
| `fields[].type` | `int` | Protobuf field type constant |
| `fields[].type_name` | `str \| None` | Type name for message/enum fields (last segment) |
| `fields[].label` | `int` | Field label (optional/repeated) |
| `fields[].proto3_optional` | `bool` | Whether the field uses proto3 optional semantics |

**Enum dict fields:**

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Enum name (e.g. `Status`) |
| `values` | `list[dict]` | List of enum value descriptors |
| `values[].name` | `str` | Value name (e.g. `ACTIVE`) |
| `values[].number` | `int` | Value number |

#### Test Templates (`--tests-template-dir`)

The test stub generator uses three template files:

| Template File | Description |
|---|---|
| `conftest.jinja2` | Root conftest with shared `grpc_channel` fixture |
| `conftest_service.jinja2` | Per-service conftest with client fixture |
| `test_method.jinja2` | Individual test file per method (one method per file) |

**Variables available in `conftest.jinja2`:**

| Variable | Type | Description |
|---|---|---|
| `async_mode` | `bool` | Whether generated clients use async mode |

**Variables available in `conftest_service.jinja2`:**

| Variable | Type | Description |
|---|---|---|
| `service` | `dict` | Service descriptor (see Service dict above) |
| `client_module` | `str` | Python module path for generated clients (e.g. `clients`) |
| `pb2_pbreflect_module` | `str` | Module name for the pbreflect client file (e.g. `service_pb2_pbreflect`) |
| `async_mode` | `bool` | Whether generated clients use async mode |

**Variables available in `test_method.jinja2`:**

| Variable | Type | Description |
|---|---|---|
| `service` | `dict` | Service descriptor (see Service dict above) |
| `method` | `dict` | Method descriptor (see Method dict above) |
| `client_module` | `str` | Python module path for generated clients |
| `pb2_module` | `str` | Module name for protobuf stubs (e.g. `service_pb2`) |
| `pb2_pbreflect_module` | `str` | Module name for the pbreflect client file |
| `local_type` | `str \| None` | Local message type to import (if input type is from same proto) |
| `extra_import` | `str \| None` | Extra import line for Google protobuf types |
| `async_mode` | `bool` | Whether generated clients use async mode |

#### Custom Filters

The test templates register a custom Jinja2 filter:

| Filter | Description |
|---|---|
| `to_snake` | Converts a string to snake_case (e.g. `UserService` → `user_service`) |

#### Example Custom Template

```jinja2
{# my-templates/client.jinja2 #}
"""Custom client for {{ package }}."""

import grpc
{% if async_mode %}import grpc.aio{% endif %}

{% for service in services %}
class {{ service.name }}Client:
    def __init__(self, channel: {% if async_mode %}grpc.aio.Channel{% else %}grpc.Channel{% endif %}) -> None:
        self._channel = channel

    {% for method in service.methods %}
    {% if async_mode %}    async {% endif %}    def {{ method.name }}(self, request: {{ method.input_type }}) -> {{ method.output_type }}:
        # TODO: implement {{ method.original_name }}
        pass
    {% endfor %}
{% endfor %}
```

### Test Stub Generation

PBReflect can automatically generate pytest test stubs with conftest fixtures for all services found in your proto files:

```bash
# Generate client code with test stubs
pbreflect generate --proto-dir ./protos --output-dir ./generated --gen-tests
```

You can customize the test generation:

```bash
# Generate tests with custom directory and templates
pbreflect generate --proto-dir ./protos --output-dir ./generated \
  --gen-tests \
  --tests-dir ./my_tests \
  --tests-template-dir ./my-test-templates \
  --tests-client-module my_clients
```

This will generate:
- A root `conftest.py` with shared gRPC channel fixtures
- Per-service test files with test stubs for each method
- `__init__.py` files for proper package structure

You can also generate test stubs directly from a running server:

```bash
# Generate client code and test stubs from a gRPC server
pbreflect reflect -h localhost:50051 -o ./clients --gen-tests
```

## CLI Commands

PBReflect provides a comprehensive CLI interface:

```
pbreflect reflect     # Generate client code directly from a gRPC server (all-in-one)
pbreflect get-protos  # Recover proto files from a running gRPC server
pbreflect generate    # Generate client code from proto files
```

Use `--help` with any command to see all available options.

## Programmatic Usage

You can also use PBReflect in your Python code:

```python
from pathlib import Path
from pbreflect.protorecover.recover_service import RecoverService

# Basic usage
with RecoverService("localhost:50051", Path("./protos")) as service:
    service.recover_proto_files()

# With TLS
with RecoverService(
    "secure.example.com:443",
    Path("./protos"),
    use_tls=True,
    root_certificates_path=Path("./certs/ca.pem"),
    private_key_path=Path("./certs/client.key"),
    certificate_chain_path=Path("./certs/client.pem")
) as service:
    service.recover_proto_files()
```

## Use Cases

- **API Exploration**: Discover and understand the API of a gRPC service
- **Client Development**: Generate client code for services without access to original proto files
- **Testing**: Create mock clients and servers for testing
- **Reverse Engineering**: Analyze and document existing gRPC services
- **Migration**: Help migrate from one gRPC implementation to another

## Requirements

- gRPC server with reflection service enabled

## Development

### Setup

```bash
# Clone the repository and install with dev dependencies
git clone https://github.com/ValeriyMenshikov/pbreflect.git
cd pbreflect
uv sync
```

### Running Tests

```bash
# Run all tests with coverage report
uv run pytest tests/ --cov=pbreflect --cov-report=term-missing

# Run linters on both source and tests
uv run ruff check pbreflect tests
uv run mypy pbreflect tests
```

The test suite mirrors the source module structure under `tests/pbreflect/`.

### Continuous Integration

CI runs automatically on push and pull requests to `main`:

- **Tests** — ruff, mypy, pytest with coverage across Python 3.11–3.14 ([workflow](https://github.com/ValeriyMenshikov/pbreflect/actions/workflows/python-test.yml))
- **Coverage** — uploaded to [Coveralls](https://coveralls.io/github/ValeriyMenshikov/pbreflect)
- **Publish** — on release, package is built with uv and published to PyPI ([workflow](https://github.com/ValeriyMenshikov/pbreflect/actions/workflows/python-publish.yml))

## How It Works

PBReflect uses the gRPC reflection service to query a server for its service definitions. The reflection service returns `FileDescriptorProto` messages, which PBReflect then processes to reconstruct the original `.proto` files.

The process involves:

1. Connecting to the gRPC server
2. Querying the reflection service for available services
3. Retrieving file descriptors for each service
4. Reconstructing the proto definitions with proper imports
5. Writing the generated proto files to disk

## Limitations

- The target gRPC server must have the reflection service enabled
- Some advanced proto features might not be perfectly reconstructed
- Comments from the original proto files are not recoverable

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Setting up your development environment
- Running tests
- Code style and conventions
- Pull request process
- Issue reporting

## Publishing

For maintainers, we have documented the release process in [PUBLISHING.md](PUBLISHING.md), which covers:

- Version bumping
- Building packages
- Publishing to PyPI
- Creating GitHub releases
- Documentation updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The gRPC team for creating the reflection service
- All contributors who have helped improve this tool