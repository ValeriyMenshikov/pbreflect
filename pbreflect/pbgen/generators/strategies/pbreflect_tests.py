"""PbReflect tests generator strategy."""

import os
import shutil
import sys
from typing import Optional

from pbreflect.pbgen.generators.protocols import GeneratorStrategy


class PbReflectTestsGeneratorStrategy(GeneratorStrategy):
    """Generator strategy that emits pytest test stubs via the pbreflect-tests protoc plugin."""

    def __init__(
        self,
        async_mode: bool = False,
        client_module: str = "clients",
        template_dir: Optional[str] = None,
    ) -> None:
        """Initialize the strategy.

        Args:
            async_mode: Whether the generated clients use async mode
            client_module: Python module path where generated clients reside
            template_dir: Optional path to custom templates directory
        """
        self.async_mode = async_mode
        self.client_module = client_module
        self.template_dir = template_dir

    @staticmethod
    def _find_plugin() -> str:
        """Locate the protoc-gen-pbreflect_tests executable.

        Returns the path to the installed plugin script.  Looks in the same
        directory as the current Python executable first (venv bin/), then
        falls back to a PATH search.

        Raises:
            FileNotFoundError: If the plugin script is not installed.
        """
        candidate = os.path.join(os.path.dirname(sys.executable), "protoc-gen-pbreflect_tests")
        if os.path.isfile(candidate):
            return candidate
        from_path = shutil.which("protoc-gen-pbreflect_tests")
        if from_path:
            return from_path
        raise FileNotFoundError(
            "protoc-gen-pbreflect_tests not found. "
            "Run 'pip install pbreflect' or 'uv sync' to install it."
        )

    @property
    def command_template(self) -> list[str]:
        """Get the command template for test code generation."""
        plugin_options = []

        if self.async_mode:
            plugin_options.append("async=true")

        plugin_options.append(f"client_module={self.client_module}")

        if self.template_dir:
            plugin_options.append(f"t={self.template_dir}")

        plugin_params = ",".join(plugin_options)
        plugin_out = (
            f"--pbreflect_tests_out={plugin_params}:{{output}}"
            if plugin_params
            else "--pbreflect_tests_out={output}"
        )

        plugin_exec = self._find_plugin()

        return [
            "python",
            "-m",
            "grpc_tools.protoc",
            "--proto_path={include}",
            f"--plugin=protoc-gen-pbreflect_tests={plugin_exec}",
            plugin_out,
            "{proto}",
        ]
