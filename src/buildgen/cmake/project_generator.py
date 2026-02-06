"""CMake project generator using templates.

Generates C/C++ projects from templates in templates/cpp/* and templates/c/*.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from mako.template import Template
from buildgen.common.config import UserConfig
from buildgen.templates.resolver import TemplateResolver


class CMakeProjectGenerator:
    """Generate CMake-based C/C++ project files from templates.

    Creates a complete project with:
    - CMakeLists.txt
    - Makefile frontend (wraps cmake commands)
    - Source files (.c or .cpp)
    - Header files (for library recipes)
    - Test files (for test recipes)

    Supported recipes:
    - cpp/executable, cpp/static, cpp/shared, cpp/header-only
    - cpp/library-with-tests, cpp/app-with-lib, cpp/full
    - c/executable, c/static, c/shared, c/header-only
    - c/library-with-tests, c/app-with-lib, c/full

    Usage:
        gen = CMakeProjectGenerator("myapp", "cpp/executable")
        files = gen.generate()
    """

    # Map recipe paths to template file lists
    TEMPLATE_FILES = {
        # C++ templates
        "cpp/executable": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.cpp": "src/main.cpp.mako",
        },
        "cpp/static": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/shared": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/header-only": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/library-with-tests": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
            "tests/test_main.cpp": "tests/test_main.cpp.mako",
        },
        "cpp/app-with-lib": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.cpp": "src/main.cpp.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/full": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.cpp": "src/main.cpp.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
            "tests/test_main.cpp": "tests/test_main.cpp.mako",
        },
        # C templates
        "c/executable": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.c": "src/main.c.mako",
        },
        "c/static": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/shared": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/header-only": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/library-with-tests": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
            "tests/test_main.c": "tests/test_main.c.mako",
        },
        "c/app-with-lib": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.c": "src/main.c.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/full": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.c": "src/main.c.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
            "tests/test_main.c": "tests/test_main.c.mako",
        },
    }

    def __init__(
        self,
        name: str,
        recipe: str,
        output_dir: Optional[Path] = None,
        project_dir: Optional[Path] = None,
        context: Optional[dict[str, Any]] = None,
        user_config: Optional[UserConfig] = None,
    ):
        """Initialize the generator.

        Args:
            name: Project name (should be valid C/C++ identifier)
            recipe: Recipe path (e.g., "cpp/executable", "c/static")
            output_dir: Output directory (default: current directory / name)
            project_dir: Project directory for template overrides.
            context: Additional template context (overrides user_config values).
            user_config: User-level config from ~/.buildgen/config.toml.
        """
        if recipe not in self.TEMPLATE_FILES:
            valid = ", ".join(sorted(self.TEMPLATE_FILES.keys()))
            raise ValueError(f"Invalid recipe: {recipe}. Valid: {valid}")

        self.name = name
        self.recipe = recipe
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / name
        self.project_dir = project_dir
        self.resolver = TemplateResolver(project_dir)

        # Build context: user config as base, explicit context overrides
        base_ctx: Dict[str, Any] = {"user": {}, "defaults": {}}
        if user_config:
            base_ctx.update(user_config.to_template_context())
        if context:
            base_ctx.update(context)
        self.context: Dict[str, Any] = base_ctx

    def _render_path(self, path_template: str) -> Path:
        """Render a path template with the project name."""
        rendered = Template(text=path_template).render(name=self.name)
        return self.output_dir / rendered

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
        else:
            return self.resolver.resolve(self.recipe, template_path)

    def _render_template(self, template_path: Path) -> str:
        """Load and render a template file."""
        template = Template(filename=str(template_path))
        render_args: dict[str, Any] = {"name": self.name}
        if self.context:
            render_args.update(self.context)
        return template.render(**render_args)

    def generate(self) -> list[Path]:
        """Generate all project files.

        Returns:
            List of paths to created files.
        """
        created_files = []
        template_files = self.TEMPLATE_FILES[self.recipe]

        for output_path_template, template_path in template_files.items():
            # Resolve template (with override support)
            resolved_path, source = self._resolve_template(template_path)

            # Render output path (substitute ${name})
            file_path = self._render_path(output_path_template)

            # Render template content
            content = self._render_template(resolved_path)

            # Create parent directories and write file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created_files.append(file_path)

        return created_files


def is_cmake_recipe(recipe: str) -> bool:
    """Check if a recipe is a CMake-based recipe (cpp/* or c/*)."""
    return recipe in CMakeProjectGenerator.TEMPLATE_FILES
