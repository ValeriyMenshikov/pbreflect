"""Shared infrastructure for protoc code-generation plugins."""

from pathlib import Path
from typing import Any

import jinja2


class TemplateRenderer:
    """Wraps a Jinja2 environment; created once and reused across render calls."""

    def __init__(
        self,
        default_dir: Path,
        custom_dir: str | None = None,
        extra_filters: dict[str, Any] | None = None,
    ) -> None:
        template_path = Path(custom_dir) if custom_dir else default_dir
        self._env = jinja2.Environment(  # noqa: S701
            loader=jinja2.FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        for name, func in (extra_filters or {}).items():
            self._env.filters[name] = func

    def render(self, template_name: str, **context: Any) -> str:
        return self._env.get_template(template_name).render(**context)


def parse_plugin_parameters(parameter_string: str) -> dict[str, Any]:
    """Parse a comma-separated key=value parameter string from protoc."""
    params: dict[str, Any] = {}
    if not parameter_string:
        return params
    for param in parameter_string.split(","):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key.strip()] = value.strip()
        else:
            params[param.strip()] = True
    return params
