"""CLI commands for Makefile generation and building."""

import argparse

from buildgen.makefile.builder import Builder
from buildgen.makefile.generator import MakefileGenerator


def cmd_build(args) -> None:
    """Build command using Builder class."""
    builder = Builder(args.target)

    if args.cc:
        builder.cc = args.cc
    if args.cxx:
        builder.cxx = args.cxx
    if args.cppfiles:
        builder.add_cppfiles(*args.cppfiles)
    if args.include_dirs:
        builder.add_include_dirs(*args.include_dirs)
    if args.cflags:
        builder.add_cflags(*args.cflags)
    if args.cxxflags:
        flags = []
        for flag_group in args.cxxflags:
            if "," in flag_group:
                flags.extend(flag_group.split(","))
            else:
                flags.append(flag_group)
        builder.add_cxxflags(*flags)
    if args.link_dirs:
        builder.add_link_dirs(*args.link_dirs)
    if args.ldflags:
        builder.add_ldflags(*args.ldflags)
    if args.ldlibs:
        builder.add_ldlibs(*args.ldlibs)

    builder.build(dry_run=args.dry_run)


def cmd_makefile(args) -> None:
    """Generate Makefile using MakefileGenerator class."""
    generator = MakefileGenerator(args.output)

    if args.cxx:
        generator.cxx = args.cxx
    if args.include_dirs:
        generator.add_include_dirs(*args.include_dirs)
    if args.cflags:
        flags = []
        for flag_group in args.cflags:
            if "," in flag_group:
                flags.extend(flag_group.split(","))
            else:
                flags.append(flag_group)
        generator.add_cflags(*flags)
    if args.cxxflags:
        flags = []
        for flag_group in args.cxxflags:
            if "," in flag_group:
                flags.extend(flag_group.split(","))
            else:
                flags.append(flag_group)
        generator.add_cxxflags(*flags)
    if args.link_dirs:
        generator.add_link_dirs(*args.link_dirs)
    if args.ldflags:
        flags = []
        for flag_group in args.ldflags:
            if "," in flag_group:
                flags.extend(flag_group.split(","))
            else:
                flags.append(flag_group)
        generator.add_ldflags(*flags)
    if args.ldlibs:
        libs = []
        for lib_group in args.ldlibs:
            if "," in lib_group:
                libs.extend(lib_group.split(","))
            else:
                libs.append(lib_group)
        generator.add_ldlibs(*libs)

    if args.variables:
        for var_def in args.variables:
            if "=" in var_def:
                key, value = var_def.split("=", 1)
                generator.add_variable(key.strip(), value.strip())

    if args.targets:
        for target_def in args.targets:
            parts = target_def.split(":", 2)
            name = parts[0].strip()
            deps = (
                parts[1].strip().split()
                if len(parts) > 1 and parts[1].strip()
                else None
            )
            recipe = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
            generator.add_target(name, recipe, deps)

    if args.pattern_rules:
        for pattern_def in args.pattern_rules:
            parts = pattern_def.split(":", 2)
            if len(parts) != 3:
                raise ValueError(
                    f"Pattern rule must have format 'target_pattern:source_pattern:recipe', got: {pattern_def}"
                )
            target_pattern = parts[0].strip()
            source_pattern = parts[1].strip()
            recipe = parts[2].strip()
            generator.add_pattern_rule(target_pattern, source_pattern, recipe)

    if args.phony:
        generator.add_phony(*args.phony)

    if args.clean:
        generator.add_clean(*args.clean)

    if args.includes:
        generator.add_include(*args.includes)
    if args.includes_optional:
        generator.add_include_optional(*args.includes_optional)

    if args.conditionals:
        for conditional_def in args.conditionals:
            parts = conditional_def.split(":", 3)
            if len(parts) < 3:
                raise ValueError(
                    f"Conditional must have format 'type:condition:content[:else_content]', got: {conditional_def}"
                )
            condition_type = parts[0].strip()
            condition = parts[1].strip()
            content = parts[2].strip()
            else_content = (
                parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
            )
            generator.add_conditional(condition_type, condition, content, else_content)

    generator.generate()
    print(f"Generated Makefile: {args.output}")


def add_build_parser(subparsers) -> None:
    """Add build subparser for direct compilation."""
    build_parser = subparsers.add_parser("build", help="Direct compilation using Builder")
    bp = build_parser.add_argument
    bp("target", help="Output target name")
    bp("-c", "--cppfiles", nargs="*", help="C++ source files")
    bp("--cc", help="C compiler (default: gcc)")
    bp("--cxx", help="C++ compiler (default: g++)")
    bp("-I", "--include-dirs", nargs="*", help="Include directories")
    bp("--cflags", nargs="*", help="C compiler flags (space-separated)")
    bp("--cxxflags", nargs="*", help="C++ compiler flags (space-separated)")
    bp("-L", "--link-dirs", nargs="*", help="Link directories")
    bp("--ldflags", nargs="*", help="Linker flags (space-separated)")
    bp("-l", "--ldlibs", nargs="*", help="Link libraries (space-separated)")
    bp("--dry-run", action="store_true", help="Show command without executing")
    build_parser.set_defaults(func=cmd_build)


def add_generate_parser(subparsers) -> None:
    """Add generate subparser for Makefile generation."""
    makefile_parser = subparsers.add_parser(
        "generate", help="Generate Makefile using MakefileGenerator"
    )
    mp = makefile_parser.add_argument
    mp("-o", "--output", default="Makefile", help="Output Makefile path")
    mp("--cxx", help="C++ compiler (default: g++)")
    mp("-I", "--include-dirs", nargs="*", help="Include directories")
    mp("--cflags", nargs="*", help="C compiler flags")
    mp("--cxxflags", nargs="*", help="C++ compiler flags")
    mp("-L", "--link-dirs", nargs="*", help="Link directories")
    mp("--ldflags", nargs="*", help="Linker flags")
    mp("-l", "--ldlibs", nargs="*", help="Link libraries")
    mp("-D", "--variables", nargs="*", help="Variables (KEY=VALUE format)")
    mp("-t", "--targets", nargs="*", help="Targets (name:deps:recipe format)")
    mp(
        "-p",
        "--pattern-rules",
        nargs="*",
        help="Pattern rules (target_pattern:source_pattern:recipe format)",
    )
    mp("--phony", nargs="*", help="Phony target names")
    mp("--clean", nargs="*", help="Clean patterns/files")
    mp("--includes", nargs="*", help="Include directives (file paths)")
    mp(
        "--includes-optional",
        nargs="*",
        help="Optional include directives (-include file paths)",
    )
    mp(
        "-c",
        "--conditionals",
        nargs="*",
        help="Conditional blocks (type:condition:content[:else_content] format)",
    )
    makefile_parser.set_defaults(func=cmd_makefile)


def add_makefile_subparsers(parent_subparsers) -> None:
    """Add makefile subcommand to parent parser."""
    makefile_parser = parent_subparsers.add_parser(
        "makefile", help="Makefile generation and direct compilation"
    )
    subparsers = makefile_parser.add_subparsers(dest="makefile_command")
    add_build_parser(subparsers)
    add_generate_parser(subparsers)
