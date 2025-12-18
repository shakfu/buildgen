"""CMake function helpers for generating CMake commands."""

from typing import Optional, Union


# -----------------------------------------------------------------------------
# Project commands


def cmake_minimum_required(version: str, fatal_error: bool = True) -> str:
    """Generate cmake_minimum_required command."""
    if fatal_error:
        return f"cmake_minimum_required(VERSION {version} FATAL_ERROR)"
    return f"cmake_minimum_required(VERSION {version})"


def cmake_project(
    name: str,
    version: Optional[str] = None,
    description: Optional[str] = None,
    homepage_url: Optional[str] = None,
    languages: Optional[list[str]] = None,
) -> str:
    """Generate project() command."""
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


# -----------------------------------------------------------------------------
# Target commands


def cmake_add_executable(
    name: str,
    *sources: str,
    win32: bool = False,
    macosx_bundle: bool = False,
    exclude_from_all: bool = False,
) -> str:
    """Generate add_executable command."""
    parts = [f"add_executable({name}"]
    if win32:
        parts.append("WIN32")
    if macosx_bundle:
        parts.append("MACOSX_BUNDLE")
    if exclude_from_all:
        parts.append("EXCLUDE_FROM_ALL")
    parts.extend(sources)
    return " ".join(parts) + ")"


def cmake_add_library(
    name: str,
    *sources: str,
    lib_type: Optional[str] = None,
    exclude_from_all: bool = False,
) -> str:
    """Generate add_library command.

    Args:
        name: Library name
        sources: Source files
        lib_type: One of STATIC, SHARED, MODULE, OBJECT, INTERFACE, IMPORTED, ALIAS
        exclude_from_all: Exclude from default build
    """
    parts = [f"add_library({name}"]
    if lib_type:
        parts.append(lib_type)
    if exclude_from_all:
        parts.append("EXCLUDE_FROM_ALL")
    parts.extend(sources)
    return " ".join(parts) + ")"


def cmake_add_custom_target(
    name: str,
    command: Optional[str] = None,
    depends: Optional[list[str]] = None,
    all_target: bool = False,
    comment: Optional[str] = None,
    working_directory: Optional[str] = None,
) -> str:
    """Generate add_custom_target command."""
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


def cmake_add_custom_command(
    output: Union[str, list[str]],
    command: str,
    depends: Optional[list[str]] = None,
    comment: Optional[str] = None,
    working_directory: Optional[str] = None,
) -> str:
    """Generate add_custom_command (output form)."""
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


# -----------------------------------------------------------------------------
# Target property commands


def cmake_target_link_libraries(
    target: str,
    *libraries: str,
    visibility: str = "PUBLIC",
) -> str:
    """Generate target_link_libraries command.

    Args:
        target: Target name
        libraries: Libraries to link
        visibility: PUBLIC, PRIVATE, or INTERFACE
    """
    libs = " ".join(libraries)
    return f"target_link_libraries({target} {visibility} {libs})"


def cmake_target_include_directories(
    target: str,
    *directories: str,
    visibility: str = "PUBLIC",
    system: bool = False,
) -> str:
    """Generate target_include_directories command."""
    parts = [f"target_include_directories({target}"]
    if system:
        parts.append("SYSTEM")
    parts.append(visibility)
    parts.extend(directories)
    return " ".join(parts) + ")"


def cmake_target_compile_definitions(
    target: str,
    *definitions: str,
    visibility: str = "PUBLIC",
) -> str:
    """Generate target_compile_definitions command."""
    defs = " ".join(definitions)
    return f"target_compile_definitions({target} {visibility} {defs})"


def cmake_target_compile_options(
    target: str,
    *options: str,
    visibility: str = "PUBLIC",
) -> str:
    """Generate target_compile_options command."""
    opts = " ".join(options)
    return f"target_compile_options({target} {visibility} {opts})"


def cmake_target_compile_features(
    target: str,
    *features: str,
    visibility: str = "PUBLIC",
) -> str:
    """Generate target_compile_features command."""
    feats = " ".join(features)
    return f"target_compile_features({target} {visibility} {feats})"


