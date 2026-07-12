"""Standalone runner for test generation.

Invokes PbReflectTestsPlugin directly (without going through the protoc plugin protocol)
by using grpc_tools.protoc to obtain file descriptors and then generating test stubs.
"""

import os
import tempfile
from pathlib import Path

from google.protobuf import descriptor_pb2
from google.protobuf.compiler import plugin_pb2
from grpc_tools import protoc

from pbreflect.log import get_logger
from pbreflect.pbgen.plugins.tests import PbReflectTestsPlugin
from pbreflect.pbgen.utils.file_finder import ProtoFileFinder

_logger = get_logger(__name__)


def run_test_generation(
    proto_dir: str,
    tests_output_dir: str,
    client_module: str = "clients",
    async_mode: bool = False,
    template_dir: str | None = None,
) -> None:
    """Generate pytest test stubs for all services found in proto_dir.

    Args:
        proto_dir: Directory containing .proto source files
        tests_output_dir: Directory where test files will be written
        client_module: Python module path where generated clients reside (e.g. 'clients')
        async_mode: Whether the generated clients use async mode
        template_dir: Optional custom Jinja2 templates directory
    """
    os.makedirs(tests_output_dir, exist_ok=True)

    proto_finder = ProtoFileFinder(proto_dir)
    proto_files = proto_finder.find_proto_files()
    if not proto_files:
        _logger.warning("No proto files found in %s – skipping test generation", proto_dir)
        return

    _logger.info("Collecting proto descriptors for test generation…")

    with tempfile.NamedTemporaryFile(suffix=".pb", delete=False) as tmp:
        desc_path = tmp.name

    try:
        ret = protoc.main(
            [
                "grpc_tools.protoc",
                f"--proto_path={proto_dir}",
                f"--descriptor_set_out={desc_path}",
                "--include_imports",
                *[str(p) for p in proto_files],
            ]
        )
        if ret != 0:
            _logger.error("protoc failed when collecting descriptors (exit %s) – skipping test generation", ret)
            return

        with open(desc_path, "rb") as f:
            fds = descriptor_pb2.FileDescriptorSet()
            fds.ParseFromString(f.read())
    finally:
        if os.path.exists(desc_path):
            os.unlink(desc_path)

    proto_file_names = {Path(p).name for p in proto_files}

    request = plugin_pb2.CodeGeneratorRequest()
    request.parameter = f"client_module={client_module}"
    if async_mode:
        request.parameter += ",async=true"

    for file_desc in fds.file:
        request.proto_file.append(file_desc)
        if file_desc.name in proto_file_names:
            request.file_to_generate.append(file_desc.name)

    plugin_instance = PbReflectTestsPlugin(template_dir=template_dir)
    response = plugin_instance.process_request(request)

    for out_file in response.file:
        out_path = Path(tests_output_dir) / out_file.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            _logger.debug("Skipping existing file: %s", out_path)
            continue
        out_path.write_text(out_file.content, encoding="utf-8")
        _logger.info("Generated test file: %s", out_path)

    _logger.info("Test generation completed → %s", tests_output_dir)
