# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.3.0]

Single place to update tools and dependencies (with update to latest).

### Added

- **`common/versions.py`** - one registry for every pinned version: PyPI floors, GitHub Action refs, CMake ranges, language standards, Python versions, FetchContent tags. Templates read it instead of holding literals, so a bump touches one file. `deps.DEFAULT_VERSIONS` and `BUILD_SYSTEM_PACKAGES` alias into it. Resolution order is unchanged: a `[deps]` pin beats a PyPI lookup, which beats the registry floor.

- **Drift guards** in `tests/test_versions.py`. They fail when a registry value appears literally in a template, and when buildgen's own dev floors diverge from the registry.

### Changed

- **buildgen's build backend is `uv_build` again**, pinned `uv_build>=0.12.6,<0.13`. The 0.2.0 note below is wrong on the reason for leaving. uv-build is a separate distribution whose documented pin is a next-minor cap you bump, not a lock to the installed uv. Wheel contents are unchanged.

- **`py/nodeps` generates a `uv_build` project** instead of hatchling. The recipe exists to have no dependencies, so requiring a backend package worked against it.

- **Dependency floors raised** to current releases: mypy 2.3.1, pytest 9.1.1, pytest-cov 7.1.0, ruff 0.16.5, pybind11-stubgen 2.5.5, scikit-build-core 1.0.3. buildgen's own dev group moves with them.

- **`scripts/update_workflow_actions.py` rewrites the `ACTIONS` table** rather than the templates, which no longer hold action refs.

- **The ruff rule set is pinned** in `[tool.ruff.lint]`. The project had no ruff config, so its lint gate was whatever the installed ruff defaulted to. An upgrade can no longer move it.

### Fixed

- **`make typecheck` failed on every generated native project.** mypy rejects the compiled `_core` module, which ships no stubs. The generated `pyproject.toml` now overrides that one module and leaves the rest under `strict`.

- **`py/pybind11-flex` could not build with its default options.** A `<%text>` block stopped `${name}` from interpolating, so the CMake test target became `_catch2`. The existing tests missed this because they set `test_framework=none`.

- **196 ruff findings** introduced by 0.16.5, which widened its default rule set. Most were `Optional[X]` to `X | None` and import ordering. `os.path` calls moved to `pathlib` throughout.

### Removed

- **`hatchling` is no longer a tracked dependency floor.** Nothing generates a hatchling project. A `hatchling` pin under `[deps]` is now inert; use `uv-build` instead.

## [0.2.0]

### Added

- **`py/nodeps` recipe** - a pure-Python package with no runtime dependencies: hatchling backend, no `CMakeLists.txt`, no compiler in the loop. The generated project ships a standard-library-only example module, a PEP 561 `py.typed` marker, and a test asserting the installed distribution declares no runtime requirements. Verified end to end under both `uv` and `venv`: sync, test, and build produce a single `py3-none-any` wheel.
  - New `common/github-workflows/publish.yml.mako` - a plain sdist/wheel publish workflow (`uv build` plus trusted publishing to TestPyPI then PyPI). The cibuildwheel matrix only makes sense for compiled extensions.
  - `ci.yml.mako`, both `Makefile` templates, and `CHANGELOG.md.mako` accept a `pure_python` option: the CI build leg collapses to a single runner, `build` no longer forces an extension reinstall, `distclean` no longer looks for a CMake cache, and the venv install drops `--no-build-isolation` so the backend is fetched rather than assumed present.
  - `hatchling` joins the PyPI-resolved dependency floors in `common/deps.py`.

- **`Recipe.template_type`** - a recipe now names its own template-registry key via `template_key`, so it no longer has to be a `skbuild-{framework}` type to be rendered. `Recipe.build_system` gains a third value, `"python"`, for recipes with no native build.

- **CI for this repository** (`.github/workflows/ci.yml`) - previously the only workflow was a tag-triggered publish, so the QA gate ran only at release time. Pushes and pull requests now run `ruff`, `mypy`, and the full suite on Python 3.11 and 3.14, plus a `make build` + `twine check` leg. A macOS/Windows leg runs `pytest --skip-skbuild-build` to exercise the generators on the platforms generated projects claim to support; it is marked `continue-on-error` until the portability gaps it finds are addressed.

