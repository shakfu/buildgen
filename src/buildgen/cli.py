"""Unified CLI entry point for buildgen."""

import argparse
import copy
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from mako.template import Template

from buildgen import __version__
from buildgen.makefile.cli import add_makefile_subparsers
from buildgen.cmake.cli import add_cmake_subparsers
from buildgen.common.project import ProjectConfig
from buildgen.recipes import (
    RECIPES,
    Recipe,
    get_recipe,
    get_recipes_by_category,
    is_valid_recipe,
)
from buildgen.templates.resolver import (
    TemplateResolver,
    copy_templates,
)


# =============================================================================
# New simplified top-level commands
# =============================================================================


def cmd_new(args: argparse.Namespace) -> None:
    """Create a new project from a recipe."""
    from buildgen.skbuild.generator import SkbuildProjectGenerator
    from buildgen.cmake.project_generator import CMakeProjectGenerator, is_cmake_recipe

    name = args.name
    recipe_name = args.recipe or "cpp/executable"

    # Validate recipe
    if not is_valid_recipe(recipe_name):
        print(f"Error: Unknown recipe '{recipe_name}'", file=sys.stderr)
        print("\nUse 'buildgen list' to see available recipes.")
        sys.exit(1)

    recipe = get_recipe(recipe_name)

    # Determine output directory
    output_dir = Path(args.output) if args.output else Path(name)

    # Configurable recipes emit config first
    if recipe.configurable:
        _generate_config_file(recipe, name, output_dir)
        return

    # Handle scikit-build-core templates (py/* recipes)
    if recipe.build_system == "skbuild":
        skbuild_type = f"skbuild-{recipe.framework}"
        env_tool = getattr(args, "env", "uv")
        gen = SkbuildProjectGenerator(name, skbuild_type, output_dir, env_tool=env_tool)
        created = gen.generate()
        print(f"Created {recipe.name} project: {gen.output_dir}/")
        print(f"  (using {env_tool} for Makefile commands)")
        for path in created:
            rel_path = path.relative_to(gen.output_dir)
            print(f"  {rel_path}")
        return

    # Handle CMake-based templates (cpp/* and c/* recipes)
    if is_cmake_recipe(recipe_name):
        cmake_gen = CMakeProjectGenerator(name, recipe_name, output_dir)
        created = cmake_gen.generate()
        print(f"Created {recipe.name} project: {cmake_gen.output_dir}/")
        for path in created:
            rel_path = path.relative_to(cmake_gen.output_dir)
            print(f"  {rel_path}")
        return

    print(f"Error: No generator available for recipe '{recipe_name}'", file=sys.stderr)
    sys.exit(1)