def cmake_target_sources(
    target: str,
    *sources: str,
    visibility: str = "PRIVATE",
) -> str:
    """Generate target_sources command."""
    srcs = " ".join(sources)
    return f"target_sources({target} {visibility} {srcs})"


def cmake_set_target_properties(
    target: str,
    **properties: str,
) -> str:
    """Generate set_target_properties command."""
    props = " ".join(f"{k} {v}" for k, v in properties.items())
    return f"set_target_properties({target} PROPERTIES {props})"


# -----------------------------------------------------------------------------
# Dependency commands


def cmake_find_package(
    package: str,
    version: Optional[str] = None,
    required: bool = True,
    components: Optional[list[str]] = None,
    config: bool = False,
    quiet: bool = False,
) -> str:
    """Generate find_package command."""
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


def cmake_find_library(
    var: str,
    name: str,
    paths: Optional[list[str]] = None,
    hints: Optional[list[str]] = None,
    required: bool = False,
) -> str:
    """Generate find_library command."""
    parts = [f"find_library({var} {name}"]
    if hints:
        parts.append("HINTS " + " ".join(hints))
    if paths:
        parts.append("PATHS " + " ".join(paths))
    if required:
        parts.append("REQUIRED")
    return " ".join(parts) + ")"


def cmake_find_path(
    var: str,
    name: str,
    paths: Optional[list[str]] = None,
    hints: Optional[list[str]] = None,
    required: bool = False,
) -> str:
    """Generate find_path command."""
    parts = [f"find_path({var} {name}"]
    if hints:
        parts.append("HINTS " + " ".join(hints))
    if paths:
        parts.append("PATHS " + " ".join(paths))
    if required:
        parts.append("REQUIRED")
    return " ".join(parts) + ")"


def cmake_pkg_check_modules(
    prefix: str,
    *modules: str,
    required: bool = True,
    imported_target: bool = True,
) -> str:
    """Generate pkg_check_modules command (requires find_package(PkgConfig))."""
    parts = [f"pkg_check_modules({prefix}"]
    if required:
        parts.append("REQUIRED")
    if imported_target:
        parts.append("IMPORTED_TARGET")
    parts.extend(modules)
    return " ".join(parts) + ")"


# -----------------------------------------------------------------------------
# FetchContent commands


def cmake_fetchcontent_declare(
    name: str,
    git_repository: Optional[str] = None,
    git_tag: Optional[str] = None,
    url: Optional[str] = None,
    url_hash: Optional[str] = None,
) -> str:
    """Generate FetchContent_Declare command."""
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


def cmake_fetchcontent_makeavailable(*names: str) -> str:
    """Generate FetchContent_MakeAvailable command."""
    return f"FetchContent_MakeAvailable({' '.join(names)})"


# -----------------------------------------------------------------------------
# Control flow


def cmake_if(condition: str, then_block: str, else_block: Optional[str] = None) -> str:
    """Generate if/else/endif block."""
    result = f"if({condition})\n    {then_block}"
    if else_block:
        result += f"\nelse()\n    {else_block}"
    result += "\nendif()"
    return result


def cmake_foreach(var: str, items: str, body: str) -> str:
    """Generate foreach loop."""
    return f"foreach({var} {items})\n    {body}\nendforeach()"


def cmake_function(name: str, args: list[str], body: str) -> str:
    """Generate function definition."""
    args_str = " ".join(args)
    return f"function({name} {args_str})\n    {body}\nendfunction()"


def cmake_macro(name: str, args: list[str], body: str) -> str:
    """Generate macro definition."""
    args_str = " ".join(args)
    return f"macro({name} {args_str})\n    {body}\nendmacro()"


# -----------------------------------------------------------------------------
# File and directory commands


def cmake_include(file: str, optional: bool = False) -> str:
    """Generate include command."""
    if optional:
        return f"include({file} OPTIONAL)"
    return f"include({file})"


def cmake_add_subdirectory(
    source_dir: str,
    binary_dir: Optional[str] = None,
    exclude_from_all: bool = False,
) -> str:
    """Generate add_subdirectory command."""
    parts = [f"add_subdirectory({source_dir}"]
    if binary_dir:
        parts.append(binary_dir)
    if exclude_from_all:
        parts.append("EXCLUDE_FROM_ALL")
    return " ".join(parts) + ")"