- **Tests for the two areas that had none.**
  - `tests/test_cli_commands.py` covers the config-driven path: the `generate --config` -> `generate --from` round trip, C and mixed-language Makefile output, library-name normalization, `cli/main.py` subcommand dispatch, and the `--test`/`--build` flag guard. It compiles and runs a generated C project end to end, and runs one check under `python -O` to prove validation is not compiled away.
  - `tests/test_registry_consistency.py` guards the three hand-synced registries (`RECIPES`, `CMakeProjectGenerator.TEMPLATE_FILES`, and the skbuild `TEMPLATE_FILES`): they must agree in both directions, the two legacy-name maps must agree with each other, every template set must be claimed by exactly one recipe, and every referenced built-in template file must exist on disk for both the `uv` and `venv` variants.

  Suite size goes from 382 to 512 tests; coverage from 67% to 72%, with `cli/main.py` at 58% (was 7%), `cli/commands.py` at 51% (was 41%), and `common/project.py` at 94%.

### Changed

- **buildgen's own build backend is now hatchling** instead of `uv_build`. The `uv_build>=0.11.25,<0.12` pin excluded the installed uv (0.12.3) and warned on every build; uv-build is version-locked to uv by design, so the cap would keep breaking. The resulting wheel contains exactly the same 134 files. The dev-group `twine` floor moves to `>=7.0.0`, which understands the Metadata-Version 2.5 that hatchling emits for PEP 639 license metadata; the generated-project floor moves with it, since `py/nodeps` uses hatchling too.

- **PyPI version resolution runs concurrently** with a 2s per-request timeout, replacing 8 sequential 5s requests. The warm path measures at roughly one round trip; the offline worst case drops from about 40s to about 2s. The bundled-defaults fallback is unchanged.

- **`generate --config` emits the schema the loader actually reads.** The template now carries `compile_options`, `compile_definitions`, `link_options`, `include_dirs`, `link_dirs`, `dependencies`, `languages`, `cc`/`cxx`, and per-target `include_dirs`/`link_libraries`. Previously it emitted `cflags`, `cxxflags`, `ldflags`, and `ldlibs` - none of which `ProjectConfig.from_dict` reads - so a user who wrote flags into the generated template got a config that loaded and round-tripped with those flags silently gone.

- **`project.flex.json` is trimmed to the fields that influence the render.** The `targets`, `dependencies`, and `compile_options` blocks described a build the render never produced and are gone. `cmake_options` stays, relabelled as a record of the flags the render bakes in rather than an input.

- **`is_cmake_recipe` answers from the recipe registry**, not from `CMakeProjectGenerator`'s template map, and `buildgen new` / `buildgen test` dispatch on `Recipe.build_system`. A recipe registered without its templates now fails with the generator's own error naming what is missing, rather than a vague "No generator available".

- **`buildgen list`** labels the `py` category "Python Recipes" rather than "Python Extension Recipes", since it now holds a non-extension recipe.

- **GitHub Actions pins** updated across this repo's workflows and the generated-project templates: `astral-sh/setup-uv` to `@v10`. The rest (`actions/checkout@v7`, `actions/upload-artifact@v7`, `actions/download-artifact@v8`, `codecov/codecov-action@v7`, `docker/setup-qemu-action@v4`, `pypa/cibuildwheel@v4`) were already current.

### Fixed

#### Config-driven Makefile generation

- **The generator is no longer C-unaware.** It emitted only `CXX`, only a `%.o: %.cpp` pattern rule, and no `-std=c<N>`, so C sources built through make's implicit rules and linked with `g++` regardless of `cc` and `c_standard`. It now emits `CC` when C is in play, one pattern rule per source extension actually used, `-std=c<N>` into `CFLAGS`, global compile options and definitions into both flag sets, and links a C-only target with `$(CC)` while anything containing C++ links with `$(CXX)`.

- **Project-level `dependencies` reach the link line at all.** `LDLIBS` was emitted as a variable that no generated recipe referenced, so every declared system library was silently dropped from every link command. Shared-library recipes also ignored their target's `link_libraries` entirely.

- **Library names are normalized before reaching the link line.** A dependency named `fmt::fmt` produced the nonsensical `-lfmt::fmt`. CMake-style namespaced names are reduced to their final component, and a value that is already a flag (`-ldl`) passes through untouched.

- **Shared libraries compile position-independent code.** Declaring any `shared` target adds `-fPIC`, which the single global object pattern rule requires.

#### Low-level Makefile API

- **Declared target order is preserved.** `_write_targets` sorted alphabetically, so declaration order - and with it make's default goal - was decided by the alphabet: `all` came first only because it happened to sort first. Targets are now written in the order they were added, and the config-driven generator declares `all` before the targets it aggregates.

