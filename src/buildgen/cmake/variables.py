"""CMake variable classes for different variable types."""


class CMakeVar:
    """Normal CMake variable set with set() command."""

    def __init__(self, name: str, *values: str, parent_scope: bool = False):
        """Create a CMake variable.

        Args:
            name: Variable name
            values: One or more values (creates a list if multiple)
            parent_scope: If True, sets variable in parent scope
        """
        self.name = name
        if not values:
            raise ValueError("must provide at least one value")
        self.values = list(values)
        self.parent_scope = parent_scope

    def __str__(self) -> str:
        value_str = " ".join(f'"{v}"' if " " in v else v for v in self.values)
        cmd = f"set({self.name} {value_str}"
        if self.parent_scope:
            cmd += " PARENT_SCOPE"
        cmd += ")"
        return cmd


class CMakeCacheVar:
    """CMake cache variable set with set(... CACHE ...)."""

    TYPES = ("BOOL", "FILEPATH", "PATH", "STRING", "INTERNAL")

    def __init__(
        self,
        name: str,
        value: str,
        var_type: str = "STRING",
        docstring: str = "",
        force: bool = False,
    ):
        """Create a CMake cache variable.

        Args:
            name: Variable name
            value: Variable value
            var_type: One of BOOL, FILEPATH, PATH, STRING, INTERNAL
            docstring: Documentation string shown in cmake-gui
            force: If True, overwrites existing cache value
        """
        if var_type not in self.TYPES:
            raise ValueError(f"var_type must be one of {self.TYPES}")
        self.name = name
        self.value = value
        self.var_type = var_type
        self.docstring = docstring
        self.force = force

    def __str__(self) -> str:
        value_str = f'"{self.value}"' if " " in self.value else self.value
        doc_str = f'"{self.docstring}"'
        cmd = f"set({self.name} {value_str} CACHE {self.var_type} {doc_str}"
        if self.force:
            cmd += " FORCE"
        cmd += ")"
        return cmd


class CMakeOption:
    """CMake option (boolean cache variable)."""

    def __init__(self, name: str, docstring: str, default: bool = False):
        """Create a CMake option.

        Args:
            name: Option name
            docstring: Documentation string
            default: Default value (ON or OFF)
        """
        self.name = name
        self.docstring = docstring
        self.default = default

    def __str__(self) -> str:
        default_str = "ON" if self.default else "OFF"
        return f'option({self.name} "{self.docstring}" {default_str})'


class CMakeEnvVar:
    """Reference to environment variable in CMake."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"$ENV{{{self.name}}}"

    def set(self, value: str) -> str:
        """Generate command to set environment variable."""
        return f'set(ENV{{{self.name}}} "{value}")'


def cmake_var(name: str) -> str:
    """Return a CMake variable reference."""
    return f"${{{name}}}"


def cmake_env_var(name: str) -> str:
    """Return a CMake environment variable reference."""
    return f"$ENV{{{name}}}"


def cmake_cache_var(name: str) -> str:
    """Return a CMake cache variable reference."""
    return f"$CACHE{{{name}}}"


def cmake_bool(value: bool) -> str:
    """Convert Python bool to CMake ON/OFF."""
    return "ON" if value else "OFF"