def _generate_config_file(
    recipe: "Recipe",
    name: str,
    output_dir: Path,
    *,
    options: Optional[dict[str, Any]] = None,
) -> None:
    """Render the config template for configurable recipes."""
    if not recipe.config_template:
        raise ValueError(
            f"Recipe {recipe.name} is marked configurable but lacks config_template"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    resolver = TemplateResolver(output_dir)
    template_path, _ = resolver.resolve(recipe.name, recipe.config_template)
    template = Template(filename=str(template_path))

    base_options = dict(recipe.default_options)
    if options:
        base_options.update(options)

    content = template.render(name=name, options=base_options)
    config_filename = Path(recipe.config_template).with_suffix("")
    config_path = output_dir / config_filename
    config_path.write_text(content)

    print(f"Created configurable recipe skeleton at {output_dir}/")
    print(f"  {config_filename}")
    print("Edit the options block, then run:")
    print(f"  buildgen render {config_path}")


def cmd_list(args: argparse.Namespace) -> None:
    """List available recipes."""
    categories = get_recipes_by_category()

    category_names = {
        "cpp": "C++ Recipes",
        "c": "C Recipes",
        "py": "Python Extension Recipes",
    }

    # Filter by category if specified
    category_filter = getattr(args, "category", None)

    print("Available recipes:\n")
    for category in ["cpp", "c", "py"]:
        if category not in categories:
            continue
        if category_filter and category != category_filter:
            continue
        print(f"{category_names.get(category, category)}:")
        for recipe in categories[category]:
            print(f"  {recipe.name:<25} {recipe.description}")
        print()


def cmd_test(args: argparse.Namespace) -> None:
    """Test recipe generation and building."""
    import subprocess
    import tempfile

    from buildgen.skbuild.generator import SkbuildProjectGenerator
    from buildgen.cmake.project_generator import CMakeProjectGenerator, is_cmake_recipe

    # Handle --all flag (shortcut for --build --test)
    do_build = args.build or getattr(args, "all", False)
    do_test = args.test or getattr(args, "all", False)

    # Determine which recipes to test
    recipes_to_test = []
    if args.name:
        if args.name not in RECIPES:
            print(f"Error: Unknown recipe '{args.name}'", file=sys.stderr)
            sys.exit(1)
        recipes_to_test = [args.name]
    elif args.category:
        categories = get_recipes_by_category()
        if args.category not in categories:
            print(f"Error: Unknown category '{args.category}'", file=sys.stderr)
            sys.exit(1)
        recipes_to_test = [r.name for r in categories[args.category]]
    else:
        recipes_to_test = list(RECIPES.keys())

    # Use provided output directory or create temp directory
    if args.output:
        base_dir = Path(args.output)
        base_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        base_dir = Path(tempfile.mkdtemp(prefix="buildgen-test-"))
        cleanup = not args.keep

    results: dict[str, dict] = {}
    print(f"Testing {len(recipes_to_test)} recipes in {base_dir}\n")

    for recipe_name in recipes_to_test:
        recipe = RECIPES[recipe_name]
        project_name = recipe_name.replace("/", "_").replace("-", "_")
        project_dir = base_dir / project_name

        result: dict[str, bool | str | None] = {
            "generate": False,
            "build": False,
            "test": False,
            "error": None,
        }

        try:
            if project_dir.exists():
                shutil.rmtree(project_dir)

            if recipe.build_system == "skbuild":
                skbuild_type = f"skbuild-{recipe.framework}"
                gen = SkbuildProjectGenerator(
                    project_name, skbuild_type, project_dir, env_tool="uv"
                )
                gen.generate()
            elif is_cmake_recipe(recipe_name):
                cmake_gen = CMakeProjectGenerator(
                    project_name, recipe_name, project_dir
                )
                cmake_gen.generate()
            else:
                result["error"] = "No generator available"
                results[recipe_name] = result
                continue

            result["generate"] = True

            if do_build:
                if recipe.build_system == "skbuild":
                    proc = subprocess.run(
                        ["uv", "sync"],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if proc.returncode == 0:
                        result["build"] = True
                    else:
                        result["error"] = (
                            proc.stderr[:500] if proc.stderr else "Build failed"
                        )
                else:
                    proc = subprocess.run(
                        ["make"],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if proc.returncode == 0:
                        result["build"] = True
                    else:
                        result["error"] = (
                            proc.stderr[:500] if proc.stderr else "Build failed"
                        )

                if result["build"] and do_test:
                    if recipe.build_system == "skbuild":
                        proc = subprocess.run(
                            ["uv", "run", "pytest", "-v"],
                            cwd=project_dir,
                            capture_output=True,
                            text=True,
                            timeout=120,
                        )
                    else:
                        proc = subprocess.run(
                            ["make", "test"],
                            cwd=project_dir,
                            capture_output=True,
                            text=True,
                            timeout=120,
                        )
                    if proc.returncode == 0:
                        result["test"] = True
                    else:
                        result["error"] = (
                            proc.stderr[:500] if proc.stderr else "Tests failed"
                        )

        except subprocess.TimeoutExpired:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)[:500]

        results[recipe_name] = result

        status_parts = []
        if result["generate"]:
            status_parts.append("generated")
        if result["build"]:
            status_parts.append("built")
        if result["test"]:
            status_parts.append("tested")
        if result["error"]:
            err = str(result["error"])
            status_parts.append(f"ERROR: {err[:60]}")

        status = ", ".join(status_parts) if status_parts else "failed"
        print(f"  {recipe_name:<25} {status}")

    print("\n" + "=" * 60)
    total = len(results)
    generated = sum(1 for r in results.values() if r["generate"])
    built = sum(1 for r in results.values() if r["build"])
    tested = sum(1 for r in results.values() if r["test"])
    failed = sum(1 for r in results.values() if r["error"])

    print(f"Total: {total}, Generated: {generated}", end="")
    if do_build:
        print(f", Built: {built}", end="")
    if do_test:
        print(f", Tested: {tested}", end="")
    if failed:
        print(f", Failed: {failed}", end="")
    print()

    if cleanup:
        shutil.rmtree(base_dir)
        print(f"\nCleaned up {base_dir}")
    else:
        print(f"\nOutput preserved in {base_dir}")

    if failed > 0:
        sys.exit(1)


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate config file or build files."""
    # Mode 1: Generate boilerplate config file
    if args.config:
        config_path = Path(args.config)

        # Create a basic config template
        if config_path.suffix in (".yaml", ".yml"):
            content = """# buildgen project configuration
name: myproject
version: "0.1.0"

# C++ standard (11, 14, 17, 20, 23)
cxx_standard: 17

# Compiler flags
cflags: []
cxxflags: []
ldflags: []

# Include directories
include_dirs: []

# Libraries to link
ldlibs: []

# Targets
targets:
  - name: myapp
    type: executable
    sources:
      - src/main.cpp
"""
        else:
            import json

            config_data = {
                "name": "myproject",
                "version": "0.1.0",
                "cxx_standard": 17,
                "cflags": [],
                "cxxflags": [],
                "ldflags": [],
                "include_dirs": [],
                "ldlibs": [],
                "targets": [
                    {
                        "name": "myapp",
                        "type": "executable",
                        "sources": ["src/main.cpp"],
                    }
                ],
            }
            content = json.dumps(config_data, indent=2)

        config_path.write_text(content)
        print(f"Created config template: {config_path}")
        return

    # Mode 2: Generate build files from existing config
    if args.from_config:
        config = ProjectConfig.load(args.from_config)

        # Default to --all if no output specified
        do_makefile = args.makefile or (not args.cmake)
        do_cmake = args.cmake or (not args.makefile)

        outputs = []
        if do_makefile:
            makefile_path = "Makefile"
            config.generate_makefile(makefile_path)
            outputs.append(f"Makefile: {makefile_path}")

        if do_cmake:
            cmake_path = "CMakeLists.txt"
            config.generate_cmake(cmake_path)
            outputs.append(f"CMakeLists.txt: {cmake_path}")

        print(f"Generated from {args.from_config}:")
        for output in outputs:
            print(f"  {output}")
        return

    # No mode specified
    print("Error: Specify --config <file> or --from <file>", file=sys.stderr)
    sys.exit(1)


def cmd_render(args: argparse.Namespace) -> None:
    """Render a configurable recipe config into a full project."""
    from buildgen.skbuild.generator import SkbuildProjectGenerator, ENV_TOOLS

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    data = _load_configurable_config(config_path)

    recipe_name = data.get("recipe")
    if not recipe_name:
        print("Error: Config file must include 'recipe'", file=sys.stderr)
        sys.exit(1)

    if not is_valid_recipe(recipe_name):
        print(f"Error: Unknown recipe '{recipe_name}'", file=sys.stderr)
        sys.exit(1)

    recipe = get_recipe(recipe_name)
    if not recipe.configurable:
        print(
            f"Error: Recipe '{recipe_name}' is not a configurable recipe. "
            "Use 'buildgen new' directly.",
            file=sys.stderr,
        )
        sys.exit(1)

    project_name = data.get("name")
    if not project_name:
        print("Error: Config file must include 'name'", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output) if args.output else config_path.parent / project_name
    options = _prepare_recipe_options(
        recipe, data.get("options", {}), override_env=getattr(args, "env", None)
    )

    env_tool = options.get("env", "uv")
    if env_tool not in ENV_TOOLS:
        valid = ", ".join(ENV_TOOLS)
        print(
            f"Error: Invalid env option '{env_tool}'. Valid: {valid}", file=sys.stderr
        )
        sys.exit(1)

    skbuild_type = f"skbuild-{recipe.framework}"
    output_dir.mkdir(parents=True, exist_ok=True)
    gen = SkbuildProjectGenerator(
        project_name,
        skbuild_type,
        output_dir,
        env_tool=env_tool,
        context={"options": options},
    )
    created = gen.generate()

    generated_flex = output_dir / config_path.name
    if generated_flex.exists():
        generated_flex.unlink()
        created = [p for p in created if p != generated_flex]

    plain_config = _create_plain_config(data, options)
    output_config_name = _determine_plain_config_name(config_path.name)
    output_config = output_dir / output_config_name
    _write_plain_config(output_config, plain_config)
    created.append(output_config)

    print(f"Rendered {recipe.name} to {output_dir}/")
    for path in created:
        rel_path = path.relative_to(output_dir)
        print(f"  {rel_path}")


def _load_configurable_config(path: Path) -> dict[str, Any]:
    """Load configurable recipe config file (YAML or JSON)."""
    ext = path.suffix.lower()

    def _load_yaml() -> dict[str, Any]:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "pyyaml is required for YAML configs. Install with 'pip install pyyaml'."
            ) from exc

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError("YAML config must be a mapping at the top level")
        return data

    def _load_json() -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("JSON config must be a mapping at the top level")
        return data

    if ext in (".yaml", ".yml"):
        return _load_yaml()
    if ext == ".json":
        return _load_json()

    # Try JSON first, then YAML for unknown extensions
    try:
        return _load_json()
    except Exception:
        return _load_yaml()


def _prepare_recipe_options(
    recipe: Recipe,
    config_options: Optional[dict[str, Any]],
    *,
    override_env: Optional[str] = None,
) -> dict[str, Any]:
    """Merge recipe default options with overrides."""
    options = dict(recipe.default_options)
    if config_options:
        options.update(config_options)
    if override_env:
        options["env"] = override_env
    return options


def _determine_plain_config_name(source_name: str) -> str:
    """Convert project.flex.* filename to plain project.*."""
    if ".flex." in source_name:
        return source_name.replace(".flex.", ".", 1)
    return source_name


def _resolve_option_tokens(value: Any, options: dict[str, Any]) -> Any:
    """Replace <options.foo> placeholders with actual option values."""
    if isinstance(value, dict):
        return {k: _resolve_option_tokens(v, options) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_option_tokens(v, options) for v in value]
    if isinstance(value, str):
        pattern = re.compile(r"<options\.([a-zA-Z0-9_]+)>")

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            if key in options:
                return str(options[key])
            return match.group(0)

        return pattern.sub(repl, value)
    return value


def _create_plain_config(
    data: dict[str, Any], options: dict[str, Any]
) -> dict[str, Any]:
    """Create a config dict without options metadata."""
    filtered = {
        key: copy.deepcopy(value)
        for key, value in data.items()
        if key not in ("options", "_notes", "_options_help")
    }
    return _resolve_option_tokens(filtered, options)


def _write_plain_config(path: Path, data: dict[str, Any]) -> None:
    """Write plain config to disk as JSON or YAML."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(json.dumps(data, indent=2) + "\n")
        return

    if suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "pyyaml is required to render YAML configs. Install with 'pip install pyyaml'."
            ) from exc

        path.write_text(yaml.safe_dump(data, sort_keys=False))
        return

    # Default to JSON for unknown extensions
    path.write_text(json.dumps(data, indent=2) + "\n")


# =============================================================================
# Parser setup for new commands
# =============================================================================


def add_new_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'new' command parser."""
    recipe_choices = list(RECIPES.keys())

    parser = subparsers.add_parser(
        "new",
        help="Create a new project from a recipe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen new myapp                          # Default recipe (cpp/executable)
  buildgen new myapp -r cpp/executable        # Explicit recipe
  buildgen new myext --recipe py/pybind11     # Python extension
  buildgen new myext -r py/cython --env venv  # Use venv instead of uv
  buildgen new mylib -r c/static -o /tmp/lib  # Custom output directory

Use 'buildgen list' to see available recipes.""",
    )
    parser.add_argument(
        "name",
        help="Project name",
    )
    parser.add_argument(
        "-r",
        "--recipe",
        choices=recipe_choices,
        help="Recipe to use (default: cpp/executable)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: ./<name>)",
    )
    parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        default="uv",
        help="Environment tool for py/* recipes (default: uv)",
    )
    parser.set_defaults(func=cmd_new)


