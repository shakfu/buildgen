"""Toolchain discovery and diagnostics."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
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
        "quarto": "quarto",
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
    if build_system == "quarto":
        return {"quarto", "make"}
    if build_system == "skbuild":
        return {"python", "cmake", "uv"}
    required = {"cmake", "make"}
    if language == "c":
        required.add("cc")
    elif language == "cpp":
        required.add("cxx")
    return required


_BUILD_ESSENTIALS = {
    "darwin": "xcode-select --install",
    "apt": "sudo apt-get install build-essential",
    "dnf": "sudo dnf install make gcc gcc-c++",
    "pacman": "sudo pacman -S base-devel",
    "winget": "winget install Microsoft.VisualStudio.2022.BuildTools",
}

# Keyed by tool, then by platform or Linux package manager.
INSTALL_HINTS: dict[str, dict[str, str]] = {
    "cmake": {
        "darwin": "brew install cmake",
        "apt": "sudo apt-get install cmake",
        "dnf": "sudo dnf install cmake",
        "pacman": "sudo pacman -S cmake",
        "winget": "winget install Kitware.CMake",
    },
    "make": {**_BUILD_ESSENTIALS, "winget": "winget install GnuWin32.Make"},
    "cc": _BUILD_ESSENTIALS,
    "cxx": _BUILD_ESSENTIALS,
    "python": {
        "darwin": "brew install python",
        "apt": "sudo apt-get install python3",
        "dnf": "sudo dnf install python3",
        "pacman": "sudo pacman -S python",
        "winget": "winget install Python.Python.3.13",
    },
    "uv": {
        "darwin": "brew install uv",
        "apt": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "dnf": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "pacman": "sudo pacman -S uv",
        "winget": "winget install astral-sh.uv",
    },
    "quarto": {
        "darwin": "brew install --cask quarto",
        "apt": "download a .deb from https://quarto.org/docs/get-started/",
        "dnf": "download a tarball from https://quarto.org/docs/get-started/",
        "pacman": "download a tarball from https://quarto.org/docs/get-started/",
        "winget": "winget install Posit.Quarto",
    },
}


def install_platform() -> str | None:
    """Return the key that selects install hints on this machine."""
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform == "win32":
        return "winget"
    for manager in ("apt", "dnf", "pacman"):
        if shutil.which("apt-get" if manager == "apt" else manager):
            return manager
    return None


def install_hint(tool: str, platform_key: str | None = None) -> str | None:
    """Return an install command for a tool; never runs it."""
    key = platform_key or install_platform()
    return INSTALL_HINTS.get(tool, {}).get(key) if key else None


def missing_tools(
    recipes: list[tuple[str, str]], tools: dict[str, ToolInfo]
) -> set[str]:
    """Return tools that (build_system, language) pairs need but PATH lacks."""
    needed: set[str] = set()
    for build_system, language in recipes:
        needed |= required_tools(build_system, language)
    return {name for name in needed if not tools[name].available}


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
                    "install": None if info.available else install_hint(name),
                }
                for name, info in tools.items()
            },
        },
        indent=2,
        sort_keys=True,
    )
