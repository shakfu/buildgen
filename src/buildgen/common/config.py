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
"""


@dataclass
class UserConfig:
    """User-level configuration from ~/.buildgen/config.toml."""

    user_name: str = ""
    user_email: str = ""
    defaults: dict[str, Any] = field(default_factory=dict)

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
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return UserConfig()

    user_section = data.get("user", {})
    defaults_section = data.get("defaults", {})

    return UserConfig(
        user_name=str(user_section.get("name", "")),
        user_email=str(user_section.get("email", "")),
        defaults=dict(defaults_section) if isinstance(defaults_section, dict) else {},
    )