- **Input validation no longer depends on how Python was started.** `check_dir` and `_add_entry_or_variable` used bare `assert`, which `python -O` strips, so an invalid include or link directory was accepted silently under optimization. They raise `ValueError` now, with a message naming the list that rejected the entry.

- **Directory validation no longer depends on call order.** A `$(VAR)` reference to a variable the generator did not yet know about raised. Such a variable may come from an include, the environment, or a later `add_variable` call, so unknown references are accepted and left for make to resolve; a reference to a *known* variable whose value is not a directory is still rejected.

#### Generated projects

- **Line continuations survive template rendering.** Mako consumes a trailing backslash together with its newline, so every generated Makefile had its `.PHONY` declaration and its multi-line `release` recipe collapsed onto one line - the latter worked only because `;` happened to separate the commands. Continuations are now emitted explicitly.

- **`make docs` no longer fails out of the box.** The uv target runs `uv run --with sphinx sphinx-build`, since Sphinx is not in the generated `dev` dependency group; the venv target documents that Sphinx must be installed first.

- **`coverage-html` help line** was missing a space before its dash.

#### CLI

- **`project.json` from a flex render agrees with what was rendered.** `-DBUILD_CPP_TESTS=ON` was hardcoded even when `test_framework: none` turned the harness off, and booleans were written with Python's capitalized spelling (`-DBUILD_EMBEDDED_CLI=False`). Derived options are resolved alongside user options now, and a boolean in a `-D` position renders as `ON`/`OFF`.

- **`buildgen test --test` without `--build` reports an error** instead of running nothing. The help text already said it required `--build`, but the build guard silently swallowed it.

- **`buildgen templates show` accepts any recipe path**, not just the five legacy `skbuild-*` names and their aliases.

### Documentation

- **The flex recipe's workflow is described accurately.** The README claimed that editing the `options` block and re-running `cmake` explores different combinations. It does not: the options are baked into `pyproject.toml`'s `[tool.scikit-build.cmake.define]` table and the `option()` defaults at render time, and scikit-build-core re-applies its own defines on every build. Changing options means running `buildgen render` again.

- **A template-override limitation is now stated rather than silently surprising.** Override resolution covers the files in a recipe's file map, not templates pulled in by a Mako `<%include>`. Every `py/*` recipe includes `common/pyproject.base.toml.mako`, which Mako resolves relative to the including template's own directory and the built-in `py/` root only - so an override dropped at `~/.buildgen/templates/py/common/pyproject.base.toml.mako` has no effect and produces no warning. The README documents this along with the two placements that do work.

- **The Makefile back end's language rules are documented**: how `languages`, source extensions, and the standard settings decide pattern rules and link drivers; that a `shared` target makes every compile position-independent; how library names are normalized; and that include and link directories must exist before `generate --from` runs.

- **The low-level generator contract is documented**: targets are written in the order added, so the first one added becomes make's default goal.

## [0.1.12]

### Added

- **`scripts/update_workflow_actions.py`** - Zero-dependency maintenance script that scans buildgen's own workflows (`.github/workflows`) and the generated-project workflow templates (`**/github-workflows`), resolves each GitHub Action's latest release via the `gh` CLI (with an `api.github.com` fallback honoring `GITHUB_TOKEN`), and rewrites the pins.
  - Dry run by default; `--write` applies changes; `--style full` pins to exact `vN.N.N` tags instead of the default major `vN`.
  - Only rewrites version tags and commit SHAs; intentionally leaves branch/floating refs such as `pypa/gh-action-pypi-publish@release/v1` untouched.

- **`make update-actions` / `make update-actions-write`** - Makefile targets wrapping the updater (dry run and apply).

- **Generated C/C++ libraries are now consumable via `find_package`** - the `static`, `shared`, `header-only`, and `library-with-tests` recipes install a CMake package config with a `write_basic_package_version_file` version file and a namespaced `<name>::<name>` ALIAS target (verified end-to-end with a consumer `find_package(<name> <ver> CONFIG REQUIRED)`).

- **`lint-check` / `format-check` Makefile targets** added to generated Python projects (non-mutating ruff checks).

### Changed

- **GitHub Actions versions** updated to latest across buildgen's own CI and the generated-project workflow templates (`ci.yml.mako`, `build-publish.yml.mako`): `setup-uv` to `@v8` (standardized from a commit SHA pin), `cibuildwheel` to `@v4`, `codecov-action` to `@v7`, `setup-qemu-action` to `@v4`. All action references are normalized to consistent major-version tags.