def add_list_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'list' command parser."""
    parser = subparsers.add_parser(
        "list",
        help="List available recipes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen list                 # List all recipes
  buildgen list --category py   # List Python extension recipes
  buildgen list -c cpp          # List C++ recipes""",
    )
    parser.add_argument(
        "-c",
        "--category",
        choices=["cpp", "c", "py"],
        help="Filter by category",
    )
    parser.set_defaults(func=cmd_list)


def add_test_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'test' command parser."""
    recipe_choices = list(RECIPES.keys())

    parser = subparsers.add_parser(
        "test",
        help="Test recipe generation and building",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen test                           # Test generation only
  buildgen test --build                   # Test generation and building
  buildgen test --all                     # Build and run tests
  buildgen test --category py --all       # Test Python recipes
  buildgen test --name py/cython --all    # Test specific recipe
  buildgen test --build --keep -o /tmp    # Keep output for inspection""",
    )
    parser.add_argument(
        "-n",
        "--name",
        choices=recipe_choices,
        help="Test only this recipe",
    )
    parser.add_argument(
        "-c",
        "--category",
        choices=["cpp", "c", "py"],
        help="Test only recipes in this category",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: temp directory)",
    )
    parser.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="Build generated projects",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Run tests (requires --build)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Build and test (shortcut for --build --test)",
    )
    parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        help="Keep output directory after testing",
    )
    parser.set_defaults(func=cmd_test)


