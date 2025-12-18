"""Project configuration for cross-generator build file generation.

Define a project once, generate both Makefile and CMakeLists.txt.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from buildgen.common.utils import PathLike


@dataclass
class TargetConfig:
    """Configuration for a build target (executable or library)."""

    name: str
    sources: list[str] = field(default_factory=list)
    target_type: str = "executable"  # executable, static, shared, object, interface
    include_dirs: list[str] = field(default_factory=list)
    link_libraries: list[str] = field(default_factory=list)
    compile_definitions: list[str] = field(default_factory=list)
    compile_options: list[str] = field(default_factory=list)
    link_options: list[str] = field(default_factory=list)
    install: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "TargetConfig":
        """Create TargetConfig from dictionary."""
        return cls(
            name=data["name"],
            sources=data.get("sources", []),
            target_type=data.get("type", "executable"),
            include_dirs=data.get("include_dirs", []),
            link_libraries=data.get("link_libraries", []),
            compile_definitions=data.get("compile_definitions", []),
            compile_options=data.get("compile_options", []),
            link_options=data.get("link_options", []),
            install=data.get("install", False),
        )


@dataclass
class DependencyConfig:
    """Configuration for an external dependency."""

    name: str
    version: Optional[str] = None
    required: bool = True
    components: list[str] = field(default_factory=list)
    # For FetchContent/git dependencies
    git_repository: Optional[str] = None
    git_tag: Optional[str] = None
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "DependencyConfig":
        """Create DependencyConfig from dictionary."""
        if isinstance(data, str):
            # Simple string format: "OpenSSL" or "Boost>=1.70"
            if ">=" in data:
                name, version = data.split(">=")
                return cls(name=name.strip(), version=version.strip())
            return cls(name=data)
        return cls(
            name=data["name"],
            version=data.get("version"),
            required=data.get("required", True),
            components=data.get("components", []),
            git_repository=data.get("git_repository"),
            git_tag=data.get("git_tag"),
            url=data.get("url"),
        )


@dataclass
class ProjectConfig:
    """Project configuration that can generate both Makefile and CMakeLists.txt."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    languages: list[str] = field(default_factory=lambda: ["CXX"])

    # Build settings
    cxx_standard: Optional[int] = None
    c_standard: Optional[int] = None

    # Compilers (primarily for Makefile)
    cc: str = "gcc"
    cxx: str = "g++"

    # Global settings
    include_dirs: list[str] = field(default_factory=list)
    link_dirs: list[str] = field(default_factory=list)
    compile_definitions: list[str] = field(default_factory=list)
    compile_options: list[str] = field(default_factory=list)
    link_options: list[str] = field(default_factory=list)

    # Targets
    targets: list[TargetConfig] = field(default_factory=list)

    # Dependencies
    dependencies: list[DependencyConfig] = field(default_factory=list)

    # Variables (key-value pairs)
    variables: dict[str, str] = field(default_factory=dict)

    # CMake-specific
    cmake_minimum_version: str = "3.16"

    # Install settings
    install_prefix: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """Create ProjectConfig from dictionary."""
        targets = [
            TargetConfig.from_dict(t) if isinstance(t, dict) else t
            for t in data.get("targets", [])
        ]
        dependencies = [
            DependencyConfig.from_dict(d) for d in data.get("dependencies", [])
        ]

        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            languages=data.get("languages", ["CXX"]),
            cxx_standard=data.get("cxx_standard"),
            c_standard=data.get("c_standard"),
            cc=data.get("cc", "gcc"),
            cxx=data.get("cxx", "g++"),
            include_dirs=data.get("include_dirs", []),
            link_dirs=data.get("link_dirs", []),
            compile_definitions=data.get("compile_definitions", []),
            compile_options=data.get("compile_options", []),
            link_options=data.get("link_options", []),
            targets=targets,
            dependencies=dependencies,
            variables=data.get("variables", {}),
            cmake_minimum_version=data.get("cmake_minimum_version", "3.16"),
            install_prefix=data.get("install_prefix"),
        )

    @classmethod
    def from_json(cls, path: PathLike) -> "ProjectConfig":
        """Load ProjectConfig from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, path: PathLike) -> "ProjectConfig":
        """Load ProjectConfig from YAML file.

        Requires pyyaml to be installed.
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "pyyaml is required for YAML support. Install with: pip install pyyaml"
            )

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: PathLike) -> "ProjectConfig":
        """Load ProjectConfig from file, detecting format by extension."""
        path = Path(path)
        ext = path.suffix.lower()

        if ext == ".json":
            return cls.from_json(path)
        elif ext in (".yaml", ".yml"):
            return cls.from_yaml(path)
        else:
            # Try JSON first, then YAML
            try:
                return cls.from_json(path)
            except json.JSONDecodeError:
                return cls.from_yaml(path)

    def to_dict(self) -> dict:
        """Convert ProjectConfig to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "languages": self.languages,
            "cxx_standard": self.cxx_standard,
            "c_standard": self.c_standard,
            "cc": self.cc,
            "cxx": self.cxx,
            "include_dirs": self.include_dirs,
            "link_dirs": self.link_dirs,
            "compile_definitions": self.compile_definitions,
            "compile_options": self.compile_options,
            "link_options": self.link_options,
            "targets": [
                {
                    "name": t.name,
                    "type": t.target_type,
                    "sources": t.sources,
                    "include_dirs": t.include_dirs,
                    "link_libraries": t.link_libraries,
                    "compile_definitions": t.compile_definitions,
                    "compile_options": t.compile_options,
                    "link_options": t.link_options,
                    "install": t.install,
                }
                for t in self.targets
            ],
            "dependencies": [
                {
                    "name": d.name,
                    "version": d.version,
                    "required": d.required,
                    "components": d.components,
                    "git_repository": d.git_repository,
                    "git_tag": d.git_tag,
                    "url": d.url,
                }
                for d in self.dependencies
            ],
            "variables": self.variables,
            "cmake_minimum_version": self.cmake_minimum_version,
            "install_prefix": self.install_prefix,
        }

    def to_json(self, path: PathLike, indent: int = 2) -> None:
        """Save ProjectConfig to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)

    def to_yaml(self, path: PathLike) -> None:
        """Save ProjectConfig to YAML file.

        Requires pyyaml to be installed.
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "pyyaml is required for YAML support. Install with: pip install pyyaml"
            )

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    def generate_makefile(self, output_path: PathLike = "Makefile") -> None:
        """Generate Makefile from project configuration."""
        from buildgen.makefile.generator import MakefileGenerator
        from buildgen.makefile.variables import Var

        gen = MakefileGenerator(output_path)
        gen.cxx = self.cxx

        # Variables
        for key, value in self.variables.items():
            gen.add_variable(key, value)

        # Global settings
        if self.include_dirs:
            gen.add_include_dirs(*self.include_dirs)
        if self.link_dirs:
            gen.add_link_dirs(*self.link_dirs)
        if self.compile_options:
            gen.add_cxxflags(*self.compile_options)
        if self.link_options:
            gen.add_ldflags(*self.link_options)

        # C++ standard
        if self.cxx_standard:
            gen.add_cxxflags(f"-std=c++{self.cxx_standard}")

        # Compile definitions
        for defn in self.compile_definitions:
            gen.add_cxxflags(f"-D{defn}")

        # Dependencies (as libraries to link)
        for dep in self.dependencies:
            if dep.name.lower() == "threads":
                gen.add_ldlibs("-lpthread")
            elif not dep.git_repository and not dep.url:
                # Assume system library
                gen.add_ldlibs(f"-l{dep.name.lower()}")

        # Targets
        all_targets = []
        clean_files = []
        phony_targets = ["all", "clean"]

        for target in self.targets:
            all_targets.append(target.name)

            # Object files
            objects = []
            for src in target.sources:
                obj = src.rsplit(".", 1)[0] + ".o"
                objects.append(obj)
                clean_files.append(obj)

            # Link command
            if target.target_type == "executable":
                link_libs = " ".join(
                    f"-l{lib}" if not lib.startswith("-") else lib
                    for lib in target.link_libraries
                )
                recipe = f"$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS) {link_libs}"
                gen.add_target(target.name, recipe, deps=objects)
                clean_files.append(target.name)
            elif target.target_type in ("static", "STATIC"):
                recipe = "$(AR) rcs $@ $^"
                lib_name = f"lib{target.name}.a"
                gen.add_target(lib_name, recipe, deps=objects)
                clean_files.append(lib_name)
                all_targets[-1] = lib_name
            elif target.target_type in ("shared", "SHARED"):
                recipe = "$(CXX) -shared -o $@ $^ $(LDFLAGS)"
                lib_name = f"lib{target.name}.so"
                gen.add_target(lib_name, recipe, deps=objects)
                clean_files.append(lib_name)
                all_targets[-1] = lib_name

        # Pattern rule for .o files
        gen.add_pattern_rule("%.o", "%.cpp", "$(CXX) $(CXXFLAGS) -c $< -o $@")

        # all target
        gen.add_target("all", deps=all_targets)
        gen.add_phony(*phony_targets)
        gen.add_clean(*clean_files)

        gen.generate()

    def generate_cmake(self, output_path: PathLike = "CMakeLists.txt") -> None:
        """Generate CMakeLists.txt from project configuration."""
        from buildgen.cmake.generator import CMakeListsGenerator

        gen = CMakeListsGenerator(output_path)

        # Project setup
        gen.set_cmake_version(self.cmake_minimum_version)
        gen.set_project(
            self.name,
            version=self.version,
            description=self.description,
            languages=self.languages,
        )

        # C++ standard
        if self.cxx_standard:
            gen.set_cxx_standard(self.cxx_standard)

        # Variables
        for key, value in self.variables.items():
            gen.add_variable(key, value)

        # Global settings
        if self.include_dirs:
            gen.add_include_dirs(*self.include_dirs)
        if self.link_dirs:
            gen.add_link_dirs(*self.link_dirs)
        if self.compile_options:
            gen.add_cxxflags(*self.compile_options)
        if self.link_options:
            gen.add_ldflags(*self.link_options)

        # Dependencies
        for dep in self.dependencies:
            if dep.git_repository:
                gen.add_fetchcontent(
                    dep.name,
                    git_repository=dep.git_repository,
                    git_tag=dep.git_tag,
                )
            elif dep.url:
                gen.add_fetchcontent(dep.name, url=dep.url)
            else:
                gen.add_find_package(
                    dep.name,
                    version=dep.version,
                    required=dep.required,
                    components=dep.components if dep.components else None,
                )

        # Targets
        install_targets = []
        for target in self.targets:
            # Compile definitions for this target
            definitions = self.compile_definitions + target.compile_definitions
            options = target.compile_options

            if target.target_type == "executable":
                gen.add_executable(
                    target.name,
                    target.sources,
                    include_dirs=target.include_dirs or None,
                    link_libraries=target.link_libraries or None,
                    compile_definitions=definitions or None,
                    compile_options=options or None,
                )
            else:
                lib_type = target.target_type.upper()
                if lib_type not in ("STATIC", "SHARED", "OBJECT", "INTERFACE"):
                    lib_type = "STATIC"
                gen.add_library(
                    target.name,
                    target.sources,
                    lib_type=lib_type,
                    include_dirs=target.include_dirs or None,
                    link_libraries=target.link_libraries or None,
                    compile_definitions=definitions or None,
                    compile_options=options or None,
                )

            if target.install:
                install_targets.append(target.name)

        # Install
        if install_targets:
            gen.add_install_target(*install_targets)

        gen.generate()

    def generate_all(
        self,
        makefile_path: PathLike = "Makefile",
        cmake_path: PathLike = "CMakeLists.txt",
    ) -> None:
        """Generate both Makefile and CMakeLists.txt."""
        self.generate_makefile(makefile_path)
        self.generate_cmake(cmake_path)


# Example schema for documentation
EXAMPLE_PROJECT_JSON = """{
    "name": "myproject",
    "version": "1.0.0",
    "description": "My awesome project",
    "languages": ["CXX"],
    "cxx_standard": 17,
    "cxx": "g++",
    "include_dirs": ["include", "src"],
    "compile_options": ["-Wall", "-Wextra"],
    "dependencies": [
        "Threads",
        {"name": "OpenSSL", "required": true},
        {
            "name": "fmt",
            "git_repository": "https://github.com/fmtlib/fmt.git",
            "git_tag": "10.1.1"
        }
    ],
    "targets": [
        {
            "name": "mylib",
            "type": "static",
            "sources": ["src/lib.cpp"],
            "include_dirs": ["include"],
            "install": true
        },
        {
            "name": "myapp",
            "type": "executable",
            "sources": ["src/main.cpp"],
            "link_libraries": ["mylib", "Threads::Threads", "OpenSSL::SSL"],
            "install": true
        }
    ],
    "variables": {
        "PROJECT_ROOT": "${CMAKE_CURRENT_SOURCE_DIR}"
    }
}"""

EXAMPLE_PROJECT_YAML = """name: myproject
version: 1.0.0
description: My awesome project
languages:
  - CXX
cxx_standard: 17
cxx: g++
include_dirs:
  - include
  - src
compile_options:
  - -Wall
  - -Wextra
dependencies:
  - Threads
  - name: OpenSSL
    required: true
  - name: fmt
    git_repository: https://github.com/fmtlib/fmt.git
    git_tag: "10.1.1"
targets:
  - name: mylib
    type: static
    sources:
      - src/lib.cpp
    include_dirs:
      - include
    install: true
  - name: myapp
    type: executable
    sources:
      - src/main.cpp
    link_libraries:
      - mylib
      - Threads::Threads
      - OpenSSL::SSL
    install: true
variables:
  PROJECT_ROOT: ${CMAKE_CURRENT_SOURCE_DIR}
"""