- **Build-system version floors** raised: `uv_build` to `>=0.11.25,<0.12`, and the default `scikit-build-core` floor (offline/`--no-update-deps` generation) from `0.8` to `0.12`.

- **Generated `qa` target is now non-mutating** - it runs `lint-check`, `format-check`, `typecheck`, and `test` (mirroring CI) instead of the auto-fixing `lint`/`format`, so a QA gate no longer rewrites source.

- **CI hardening in generated workflows** - the codecov upload now passes a `CODECOV_TOKEN` secret, and the TestPyPI publish uses `skip-existing: true` so a re-tag no longer errors and blocks the subsequent PyPI publish.

- **Python trove classifiers are generated from `requires-python`** - `Programming Language :: Python :: 3.x` entries now span the `python_version` floor up to the latest known release instead of a hardcoded list, in both `pyproject.base` and `pybind11-flex`.

- **`header-only` CMake recipes** now use `target_compile_features(<name> INTERFACE cxx_std/c_std)` instead of setting a global `CMAKE_*_STANDARD` that did not propagate to consumers.

- **`gitignore.python`** now ignores `.coverage`, `coverage.xml`, and `htmlcov/`.

### Fixed

- **CMake `.gitignore` no longer ignores the generated `Makefile` frontend** - `gitignore.cmake.mako` previously listed `Makefile` and `*.cmake`, which excluded the tracked root `Makefile` frontend (and legitimate `cmake/*.cmake` modules) from version control. Generated projects use out-of-source `build/`, so these entries were both wrong.

- **Project names are validated for C/C++ recipes** - `CMakeProjectGenerator` now rejects names that are not valid identifiers, mirroring the existing skbuild check. Previously a name like `my-lib` produced invalid C++ (`namespace my-lib`, header guard `MY-LIB_LIB_HPP`).

- **CI type-checks the whole package** - the generated `ci.yml` mypy step now runs `mypy src/<name> tests/` instead of only `src/<name>/__init__.py` (which silently skipped the rest of the package and diverged from the Makefile).

- **Portable `sed` in the Makefile `release` target** - replaced macOS-only `sed -i ''` (which fails on GNU sed/Linux) with a temp-file rewrite in `Makefile.uv` and `Makefile.venv`.

- **Generated workflow Python versions track `requires-python`** - `ci.yml.mako` and `build-publish.yml.mako` now derive their Python floor from `defaults.python_version` (the same source as `requires-python`) instead of a hardcoded `3.9`, so the CI matrix and cibuildwheel no longer target versions below the package's declared minimum. The newest matrix leg is clamped to the floor and deduplicated.

- **Sample executables compile cleanly under `-Wall -Wextra`** - the `executable`, `app-with-lib`, and `full` C/C++ mains used `int main(int argc, char* argv[])` without referencing the arguments, warning under the templates' own flags; they now use `int main(void)` / `int main()`.

- **`pybind11-flex` pyproject aligned with the shared base** - its `scikit-build-core` build requirement now uses the resolved `dep_versions` floor instead of a hardcoded `>=0.12`, the redundant `pyproject-metadata` build requirement was removed, and the trove classifiers (development status, Python versions) were synced with `pyproject.base`.

- **Markdown headings were silently stripped from generated files** - Mako treats a line-leading `##` as a comment, so every `##`/`###` heading was dropped from the generated `CHANGELOG.md` (3 headings) and the five extension `README.md` files (`## Quick Start`). Headings are now emitted so they render correctly. This was masked because tests only asserted file existence.

- **`CHANGELOG.md` seed uses a Keep a Changelog date** - the `## [0.1.0]` entry is dated with the generation date instead of `- Initial Release`.

- **`full` CMake recipes no longer require Threads** - dropped the gratuitous `find_package(Threads REQUIRED)` / `Threads::Threads` link that no generated source used.

- **venv Makefile `upgrade`** now installs `build`, which `wheel`/`sdist` require.

## [0.1.11]

### Added

- **Dependency Version Resolution** - Generated Python projects now resolve the latest dependency versions from PyPI at generation time instead of using hardcoded version pins.
  - New module `buildgen.common.deps` with `resolve_latest_versions()` (queries PyPI via stdlib `urllib`) and `get_default_versions()` (offline fallback)
  - Resolution order: user config `[deps]` > PyPI latest > bundled defaults
  - Applies to all dev dependencies (ruff, mypy, pytest, pytest-cov, twine, pybind11-stubgen) and build-system requirements (scikit-build-core)
  - Graceful per-package fallback: if any individual PyPI request fails, the bundled default is used for that package

