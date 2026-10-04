"""CMake project generator using templates.

Generates C/C++ projects from templates in templates/cpp/* and templates/c/*.
"""

from typing import ClassVar

from buildgen.templates.generator import TemplateProjectGenerator


class CMakeProjectGenerator(TemplateProjectGenerator):
    """Generate CMake-based C/C++ project files from templates.

    Creates a complete project with:
    - CMakeLists.txt
    - Makefile frontend (wraps cmake commands)
    - Source files (.c or .cpp)
    - Header files (for library recipes)
    - Test files (for test recipes)

    Supported recipes:
    - cpp/executable, cpp/static, cpp/shared, cpp/header-only
    - cpp/library-with-tests, cpp/app-with-lib, cpp/full
    - c/executable, c/static, c/shared, c/header-only
    - c/library-with-tests, c/app-with-lib, c/full

    Usage:
        gen = CMakeProjectGenerator("myapp", "cpp/executable")
        files = gen.generate()
    """

    # Map recipe paths to template file lists
    TEMPLATE_FILES: ClassVar[dict[str, dict[str, str]]] = {
        # C++ templates
        "cpp/executable": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.cpp": "src/main.cpp.mako",
        },
        "cpp/static": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/shared": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/header-only": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/library-with-tests": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
            "tests/test_main.cpp": "tests/test_main.cpp.mako",
        },
        "cpp/app-with-lib": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.cpp": "src/main.cpp.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
        },
        "cpp/full": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.cpp": "src/main.cpp.mako",
            "src/lib.cpp": "src/lib.cpp.mako",
            "include/${name}/lib.hpp": "include/${name}/lib.hpp.mako",
            "tests/test_main.cpp": "tests/test_main.cpp.mako",
        },
        # C templates
        "c/executable": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.c": "src/main.c.mako",
        },
        "c/static": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/shared": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/header-only": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/library-with-tests": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
            "tests/test_main.c": "tests/test_main.c.mako",
        },
        "c/app-with-lib": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.c": "src/main.c.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
        },
        "c/full": {
            ".gitignore": "common/gitignore.cmake.mako",
            "Makefile": "common/Makefile.cmake.mako",
            "TODO.md": "common/TODO.md.mako",
            "CMakeLists.txt": "CMakeLists.txt.mako",
            "src/main.c": "src/main.c.mako",
            "src/lib.c": "src/lib.c.mako",
            "include/${name}/lib.h": "include/${name}/lib.h.mako",
            "tests/test_main.c": "tests/test_main.c.mako",
        },
    }

    @staticmethod
    def validate_name(name: str) -> None:
        """Raise ValueError unless *name* is a valid C/C++ identifier."""
        # The name is substituted into C/C++ namespaces, header guards, and
        # symbol prefixes, so it must be a valid identifier (e.g. "my-lib"
        # would produce "namespace my-lib" and "MY-LIB_LIB_HPP").
        if not name.isidentifier():
            raise ValueError(
                f"Invalid project name: {name}. Must be a valid C/C++ identifier."
            )


def is_cmake_recipe(recipe: str) -> bool:
    """Check whether *recipe* is a CMake-based recipe (cpp/* or c/*).

    Answers from the recipe registry, not from this module's template map, so
    a recipe registered as CMake-based but missing its templates reports as
    CMake-based and fails later with a message naming the missing template set.
    Callers dispatching to a generator should test ``build_system`` directly.
    """
    from buildgen.recipes import RECIPES, resolve_recipe_name

    entry = RECIPES.get(resolve_recipe_name(recipe))
    return entry is not None and entry.build_system == "cmake"
