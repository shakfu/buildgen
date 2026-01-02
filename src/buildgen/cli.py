"""Unified CLI entry point for buildgen."""

import argparse
import sys
from pathlib import Path

from buildgen import __version__
from buildgen.makefile.cli import add_makefile_subparsers
from buildgen.cmake.cli import add_cmake_subparsers
from buildgen.common.project import ProjectConfig
from buildgen.recipes import (
    RECIPES,
    LEGACY_TYPE_MAPPING,
    get_recipe,
    get_recipes_by_category,
    is_valid_recipe,
    resolve_recipe_name,
)
from buildgen.templates.resolver import (
    TemplateResolver,
    copy_templates,
)


def cmd_project_generate(args: argparse.Namespace) -> None:
    """Generate build files from project configuration."""
    config = ProjectConfig.load(args.config)

    outputs = []
    if args.makefile or args.all:
        makefile_path = args.makefile_output or "Makefile"
        config.generate_makefile(makefile_path)
        outputs.append(f"Makefile: {makefile_path}")

    if args.cmake or args.all:
        cmake_path = args.cmake_output or "CMakeLists.txt"
        config.generate_cmake(cmake_path)
        outputs.append(f"CMakeLists.txt: {cmake_path}")

    if outputs:
        print(f"Generated from {args.config}:")
        for output in outputs:
            print(f"  {output}")
    else:
        print("No output format specified. Use --makefile, --cmake, or --all")


def cmd_project_types(args: argparse.Namespace) -> None:
    """List available project build types (legacy, redirects to recipes)."""
    cmd_project_recipes(args)


def cmd_project_recipes(args: argparse.Namespace) -> None:
    """List available project recipes."""
    categories = get_recipes_by_category()

    # Category display names
    category_names = {
        "cpp": "C++ Recipes",
        "c": "C Recipes",
        "py": "Python Extension Recipes",
    }

    print("Available recipes:\n")
    for category in ["cpp", "c", "py"]:
        if category not in categories:
            continue
        print(f"{category_names.get(category, category)}:")
        for recipe in categories[category]:
            print(f"  {recipe.name:<25} {recipe.description}")
        print()


def cmd_test_recipes(args: argparse.Namespace) -> None:
    """Test recipe generation and building."""
    import shutil
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
        # Create a valid Python identifier from recipe name
        project_name = recipe_name.replace("/", "_").replace("-", "_")
        project_dir = base_dir / project_name

        result = {"generate": False, "build": False, "test": False, "error": None}

        try:
            # Clean up existing directory
            if project_dir.exists():
                shutil.rmtree(project_dir)

            # Generate project
            if recipe.build_system == "skbuild":
                skbuild_type = f"skbuild-{recipe.framework}"
                gen = SkbuildProjectGenerator(
                    project_name, skbuild_type, project_dir, env_tool="uv"
                )
                gen.generate()
            elif is_cmake_recipe(recipe_name):
                cmake_gen = CMakeProjectGenerator(project_name, recipe_name, project_dir)
                cmake_gen.generate()
            else:
                result["error"] = "No generator available"
                results[recipe_name] = result
                continue

            result["generate"] = True

            # Build project if requested
            if do_build:
                if recipe.build_system == "skbuild":
                    # Python extension: uv sync
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
                        result["error"] = proc.stderr[:500] if proc.stderr else "Build failed"
                else:
                    # CMake project: make
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
                        result["error"] = proc.stderr[:500] if proc.stderr else "Build failed"

                # Run tests if build succeeded and tests requested
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
                        result["error"] = proc.stderr[:500] if proc.stderr else "Tests failed"

        except subprocess.TimeoutExpired:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)[:500]

        results[recipe_name] = result

        # Print progress
        status_parts = []
        if result["generate"]:
            status_parts.append("generated")
        if result["build"]:
            status_parts.append("built")
        if result["test"]:
            status_parts.append("tested")
        if result["error"]:
            status_parts.append(f"ERROR: {result['error'][:60]}")

        status = ", ".join(status_parts) if status_parts else "failed"
        print(f"  {recipe_name:<25} {status}")

    # Summary
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

    # Exit with error if any failures
    if failed > 0:
        sys.exit(1)