def add_generate_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'generate' command parser."""
    parser = subparsers.add_parser(
        "generate",
        help="Generate config or build files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a boilerplate config file
  buildgen generate --config project.json
  buildgen generate --config project.yaml

  # Generate build files from existing config
  buildgen generate --from project.json
  buildgen generate --from project.json --makefile
  buildgen generate --from project.yaml --cmake""",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        help="Generate a boilerplate config file",
    )
    parser.add_argument(
        "--from",
        dest="from_config",
        metavar="FILE",
        help="Generate build files from existing config",
    )
    parser.add_argument(
        "--makefile",
        action="store_true",
        help="Generate Makefile only (with --from)",
    )
    parser.add_argument(
        "--cmake",
        action="store_true",
        help="Generate CMakeLists.txt only (with --from)",
    )
    parser.set_defaults(func=cmd_generate)


def add_render_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'render' command parser for configurable recipes."""
    parser = subparsers.add_parser(
        "render",
        help="Render a configurable recipe config into project files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen render myext/project.flex.json
  buildgen render project.json -o out/myext
  buildgen render project.flex.json --env venv
        """,
    )
    parser.add_argument(
        "config",
        help="Config file generated by 'buildgen new <name> -r <configurable>'",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: alongside config, named after project)",
    )
    parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        help="Override environment tool from the config options",
    )
    parser.set_defaults(func=cmd_render)


