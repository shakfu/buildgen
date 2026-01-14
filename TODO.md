# TODO

## Extended Recipes

- [ ] Testing recipes: `cpp/catch2`, `cpp/gtest`
- [ ] GUI recipes: `cpp/qt`, `c/gtk`
- [ ] Mixed recipes: `cpp/pybind11-catch2` (extension + tests)

## New Language Categories

- [ ] Rust: `rust/executable`, `rust/lib`, `rust/py-pyo3`
- [ ] Go: `go/executable`, `go/lib`
- [ ] Multi-language projects

## Open Questions

1. **Recipe depth**: Should recipes support more than two levels? (e.g., `cpp/lib/static` vs `cpp/static`)

   > Two-tier is sufficient for now

2. **Configurable recipes with reaonable defaults**: How to handle combinations like pybind11 + catch2 testing?
   - Option A: `py/pybind11-catch2` (explicit compound recipe)
   - Option B: `py/pybind11 --with catch2` (modifier flag)
   - Option C: Separate test recipe that integrates
   
   > It will be impossible to implement configuration for all build variants from the command-line. It is better to generate a recipe which includes options: i.e. a configuragable recipe, which requires further input from the user.
    > The new `py/pybind11-flex` recipe demonstrates this approach with native test toggles.

   Here’s a sketch of a “configurable recipe with reasonable defaults” that pairs a `pybind11` module with optional C++ tests. The idea is that `buildgen new myext -r py/pybind11-flex` drops a config like the example below into the project, and the contributor tweaks the option switches before running buildgen render (the current implementation emits `project.flex.json`).
   
   This follows the README’s structure (name/version/dependencies/targets) but adds an options block plus clearly commented toggles.

   ```yaml
   # project.yaml produced by recipe py/pybind11-flex

   name: myext
   version: 0.1.0
   recipe: py/pybind11-flex

   options:
     env: uv                  # change to venv if you don’t want uv make targets
     test_framework: catch2   # catch2 | gtest | none
     build_examples: false    # flip to true to build CLI demo binary

   compile_options:
     - -Wall
     - -Wextra
     - -O2

   dependencies:
     - pybind11
     - ${options.test_framework == "catch2" and "Catch2" or null}
     - ${options.test_framework == "gtest" and "GTest" or null}

   targets:
     - name: myext
       type: pybind11-extension
       sources:
         - src/myext/bindings.cpp
       include_dirs:
         - include
       install: true

     - name: myext_tests
       type: executable
       enabled: ${options.test_framework != "none"}
       framework: ${options.test_framework}
       sources:
         - tests/${options.test_framework}/test_module.cpp
       link_libraries:
         - myext
         - ${options.test_framework == "catch2" and "Catch2::Catch2WithMain" or "GTest::gtest_main"}

     - name: myext_cli
       type: executable
       enabled: ${options.build_examples}
       sources:
         - examples/cli/main.cpp
       link_libraries:
         - myext

   env:
     toolchain: clang
     python_backend: ${options.env}
   ```

   Defaults give you a `pybind11` extension with `Catch2` tests and no extra CLI. If a user wants `GoogleTest` or no native tests, they only edit the options block; template logic (e.g., via `Mako conditionals) takes care of wiring dependencies, test targets, and Makefile snippets.

3. **Recipe aliases**: Should common recipes have short aliases?
   ```bash
   buildgen project init -n myapp -r cppexe  # alias for cpp/executable
   ```

   > No

4. **User-defined recipes**: Allow users to define custom recipes in `~/.buildgen/recipes/`?

   > Yes

5. **Recipe metadata**: Should recipes include metadata like author, version, tags?
   ```yaml
   # templates/cpp/executable/recipe.yaml
   name: cpp/executable
   description: C++ executable project
   tags: [c++, cmake, console]
   ```

   > No

6. **Environment options**: How do `--env uv/venv` fit with recipes?
   - Keep as separate flag (orthogonal to recipe)
   - Encode in recipe: `py/pybind11-uv` vs `py/pybind11-venv`

   > The default should be `uv`, but see above, this can be changed by the user to `venv` at the recipe level.
