"""CMake function helpers for generating CMake commands.

Usage:
    from buildgen.cmake.functions import Cm

    Cm.minimum_required("3.16")
    Cm.project("myapp", version="1.0.0")
    Cm.add_executable("myapp", "main.cpp", "utils.cpp")
"""

from typing import Optional, Union


class Cm:
    """CMake command generators.

    Generates CMake command syntax as strings.
    All methods are static - no instance needed.

    Usage:
        from buildgen.cmake.functions import Cm

        Cm.minimum_required("3.16")
        Cm.add_executable("myapp", "main.cpp")
        Cm.target_link_libraries("myapp", "pthread")
    """

    # -------------------------------------------------------------------------
    # Project commands

    @staticmethod
    def minimum_required(version: str, fatal_error: bool = True) -> str:
        """cmake_minimum_required(VERSION ...) command."""
        if fatal_error:
            return f"cmake_minimum_required(VERSION {version} FATAL_ERROR)"
        return f"cmake_minimum_required(VERSION {version})"

    @staticmethod
    def project(
        name: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        homepage_url: Optional[str] = None,
        languages: Optional[list[str]] = None,
    ) -> str:
        """project() command."""
        parts = [f"project({name}"]
        if version:
            parts.append(f"VERSION {version}")
        if description:
            parts.append(f'DESCRIPTION "{description}"')
        if homepage_url:
            parts.append(f'HOMEPAGE_URL "{homepage_url}"')
        if languages:
            parts.append("LANGUAGES " + " ".join(languages))
        return " ".join(parts) + ")"

    # -------------------------------------------------------------------------
    # Target commands

    @staticmethod
    def add_executable(
        name: str,
        *sources: str,
        win32: bool = False,
        macosx_bundle: bool = False,
        exclude_from_all: bool = False,
    ) -> str:
        """add_executable() command."""
        parts = [f"add_executable({name}"]
        if win32:
            parts.append("WIN32")
        if macosx_bundle:
            parts.append("MACOSX_BUNDLE")
        if exclude_from_all:
            parts.append("EXCLUDE_FROM_ALL")
        parts.extend(sources)
        return " ".join(parts) + ")"

    @staticmethod
    def add_library(
        name: str,
        *sources: str,
        lib_type: Optional[str] = None,
        exclude_from_all: bool = False,
    ) -> str:
        """add_library() command.

        lib_type: STATIC, SHARED, MODULE, OBJECT, INTERFACE, IMPORTED, ALIAS
        """
        parts = [f"add_library({name}"]
        if lib_type:
            parts.append(lib_type)
        if exclude_from_all:
            parts.append("EXCLUDE_FROM_ALL")
        parts.extend(sources)
        return " ".join(parts) + ")"

    @staticmethod
    def add_custom_target(
        name: str,
        command: Optional[str] = None,
        depends: Optional[list[str]] = None,
        all_target: bool = False,
        comment: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> str:
        """add_custom_target() command."""
        parts = [f"add_custom_target({name}"]
        if all_target:
            parts.append("ALL")
        if command:
            parts.append(f"COMMAND {command}")
        if depends:
            parts.append("DEPENDS " + " ".join(depends))
        if comment:
            parts.append(f'COMMENT "{comment}"')
        if working_directory:
            parts.append(f"WORKING_DIRECTORY {working_directory}")
        return " ".join(parts) + ")"

    @staticmethod
    def add_custom_command(
        output: Union[str, list[str]],
        command: str,
        depends: Optional[list[str]] = None,
        comment: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> str:
        """add_custom_command() (output form)."""
        if isinstance(output, list):
            output_str = " ".join(output)
        else:
            output_str = output
        parts = [f"add_custom_command(OUTPUT {output_str}"]
        parts.append(f"COMMAND {command}")
        if depends:
            parts.append("DEPENDS " + " ".join(depends))
        if comment:
            parts.append(f'COMMENT "{comment}"')
        if working_directory:
            parts.append(f"WORKING_DIRECTORY {working_directory}")
        return "\n    ".join(parts) + ")"

    # -------------------------------------------------------------------------
    # Target property commands

    @staticmethod
    def target_link_libraries(
        target: str,
        *libraries: str,
        visibility: str = "PUBLIC",
    ) -> str:
        """target_link_libraries() command."""
        libs = " ".join(libraries)
        return f"target_link_libraries({target} {visibility} {libs})"

    @staticmethod
    def target_include_directories(
        target: str,
        *directories: str,
        visibility: str = "PUBLIC",
        system: bool = False,
    ) -> str:
        """target_include_directories() command."""
        parts = [f"target_include_directories({target}"]
        if system:
            parts.append("SYSTEM")
        parts.append(visibility)
        parts.extend(directories)
        return " ".join(parts) + ")"

    @staticmethod
    def target_compile_definitions(
        target: str,
        *definitions: str,
        visibility: str = "PUBLIC",
    ) -> str:
        """target_compile_definitions() command."""
        defs = " ".join(definitions)
        return f"target_compile_definitions({target} {visibility} {defs})"

    @staticmethod
    def target_compile_options(
        target: str,
        *options: str,
        visibility: str = "PUBLIC",
    ) -> str:
        """target_compile_options() command."""
        opts = " ".join(options)
        return f"target_compile_options({target} {visibility} {opts})"

    @staticmethod
    def target_compile_features(
        target: str,
        *features: str,
        visibility: str = "PUBLIC",
    ) -> str:
        """target_compile_features() command."""
        feats = " ".join(features)
        return f"target_compile_features({target} {visibility} {feats})"

    @staticmethod
    def target_sources(
        target: str,
        *sources: str,
        visibility: str = "PRIVATE",
    ) -> str:
        """target_sources() command."""
        srcs = " ".join(sources)
        return f"target_sources({target} {visibility} {srcs})"

    @staticmethod
    def set_target_properties(
        target: str,
        **properties: str,
    ) -> str:
        """set_target_properties() command."""
        props = " ".join(f"{k} {v}" for k, v in properties.items())
        return f"set_target_properties({target} PROPERTIES {props})"

    # -------------------------------------------------------------------------
    # Dependency commands

    @staticmethod
    def find_package(
        package: str,
        version: Optional[str] = None,
        required: bool = True,
        components: Optional[list[str]] = None,
        config: bool = False,
        quiet: bool = False,
    ) -> str:
        """find_package() command."""
        parts = [f"find_package({package}"]
        if version:
            parts.append(version)
        if components:
            parts.append("COMPONENTS " + " ".join(components))
        if config:
            parts.append("CONFIG")
        if required:
            parts.append("REQUIRED")
        if quiet:
            parts.append("QUIET")
        return " ".join(parts) + ")"

    @staticmethod
    def find_library(
        var: str,
        name: str,
        paths: Optional[list[str]] = None,
        hints: Optional[list[str]] = None,
        required: bool = False,
    ) -> str:
        """find_library() command."""
        parts = [f"find_library({var} {name}"]
        if hints:
            parts.append("HINTS " + " ".join(hints))
        if paths:
            parts.append("PATHS " + " ".join(paths))
        if required:
            parts.append("REQUIRED")
        return " ".join(parts) + ")"

    @staticmethod
    def find_path(
        var: str,
        name: str,
        paths: Optional[list[str]] = None,
        hints: Optional[list[str]] = None,
        required: bool = False,
    ) -> str:
        """find_path() command."""
        parts = [f"find_path({var} {name}"]
        if hints:
            parts.append("HINTS " + " ".join(hints))
        if paths:
            parts.append("PATHS " + " ".join(paths))
        if required:
            parts.append("REQUIRED")
        return " ".join(parts) + ")"

    @staticmethod
    def pkg_check_modules(
        prefix: str,
        *modules: str,
        required: bool = True,
        imported_target: bool = True,
    ) -> str:
        """pkg_check_modules() command (requires find_package(PkgConfig))."""
        parts = [f"pkg_check_modules({prefix}"]
        if required:
            parts.append("REQUIRED")
        if imported_target:
            parts.append("IMPORTED_TARGET")
        parts.extend(modules)
        return " ".join(parts) + ")"

    # -------------------------------------------------------------------------
    # FetchContent commands

    @staticmethod
    def fetchcontent_declare(
        name: str,
        git_repository: Optional[str] = None,
        git_tag: Optional[str] = None,
        url: Optional[str] = None,
        url_hash: Optional[str] = None,
    ) -> str:
        """FetchContent_Declare() command."""
        parts = [f"FetchContent_Declare({name}"]
        if git_repository:
            parts.append(f"GIT_REPOSITORY {git_repository}")
            if git_tag:
                parts.append(f"GIT_TAG {git_tag}")
        elif url:
            parts.append(f"URL {url}")
            if url_hash:
                parts.append(f"URL_HASH {url_hash}")
        return "\n    ".join(parts) + ")"

    @staticmethod
    def fetchcontent_makeavailable(*names: str) -> str:
        """FetchContent_MakeAvailable() command."""
        return f"FetchContent_MakeAvailable({' '.join(names)})"

    # -------------------------------------------------------------------------
    # Control flow

    @staticmethod
    def if_(condition: str, then_block: str, else_block: Optional[str] = None) -> str:
        """if/else/endif block."""
        result = f"if({condition})\n    {then_block}"
        if else_block:
            result += f"\nelse()\n    {else_block}"
        result += "\nendif()"
        return result

    @staticmethod
    def foreach(var: str, items: str, body: str) -> str:
        """foreach loop."""
        return f"foreach({var} {items})\n    {body}\nendforeach()"

    @staticmethod
    def function(name: str, args: list[str], body: str) -> str:
        """function definition."""
        args_str = " ".join(args)
        return f"function({name} {args_str})\n    {body}\nendfunction()"

    @staticmethod
    def macro(name: str, args: list[str], body: str) -> str:
        """macro definition."""
        args_str = " ".join(args)
        return f"macro({name} {args_str})\n    {body}\nendmacro()"

    # -------------------------------------------------------------------------
    # File and directory commands

    @staticmethod
    def include(file: str, optional: bool = False) -> str:
        """include() command."""
        if optional:
            return f"include({file} OPTIONAL)"
        return f"include({file})"

    @staticmethod
    def add_subdirectory(
        source_dir: str,
        binary_dir: Optional[str] = None,
        exclude_from_all: bool = False,
    ) -> str:
        """add_subdirectory() command."""
        parts = [f"add_subdirectory({source_dir}"]
        if binary_dir:
            parts.append(binary_dir)
        if exclude_from_all:
            parts.append("EXCLUDE_FROM_ALL")
        return " ".join(parts) + ")"

    @staticmethod
    def file_glob(
        var: str,
        *patterns: str,
        configure_depends: bool = True,
    ) -> str:
        """file(GLOB ...) command."""
        parts = [f"file(GLOB {var}"]
        if configure_depends:
            parts.append("CONFIGURE_DEPENDS")
        parts.extend(patterns)
        return " ".join(parts) + ")"

    @staticmethod
    def configure_file(
        input_file: str,
        output_file: str,
        at_only: bool = False,
        copyonly: bool = False,
    ) -> str:
        """configure_file() command."""
        parts = [f"configure_file({input_file} {output_file}"]
        if at_only:
            parts.append("@ONLY")
        if copyonly:
            parts.append("COPYONLY")
        return " ".join(parts) + ")"

    # -------------------------------------------------------------------------
    # Install commands

    @staticmethod
    def install_targets(
        *targets: str,
        destination: Optional[str] = None,
        runtime_destination: Optional[str] = None,
        library_destination: Optional[str] = None,
        archive_destination: Optional[str] = None,
    ) -> str:
        """install(TARGETS ...) command."""
        parts = [f"install(TARGETS {' '.join(targets)}"]
        if destination:
            parts.append(f"DESTINATION {destination}")
        else:
            if runtime_destination:
                parts.append(f"RUNTIME DESTINATION {runtime_destination}")
            if library_destination:
                parts.append(f"LIBRARY DESTINATION {library_destination}")
            if archive_destination:
                parts.append(f"ARCHIVE DESTINATION {archive_destination}")
        return "\n    ".join(parts) + ")"

    @staticmethod
    def install_files(
        *files: str,
        destination: str,
        permissions: Optional[list[str]] = None,
    ) -> str:
        """install(FILES ...) command."""
        parts = [f"install(FILES {' '.join(files)}"]
        parts.append(f"DESTINATION {destination}")
        if permissions:
            parts.append("PERMISSIONS " + " ".join(permissions))
        return "\n    ".join(parts) + ")"

    @staticmethod
    def install_directory(
        directory: str,
        destination: str,
        pattern: Optional[str] = None,
    ) -> str:
        """install(DIRECTORY ...) command."""
        parts = [f"install(DIRECTORY {directory}"]
        parts.append(f"DESTINATION {destination}")
        if pattern:
            parts.append(f"FILES_MATCHING PATTERN {pattern}")
        return "\n    ".join(parts) + ")"

    # -------------------------------------------------------------------------
    # Message and output commands

    @staticmethod
    def message(
        message: str,
        mode: str = "STATUS",
    ) -> str:
        """message() command.

        mode: STATUS, WARNING, AUTHOR_WARNING, SEND_ERROR, FATAL_ERROR, DEPRECATION
        """
        return f'message({mode} "{message}")'

    # -------------------------------------------------------------------------
    # Generator expressions

    @staticmethod
    def genex_target_file(target: str) -> str:
        """$<TARGET_FILE:target> expression."""
        return f"$<TARGET_FILE:{target}>"

    @staticmethod
    def genex_target_property(target: str, prop: str) -> str:
        """$<TARGET_PROPERTY:target,prop> expression."""
        return f"$<TARGET_PROPERTY:{target},{prop}>"

    @staticmethod
    def genex_build_interface(path: str) -> str:
        """$<BUILD_INTERFACE:path> expression."""
        return f"$<BUILD_INTERFACE:{path}>"

    @staticmethod
    def genex_install_interface(path: str) -> str:
        """$<INSTALL_INTERFACE:path> expression."""
        return f"$<INSTALL_INTERFACE:{path}>"

    @staticmethod
    def genex_config(config: str, true_val: str, false_val: str = "") -> str:
        """$<IF:$<CONFIG:config>,true_val,false_val> expression."""
        if false_val:
            return f"$<IF:$<CONFIG:{config}>,{true_val},{false_val}>"
        return f"$<$<CONFIG:{config}>:{true_val}>"

    @staticmethod
    def genex_platform(platform: str, true_val: str) -> str:
        """$<$<PLATFORM_ID:platform>:true_val> expression."""
        return f"$<$<PLATFORM_ID:{platform}>:{true_val}>"

    @staticmethod
    def genex_compiler(compiler: str, true_val: str) -> str:
        """$<$<CXX_COMPILER_ID:compiler>:true_val> expression."""
        return f"$<$<CXX_COMPILER_ID:{compiler}>:{true_val}>"