- **`[deps]` section in user config** (`~/.buildgen/config.toml`) - Pin specific dependency versions that override both PyPI resolution and bundled defaults. Unpinned packages are resolved normally.
  - `buildgen config show` now displays the `[deps]` section
  - `buildgen config init` template includes commented `[deps]` examples

- **`--no-update-deps` CLI flag** - Skip PyPI resolution on `buildgen new` and `buildgen render` for offline or reproducible generation. Bundled defaults are used instead (still overridden by user config `[deps]` pins).

### Changed

- **`SkbuildProjectGenerator`** now accepts an `update_deps` parameter (default: `True`). Templates receive a `dep_versions` dict in their context instead of containing hardcoded version strings.

- **`buildgen test`** uses `update_deps=False` internally to avoid network calls during recipe testing.

- **Mako templates** (`pyproject.base.toml.mako`, `py/pybind11-flex/pyproject.toml.mako`) now use `dep_versions` context variable for all version pins instead of hardcoded strings.

## [0.1.10]

### Added

- **User Configuration** (`~/.buildgen/config.toml`) - Global user-level configuration loaded via stdlib `tomllib`.
  - `[user]` section: `name` and `email` fields for author identity
  - `[defaults]` section: `license`, `cxx_standard`, `c_standard`, `python_version`, `env_tool`
  - `UserConfig` dataclass and `load_user_config()` in `buildgen.common.config`
  - User info flows into templates: LICENSE copyright, pyproject.toml `authors` field
  - Defaults flow into templates: C/C++ standard in CMakeLists.txt, license and requires-python in pyproject.toml

- **`buildgen config` subcommand**:
  - `buildgen config init` - Creates `~/.buildgen/config.toml` with commented template (refuses to overwrite)
  - `buildgen config show` - Displays current resolved config
  - `buildgen config path` - Prints the config file path

- **Comprehensive config tests** (`tests/test_config.py`) - 39 tests covering config loading, template integration, CLI commands, defaults wiring, license body rendering, and backward compatibility.

### Fixed

- **LICENSE body matches `defaults.license`** - The generated LICENSE file now renders the correct license text for MIT, BSD-2-Clause, BSD-3-Clause, ISC, and Apache-2.0. Previously, the LICENSE file always contained MIT text regardless of the configured license. Unsupported SPDX identifiers get a stub with a link to the full text.

- **`--env` flag sentinel bug** - Changed argparse default for `--env` from `"uv"` to `None` so that `defaults.env_tool` from user config is only applied when the user doesn't explicitly pass `--env`. Previously, `--env uv` (explicit) was indistinguishable from the argparse default, causing user config to incorrectly override an explicit CLI choice.

- **`_generate_config_file` missing context** - Configurable recipe templates (e.g., `py/pybind11-flex`) now receive user config context, enabling them to pre-fill author info and apply defaults.

- **pybind11-flex `python_version` fallback inconsistency** - Changed fallback from `"3.9"` to `"3.10"` to match the base pyproject template and documentation.

- **`_generate_config_file` type annotation** - Changed `user_config` parameter type from `Optional[Any]` to `Optional["UserConfig"]` for clarity.

### Changed

