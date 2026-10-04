"""Render a recipe's template map into a project directory.

Subclasses supply ``TEMPLATE_FILES`` (recipe path -> {output path: template
path}) and may tighten ``validate_name``.
"""

from pathlib import Path
from typing import Any, ClassVar

from mako.template import Template

from buildgen.common.config import UserConfig
from buildgen.templates.resolver import TemplateResolver


class TemplateProjectGenerator:
    """Generate project files from a recipe's template map."""

    TEMPLATE_FILES: ClassVar[dict[str, dict[str, str]]] = {}

    def __init__(
        self,
        name: str,
        recipe: str,
        output_dir: Path | None = None,
        project_dir: Path | None = None,
        context: dict[str, Any] | None = None,
        user_config: UserConfig | None = None,
    ):
        """Initialize the generator.

        Args:
            name: Project name.
            recipe: Recipe path (e.g., "cpp/executable", "quarto/book").
            output_dir: Output directory (default: current directory / name)
            project_dir: Project directory for template overrides.
            context: Additional template context (overrides user_config values).
            user_config: User-level config from ~/.buildgen/config.toml.

        Raises:
            ValueError: If the recipe or name is invalid.
        """
        if recipe not in self.TEMPLATE_FILES:
            valid = ", ".join(sorted(self.TEMPLATE_FILES.keys()))
            raise ValueError(f"Invalid recipe: {recipe}. Valid: {valid}")
        self.validate_name(name)

        self.name = name
        self.recipe = recipe
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / name
        self.project_dir = project_dir
        self.resolver = TemplateResolver(project_dir)

        # Build context: user config as base, explicit context overrides
        base_ctx: dict[str, Any] = {"user": {}, "defaults": {}}
        if user_config:
            base_ctx.update(user_config.to_template_context())
        if context:
            base_ctx.update(context)
        self.context: dict[str, Any] = base_ctx

    @staticmethod
    def validate_name(name: str) -> None:
        """Raise ValueError if *name* is unusable for this generator."""
        if not name:
            raise ValueError("Project name must not be empty.")

    def _render_path(self, path_template: str) -> Path:
        """Render a path template with the project name."""
        rendered = Template(text=path_template).render(name=self.name)
        return self.output_dir / rendered

    def output_paths(self) -> list[Path]:
        """Paths generate() would write, without writing them."""
        return [self._render_path(path) for path in self.TEMPLATE_FILES[self.recipe]]

    def _resolve_template(self, template_path: str) -> tuple[Path, str]:
        """Resolve a template path to actual file path.

        Args:
            template_path: Template path relative to recipe or common dir

        Returns:
            Tuple of (resolved path, source label)
        """
        if template_path.startswith("common/"):
            filename = template_path.replace("common/", "")
            return self.resolver.resolve_common(filename)
        return self.resolver.resolve(self.recipe, template_path)

    def _render_template(self, template_path: Path) -> str:
        """Load and render a template file."""
        template = Template(filename=str(template_path))
        render_args: dict[str, Any] = {"name": self.name}
        if self.context:
            render_args.update(self.context)
        # Mako keeps a CRLF template's line endings; write_text would then emit
        # \r\r\n on Windows.
        return template.render(**render_args).replace("\r\n", "\n")

    def generate(self) -> list[Path]:
        """Generate all project files.

        Returns:
            List of paths to created files.
        """
        created_files = []
        template_files = self.TEMPLATE_FILES[self.recipe]

        for output_path_template, template_path in template_files.items():
            # Resolve template (with override support)
            resolved_path, _source = self._resolve_template(template_path)

            # Render output path (substitute ${name})
            file_path = self._render_path(output_path_template)

            # Render template content
            content = self._render_template(resolved_path)

            # Create parent directories and write file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created_files.append(file_path)

        return created_files
