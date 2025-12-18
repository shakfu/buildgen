"""CLI commands for CMake generation and building."""

import argparse

from buildgen.cmake.generator import CMakeListsGenerator
from buildgen.cmake.builder import CMakeBuilder


def cmd_generate(args) -> None:
    """Generate CMakeLists.txt using CMakeListsGenerator."""
    generator = CMakeListsGenerator(args.output)

    # Project settings
    if args.project:
        generator.set_project(
            args.project,
            version=args.version,
            description=args.description,
        )

    if args.cmake_version:
        generator.set_cmake_version(args.cmake_version)

    if args.cxx_standard:
        generator.set_cxx_standard(args.cxx_standard)

    # Variables
    if args.variables:
        for var_def in args.variables:
            if "=" in var_def:
                key, value = var_def.split("=", 1)
                generator.add_variable(key.strip(), value.strip())

    # Options
    if args.options:
        for opt_def in args.options:
            parts = opt_def.split(":", 2)
            name = parts[0].strip()
            docstring = parts[1].strip() if len(parts) > 1 else ""
            default = parts[2].strip().lower() == "on" if len(parts) > 2 else False
            generator.add_option(name, docstring, default)

    # Dependencies
    if args.find_packages:
        for pkg in args.find_packages:
            parts = pkg.split(":")
            name = parts[0].strip()
            version = parts[1].strip() if len(parts) > 1 else None
            generator.add_find_package(name, version=version)

    # Executables
    if args.executables:
        for exe_def in args.executables:
            parts = exe_def.split(":", 1)
            name = parts[0].strip()
            sources = parts[1].strip().split() if len(parts) > 1 else []
            generator.add_executable(name, sources)

    # Libraries
    if args.libraries:
        for lib_def in args.libraries:
            parts = lib_def.split(":", 2)
            name = parts[0].strip()
            lib_type = parts[1].strip() if len(parts) > 1 else "STATIC"
            sources = parts[2].strip().split() if len(parts) > 2 else []
            generator.add_library(name, sources, lib_type=lib_type)

    # Global settings
    if args.include_dirs:
        generator.add_include_dirs(*args.include_dirs)
    if args.cxxflags:
        generator.add_cxxflags(*args.cxxflags)
    if args.ldflags:
        generator.add_ldflags(*args.ldflags)

    # Install
    if args.install:
        generator.add_install_target(*args.install)

    generator.generate()
    print(f"Generated: {args.output}")


def cmd_build(args) -> None:
    """Build using CMakeBuilder."""
    builder = CMakeBuilder(
        source_dir=args.source_dir,
        build_dir=args.build_dir,
    )

    if args.generator:
        builder.set_generator(args.generator)

    if args.build_type:
        builder.set_build_type(args.build_type)

    if args.install_prefix:
        builder.set_install_prefix(args.install_prefix)

    if args.jobs:
        builder.set_parallel_jobs(args.jobs)

    if args.targets:
        for target in args.targets:
            builder.add_build_target(target)

    # CMake options
    if args.define:
        for opt in args.define:
            if "=" in opt:
                key, value = opt.split("=", 1)
                # Try to parse as bool or int
                if value.upper() in ("ON", "TRUE", "YES", "1"):
                    builder.set_option(key, True)
                elif value.upper() in ("OFF", "FALSE", "NO", "0"):
                    builder.set_option(key, False)
                else:
                    try:
                        builder.set_option(key, int(value))
                    except ValueError:
                        builder.set_option(key, value)

    # Compiler flags
    if args.cxxflags:
        builder.add_cxxflags(*args.cxxflags)
    if args.cflags:
        builder.add_cflags(*args.cflags)
    if args.ldflags:
        builder.add_ldflags(*args.ldflags)

    # Execute
    if args.configure_only:
        builder.configure(dry_run=args.dry_run)
    elif args.build_only:
        builder.build(dry_run=args.dry_run)
    elif args.install:
        builder.full_build(dry_run=args.dry_run)
    else:
        builder.configure_and_build(dry_run=args.dry_run)


def cmd_clean(args) -> None:
    """Clean CMake build directory."""
    builder = CMakeBuilder(build_dir=args.build_dir)
    builder.clean()


def add_generate_parser(subparsers) -> None:
    """Add generate subparser for CMakeLists.txt generation."""
    parser = subparsers.add_parser(
        "generate", help="Generate CMakeLists.txt"
    )
    p = parser.add_argument

    p("-o", "--output", default="CMakeLists.txt", help="Output file path")
    p("-p", "--project", help="Project name")
    p("--version", help="Project version")
    p("--description", help="Project description")
    p("--cmake-version", default="3.16", help="Minimum CMake version")
    p("--cxx-standard", type=int, help="C++ standard (11, 14, 17, 20, 23)")

    p("-D", "--variables", nargs="*", help="Variables (KEY=VALUE format)")
    p("--options", nargs="*", help="Options (NAME:docstring:ON/OFF format)")
    p("-f", "--find-packages", nargs="*", help="Packages to find (name:version format)")

    p("-e", "--executables", nargs="*", help="Executables (name:source1 source2 format)")
    p("-l", "--libraries", nargs="*", help="Libraries (name:TYPE:source1 source2 format)")

    p("-I", "--include-dirs", nargs="*", help="Include directories")
    p("--cxxflags", nargs="*", help="C++ compiler flags")
    p("--ldflags", nargs="*", help="Linker flags")

    p("--install", nargs="*", help="Targets to install")

    parser.set_defaults(func=cmd_generate)


def add_build_parser(subparsers) -> None:
    """Add build subparser for CMake build operations."""
    parser = subparsers.add_parser(
        "build", help="Configure and build with CMake"
    )
    p = parser.add_argument

    p("-S", "--source-dir", default=".", help="Source directory")
    p("-B", "--build-dir", default="build", help="Build directory")
    p("-G", "--generator", help="CMake generator (e.g., Ninja)")
    p("--build-type", default="Release", help="Build type (Debug, Release, etc.)")
    p("--install-prefix", help="Installation prefix")

    p("-j", "--jobs", type=int, help="Parallel build jobs")
    p("-t", "--targets", nargs="*", help="Specific targets to build")

    p("-D", "--define", nargs="*", help="CMake options (KEY=VALUE format)")
    p("--cxxflags", nargs="*", help="C++ compiler flags")
    p("--cflags", nargs="*", help="C compiler flags")
    p("--ldflags", nargs="*", help="Linker flags")

    p("--configure-only", action="store_true", help="Only run configure step")
    p("--build-only", action="store_true", help="Only run build step (skip configure)")
    p("--install", action="store_true", help="Also run install step")
    p("--dry-run", action="store_true", help="Show commands without executing")

    parser.set_defaults(func=cmd_build)


def add_clean_parser(subparsers) -> None:
    """Add clean subparser."""
    parser = subparsers.add_parser(
        "clean", help="Clean CMake build directory"
    )
    parser.add_argument(
        "-B", "--build-dir", default="build", help="Build directory to clean"
    )
    parser.set_defaults(func=cmd_clean)


def add_cmake_subparsers(parent_subparsers) -> None:
    """Add cmake subcommand to parent parser."""
    cmake_parser = parent_subparsers.add_parser(
        "cmake", help="CMake generation and building"
    )
    subparsers = cmake_parser.add_subparsers(dest="cmake_command")
    add_generate_parser(subparsers)
    add_build_parser(subparsers)
    add_clean_parser(subparsers)
