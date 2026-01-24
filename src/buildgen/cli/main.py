"""Main CLI entry point for buildgen."""

import sys

from buildgen.cli.parsers import create_parser


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
