"""Makefile function helpers and automatic variables."""

from typing import Optional

# Makefile automatic variables reference
AUTOMATIC_VARIABLES = {
    "$@": "The file name of the target of the rule.",
    "$%": "The target member name, when the target is an archive member.",
    "$<": "The name of the first prerequisite.",
    "$?": "The names of all the prerequisites that are newer than the target, with spaces between them.",
    "$^": "The names of all the prerequisites, with spaces between them.",
    "$+": "This is like `$^`, but prerequisites listed more than once are duplicated in the order they were listed in the makefile.",
    "$|": "The names of all the order-only prerequisites, with spaces between them.",
    "$*": "The stem with which an implicit rule matches.",
    "$(@D)": "The directory part of the file name of the target, with the trailing slash removed.",
    "$(@F)": "The file-within-directory part of the file name of the target.",
    "$(*D)": "The directory part of the stem.",
    "$(*F)": "The file-within-directory part of the stem.",
    "$(%D)": "The directory part of the target archive member name.",
    "$(%F)": "The file-within-directory part of the target archive member name.",
    "$(^D)": "Lists of the directory parts of all prerequisites.",
    "$(^F)": "Lists of the file-within-directory parts of all prerequisites.",
    "$(+D)": "Lists of the directory parts of all prerequisites, including multiple instances of duplicated prerequisites.",
    "$(+F)": "Lists of the file-within-directory parts of all prerequisites, including multiple instances of duplicated prerequisites.",
    "$(?D)": "Lists of the directory parts of all prerequisites that are newer than the target.",
    "$(?F)": "Lists of the file-within-directory parts of all prerequisites that are newer than the target.",
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
        else:
            raise ValueError(f"Invalid automatic variable: {var}")

    help_text = "Makefile Automatic Variables:\n"
    for var_name, description in AUTOMATIC_VARIABLES.items():
        help_text += f"  {var_name}: {description}\n"
    return help_text


# String/filename functions

def makefile_wildcard(*patterns: str) -> str:
    """Generate a Makefile wildcard function call."""
    pattern_list = " ".join(patterns)
    return f"$(wildcard {pattern_list})"


def makefile_patsubst(pattern: str, replacement: str, text: str) -> str:
    """Generate a Makefile patsubst function call."""
    return f"$(patsubst {pattern},{replacement},{text})"


def makefile_subst(from_str: str, to_str: str, text: str) -> str:
    """Generate a Makefile subst function call."""
    return f"$(subst {from_str},{to_str},{text})"


def makefile_filter(patterns: str, text: str) -> str:
    """Generate a Makefile filter function call."""
    return f"$(filter {patterns},{text})"


def makefile_filter_out(patterns: str, text: str) -> str:
    """Generate a Makefile filter-out function call."""
    return f"$(filter-out {patterns},{text})"


def makefile_sort(text: str) -> str:
    """Generate a Makefile sort function call."""
    return f"$(sort {text})"


def makefile_word(n: int, text: str) -> str:
    """Generate a Makefile word function call."""
    return f"$(word {n},{text})"


def makefile_words(text: str) -> str:
    """Generate a Makefile words function call."""
    return f"$(words {text})"


def makefile_wordlist(start: int, end: int, text: str) -> str:
    """Generate a Makefile wordlist function call."""
    return f"$(wordlist {start},{end},{text})"


def makefile_firstword(text: str) -> str:
    """Generate a Makefile firstword function call."""
    return f"$(firstword {text})"


def makefile_lastword(text: str) -> str:
    """Generate a Makefile lastword function call."""
    return f"$(lastword {text})"


# Filename functions

def makefile_dir(names: str) -> str:
    """Generate a Makefile dir function call."""
    return f"$(dir {names})"


def makefile_notdir(names: str) -> str:
    """Generate a Makefile notdir function call."""
    return f"$(notdir {names})"


def makefile_suffix(names: str) -> str:
    """Generate a Makefile suffix function call."""
    return f"$(suffix {names})"


def makefile_basename(names: str) -> str:
    """Generate a Makefile basename function call."""
    return f"$(basename {names})"


def makefile_addsuffix(suffix: str, names: str) -> str:
    """Generate a Makefile addsuffix function call."""
    return f"$(addsuffix {suffix},{names})"


def makefile_addprefix(prefix: str, names: str) -> str:
    """Generate a Makefile addprefix function call."""
    return f"$(addprefix {prefix},{names})"


def makefile_join(list1: str, list2: str) -> str:
    """Generate a Makefile join function call."""
    return f"$(join {list1},{list2})"


def makefile_realpath(names: str) -> str:
    """Generate a Makefile realpath function call."""
    return f"$(realpath {names})"


def makefile_abspath(names: str) -> str:
    """Generate a Makefile abspath function call."""
    return f"$(abspath {names})"


# Conditional functions

def makefile_if(condition: str, then_part: str, else_part: str = "") -> str:
    """Generate a Makefile if function call."""
    if else_part:
        return f"$(if {condition},{then_part},{else_part})"
    return f"$(if {condition},{then_part})"


def makefile_or(*conditions: str) -> str:
    """Generate a Makefile or function call."""
    condition_list = ",".join(conditions)
    return f"$(or {condition_list})"


def makefile_and(*conditions: str) -> str:
    """Generate a Makefile and function call."""
    condition_list = ",".join(conditions)
    return f"$(and {condition_list})"


# Control functions

def makefile_foreach(var: str, list_: str, text: str) -> str:
    """Generate a Makefile foreach function call."""
    return f"$(foreach {var},{list_},{text})"


def makefile_call(variable: str, *params: str) -> str:
    """Generate a Makefile call function call."""
    if params:
        param_list = ",".join(params)
        return f"$(call {variable},{param_list})"
    return f"$(call {variable})"


def makefile_eval(text: str) -> str:
    """Generate a Makefile eval function call."""
    return f"$(eval {text})"


# Variable functions

def makefile_origin(variable: str) -> str:
    """Generate a Makefile origin function call."""
    return f"$(origin {variable})"


def makefile_flavor(variable: str) -> str:
    """Generate a Makefile flavor function call."""
    return f"$(flavor {variable})"


def makefile_value(variable: str) -> str:
    """Generate a Makefile value function call."""
    return f"$(value {variable})"


# Shell and misc functions

def makefile_shell(command: str) -> str:
    """Generate a Makefile shell function call."""
    return f"$(shell {command})"


def makefile_strip(text: str) -> str:
    """Generate a Makefile strip function call."""
    return f"$(strip {text})"


def makefile_findstring(find: str, text: str) -> str:
    """Generate a Makefile findstring function call."""
    return f"$(findstring {find},{text})"
