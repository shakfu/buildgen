"""CMakeLists.txt generator class."""

import os
from typing import Optional

from buildgen.common.utils import UniqueList, PathLike
from buildgen.common.base import BaseGenerator
from buildgen.cmake.variables import CMakeVar, CMakeCacheVar, CMakeOption, cmake_var
from buildgen.cmake.functions import (
    cmake_minimum_required,
    cmake_project,
    cmake_add_executable,
    cmake_add_library,
    cmake_target_link_libraries,
    cmake_target_include_directories,
    cmake_target_compile_definitions,
    cmake_target_compile_options,
    cmake_find_package,
    cmake_message,
)


class CMakeWriter:
    """Handles writing CMakeLists.txt contents."""

    def __init__(self, path: PathLike):
        self.path = path
        self.lines: list[str] = []

    def write(self, line: str = "") -> None:
        """Add a line to the buffer."""
        self.lines.append(line)

    def close(self) -> None:
        """Write buffer to file."""
        with open(self.path, "w", encoding="utf8") as f:
            f.write("\n".join(self.lines))
            f.write("\n")


class CMakeListsGenerator(BaseGenerator):
    """Generates CMakeLists.txt for C/C++ projects."""

    def __init__(self, path: PathLike = "CMakeLists.txt", strict: bool = False):
        super().__init__(path, strict)
        self.cmake_version = "3.16"
        self.project_name: Optional[str] = None
        self.project_version: Optional[str] = None
        self.project_description: Optional[str] = None
        self.project_languages: list[str] = ["CXX"]

        # Target tracking
        self.executables: dict[str, dict] = {}
        self.libraries: dict[str, dict] = {}

        # Dependencies
        self.find_packages: UniqueList = UniqueList()
        self.fetchcontent_deps: UniqueList = UniqueList()

        # Global settings
        self.cxx_standard: Optional[int] = None
        self.cxx_standard_required: bool = True
        self.cxx_extensions: bool = False

        # Custom commands/content
        self.custom_sections: list[str] = []
        self.install_targets: UniqueList = UniqueList()

        # Writer
        self.writer = CMakeWriter(path)

    def write(self, text: str = "") -> None:
        """Write a line to the CMakeLists.txt."""
        self.writer.write(text)

    def close(self) -> None:
        """Close the CMakeLists.txt."""
        self.writer.close()

    def set_project(
        self,
        name: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        languages: Optional[list[str]] = None,
    ) -> None:
        """Set project information."""
        self.project_name = name
        self.project_version = version
        self.project_description = description
        if languages:
            self.project_languages = languages

    def set_cmake_version(self, version: str) -> None:
        """Set minimum required CMake version."""
        self.cmake_version = version

    def set_cxx_standard(
        self, standard: int, required: bool = True, extensions: bool = False
    ) -> None:
        """Set C++ standard for all targets."""
        self.cxx_standard = standard
        self.cxx_standard_required = required
        self.cxx_extensions = extensions

    def add_variable(self, key: str, value: str, var_type=CMakeVar) -> None:
        """Add a variable to the CMakeLists.txt."""
        self.vars[key] = var_type(key, value)
        self.var_order.append(key)

    def add_cache_variable(
        self,
        key: str,
        value: str,
        var_type: str = "STRING",
        docstring: str = "",
        force: bool = False,
    ) -> None:
        """Add a cache variable."""
        self.vars[key] = CMakeCacheVar(key, value, var_type, docstring, force)
        self.var_order.append(key)

    def add_option(self, name: str, docstring: str, default: bool = False) -> None:
        """Add an option (boolean cache variable)."""
        self.vars[name] = CMakeOption(name, docstring, default)
        self.var_order.append(name)

    def add_executable(
        self,
        name: str,
        sources: list[str],
        include_dirs: Optional[list[str]] = None,
        link_libraries: Optional[list[str]] = None,
        compile_definitions: Optional[list[str]] = None,
        compile_options: Optional[list[str]] = None,
    ) -> None:
        """Add an executable target."""
        self.executables[name] = {
            "sources": sources,
            "include_dirs": include_dirs or [],
            "link_libraries": link_libraries or [],
            "compile_definitions": compile_definitions or [],
            "compile_options": compile_options or [],
        }

    def add_library(
        self,
        name: str,
        sources: list[str],
        lib_type: str = "STATIC",
        include_dirs: Optional[list[str]] = None,
        link_libraries: Optional[list[str]] = None,
        compile_definitions: Optional[list[str]] = None,
        compile_options: Optional[list[str]] = None,
    ) -> None:
        """Add a library target."""
        self.libraries[name] = {
            "sources": sources,
            "lib_type": lib_type,
            "include_dirs": include_dirs or [],
            "link_libraries": link_libraries or [],
            "compile_definitions": compile_definitions or [],
            "compile_options": compile_options or [],
        }

    def add_target(
        self, name: str, recipe: Optional[str] = None, deps: Optional[list[str]] = None
    ) -> None:
        """Add a target (BaseGenerator interface).

        For CMake, this adds an executable with sources from deps.
        """
        sources = deps or []
        self.add_executable(name, sources)

    def add_find_package(
        self,
        package: str,
        version: Optional[str] = None,
        required: bool = True,
        components: Optional[list[str]] = None,
    ) -> None:
        """Add a find_package dependency."""
        self.find_packages.add(
            {
                "package": package,
                "version": version,
                "required": required,
                "components": components,
            }
        )

    def add_fetchcontent(
        self,
        name: str,
        git_repository: Optional[str] = None,
        git_tag: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        """Add a FetchContent dependency."""
        self.fetchcontent_deps.add(
            {
                "name": name,
                "git_repository": git_repository,
                "git_tag": git_tag,
                "url": url,
            }
        )

    def add_install_target(self, *targets: str) -> None:
        """Add targets to install."""
        for target in targets:
            self.install_targets.add(target)

    def add_custom(self, content: str) -> None:
        """Add custom CMake content."""
        self.custom_sections.append(content)

    def add_include_dirs(self, *entries, **kwargs) -> None:
        """Add global include directories."""
        for entry in entries:
            self.include_dirs.add(entry)

    def add_cflags(self, *entries, **kwargs) -> None:
        """Add global C compiler flags."""
        for entry in entries:
            self.cflags.add(entry)

    def add_cxxflags(self, *entries, **kwargs) -> None:
        """Add global C++ compiler flags."""
        for entry in entries:
            self.cxxflags.add(entry)

    def add_link_dirs(self, *entries, **kwargs) -> None:
        """Add global link directories."""
        for entry in entries:
            self.link_dirs.add(entry)

    def add_ldlibs(self, *entries, **kwargs) -> None:
        """Add global link libraries."""
        for entry in entries:
            self.ldlibs.add(entry)

    def add_ldflags(self, *entries, **kwargs) -> None:
        """Add global linker flags."""
        for entry in entries:
            self.ldflags.add(entry)

    def _write_header(self) -> None:
        """Write CMake header (minimum version, project)."""
        self.write(cmake_minimum_required(self.cmake_version))
        self.write()

        if self.project_name:
            self.write(
                cmake_project(
                    self.project_name,
                    version=self.project_version,
                    description=self.project_description,
                    languages=self.project_languages,
                )
            )
            self.write()

    def _write_standards(self) -> None:
        """Write C++ standard settings."""
        if self.cxx_standard:
            self.write("# C++ Standard")
            self.write(f"set(CMAKE_CXX_STANDARD {self.cxx_standard})")
            self.write(
                f"set(CMAKE_CXX_STANDARD_REQUIRED {'ON' if self.cxx_standard_required else 'OFF'})"
            )
            self.write(
                f"set(CMAKE_CXX_EXTENSIONS {'ON' if self.cxx_extensions else 'OFF'})"
            )
            self.write()

    def _write_variables(self) -> None:
        """Write variables."""
        if self.var_order:
            self.write("# Variables")
            for key in self.var_order:
                var = self.vars[key]
                self.write(str(var))
            self.write()

    def _write_global_settings(self) -> None:
        """Write global compiler/linker settings."""
        if self.include_dirs:
            self.write("# Global include directories")
            dirs = " ".join(self.include_dirs)
            self.write(f"include_directories({dirs})")
            self.write()

        if self.link_dirs:
            self.write("# Global link directories")
            dirs = " ".join(self.link_dirs)
            self.write(f"link_directories({dirs})")
            self.write()

        if self.cxxflags:
            self.write("# Global compile options")
            flags = " ".join(self.cxxflags)
            self.write(f"add_compile_options({flags})")
            self.write()

        if self.ldflags:
            self.write("# Global link options")
            flags = " ".join(self.ldflags)
            self.write(f"add_link_options({flags})")
            self.write()

    def _write_dependencies(self) -> None:
        """Write dependency finding."""
        if self.find_packages:
            self.write("# Dependencies")
            for dep in self.find_packages:
                self.write(
                    cmake_find_package(
                        dep["package"],
                        version=dep["version"],
                        required=dep["required"],
                        components=dep["components"],
                    )
                )
            self.write()

        if self.fetchcontent_deps:
            self.write("# FetchContent dependencies")
            self.write("include(FetchContent)")
            for dep in self.fetchcontent_deps:
                self.write()
                parts = [f"FetchContent_Declare({dep['name']}"]
                if dep["git_repository"]:
                    parts.append(f"    GIT_REPOSITORY {dep['git_repository']}")
                    if dep["git_tag"]:
                        parts.append(f"    GIT_TAG {dep['git_tag']}")
                elif dep["url"]:
                    parts.append(f"    URL {dep['url']}")
                self.write("\n".join(parts) + ")")

            names = " ".join(d["name"] for d in self.fetchcontent_deps)
            self.write()
            self.write(f"FetchContent_MakeAvailable({names})")
            self.write()

    def _write_libraries(self) -> None:
        """Write library targets."""
        if self.libraries:
            self.write("# Libraries")
            for name, config in self.libraries.items():
                sources = " ".join(config["sources"])
                self.write(
                    cmake_add_library(name, *config["sources"], lib_type=config["lib_type"])
                )

                if config["include_dirs"]:
                    self.write(
                        cmake_target_include_directories(
                            name, *config["include_dirs"], visibility="PUBLIC"
                        )
                    )

                if config["link_libraries"]:
                    self.write(
                        cmake_target_link_libraries(
                            name, *config["link_libraries"], visibility="PUBLIC"
                        )
                    )

                if config["compile_definitions"]:
                    self.write(
                        cmake_target_compile_definitions(
                            name, *config["compile_definitions"], visibility="PUBLIC"
                        )
                    )

                if config["compile_options"]:
                    self.write(
                        cmake_target_compile_options(
                            name, *config["compile_options"], visibility="PRIVATE"
                        )
                    )

                self.write()

    def _write_executables(self) -> None:
        """Write executable targets."""
        if self.executables:
            self.write("# Executables")
            for name, config in self.executables.items():
                self.write(cmake_add_executable(name, *config["sources"]))

                if config["include_dirs"]:
                    self.write(
                        cmake_target_include_directories(
                            name, *config["include_dirs"], visibility="PRIVATE"
                        )
                    )

                if config["link_libraries"]:
                    self.write(
                        cmake_target_link_libraries(
                            name, *config["link_libraries"], visibility="PRIVATE"
                        )
                    )

                if config["compile_definitions"]:
                    self.write(
                        cmake_target_compile_definitions(
                            name, *config["compile_definitions"], visibility="PRIVATE"
                        )
                    )

                if config["compile_options"]:
                    self.write(
                        cmake_target_compile_options(
                            name, *config["compile_options"], visibility="PRIVATE"
                        )
                    )

                self.write()

    def _write_install(self) -> None:
        """Write install rules."""
        if self.install_targets:
            self.write("# Install")
            targets = " ".join(self.install_targets)
            self.write(f"install(TARGETS {targets}")
            self.write("    RUNTIME DESTINATION bin")
            self.write("    LIBRARY DESTINATION lib")
            self.write("    ARCHIVE DESTINATION lib)")
            self.write()

    def _write_custom(self) -> None:
        """Write custom sections."""
        for section in self.custom_sections:
            self.write(section)
            self.write()

    def generate(self) -> None:
        """Generate the CMakeLists.txt file."""
        self._write_header()
        self._write_standards()
        self._write_variables()
        self._write_global_settings()
        self._write_dependencies()
        self._write_libraries()
        self._write_executables()
        self._write_install()
        self._write_custom()
        self.close()