def cmd_project_init(args: argparse.Namespace) -> None:
    """Create a project from a recipe template."""
    from buildgen.skbuild.generator import SkbuildProjectGenerator
    from buildgen.cmake.project_generator import CMakeProjectGenerator, is_cmake_recipe

    name = args.name or "myproject"

    # Resolve recipe: prefer --recipe, fall back to --type with legacy mapping
    recipe_name = getattr(args, "recipe", None)
    if not recipe_name:
        # Fall back to legacy --type option
        legacy_type = getattr(args, "type", None)
        if legacy_type:
            recipe_name = resolve_recipe_name(legacy_type)
        else:
            # Default to cpp/executable if neither --recipe nor --type specified
            recipe_name = "cpp/executable"

    # Validate and get recipe
    if not is_valid_recipe(recipe_name):
        print(f"Error: Unknown recipe '{recipe_name}'", file=sys.stderr)
        print("\nUse 'buildgen project recipes' to list available recipes.")
        sys.exit(1)

    recipe = get_recipe(recipe_name)

    # Determine output directory
    if args.output == "project.json":
        output_dir = Path(name)
    else:
        output_dir = Path(args.output)

    # Handle scikit-build-core templates (py/* recipes)
    if recipe.build_system == "skbuild":
        # Map recipe variant to skbuild template type
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

    # Fallback: should not reach here for valid recipes
    print(f"Error: No generator available for recipe '{recipe_name}'", file=sys.stderr)
    sys.exit(1)


def add_project_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Add project subcommand parsers."""
    project_parser = subparsers.add_parser(
        "project",
        help="Generate build files from project configuration (JSON/YAML)",
    )

    project_subparsers = project_parser.add_subparsers(
        dest="project_command", help="Project commands"
    )

    # project generate
    gen_parser = project_subparsers.add_parser(
        "generate",
        help="Generate Makefile and/or CMakeLists.txt from config",
    )
    gen_parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to project configuration file (JSON or YAML)",
    )
    gen_parser.add_argument(
        "--makefile",
        action="store_true",
        help="Generate Makefile",
    )
    gen_parser.add_argument(
        "--makefile-output",
        default=None,
        help="Output path for Makefile (default: Makefile)",
    )
    gen_parser.add_argument(
        "--cmake",
        action="store_true",
        help="Generate CMakeLists.txt",
    )
    gen_parser.add_argument(
        "--cmake-output",
        default=None,
        help="Output path for CMakeLists.txt (default: CMakeLists.txt)",
    )
    gen_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate both Makefile and CMakeLists.txt",
    )
    gen_parser.set_defaults(func=cmd_project_generate)

    # project types (legacy, redirects to recipes)
    types_parser = project_subparsers.add_parser(
        "types",
        help="List available project types (legacy, use 'recipes' instead)",
    )
    types_parser.set_defaults(func=cmd_project_types)

    # project recipes
    recipes_parser = project_subparsers.add_parser(
        "recipes",
        help="List available project recipes",
    )
    recipes_parser.set_defaults(func=cmd_project_recipes)

    # Build valid choices for --type (legacy names) and --recipe (new names)
    legacy_choices = list(LEGACY_TYPE_MAPPING.keys())
    recipe_choices = list(RECIPES.keys())

    # project init
    init_parser = project_subparsers.add_parser(
        "init",
        help="Create a sample project configuration file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen project init -n myapp --recipe cpp/executable
  buildgen project init -n mylib --recipe c/static
  buildgen project init -n myext --recipe py/pybind11

Use 'buildgen project recipes' to list available recipes.""",
    )
    init_parser.add_argument(
        "-o",
        "--output",
        default="project.json",
        help="Output path for configuration file (default: project.json)",
    )
    init_parser.add_argument(
        "-n",
        "--name",
        help="Project name (default: myproject)",
    )
    init_parser.add_argument(
        "-r",
        "--recipe",
        choices=recipe_choices,
        help="Project recipe (e.g., cpp/executable, py/pybind11)",
    )
    init_parser.add_argument(
        "-t",
        "--type",
        choices=legacy_choices,
        help="(Legacy) Project type - use --recipe instead",
    )
    init_parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        default="uv",
        help="Environment tool for Makefile (py/* recipes only, default: uv)",
    )
    init_parser.set_defaults(func=cmd_project_init)