def cmake_file_glob(
    var: str,
    *patterns: str,
    configure_depends: bool = True,
) -> str:
    """Generate file(GLOB ...) command."""
    parts = [f"file(GLOB {var}"]
    if configure_depends:
        parts.append("CONFIGURE_DEPENDS")
    parts.extend(patterns)
    return " ".join(parts) + ")"


def cmake_configure_file(
    input_file: str,
    output_file: str,
    at_only: bool = False,
    copyonly: bool = False,
) -> str:
    """Generate configure_file command."""
    parts = [f"configure_file({input_file} {output_file}"]
    if at_only:
        parts.append("@ONLY")
    if copyonly:
        parts.append("COPYONLY")
    return " ".join(parts) + ")"


# -----------------------------------------------------------------------------
# Install commands


def cmake_install_targets(
    *targets: str,
    destination: Optional[str] = None,
    runtime_destination: Optional[str] = None,
    library_destination: Optional[str] = None,
    archive_destination: Optional[str] = None,
) -> str:
    """Generate install(TARGETS ...) command."""
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


def cmake_install_files(
    *files: str,
    destination: str,
    permissions: Optional[list[str]] = None,
) -> str:
    """Generate install(FILES ...) command."""
    parts = [f"install(FILES {' '.join(files)}"]
    parts.append(f"DESTINATION {destination}")
    if permissions:
        parts.append("PERMISSIONS " + " ".join(permissions))
    return "\n    ".join(parts) + ")"


def cmake_install_directory(
    directory: str,
    destination: str,
    pattern: Optional[str] = None,
) -> str:
    """Generate install(DIRECTORY ...) command."""
    parts = [f"install(DIRECTORY {directory}"]
    parts.append(f"DESTINATION {destination}")
    if pattern:
        parts.append(f"FILES_MATCHING PATTERN {pattern}")
    return "\n    ".join(parts) + ")"


# -----------------------------------------------------------------------------
# Message and output commands


def cmake_message(
    message: str,
    mode: str = "STATUS",
) -> str:
    """Generate message command.

    Args:
        message: Message text
        mode: One of STATUS, WARNING, AUTHOR_WARNING, SEND_ERROR, FATAL_ERROR, DEPRECATION
    """
    return f'message({mode} "{message}")'


# -----------------------------------------------------------------------------
# Generator expressions


def cmake_genex_target_file(target: str) -> str:
    """Generate $<TARGET_FILE:target> expression."""
    return f"$<TARGET_FILE:{target}>"


def cmake_genex_target_property(target: str, prop: str) -> str:
    """Generate $<TARGET_PROPERTY:target,prop> expression."""
    return f"$<TARGET_PROPERTY:{target},{prop}>"


def cmake_genex_build_interface(path: str) -> str:
    """Generate $<BUILD_INTERFACE:path> expression."""
    return f"$<BUILD_INTERFACE:{path}>"


def cmake_genex_install_interface(path: str) -> str:
    """Generate $<INSTALL_INTERFACE:path> expression."""
    return f"$<INSTALL_INTERFACE:{path}>"


def cmake_genex_config(config: str, true_val: str, false_val: str = "") -> str:
    """Generate $<IF:$<CONFIG:config>,true_val,false_val> expression."""
    if false_val:
        return f"$<IF:$<CONFIG:{config}>,{true_val},{false_val}>"
    return f"$<$<CONFIG:{config}>:{true_val}>"


def cmake_genex_platform(platform: str, true_val: str) -> str:
    """Generate $<$<PLATFORM_ID:platform>:true_val> expression."""
    return f"$<$<PLATFORM_ID:{platform}>:{true_val}>"


def cmake_genex_compiler(compiler: str, true_val: str) -> str:
    """Generate $<$<CXX_COMPILER_ID:compiler>:true_val> expression."""
    return f"$<$<CXX_COMPILER_ID:{compiler}>:{true_val}>"
