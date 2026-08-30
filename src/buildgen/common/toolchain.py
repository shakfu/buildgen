"""Toolchain discovery and diagnostics."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolInfo:
    """Information about one executable on PATH."""

    name: str
    path: str | None
    version: str | None

    @property
    def available(self) -> bool:
        return self.path is not None


def _version(path: str) -> str | None:
    """Read the first line of an executable's version output."""
    try:
        result = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=2, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (result.stdout or result.stderr).splitlines()
    return output[0].strip() if output else None


def discover_tools() -> dict[str, ToolInfo]:
    """Discover tools commonly needed by generated projects."""
    candidates = {
        "cmake": "cmake",
        "make": "make",
        "cc": "cc",
        "cxx": "c++",
        "python": "python3",
        "uv": "uv",
    }
    tools: dict[str, ToolInfo] = {}
    for name, executable in candidates.items():
        path = shutil.which(executable)
        tools[name] = ToolInfo(name, path, _version(path) if path else None)
    return tools


def required_tools(build_system: str, language: str) -> set[str]:
    """Return tools required by a recipe's build system and language."""
    if build_system == "python":
        return {"python", "uv"}
    if build_system == "skbuild":
        return {"python", "cmake", "uv"}
    required = {"cmake", "make"}
    if language == "c":
        required.add("cc")
    elif language == "cpp":
        required.add("cxx")
    return required


def diagnostics_json(tools: dict[str, ToolInfo]) -> str:
    """Serialize tool diagnostics for scripts and CI."""
    return json.dumps(
        {
            "platform": platform.platform(),
            "tools": {
                name: {
                    "available": info.available,
                    "path": info.path,
                    "version": info.version,
                }
                for name, info in tools.items()
            },
        },
        indent=2,
        sort_keys=True,
    )
