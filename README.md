# PBReflect

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen)

PBReflect is a powerful tool for recovering Protocol Buffer (protobuf) definitions from gRPC services using the reflection API. It allows developers to generate `.proto` files from running gRPC servers without having access to the original source code.

## Features

- **Automatic Discovery**: Automatically discovers all services and messages exposed by a gRPC server
- **Proto Generation**: Generates complete `.proto` files with proper package structure
- **TLS Support**: Supports secure connections with custom certificates
- **Dependency Resolution**: Correctly handles dependencies between proto files
- **Simple CLI**: Easy-to-use command-line interface

## Installation

```bash
# Install using pip
pip install pbreflect

# Or using Poetry
poetry add pbreflect
```

## Quick Start

### Basic Usage

To recover proto files from a gRPC server:

```bash
# Basic usage
pbreflect get-protos -h localhost:50051 -o ./protos
```

This will connect to the gRPC server at `localhost:50051`, retrieve all available proto definitions, and save them to the `./protos` directory.

### Using TLS/SSL

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

## Programmatic Usage

You can also use PBReflect in your Python code:

```python
from pathlib import Path
from pbreflect.protorecover.recover_service import RecoverService

# Basic usage
with RecoverService("localhost:50051", Path("./protos")) as service:
    service.recover_protos()

# With TLS
with RecoverService(
    "secure.example.com:443",
    Path("./protos"),
    use_tls=True,
    root_certificates_path=Path("./certs/ca.pem"),
    private_key_path=Path("./certs/client.key"),
    certificate_chain_path=Path("./certs/client.pem")
) as service:
    service.recover_protos()
```

## Use Cases

- **API Exploration**: Discover and understand the API of a gRPC service
- **Client Development**: Generate client code for services without access to original proto files
- **Testing**: Create mock clients and servers for testing
- **Reverse Engineering**: Analyze and document existing gRPC services
- **Migration**: Help migrate from one gRPC implementation to another

## Requirements

- Python 3.8 or higher
- gRPC server with reflection service enabled

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

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The gRPC team for creating the reflection service
- All contributors who have helped improve this tool