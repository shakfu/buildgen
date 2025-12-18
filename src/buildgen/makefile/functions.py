"""Makefile function helpers and automatic variables.

Usage:
    from buildgen.makefile.functions import Mk

    Mk.wildcard("*.cpp")           # $(wildcard *.cpp)
    Mk.patsubst("%.cpp", "%.o", "$(SOURCES)")
    Mk.shell("pkg-config --cflags libfoo")
"""

from typing import Optional


# Makefile automatic variables reference
AUTOMATIC_VARIABLES = {
    "$@": "The file name of the target of the rule.",
    "$%": "The target member name, when the target is an archive member.",
    "$<": "The name of the first prerequisite.",
    "$?": "The names of all the prerequisites that are newer than the target.",
    "$^": "The names of all the prerequisites, with spaces between them.",
    "$+": "Like $^, but prerequisites listed more than once are duplicated.",
    "$|": "The names of all the order-only prerequisites.",
    "$*": "The stem with which an implicit rule matches.",
    "$(@D)": "The directory part of the target file name.",
    "$(@F)": "The file-within-directory part of the target.",
    "$(*D)": "The directory part of the stem.",
    "$(*F)": "The file-within-directory part of the stem.",
    "$(%D)": "The directory part of the target archive member name.",
    "$(%F)": "The file-within-directory part of the archive member name.",
    "$(^D)": "Directory parts of all prerequisites.",
    "$(^F)": "File-within-directory parts of all prerequisites.",
    "$(+D)": "Directory parts of all prerequisites (with duplicates).",
    "$(+F)": "File-within-directory parts of all prerequisites (with duplicates).",
    "$(?D)": "Directory parts of prerequisites newer than the target.",
    "$(?F)": "File-within-directory parts of prerequisites newer than the target.",
}


def auto_var(var: str) -> str:
    """Return a Makefile automatic variable."""
    if var not in AUTOMATIC_VARIABLES:
        raise ValueError(f"Invalid automatic variable: {var}")
    return var


def get_auto_var_help(var: Optional[str] = None) -> str:
    """Get help text for automatic variables."""
    if var:
        if var in AUTOMATIC_VARIABLES:
            return f"{var}: {AUTOMATIC_VARIABLES[var]}"
        raise ValueError(f"Invalid automatic variable: {var}")

    lines = ["Makefile Automatic Variables:"]
    for var_name, description in AUTOMATIC_VARIABLES.items():
        lines.append(f"  {var_name}: {description}")
    return "\n".join(lines)


