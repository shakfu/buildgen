"""CMake builder class for configuring and building with CMake."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Union

from buildgen.common.utils import UniqueList, PathLike
from buildgen.common.base import BaseBuilder


def cmake_bool(value: bool) -> str:
    """Convert Python bool to CMake ON/OFF."""
    return "ON" if value else "OFF"


class CMakeBuilder(BaseBuilder):
    """Configure and build projects using CMake."""

    def __init__(
        self,
        source_dir: PathLike = ".",
        build_dir: PathLike = "build",
        target: Optional[str] = None,
        strict: bool = False,
    ):
        """Initialize CMakeBuilder.

        Args:
            source_dir: Directory containing CMakeLists.txt
            build_dir: Build output directory
            target: Optional target name (for BaseBuilder compatibility)
            strict: If True, raise errors on duplicate entries
        """
        super().__init__(target or str(build_dir), strict)
        self.source_dir = Path(source_dir)
        self.build_dir = Path(build_dir)

        # CMake options
        self.generator: Optional[str] = None
        self.cmake_options: dict[str, Union[str, bool, int]] = {}
        self.cache_scripts: UniqueList = UniqueList()
        self.build_config: str = "Release"
        self.parallel_jobs: Optional[int] = None
        self.build_targets: UniqueList = UniqueList()
        self.install_prefix: Optional[str] = None

        # Environment
        self.env_vars: dict[str, str] = {}

    def set_generator(self, generator: str) -> None:
        """Set CMake generator (e.g., 'Ninja', 'Unix Makefiles')."""
        self.generator = generator

    def set_option(self, name: str, value: Union[str, bool, int]) -> None:
        """Set a CMake option (-D)."""
        self.cmake_options[name] = value

    def set_build_type(self, build_type: str) -> None:
        """Set CMAKE_BUILD_TYPE (Debug, Release, RelWithDebInfo, MinSizeRel)."""
        self.cmake_options["CMAKE_BUILD_TYPE"] = build_type
        self.build_config = build_type

    def set_install_prefix(self, prefix: str) -> None:
        """Set CMAKE_INSTALL_PREFIX."""
        self.cmake_options["CMAKE_INSTALL_PREFIX"] = prefix
        self.install_prefix = prefix

    def add_cache_script(self, script_path: str) -> None:
        """Add a cache initialization script (-C)."""
        self.cache_scripts.add(script_path)

    def add_build_target(self, target: str) -> None:
        """Add a specific target to build."""
        self.build_targets.add(target)

    def set_parallel_jobs(self, jobs: int) -> None:
        """Set number of parallel build jobs."""
        self.parallel_jobs = jobs

    def set_env(self, name: str, value: str) -> None:
        """Set environment variable for CMake commands."""
        self.env_vars[name] = value

    # BaseBuilder interface implementation
    def add_include_dirs(self, *entries) -> None:
        """Add include directories via CMAKE_INCLUDE_PATH."""
        current = self.cmake_options.get("CMAKE_INCLUDE_PATH", "")
        new_dirs = ";".join(entries)
        if current:
            self.cmake_options["CMAKE_INCLUDE_PATH"] = f"{current};{new_dirs}"
        else:
            self.cmake_options["CMAKE_INCLUDE_PATH"] = new_dirs

    def add_link_dirs(self, *entries) -> None:
        """Add link directories via CMAKE_LIBRARY_PATH."""
        current = self.cmake_options.get("CMAKE_LIBRARY_PATH", "")
        new_dirs = ";".join(entries)
        if current:
            self.cmake_options["CMAKE_LIBRARY_PATH"] = f"{current};{new_dirs}"
        else:
            self.cmake_options["CMAKE_LIBRARY_PATH"] = new_dirs

    def add_cxxflags(self, *entries) -> None:
        """Add C++ flags via CMAKE_CXX_FLAGS."""
        current = self.cmake_options.get("CMAKE_CXX_FLAGS", "")
        new_flags = " ".join(entries)
        if current:
            self.cmake_options["CMAKE_CXX_FLAGS"] = f"{current} {new_flags}"
        else:
            self.cmake_options["CMAKE_CXX_FLAGS"] = new_flags

    def add_cflags(self, *entries) -> None:
        """Add C flags via CMAKE_C_FLAGS."""
        current = self.cmake_options.get("CMAKE_C_FLAGS", "")
        new_flags = " ".join(entries)
        if current:
            self.cmake_options["CMAKE_C_FLAGS"] = f"{current} {new_flags}"
        else:
            self.cmake_options["CMAKE_C_FLAGS"] = new_flags

    def add_ldflags(self, *entries) -> None:
        """Add linker flags via CMAKE_EXE_LINKER_FLAGS."""
        current = self.cmake_options.get("CMAKE_EXE_LINKER_FLAGS", "")
        new_flags = " ".join(entries)
        if current:
            self.cmake_options["CMAKE_EXE_LINKER_FLAGS"] = f"{current} {new_flags}"
        else:
            self.cmake_options["CMAKE_EXE_LINKER_FLAGS"] = new_flags

    def _get_env(self) -> dict:
        """Get environment for subprocess calls."""
        env = os.environ.copy()
        env.update(self.env_vars)
        return env

    def _format_cmake_value(self, value: Union[str, bool, int]) -> str:
        """Format a value for CMake command line."""
        if isinstance(value, bool):
            return cmake_bool(value)
        return str(value)

    def get_configure_cmd(self) -> list[str]:
        """Get the cmake configure command."""
        cmd = ["cmake"]

        # Source and build directories
        cmd.extend(["-S", str(self.source_dir), "-B", str(self.build_dir)])

        # Generator
        if self.generator:
            cmd.extend(["-G", self.generator])

        # Cache scripts
        for script in self.cache_scripts:
            cmd.extend(["-C", script])

        # Options
        for key, value in self.cmake_options.items():
            cmd.append(f"-D{key}={self._format_cmake_value(value)}")

        return cmd

    def get_build_cmd(self) -> list[str]:
        """Get the cmake --build command."""
        cmd = ["cmake", "--build", str(self.build_dir)]

        # Config (for multi-config generators)
        cmd.extend(["--config", self.build_config])

        # Parallel jobs
        if self.parallel_jobs:
            cmd.extend(["--parallel", str(self.parallel_jobs)])

        # Specific targets
        for target in self.build_targets:
            cmd.extend(["--target", target])

        return cmd

    def get_install_cmd(self) -> list[str]:
        """Get the cmake --install command."""
        cmd = ["cmake", "--install", str(self.build_dir)]

        if self.install_prefix:
            cmd.extend(["--prefix", self.install_prefix])

        return cmd

    def configure(self, dry_run: bool = False) -> None:
        """Run CMake configuration step."""
        cmd = self.get_configure_cmd()
        cmd_str = " ".join(cmd)

        if dry_run:
            print(cmd_str)
            return

        print(f"Configuring: {cmd_str}")
        self.build_dir.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(cmd, env=self._get_env())

    def build(self, dry_run: bool = False) -> None:
        """Run CMake build step."""
        cmd = self.get_build_cmd()
        cmd_str = " ".join(cmd)

        if dry_run:
            print(cmd_str)
            return

        print(f"Building: {cmd_str}")
        subprocess.check_call(cmd, env=self._get_env())

    def install(self, dry_run: bool = False) -> None:
        """Run CMake install step."""
        cmd = self.get_install_cmd()
        cmd_str = " ".join(cmd)

        if dry_run:
            print(cmd_str)
            return

        print(f"Installing: {cmd_str}")
        subprocess.check_call(cmd, env=self._get_env())

    def configure_and_build(self, dry_run: bool = False) -> None:
        """Run configure followed by build."""
        self.configure(dry_run=dry_run)
        if not dry_run:
            self.build(dry_run=dry_run)

    def full_build(self, dry_run: bool = False) -> None:
        """Run configure, build, and install."""
        self.configure(dry_run=dry_run)
        if not dry_run:
            self.build(dry_run=dry_run)
            if self.install_prefix:
                self.install(dry_run=dry_run)

    def clean(self) -> None:
        """Clean build directory."""
        if self.build_dir.exists():
            import shutil
            shutil.rmtree(self.build_dir)
            print(f"Removed: {self.build_dir}")
