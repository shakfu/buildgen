"""scikit-build-core project generator."""

from pathlib import Path
from typing import Optional, Any, Dict

from mako.lookup import TemplateLookup
from mako.template import Template
from buildgen.common.config import UserConfig
from buildgen.skbuild.templates import (
    SKBUILD_TYPES,
    TEMPLATE_FILES,
    resolve_template_files,
)
from buildgen.templates.resolver import BUILTIN_TEMPLATES_DIR

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

    Template Override Support:
    Templates are resolved in this order (first match wins):
    1. $BUILDGEN_TEMPLATES/skbuild/{type}/
    2. {project_dir}/.buildgen/templates/skbuild/{type}/
    3. ~/.buildgen/templates/skbuild/{type}/
    4. Built-in templates

    Usage:
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11")
        files = gen.generate()
        print(f"Created {len(files)} files")

        # Use venv instead of uv
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", env_tool="venv")

        # Use template overrides from a specific project directory
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11",
                                      project_dir=Path("/path/to/project"))
    """

    def __init__(
        self,
        name: str,
        template_type: str,
        output_dir: Optional[Path] = None,
        env_tool: str = "uv",
        project_dir: Optional[Path] = None,
        context: Optional[dict[str, Any]] = None,
        user_config: Optional[UserConfig] = None,
    ):
        """Initialize the generator.

        Args:
            name: Project/package name (must be valid Python identifier)
            template_type: One of the SKBUILD_TYPES keys
            output_dir: Output directory (default: current directory / name)
            env_tool: Environment tool for Makefile ("uv" or "venv", default: "uv")
            project_dir: Project directory for template overrides. If None,
                         uses output_dir's parent for local override lookup.
            context: Additional template context (overrides user_config values).
            user_config: User-level config from ~/.buildgen/config.toml.
        """
        if template_type not in TEMPLATE_FILES:
            valid = ", ".join(TEMPLATE_FILES.keys())
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
        self.project_dir = project_dir

        # Build context: user config as base, explicit context overrides
        base_ctx: Dict[str, Any] = {"user": {}, "defaults": {}}
        if user_config:
            base_ctx.update(user_config.to_template_context())
        if context:
            base_ctx.update(context)
        self.context: Dict[str, Any] = base_ctx
        if "options" not in self.context:
            self.context["options"] = {}

        # Get resolved template paths (with override support)
        self.resolved_templates = resolve_template_files(
            template_type, env_tool, project_dir
        )

    def _render_path(self, path_template: str) -> Path:
        """Render a path template with the project name.

        Converts ${name} in path to actual name.
        """
        # Use Mako to render the path (handles ${name} syntax)
        rendered = Template(text=path_template).render(name=self.name)
        return self.output_dir / rendered

    def _render_template(self, template_path: Path) -> str:
        """Load and render a template file.

        Args:
            template_path: Full path to template file.

        Returns:
            Rendered template content.
        """
        # Use TemplateLookup to enable <%include> directives
        # Search in the template's parent directory and the py/ templates root
        lookup = TemplateLookup(
            directories=[
                str(template_path.parent),
                str(BUILTIN_TEMPLATES_DIR / "py"),
            ],
            input_encoding="utf-8",
        )
        template = lookup.get_template(template_path.name)
        render_args = {"name": self.name}
        if self.context:
            render_args.update(self.context)
        return template.render(**render_args)

    def generate(self) -> list[Path]:
        """Generate all project files.

        Returns:
            List of paths to created files.
        """
        created_files = []

        for output_path_template, (
            template_path,
            source,
        ) in self.resolved_templates.items():
            file_path = self._render_path(output_path_template)
            content = self._render_template(template_path)

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content)
            created_files.append(file_path)

        return created_files

    def get_description(self) -> str:
        """Get description for this template type."""
        return SKBUILD_TYPES.get(self.template_type, "Unknown template type")

    def get_template_sources(self) -> dict[str, str]:
        """Get the source location for each template file.

        Returns:
            Dict mapping output filename to source label
            ("env", "local", "global", or "built-in")
        """
        return {
            output_path: source
            for output_path, (_, source) in self.resolved_templates.items()
        }


def get_skbuild_types() -> dict[str, str]:
    """Get available scikit-build template types and descriptions."""
    return SKBUILD_TYPES.copy()


def is_skbuild_type(template_type: str) -> bool:
    """Check if a template type is a scikit-build type."""
    return template_type in SKBUILD_TYPES