class Mk:
    """Makefile function generators.

    Generates Makefile function call syntax as strings.
    All methods are static - no instance needed.

    Usage:
        from buildgen.makefile.functions import Mk

        Mk.wildcard("src/*.cpp")        # $(wildcard src/*.cpp)
        Mk.patsubst("%.cpp", "%.o", x)  # $(patsubst %.cpp,%.o,x)
        Mk.shell("date +%Y")            # $(shell date +%Y)
    """

    # String functions

    @staticmethod
    def wildcard(*patterns: str) -> str:
        """$(wildcard pattern...) - Expand wildcards."""
        return f"$(wildcard {' '.join(patterns)})"

    @staticmethod
    def patsubst(pattern: str, replacement: str, text: str) -> str:
        """$(patsubst pattern,replacement,text) - Pattern substitution."""
        return f"$(patsubst {pattern},{replacement},{text})"

    @staticmethod
    def subst(from_str: str, to_str: str, text: str) -> str:
        """$(subst from,to,text) - Simple substitution."""
        return f"$(subst {from_str},{to_str},{text})"

    @staticmethod
    def filter(patterns: str, text: str) -> str:
        """$(filter pattern...,text) - Keep matching words."""
        return f"$(filter {patterns},{text})"

    @staticmethod
    def filter_out(patterns: str, text: str) -> str:
        """$(filter-out pattern...,text) - Remove matching words."""
        return f"$(filter-out {patterns},{text})"

    @staticmethod
    def sort(text: str) -> str:
        """$(sort list) - Sort and deduplicate."""
        return f"$(sort {text})"

    @staticmethod
    def word(n: int, text: str) -> str:
        """$(word n,text) - Get nth word (1-indexed)."""
        return f"$(word {n},{text})"

    @staticmethod
    def words(text: str) -> str:
        """$(words text) - Count words."""
        return f"$(words {text})"

    @staticmethod
    def wordlist(start: int, end: int, text: str) -> str:
        """$(wordlist start,end,text) - Get word range."""
        return f"$(wordlist {start},{end},{text})"

    @staticmethod
    def firstword(text: str) -> str:
        """$(firstword text) - Get first word."""
        return f"$(firstword {text})"

    @staticmethod
    def lastword(text: str) -> str:
        """$(lastword text) - Get last word."""
        return f"$(lastword {text})"

    @staticmethod
    def strip(text: str) -> str:
        """$(strip text) - Remove leading/trailing whitespace."""
        return f"$(strip {text})"

    @staticmethod
    def findstring(find: str, text: str) -> str:
        """$(findstring find,text) - Search for substring."""
        return f"$(findstring {find},{text})"

    # Filename functions

    @staticmethod
    def dir(names: str) -> str:
        """$(dir names...) - Extract directory part."""
        return f"$(dir {names})"

    @staticmethod
    def notdir(names: str) -> str:
        """$(notdir names...) - Extract non-directory part."""
        return f"$(notdir {names})"

    @staticmethod
    def suffix(names: str) -> str:
        """$(suffix names...) - Extract suffix."""
        return f"$(suffix {names})"

    @staticmethod
    def basename(names: str) -> str:
        """$(basename names...) - Extract basename (without suffix)."""
        return f"$(basename {names})"

    @staticmethod
    def addsuffix(suffix: str, names: str) -> str:
        """$(addsuffix suffix,names) - Add suffix to each word."""
        return f"$(addsuffix {suffix},{names})"

    @staticmethod
    def addprefix(prefix: str, names: str) -> str:
        """$(addprefix prefix,names) - Add prefix to each word."""
        return f"$(addprefix {prefix},{names})"

    @staticmethod
    def join(list1: str, list2: str) -> str:
        """$(join list1,list2) - Join corresponding words."""
        return f"$(join {list1},{list2})"

    @staticmethod
    def realpath(names: str) -> str:
        """$(realpath names...) - Canonical absolute path."""
        return f"$(realpath {names})"

    @staticmethod
    def abspath(names: str) -> str:
        """$(abspath names...) - Absolute path (no symlink resolution)."""
        return f"$(abspath {names})"

    # Conditional functions

    @staticmethod
    def if_(condition: str, then_part: str, else_part: str = "") -> str:
        """$(if condition,then[,else]) - Conditional."""
        if else_part:
            return f"$(if {condition},{then_part},{else_part})"
        return f"$(if {condition},{then_part})"

    @staticmethod
    def or_(*conditions: str) -> str:
        """$(or condition...) - Logical OR."""
        return f"$(or {','.join(conditions)})"

    @staticmethod
    def and_(*conditions: str) -> str:
        """$(and condition...) - Logical AND."""
        return f"$(and {','.join(conditions)})"

    # Control functions

    @staticmethod
    def foreach(var: str, list_: str, text: str) -> str:
        """$(foreach var,list,text) - Loop expansion."""
        return f"$(foreach {var},{list_},{text})"

    @staticmethod
    def call(variable: str, *params: str) -> str:
        """$(call variable,param...) - Call user-defined function."""
        if params:
            return f"$(call {variable},{','.join(params)})"
        return f"$(call {variable})"

    @staticmethod
    def eval(text: str) -> str:
        """$(eval text) - Evaluate as Makefile syntax."""
        return f"$(eval {text})"

    # Variable functions

    @staticmethod
    def origin(variable: str) -> str:
        """$(origin variable) - Get variable origin."""
        return f"$(origin {variable})"

    @staticmethod
    def flavor(variable: str) -> str:
        """$(flavor variable) - Get variable flavor."""
        return f"$(flavor {variable})"

    @staticmethod
    def value(variable: str) -> str:
        """$(value variable) - Get unexpanded value."""
        return f"$(value {variable})"

    # Shell function

    @staticmethod
    def shell(command: str) -> str:
        """$(shell command) - Execute shell command."""
        return f"$(shell {command})"
