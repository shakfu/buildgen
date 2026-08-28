"""Makefile generator class."""

import re
from pathlib import Path

from buildgen.common.base import BaseGenerator
from buildgen.common.utils import PathLike, TestFunc, UniqueList, always_true
from buildgen.makefile.variables import Var


class MakefileWriter:
    """Handles writing Makefile contents.

    Buffers all writes in memory and flushes to disk on close.
    This avoids file handle leaks and ensures atomic writes.
    """

    def __init__(self, path: PathLike):
        self.path = path
        self.lines: list[str] = []

    def write(self, line: str = "") -> None:
        """Buffer a line to be written."""
        self.lines.append(line)

    def close(self) -> None:
        """Write all buffered lines to the file."""
        with Path(self.path).open("w", encoding="utf-8") as f:
            f.write("\n".join(self.lines))
            f.write("\n")


class MakefileGenerator(BaseGenerator):
    """Generates Makefile for C/C++ code."""

    def __init__(self, path: PathLike, strict: bool = False):
        super().__init__(path, strict)
        self.cxx = "g++"
        # Emitted only when set: projects with no C sources should not carry a
        # CC assignment that overrides make's own default.
        self.cc: str | None = None
        self.pattern_rules: UniqueList = UniqueList()
        self.includes: UniqueList = UniqueList()
        self.includes_optional: UniqueList = UniqueList()
        self.conditionals: UniqueList = UniqueList()
        self.phony: UniqueList = UniqueList()
        self.clean: UniqueList = UniqueList()
        self.writer = MakefileWriter(path)

    def write(self, text: str | None = None) -> None:
        """Write a line to the Makefile."""
        if not text:
            self.writer.write("")
        else:
            self.writer.write(text)

    def close(self) -> None:
        """Close the Makefile."""
        self.writer.close()

    def check_dir(self, path: PathLike) -> bool:
        """Check whether *path* is usable as a directory reference.

        A ``$(VAR)`` reference is resolved when the generator already knows the
        variable, and accepted when it does not: the variable may be defined by
        an include, by the environment, or by a later ``add_variable`` call, so
        rejecting it here would make validation depend on call order.
        """
        defaults = {"HOME": "$(HOME)", "PWD": "$(PWD)", "CURDIR": "$(CURDIR)"}
        str_path = str(path)
        if str(path) in defaults.values():
            return True
        match = re.match(r".*\$+\((.+)\).*", str_path)
        if match:
            key = match.group(1)
            if key in defaults:
                return True
            var = self.vars.get(key)
            if var is None:
                # Resolved by make at build time, not by us at generation time.
                return True
            var_value = var.value if isinstance(var, Var) else str(var)
            return Path(var_value).is_dir()
        return Path(str_path).is_dir()

    def _normalize_path(self, path: str) -> str:
        """Normalize a path."""
        cwd = str(Path.cwd())
        home = str(Path.home())
        return path.replace(cwd, "$(CURDIR)").replace(home, "$(HOME)")

    def _normalize_paths(self, filenames: UniqueList) -> UniqueList:
        """Replace filenames with current directory."""
        cwd = str(Path.cwd())
        home = str(Path.home())
        return UniqueList(
            [f.replace(cwd, "$(CURDIR)").replace(home, "$(HOME)") for f in filenames]
        )

    def _add_entry_or_variable(
        self,
        attr: str,
        prefix: str = "",
        test_func: TestFunc | None = None,
        *entries,
        **kwargs,
    ) -> None:
        """Add an entry or variable to the Makefile.

        Validation failures raise ValueError rather than asserting: assertions
        are stripped under ``python -O``, which would make the generator accept
        silently-wrong input depending on how the interpreter was started.
        """
        if not hasattr(self, attr):
            raise ValueError(f"Invalid attribute: {attr}")
        _list = getattr(self, attr)
        if not test_func:
            test_func = always_true
        for entry in entries:
            if not test_func(entry):
                raise ValueError(f"Invalid entry for {attr}: {entry}")
            if entry in _list:
                if self.strict:
                    raise ValueError(f"entry: {entry} already exists in {attr} list")
                continue
            _list.append(f"{prefix}{entry}")
        for key, value in kwargs.items():
            if not test_func(value):
                raise ValueError(f"Invalid value for {attr} variable {key}: {value}")
            if key in self.vars:
                if self.strict:
                    raise ValueError(f"variable: {key} already exists in vars dict")
                continue
            self.vars[key] = Var(key, value)
            _list.append(f"{prefix}$({key})")
            self.var_order.append(key)

    def add_var(self, var: Var) -> None:
        """Add a variable to the Makefile."""
        self.vars[var.key] = var
        self.var_order.append(var.key)

    def add_variable(self, key: str, value: str, var_type=Var) -> None:
        """Add a variable to the Makefile."""
        self.vars[key] = var_type(key, value)
        self.var_order.append(key)

    def add_include_dirs(self, *entries, **kwargs):
        """Add include directories to the Makefile."""
        self._add_entry_or_variable(
            "include_dirs", "-I", self.check_dir, *entries, **kwargs
        )

    def add_cflags(self, *entries, **kwargs):
        """Add compiler flags to the Makefile."""
        self._add_entry_or_variable("cflags", "", None, *entries, **kwargs)

    def add_cxxflags(self, *entries, **kwargs):
        """Add c++ compiler flags to the Makefile."""
        self._add_entry_or_variable("cxxflags", "", None, *entries, **kwargs)

    def add_link_dirs(self, *entries, **kwargs):
        """Add link directories to the Makefile."""
        self._add_entry_or_variable(
            "link_dirs", "-L", self.check_dir, *entries, **kwargs
        )

    def add_ldlibs(self, *entries, **kwargs):
        """Add link libraries to the Makefile."""
        self._add_entry_or_variable("ldlibs", "", None, *entries, **kwargs)

    def add_ldflags(self, *entries, **kwargs):
        """Add linker flags to the Makefile."""
        self._add_entry_or_variable("ldflags", "", None, *entries, **kwargs)

    def add_target(
        self, name: str, recipe: str | None = None, deps: list[str] | None = None
    ):
        """Add targets to the Makefile."""
        if not recipe and not deps:
            raise ValueError("Either recipe or dependencies must be provided")
        if recipe and deps:
            _deps = " ".join(deps)
            _target = f"{name}: {_deps}\n\t{recipe}"
        elif recipe and not deps:
            _target = f"{name}:\n\t{recipe}"
        elif not recipe and deps:
            _deps = " ".join(deps)
            _target = f"{name}: {_deps}"
        if _target in self.targets:
            raise ValueError(f"target: '{_target}' already exists in `targets` list")
        self.targets.append(_target)

    def add_pattern_rule(self, target_pattern: str, source_pattern: str, recipe: str):
        """Add a pattern rule to the Makefile (e.g., %.o: %.cpp)."""
        if not target_pattern or not source_pattern or not recipe:
            raise ValueError(
                "target_pattern, source_pattern, and recipe are all required"
            )
        if "%" not in target_pattern:
            raise ValueError("target_pattern must contain '%' wildcard")
        if "%" not in source_pattern:
            raise ValueError("source_pattern must contain '%' wildcard")

        pattern_rule = f"{target_pattern}: {source_pattern}\n\t{recipe}"
        if pattern_rule in self.pattern_rules:
            raise ValueError(f"pattern rule: '{pattern_rule}' already exists")
        self.pattern_rules.append(pattern_rule)

    def add_include(self, *paths: str):
        """Add include directives to the Makefile."""
        for path in paths:
            if path and path not in self.includes:
                self.includes.append(path)

    def add_include_optional(self, *paths: str):
        """Add optional include directives (-include) to the Makefile."""
        for path in paths:
            if path and path not in self.includes_optional:
                self.includes_optional.append(path)

    def add_conditional(
        self,
        condition_type: str,
        condition: str,
        content: str,
        else_content: str | None = None,
    ):
        """Add conditional compilation block to the Makefile.

        Args:
            condition_type: 'ifeq', 'ifneq', 'ifdef', or 'ifndef'
            condition: The condition to test (e.g., '$(CC),gcc' for ifeq)
            content: Content to include if condition is true
            else_content: Optional content to include if condition is false (else block)
        """
        valid_types = ["ifeq", "ifneq", "ifdef", "ifndef"]
        if condition_type not in valid_types:
            raise ValueError(f"condition_type must be one of {valid_types}")

        if condition_type in ["ifeq", "ifneq"]:
            conditional_block = f"{condition_type} ({condition})\n{content}"
        else:  # ifdef, ifndef
            conditional_block = f"{condition_type} {condition}\n{content}"

        if else_content:
            conditional_block += f"\nelse\n{else_content}"

        conditional_block += "\nendif"

        self.conditionals.append(conditional_block)

    def add_ifeq(self, condition: str, content: str, else_content: str | None = None):
        """Add ifeq conditional block."""
        self.add_conditional("ifeq", condition, content, else_content)

    def add_ifneq(self, condition: str, content: str, else_content: str | None = None):
        """Add ifneq conditional block."""
        self.add_conditional("ifneq", condition, content, else_content)

    def add_ifdef(self, variable: str, content: str, else_content: str | None = None):
        """Add ifdef conditional block."""
        self.add_conditional("ifdef", variable, content, else_content)

    def add_ifndef(self, variable: str, content: str, else_content: str | None = None):
        """Add ifndef conditional block."""
        self.add_conditional("ifndef", variable, content, else_content)

    def add_phony(self, *entries):
        """Add phony targets to the Makefile."""
        for entry in entries:
            if entry and entry not in self.phony:
                self.phony.append(entry)

    def add_clean(self, *entries):
        """Add clean target to the Makefile."""
        for entry in entries:
            if entry and entry not in self.clean:
                self.clean.append(entry)

    def _setup_defaults(self):
        """Setup default model configuration."""
        self.add_include_dirs("$(CURDIR)")

    def _write_filelist(self, name: str, files: UniqueList) -> None:
        """Write a file list to the Makefile."""
        if not files:
            return
        if len(files) == 1:
            self.write(f"{name}={files[0]}")
        else:
            filelist = " \\\n\t".join(files)
            self.write(f"{name}=\\\n\t{filelist}\n")

    def _write_variables(self) -> None:
        """Write variables to the Makefile."""
        self.write("# project variables")
        for key in self.var_order:
            var = self.vars[key]
            self.write(f"{var}")
        self.write()

        if self.include_dirs:
            include_dirs = " ".join(self.include_dirs)
            self.write(f"INCLUDEDIRS = {include_dirs}")
        if self.link_dirs:
            link_dirs = " ".join(self.link_dirs)
            self.write(f"LINKDIRS = {link_dirs}")
        self.write()

        if self.cc:
            self.write(f"CC = {self.cc}")
        self.write(f"CXX = {self.cxx}")
        if self.cflags:
            cflags = " ".join(self.cflags)
            self.write(f"CFLAGS += {cflags} $(INCLUDEDIRS)")
        if self.cxxflags:
            cxxflags = " ".join(self.cxxflags)
            self.write(f"CXXFLAGS += {cxxflags} $(INCLUDEDIRS)")
        if self.ldflags or self.link_dirs:
            ldflags = " ".join(self.ldflags)
            self.write(f"LDFLAGS += {ldflags} $(LINKDIRS)")
        if self.ldlibs:
            ldlibs = " ".join(self.ldlibs)
            self.write(f"LDLIBS = {ldlibs}")
        self.write()

    def _write_phony(self) -> None:
        """Write phony targets to the Makefile."""
        if self.phony:
            phony_targets = " ".join(self.phony)
            self.write()
            self.write(f".PHONY: {phony_targets}")
            self.write()

    def _write_includes(self) -> None:
        """Write include directives to the Makefile."""
        if self.includes or self.includes_optional:
            self.write("# Include directives")
            for include_file in self.includes:
                self.write(f"include {include_file}")
            for include_file in self.includes_optional:
                self.write(f"-include {include_file}")
            self.write()

    def _write_conditionals(self) -> None:
        """Write conditional blocks to the Makefile."""
        if self.conditionals:
            self.write("# Conditional blocks")
            for conditional in self.conditionals:
                self.write(conditional)
                self.write()

    def _write_pattern_rules(self) -> None:
        """Write pattern rules to the Makefile."""
        if self.pattern_rules:
            self.write("# Pattern rules")
            for pattern_rule in self.pattern_rules:
                self.write(pattern_rule)
                self.write()

    def _write_targets(self) -> None:
        """Write targets to the Makefile in the order they were declared.

        Order is significant: make takes the first target in the file as the
        default goal, so callers control it by declaring that target first.
        """
        for target in self.targets:
            self.write(target)
            self.write()

    def _write_clean(self) -> None:
        """Write clean target to the Makefile."""
        if self.clean:
            clean_targets = " ".join(self.clean)
            self.write(f"clean:\n\t@rm -rf {clean_targets}")
            self.write()

    def generate(self) -> None:
        """Generate the Makefile."""
        self._setup_defaults()
        self._write_variables()
        self._write_includes()
        self._write_conditionals()
        self._write_phony()
        self._write_pattern_rules()
        self._write_targets()
        self._write_clean()
        self.close()