def cmd_templates_list(args: argparse.Namespace) -> None:
    """List available template types."""
    from buildgen.templates.resolver import get_builtin_template_recipes

    resolver = TemplateResolver(Path.cwd())
    recipes = get_builtin_template_recipes()

    # Group by category
    by_category: dict[str, list[str]] = {}
    for recipe in recipes:
        category = recipe.split("/")[0]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(recipe)

    category_names = {
        "py": "Python Extension Templates",
        "cpp": "C++ Templates",
        "c": "C Templates",
    }

    print("Available templates:\n")
    for category, recipe_list in by_category.items():
        print(f"{category_names.get(category, category)}:")
        for recipe in recipe_list:
            # Check for overrides
            overrides = resolver.list_overrides(recipe)
            if overrides:
                sources = set(overrides.values())
                source_str = ", ".join(sorted(sources))
                print(f"  {recipe:<20} (override: {source_str})")
            else:
                print(f"  {recipe:<20}")
        print()


def cmd_templates_copy(args: argparse.Namespace) -> None:
    """Copy templates for customization."""
    from buildgen.skbuild.templates import get_recipe_path

    template_type = args.recipe
    # Convert legacy type to recipe path if needed
    recipe_path = get_recipe_path(template_type)

    # Determine destination
    if args.to_global:
        dest_dir = Path.home() / ".buildgen/templates"
    else:
        dest_dir = Path.cwd() / ".buildgen/templates"

    try:
        copied = copy_templates(recipe_path, dest_dir)
        print(f"Copied {len(copied)} files to {dest_dir / recipe_path}/")
        for path in copied:
            rel_path = path.relative_to(dest_dir)
            print(f"  {rel_path}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_templates_show(args: argparse.Namespace) -> None:
    """Show template resolution details."""
    from buildgen.skbuild.templates import (
        resolve_template_files,
        SKBUILD_TYPES,
        get_recipe_path,
        LEGACY_TO_RECIPE_PATH,
    )

    template_type = args.recipe
    recipe_path = get_recipe_path(template_type)

    # Check if it's a valid skbuild type (either legacy or recipe path)
    if (
        template_type not in SKBUILD_TYPES
        and template_type not in LEGACY_TO_RECIPE_PATH.values()
    ):
        print(f"Unknown template: {template_type}", file=sys.stderr)
        print("\nUse 'buildgen templates list' to see available templates.")
        sys.exit(1)

    # For show, we need the legacy type name to look up TEMPLATE_FILES
    # Find the legacy name from recipe path
    legacy_type = template_type
    if template_type in LEGACY_TO_RECIPE_PATH.values():
        for legacy, recipe in LEGACY_TO_RECIPE_PATH.items():
            if recipe == template_type:
                legacy_type = legacy
                break

    env_tool = args.env
    resolved = resolve_template_files(legacy_type, env_tool, Path.cwd())

    print(f"Template: {recipe_path}")
    print(f"Environment tool: {env_tool}")
    print("\nFiles:")
    for output_path, (template_path, source) in resolved.items():
        # Clean up output path for display
        display_path = output_path.replace("${name}", "<name>")
        print(f"  {display_path:<30} -> ({source}) {template_path.name}")


def add_templates_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Add templates subcommand parsers."""
    from buildgen.skbuild.templates import SKBUILD_TYPES
    from buildgen.templates.resolver import get_builtin_template_recipes

    # Build choices: recipe paths + legacy names for backward compat
    recipe_choices = get_builtin_template_recipes()
    legacy_choices = list(SKBUILD_TYPES.keys())
    all_choices = recipe_choices + legacy_choices

    templates_parser = subparsers.add_parser(
        "templates",
        help="Manage project templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Template Override Hierarchy:
  Templates are resolved in this order (first match wins):
  1. $BUILDGEN_TEMPLATES/{recipe}/  (environment variable)
  2. .buildgen/templates/{recipe}/  (project-local)
  3. ~/.buildgen/templates/{recipe}/ (user-global)
  4. Built-in templates

Examples:
  # List available templates
  buildgen templates list

  # Copy pybind11 templates for local customization
  buildgen templates copy py/pybind11

  # Copy templates to global location
  buildgen templates copy py/pybind11 --global

  # Show where templates are resolved from
  buildgen templates show py/pybind11
        """,
    )

    templates_subparsers = templates_parser.add_subparsers(
        dest="templates_command", help="Template commands"
    )

    # templates list
    list_parser = templates_subparsers.add_parser(
        "list",
        help="List available template types",
    )
    list_parser.set_defaults(func=cmd_templates_list)

    # templates copy
    copy_parser = templates_subparsers.add_parser(
        "copy",
        help="Copy templates for customization",
    )
    copy_parser.add_argument(
        "recipe",
        choices=all_choices,
        help="Recipe template to copy (e.g., py/pybind11)",
    )
    copy_parser.add_argument(
        "--global",
        dest="to_global",
        action="store_true",
        help="Copy to ~/.buildgen/templates/ instead of .buildgen/templates/",
    )
    copy_parser.set_defaults(func=cmd_templates_copy)

    # templates show
    show_parser = templates_subparsers.add_parser(
        "show",
        help="Show template resolution details",
    )
    show_parser.add_argument(
        "recipe",
        choices=all_choices,
        help="Recipe template to show (e.g., py/pybind11)",
    )
    show_parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        default="uv",
        help="Environment tool (default: uv)",
    )
    show_parser.set_defaults(func=cmd_templates_show)