def add_test_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Add test subcommand parsers."""
    recipe_choices = list(RECIPES.keys())

    test_parser = subparsers.add_parser(
        "test",
        help="Test buildgen functionality",
    )

    test_subparsers = test_parser.add_subparsers(
        dest="test_command", help="Test commands"
    )

    # test recipes
    recipes_parser = test_subparsers.add_parser(
        "recipes",
        help="Test recipe generation and building",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test generation only (fast, no build)
  buildgen test recipes

  # Test generation and building
  buildgen test recipes --build

  # Test generation, building, and run tests
  buildgen test recipes --build --test
  buildgen test recipes --all

  # Test only Python extension recipes
  buildgen test recipes --category py --build
  buildgen test recipes --category py --all

  # Test a specific recipe
  buildgen test recipes --name py/cython --build --test
  buildgen test recipes --name py/cython --all

  # Keep output for inspection
  buildgen test recipes --build --keep -o /tmp/recipe-tests""",
    )
    recipes_parser.add_argument(
        "-n",
        "--name",
        choices=recipe_choices,
        help="Test only this recipe",
    )
    recipes_parser.add_argument(
        "-c",
        "--category",
        choices=["cpp", "c", "py"],
        help="Test only recipes in this category",
    )
    recipes_parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: temp directory)",
    )
    recipes_parser.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="Build generated projects",
    )
    recipes_parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Run tests (requires --build)",
    )
    recipes_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Build and test (shortcut for --build --test)",
    )
    recipes_parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        help="Keep output directory after testing",
    )
    recipes_parser.set_defaults(func=cmd_test_recipes)


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
Examples:
  # Generate a Makefile
  %(prog)s makefile generate -o Makefile \\
    --include-dirs /usr/local/include --ldlibs pthread \\
    --targets "all:main.o:" --phony all clean

  # Direct compilation (Makefile-style)
  %(prog)s makefile build myprogram --cppfiles main.cpp utils.cpp \\
    --include-dirs /usr/local/include --ldlibs pthread

  # Generate CMakeLists.txt
  %(prog)s cmake generate -o CMakeLists.txt --project myproject \\
    --cxx-standard 17 --executables "myapp:main.cpp utils.cpp"

  # Build with CMake
  %(prog)s cmake build -S . -B build --build-type Release

  # Generate from project config (define once, generate both)
  %(prog)s project init -o project.json
  %(prog)s project generate -c project.json --all

Note: Escape dollar signs with backslash when passing Makefile/CMake variables via CLI.
        """,
    )

    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add makefile subcommands
    add_makefile_subparsers(subparsers)

    # Add cmake subcommands
    add_cmake_subparsers(subparsers)

    # Add project subcommands
    add_project_subparsers(subparsers)

    # Add templates subcommands
    add_templates_subparsers(subparsers)

    # Add test subcommands
    add_test_subparsers(subparsers)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

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

    # Handle project subcommands
    elif args.command == "project":
        if not hasattr(args, "project_command") or not args.project_command:
            parser.parse_args(["project", "--help"])
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

    # Handle test subcommands
    elif args.command == "test":
        if not hasattr(args, "test_command") or not args.test_command:
            parser.parse_args(["test", "--help"])
        elif hasattr(args, "func"):
            try:
                args.func(args)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
