# TODO

## Bootstrapping

Currently require `cmake`, `make`, and `uv`. How do we deal if one of these is not available?

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
  >
  > The new `py/pybind11-flex` recipe demonstrates this approach with native test toggles.

  Here’s a sketch of a “configurable recipe with reasonable defaults” that pairs a `pybind11` module with optional C++ tests. The idea is that `buildgen new myext -r py/pybind11-flex` drops a config like the example below into the project, and the contributor tweaks the option switches before running buildgen render (the current implementation emits `project.flex.json`).

  This follows the README’s structure (name/version/dependencies/targets) but adds an options block plus clearly commented toggles.

  ```yaml
  # project.yaml produced by recipe py/pybind11-flex
  recipe: py/pybind11-flex
  name: myproject
  version: "0.1.0"
  env: uv
  test_framework: catch2
  build_examples: false

  options:
    env: Set to 'venv' to use pip/python in the generated Makefile.
    test_framework: Choose catch2, gtest, or none to disable native harness.
    build_examples: true
  compile_options:
    - -Wall
    - -Wextra
    - -O2

  cmake_options:
    - "-DBUILD_CPP_TESTS=ON"
    - "-DTEST_FRAMEWORK=${options.test_framework}"
    - "-DBUILD_EMBEDDED_CLI=${options.build_examples}"

  dependencies:
    - pybind11
    - Threads
    - Catch2
    - GTest

  targets:
    - name: mylib_core
      type: shared
      sources: ["src/${name}/_core.cpp"]
      include_dirs: ["src/${name}"]
      install: true

    - name: myapp
      type: executable
      sources:
        - tests/native/test_module.catch2.cpp
      link_libraries:
        - mylib_core
        - Catch2::Catch2WithMain

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