- **CMakeProjectGenerator** now accepts `context` and `user_config` parameters, and passes context to template rendering (matching SkbuildProjectGenerator's pattern).

- **SkbuildProjectGenerator** now accepts an optional `user_config` parameter that merges user identity and defaults into the template context.

- **Template defaults are no longer hardcoded** - C++ templates read `defaults.cxx_standard` (fallback: 17), C templates read `defaults.c_standard` (fallback: 11), pyproject.toml templates read `defaults.license` (fallback: MIT) and `defaults.python_version` (fallback: 3.10).

## [0.1.9]

### Added

- **CLI Modularization** - Restructured CLI from single `cli.py` into a proper module (`cli/__init__.py`, `cli/commands.py`, `cli/main.py`, `cli/parsers.py`) for better maintainability and extensibility.

- **New Project Templates** - Added common templates for generated projects:
  - `CHANGELOG.md.mako` - Changelog template
  - `LICENSE.mako` - MIT license template
  - `gitignore.cmake.mako` - CMake project .gitignore
  - `gitignore.python.mako` - Python project .gitignore
  - GitHub workflow templates (`build-publish.yml.mako`, `ci.yml.mako`)

- **Python Extension Improvements**:
  - Added `py.typed` marker files to all Python extension templates (pybind11, nanobind, cython, cext) for PEP 561 compliance
  - Added base pyproject template (`pyproject.base.toml.mako`) for shared configuration

- **Enhanced Makefile Templates** - Expanded `Makefile.uv.mako` and `Makefile.venv.mako` with additional targets and improved functionality.

- **Comprehensive Test Suite**:
  - Added CLI tests (`tests/test_cli.py`) covering command parsing and execution
  - Added `UniqueList` tests (`tests/test_unique_list.py`)

### Fixed

- **Makefile variable handling** - Fixed bug in `makefile/variables.py` affecting variable generation.

## [0.1.8]

### Fixed

- **bug which caused crash of cli** -- due to missing subcmd.

## [0.1.7]

### Added

- **Recipe regression tests** - Added pytest coverage that instantiates every recipe, runs CMake builds for C/C++ templates, and keeps artifacts under `build/build-output/<test>/<recipe>/` for inspection.
- **Persistent build/test outputs** - Test session now resets both `build/test-output/` (legacy file-render fixtures) and the new `build/build-output/` folders before each run so inspection directories are always fresh.
- **Skbuild builds by default** - Recipe tests now run `uv sync` followed by `uv build` for Python extension templates automatically; pass `--skip-skbuild-build` to pytest when you need to opt out.
- **Pybind11-flex README** - The configurable recipe now generates a short `README.md` so scikit-build-core metadata parsing succeeds out of the box.
- **Pybind11-flex test harness defaults** - Automated regression tests disable the native Catch2/GTest harness (and CLI example) when rendering `py/pybind11-flex` so CI-only build toolchains without Catch2 can still compile the template.

### Changed

- **Pybind11-flex dev dependency floor lowered** - The generated `pybind11-stubgen` requirement now targets `>=0.14` so offline development environments (like CI mirrors) can satisfy it with the commonly mirrored 2.5.x releases.


## [0.1.6]

### Added

- **Configurable Flex Recipes** - `buildgen new <name> -r py/pybind11-flex` now emits a `project.flex.json` that describes toggleable options (env tool, native test framework, CLI example). After editing, run the new `buildgen render <config>` command to materialize the project; the renderer forwards the selected options into the templates so `pyproject.toml`, `CMakeLists.txt`, and generated sources reflect your choices.

### Changed

- **mako & pyyaml are now dependencies** - All of the features are available in one shot.

- **Plain Config Output After Render** - Rendering a flex config now produces a regular `project.json` inside the project (with placeholders resolved and `options` removed) while keeping the original `project.flex.json` alongside the config you edited. This keeps the configurable template for future edits without duplicating it in the generated project.

## [0.1.5]

### BREAKING CHANGES

- **CLI API Redesign** - The `project` command has been removed and replaced with simpler top-level commands:
  - `buildgen project init -n <name> -r <recipe>` -> `buildgen new <name> -r <recipe>`
  - `buildgen project recipes` -> `buildgen list`
  - `buildgen project generate -c <file>` -> `buildgen generate --from <file>`

### Added

- **Simplified CLI API** - New top-level commands replacing verbose nested subcommands
  - `buildgen new <name> [-r/--recipe]` - Create project from recipe (default: cpp/executable)
  - `buildgen list [-c/--category]` - List available recipes
  - `buildgen test [options]` - Test recipe generation and building
  - `buildgen generate --config FILE` - Generate boilerplate config file
  - `buildgen generate --from FILE` - Generate build files from existing config

- **Recipe Testing Command** (`buildgen test`)
  - `--name/-n` - Test specific recipe
  - `--category/-c` - Test all recipes in category
  - `--build/-b` - Build generated projects
  - `--test/-t` - Run project tests
  - `--all/-a` - Build and test (same as --build --test)
  - `--keep/-k` - Keep output after testing
  - `--output/-o` - Custom output directory

- **pytest in Python Extension Templates** - All py/* templates now include pytest>=8.0 in dev dependencies

### Changed

- Removed legacy `project` command (use `new`, `list`, `generate` instead)
- CLI examples in README updated to new simplified syntax

### Fixed

- **Cython template for scikit-build-core** - Replaced old scikit-build style (`find_package(Cython)`, `cython_transpile()`) with scikit-build-core compatible approach using `add_custom_command` and `Python::Interpreter -m cython`
- **py/cext recipe framework** - Changed from `framework="cext"` to `framework="c"` to match skbuild-c template

## [0.1.4]

### Added

- **Recipe-Based Project System** - New hierarchical naming convention for project types
  - Recipes use `category/variant` format: `cpp/executable`, `c/static`, `py/pybind11`
  - `--recipe` / `-r` CLI option: `buildgen project init -n myapp --recipe cpp/executable`
  - `buildgen project recipes` command to list all available recipes by category
  - Language is now encoded in recipe name (no need for separate `--lang` flag)

- **Recipe Registry** (`src/buildgen/recipes.py`)
  - `Recipe` dataclass with name, description, category, variant, build_system, language, framework
  - 21 built-in recipes: 7 C++, 7 C, 4 Python extension
  - Helper functions: `get_recipe()`, `get_recipes_by_category()`, `is_valid_recipe()`

- **C++ Template Files** (`templates/cpp/`)
  - `cpp/executable` - C++17 executable with CMakeLists.txt and src/main.cpp
  - `cpp/static` - Static library with source and headers
  - `cpp/shared` - Shared library (-fPIC) with source and headers
  - `cpp/header-only` - Interface library (header-only)
  - `cpp/library-with-tests` - Static library with test executable
  - `cpp/app-with-lib` - Executable with internal library
  - `cpp/full` - Complete project: library + app + tests

- **C Template Files** (`templates/c/`)
  - `c/executable` - C11 executable with CMakeLists.txt and src/main.c
  - `c/static` - Static library with source and headers
  - `c/shared` - Shared library (-fPIC) with source and headers
  - `c/header-only` - Interface library (header-only)
  - `c/library-with-tests` - Static library with test executable
  - `c/app-with-lib` - Executable with internal library
  - `c/full` - Complete project: library + app + tests

- **CMake Project Generator** (`src/buildgen/cmake/project_generator.py`)
  - Template-based generation for all C++ and C recipes
  - `CMakeProjectGenerator` class with template override support
  - Generates: CMakeLists.txt, Makefile, source files, headers, test files

- **CMake Makefile Frontend** (`templates/common/Makefile.cmake.mako`)
  - Convenience wrapper for cmake commands
  - Targets: build, configure, clean, rebuild, install, test
  - Variables: BUILD_DIR, BUILD_TYPE, CMAKE_FLAGS

### Changed

- **Template Directory Restructure** - Templates now use recipe-based paths
  - `templates/skbuild-pybind11/` -> `templates/py/pybind11/`
  - `templates/skbuild-cython/` -> `templates/py/cython/`
  - `templates/skbuild-c/` -> `templates/py/cext/`
  - `templates/skbuild-nanobind/` -> `templates/py/nanobind/`
- Template CLI commands updated to use recipe paths: `buildgen templates copy py/pybind11`
- Removed `--lang` flag from `project init` (language now determined by recipe)
- `project types` command now redirects to `project recipes`

## [0.1.3]

### Added

- **Template Override System** - Customize templates without modifying buildgen
  - Four-tier resolution: `$BUILDGEN_TEMPLATES` > `.buildgen/templates/` > `~/.buildgen/templates/` > built-in
  - Per-file override granularity (override just pyproject.toml, keep other defaults)
  - `TemplateResolver` class for programmatic template resolution

- **Template CLI Commands** (`buildgen templates`)
  - `buildgen templates list` - List available templates and show override status
  - `buildgen templates copy <type>` - Copy templates to `.buildgen/templates/` for customization
  - `buildgen templates copy <type> --global` - Copy to `~/.buildgen/templates/` for user defaults
  - `buildgen templates show <type>` - Show template file resolution details

- **Embedded Mako Template Engine** (Mako-Lite)
  - Integrated Mako template library for `${variable}` syntax
  - Removed external markupsafe dependency (inlined html_escape)
  - Reduced from ~16k to ~7k lines by removing unused modules

### Changed

- Templates are now `.mako` files in `src/buildgen/templates/` instead of Python strings
- Simplified template directory structure (removed redundant category nesting)
- Template paths: `templates/skbuild-pybind11/` instead of `templates/skbuild/skbuild-pybind11/`

## [0.1.2]

### Added

- **scikit-build-core Project Templates** (`buildgen project init -t <type>`)
  - `skbuild-pybind11` - Python extension using pybind11 (C++ bindings)
  - `skbuild-cython` - Python extension using Cython
  - `skbuild-c` - Python C extension (direct Python.h)
  - `skbuild-nanobind` - Python extension using nanobind (modern C++ bindings)
  - Each template includes: pyproject.toml, CMakeLists.txt, source files, **init**.py, tests

- **Makefile Frontend for skbuild Projects**
  - `make sync` - Initial environment setup (`uv sync`)
  - `make build` - Rebuild extension (`uv sync --reinstall-package <name>`)
  - `make test` - Run tests (`uv run pytest`)
  - `make wheel` / `make sdist` - Build distributions (`uv build`)
  - `make clean` / `make distclean` - Clean build artifacts

- **Environment Tool Option** (`--env`)
  - `--env uv` (default) - Use uv commands in generated Makefile
  - `--env venv` - Use pip/python commands for traditional virtualenv workflows
  - Example: `buildgen project init -t skbuild-pybind11 -n myext --env venv`

## [0.1.1]

### Added

- **CMake Generator**: Full CMakeLists.txt generation support
  - `CMakeListsGenerator` class for programmatic generation
  - Support for executables, static/shared/interface libraries
  - `find_package()` for system dependencies
  - `FetchContent` for git/URL dependencies
  - Install rules generation
  - C++ standard configuration

- **CMake Builder**: Wrapper for cmake commands
  - `CMakeBuilder.configure()` - cmake -S -B
  - `CMakeBuilder.build()` - cmake --build
  - `CMakeBuilder.install()` - cmake --install

- **Cross-Generator Project Configuration**
  - `ProjectConfig` dataclass for defining projects once
  - JSON and YAML configuration file support
  - `generate_makefile()` - generate Makefile from config
  - `generate_cmake()` - generate CMakeLists.txt from config
  - `generate_all()` - generate both build systems
  - `generate_cmake_with_frontend()` - CMake with Makefile wrapper

- **CMake Frontend Mode**
  - Generate CMakeLists.txt as the build system
  - Generate Makefile as a convenience wrapper
  - Targets: all, build, configure, clean, rebuild, install, test, help
  - Configurable BUILD_DIR, BUILD_TYPE, CMAKE_FLAGS

- **Project Templates** (`buildgen project init -t <type>`)
  - `executable` - Single executable
  - `static` - Static library
  - `shared` - Shared library
  - `header-only` - Header-only/interface library
  - `library-with-tests` - Library with test executable
  - `app-with-lib` - Executable with internal library
  - `full` - Library + app + tests with dependencies

- **CLI Commands**
  - `buildgen cmake generate` - Generate CMakeLists.txt
  - `buildgen cmake build` - Configure and build with cmake
  - `buildgen cmake clean` - Clean build directory
  - `buildgen project init` - Create project config from template
  - `buildgen project generate` - Generate from config file
  - `buildgen project types` - List available templates

- **Enhanced Makefile** for development workflow
  - `make lint` - Run ruff check
  - `make format` / `make format-check` - Code formatting with ruff
  - `make typecheck` - Run ty and mypy type checkers
  - `make build` - Build distribution with uv
  - `make check` - Build and verify with twine
  - `make publish` - Publish to PyPI

### Changed

- Refactored Makefile functions to `Mk` namespace class
  - `makefile_wildcard(...)` -> `Mk.wildcard(...)`
  - `makefile_patsubst(...)` -> `Mk.patsubst(...)`
  - All 30+ functions now accessed via `Mk.*`
  - Import: `from buildgen.makefile.functions import Mk`

- Refactored CMake functions to `Cm` namespace class
  - `cmake_minimum_required(...)` -> `Cm.minimum_required(...)`
  - `cmake_project(...)` -> `Cm.project(...)`
  - All 40+ functions now accessed via `Cm.*`
  - Import: `from buildgen.cmake.functions import Cm`

- Removed backward compatibility aliases for old function names

- Minimized package `__init__.py` exports for API flexibility

- Package restructured from single file to multi-module
- `MakefileGenerator` now inherits from `BaseGenerator`
- Unified CLI entry point (`buildgen`)

### Fixed

- Type checking errors for both `ty` and `mypy`
- Ruff lint errors and code formatting
- `UniqueList` generic type annotations

## [0.1.0] - Initial Release

### Added

- **Makefile Generator**: Programmatic Makefile generation
  - Variable types: `Var`, `SVar`, `IVar`, `CVar`, `AVar`
  - Pattern rules, phony targets, clean targets
  - Conditional blocks (ifeq, ifdef, ifndef)
  - Include directives

- **Direct Builder**: Compile without generating Makefile
  - `Builder` class for direct compilation

- **Makefile Functions**: Python helpers for Makefile functions
  - `Mk.wildcard()`, `Mk.patsubst()`, `Mk.subst()`
  - `Mk.if_()`, `Mk.foreach()`, `Mk.shell()`
  - And 20+ more via `Mk.*` namespace

- **Utilities**
  - `UniqueList` - Ordered set-like list
  - `PythonSystem` - Python installation info
  - `PLATFORM` - Platform detection
