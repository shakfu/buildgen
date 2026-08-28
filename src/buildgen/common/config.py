"""User configuration loaded from ~/.buildgen/config.toml."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path.home() / ".buildgen" / "config.toml"

CONFIG_TEMPLATE = """\
# buildgen user configuration

[user]
# name = "Your Name"
# email = "you@example.com"

[defaults]
# license = "MIT"
# cxx_standard = 17
# c_standard = 11
# python_version = "3.10"
# env_tool = "uv"

[deps]
# Pin dependency versions used in generated projects.
# These override both PyPI resolution and bundled defaults.
# Omitted packages are resolved normally.
# ruff = "0.14.0"
# mypy = "1.18.0"
# pytest = "8.4.0"
# scikit-build-core = "1.0.3"
# uv-build = "0.12.6"
"""


@dataclass
class UserConfig:
    """User-level configuration from ~/.buildgen/config.toml."""

    user_name: str = ""
    user_email: str = ""
    defaults: dict[str, Any] = field(default_factory=dict)
    deps: dict[str, str] = field(default_factory=dict)

    def to_template_context(self) -> dict[str, Any]:
        """Return a dict suitable for merging into template render context."""
        return {
            "user": {
                "name": self.user_name,
                "email": self.user_email,
            },
            "defaults": dict(self.defaults),
        }


def load_user_config(path: Path | None = None) -> UserConfig:
    """Load user configuration from a TOML file.

    Args:
        path: Path to config file. Defaults to ~/.buildgen/config.toml.

    Returns:
        UserConfig populated from the file, or empty UserConfig if the
        file does not exist or is malformed.
    """
    config_path = path or DEFAULT_CONFIG_PATH

    if not config_path.is_file():
        return UserConfig()

    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return UserConfig()

    user_section = data.get("user", {})
    defaults_section = data.get("defaults", {})
    deps_section = data.get("deps", {})

    return UserConfig(
        user_name=str(user_section.get("name", "")),
        user_email=str(user_section.get("email", "")),
        defaults=dict(defaults_section) if isinstance(defaults_section, dict) else {},
        deps={str(k): str(v) for k, v in deps_section.items()}
        if isinstance(deps_section, dict)
        else {},
    )
