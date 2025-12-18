"""scikit-build-core project generator."""

from pathlib import Path
from typing import Optional

from buildgen.skbuild.templates import TEMPLATES, SKBUILD_TYPES, MAKEFILE_BY_ENV

# Valid environment tool choices
ENV_TOOLS = ("uv", "venv")


class SkbuildProjectGenerator:
    """Generate scikit-build-core project files.

    Creates a complete Python extension project with:
    - pyproject.toml (scikit-build-core configuration)
    - CMakeLists.txt (build instructions)
    - Source files (C/C++/Cython)
    - Python package structure
    - Test file
    - Makefile frontend

    Supported template types:
    - skbuild-pybind11: C++ bindings with pybind11
    - skbuild-cython: Cython extension
    - skbuild-c: Pure C extension
    - skbuild-nanobind: Modern C++ bindings with nanobind

    Usage:
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11")
        files = gen.generate()
        print(f"Created {len(files)} files")

        # Use venv instead of uv
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", env_tool="venv")
    """

    def __init__(
        self,
        name: str,
        template_type: str,
        output_dir: Optional[Path] = None,
        env_tool: str = "uv",
    ):
        """Initialize the generator.

        Args:
            name: Project/package name (must be valid Python identifier)
            template_type: One of the SKBUILD_TYPES keys
            output_dir: Output directory (default: current directory / name)
            env_tool: Environment tool for Makefile ("uv" or "venv", default: "uv")
        """
        if template_type not in TEMPLATES:
            valid = ", ".join(TEMPLATES.keys())
            raise ValueError(f"Invalid template type: {template_type}. Valid: {valid}")

        if not name.isidentifier():
            raise ValueError(
                f"Invalid project name: {name}. Must be a valid Python identifier."
            )

        if env_tool not in ENV_TOOLS:
            valid = ", ".join(ENV_TOOLS)
            raise ValueError(f"Invalid env_tool: {env_tool}. Valid: {valid}")

        self.name = name
        self.template_type = template_type
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / name
        self.env_tool = env_tool

        # Build templates dict with the appropriate Makefile
        self.templates = dict(TEMPLATES[template_type])
        self.templates["Makefile"] = MAKEFILE_BY_ENV[env_tool]

    def _format_path(self, path_template: str) -> Path:
        """Format a path template with the project name."""
        return self.output_dir / path_template.format(name=self.name)

    def _format_content(self, content: str) -> str:
        """Format content template with the project name."""
        return content.format(name=self.name)

    def generate(self) -> list[Path]:
        """Generate all project files.

        Returns:
            List of paths to created files.
        """
        created_files = []

        for path_template, content_template in self.templates.items():
            file_path = self._format_path(path_template)
            content = self._format_content(content_template)

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content)
            created_files.append(file_path)

        return created_files

    def get_description(self) -> str:
        """Get description for this template type."""
        return SKBUILD_TYPES.get(self.template_type, "Unknown template type")


def get_skbuild_types() -> dict[str, str]:
    """Get available scikit-build template types and descriptions."""
    return SKBUILD_TYPES.copy()


def is_skbuild_type(template_type: str) -> bool:
    """Check if a template type is a scikit-build type."""
    return template_type in SKBUILD_TYPES
