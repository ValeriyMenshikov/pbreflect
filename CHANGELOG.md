# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-08-03

### Added
- New `reflect` command for generating client code directly from a gRPC server in one step
- Support for custom templates via `--template-dir` option in both `generate` and `reflect` commands
- Automatic creation of `__init__.py` files in all generated code directories for proper Python package structure
- Updated documentation with examples for new features

### Changed
- Improved error handling in code generation process
- Updated README.md with comprehensive examples for new commands and options

## [0.1.1] - 2025-05-17

### Added
- Client code generation with improved typing
- Support for all Google Protobuf types in generated code

### Fixed
- Correct conversion of Google Protobuf types to Python module paths
- Fixed handling of Empty type from Google Protobuf
- Fixed escape sequence in proto_builder.py

### Changed
- Improved code documentation
- Updated README.md with more detailed examples
- Simplified gRPC client implementation, removed dependency on BaseGrpcClient

## [0.1.0] - 2025-05-01

### Added
- Initial release
- Recovery of proto files from gRPC servers using reflection API
- Client code generation based on proto files
- TLS/SSL support for secure connections
- CLI interface for convenient usage
