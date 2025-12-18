"""Unified CLI entry point for buildgen."""

import argparse
import sys
from pathlib import Path

from buildgen import __version__
from buildgen.makefile.cli import add_makefile_subparsers
from buildgen.cmake.cli import add_cmake_subparsers
from buildgen.common.project import ProjectConfig


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


BUILD_TYPES = {
    "executable": "Single executable (src/main.cpp)",
    "static": "Static library (src/lib.cpp, include/)",
    "shared": "Shared library with -fPIC",
    "header-only": "Header-only/interface library",
    "library-with-tests": "Static library with test executable",
    "app-with-lib": "Executable linked to internal static library",
    "full": "Library + app + tests with Threads dependency",
    # scikit-build-core templates
    "skbuild-pybind11": "Python extension using pybind11 (C++ bindings)",
    "skbuild-cython": "Python extension using Cython",
    "skbuild-c": "Python C extension (direct Python.h)",
    "skbuild-nanobind": "Python extension using nanobind (modern C++ bindings)",
}


def cmd_project_types(args: argparse.Namespace) -> None:
    """List available project build types."""
    print("Available build types:\n")
    for name, description in BUILD_TYPES.items():
        print(f"  {name:<20} {description}")


def cmd_project_init(args: argparse.Namespace) -> None:
    """Create a sample project configuration file."""
    from buildgen.common.project import TargetConfig, DependencyConfig
    from buildgen.skbuild.generator import is_skbuild_type, SkbuildProjectGenerator

    output = Path(args.output)
    ext = output.suffix.lower()
    name = args.name or "myproject"
    build_type = args.type

    # Handle scikit-build-core templates separately
    if is_skbuild_type(build_type):
        # For skbuild projects, -o specifies output directory (default: ./{name})
        if args.output == "project.json":
            output_dir = Path(name)
        else:
            output_dir = Path(args.output)
        env_tool = getattr(args, "env", "uv")
        gen = SkbuildProjectGenerator(name, build_type, output_dir, env_tool=env_tool)
        created = gen.generate()
        print(f"Created {build_type} project: {gen.output_dir}/")
        print(f"  (using {env_tool} for Makefile commands)")
        for path in created:
            rel_path = path.relative_to(gen.output_dir)
            print(f"  {rel_path}")
        return

    targets: list[TargetConfig] = []
    dependencies: list[DependencyConfig] = []

    if build_type == "executable":
        targets = [
            TargetConfig(
                name=name,
                target_type="executable",
                sources=["src/main.cpp"],
                install=True,
            ),
        ]

    elif build_type == "static":
        targets = [
            TargetConfig(
                name=name,
                target_type="static",
                sources=["src/lib.cpp"],
                include_dirs=["include"],
                install=True,
            ),
        ]

    elif build_type == "shared":
        targets = [
            TargetConfig(
                name=name,
                target_type="shared",
                sources=["src/lib.cpp"],
                include_dirs=["include"],
                compile_options=["-fPIC"],
                install=True,
            ),
        ]

    elif build_type == "header-only":
        targets = [
            TargetConfig(
                name=name,
                target_type="interface",
                sources=[],
                include_dirs=["include"],
                install=True,
            ),
        ]

    elif build_type == "library-with-tests":
        targets = [
            TargetConfig(
                name=name,
                target_type="static",
                sources=["src/lib.cpp"],
                include_dirs=["include"],
                install=True,
            ),
            TargetConfig(
                name=f"{name}_tests",
                target_type="executable",
                sources=["tests/test_main.cpp"],
                include_dirs=["include"],
                link_libraries=[name],
            ),
        ]

    elif build_type == "app-with-lib":
        targets = [
            TargetConfig(
                name=f"{name}_lib",
                target_type="static",
                sources=["src/lib.cpp"],
                include_dirs=["include"],
            ),
            TargetConfig(
                name=name,
                target_type="executable",
                sources=["src/main.cpp"],
                link_libraries=[f"{name}_lib"],
                install=True,
            ),
        ]

    elif build_type == "full":
        dependencies = [
            DependencyConfig(name="Threads"),
        ]
        targets = [
            TargetConfig(
                name=f"{name}_lib",
                target_type="static",
                sources=["src/lib.cpp"],
                include_dirs=["include"],
                install=True,
            ),
            TargetConfig(
                name=name,
                target_type="executable",
                sources=["src/main.cpp"],
                link_libraries=[f"{name}_lib", "Threads::Threads"],
                install=True,
            ),
            TargetConfig(
                name=f"{name}_tests",
                target_type="executable",
                sources=["tests/test_main.cpp"],
                include_dirs=["include"],
                link_libraries=[f"{name}_lib"],
            ),
        ]

    sample = ProjectConfig(
        name=name,
        version="1.0.0",
        description=f"A {build_type} project",
        cxx_standard=17,
        compile_options=["-Wall", "-Wextra"],
        targets=targets,
        dependencies=dependencies,
    )

    if ext in (".yaml", ".yml"):
        sample.to_yaml(output)
    else:
        sample.to_json(output)

    print(f"Created {build_type} project configuration: {output}")


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

    # project types
    types_parser = project_subparsers.add_parser(
        "types",
        help="List available project build types",
    )
    types_parser.set_defaults(func=cmd_project_types)

    # project init
    init_parser = project_subparsers.add_parser(
        "init",
        help="Create a sample project configuration file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use 'buildgen project types' to list available build types.",
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
        "-t",
        "--type",
        choices=list(BUILD_TYPES.keys()),
        default="executable",
        help="Project type template (default: executable)",
    )
    init_parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        default="uv",
        help="Environment tool for Makefile (skbuild-* only, default: uv)",
    )
    init_parser.set_defaults(func=cmd_project_init)


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


if __name__ == "__main__":
    main()