def create_parser() -> argparse.ArgumentParser:
    """Create the main CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="buildgen",
        description="Build system generator - Makefile, CMake, and more",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Common Commands:
  new <name>            Create a new project from a recipe
  list                  List available recipes
  test                  Test recipe generation and building
  generate              Generate config or build files
  render <config>       Render configurable recipe configs

Advanced Commands:
  makefile              Direct Makefile generation
  cmake                 Direct CMake generation
  templates             Manage project templates

Examples:
  buildgen new myapp
  buildgen new myext -r py/pybind11
  buildgen list --category py
  buildgen test --all
  buildgen generate --config project.json
  buildgen generate --from project.json
  buildgen render project.flex.json
        """,
    )

    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # New simplified commands (Tier 1)
    add_new_subparser(subparsers)
    add_list_subparser(subparsers)
    add_test_subparser(subparsers)
    add_generate_subparser(subparsers)
    add_render_subparser(subparsers)

    # Advanced commands (Tier 3)
    add_makefile_subparsers(subparsers)
    add_cmake_subparsers(subparsers)
    add_templates_subparsers(subparsers)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Commands with direct func (new, list, test, generate)
    if args.command in ("new", "list", "test", "generate", "render"):
        if hasattr(args, "func"):
            try:
                args.func(args)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        return

    # Handle makefile subcommands
    if args.command == "makefile":
        if not hasattr(args, "makefile_command") or not args.makefile_command:
            parser.parse_args(["makefile", "--help"])
        elif hasattr(args, "func"):
            try:
                args.func(args)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

    # Handle cmake subcommands
    elif args.command == "cmake":
        if not hasattr(args, "cmake_command") or not args.cmake_command:
            parser.parse_args(["cmake", "--help"])
        elif hasattr(args, "func"):
            try:
                args.func(args)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

    # Handle templates subcommands
    elif args.command == "templates":
        if not hasattr(args, "templates_command") or not args.templates_command:
            parser.parse_args(["templates", "--help"])
        elif hasattr(args, "func"):
            try:
                args.func(args)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
