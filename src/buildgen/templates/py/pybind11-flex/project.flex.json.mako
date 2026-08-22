{
  "_notes": [
    "Configurable recipe produced by py/pybind11-flex.",
    "1. Edit the options block below -- these three values are the only",
    "   inputs to the render.",
    "2. Run `buildgen render project.flex.json`.",
    "The render bakes the chosen options into pyproject.toml's",
    "[tool.scikit-build.cmake.define] table and into the CMakeLists.txt",
    "option() defaults, so a rebuild picks them up with no extra flags.",
    "To try a different combination, edit this file and render again."
  ],
  "name": "${name}",
  "version": "0.1.0",
  "recipe": "py/pybind11-flex",
  "options": {
    "env": "uv",
    "test_framework": "catch2",
    "build_examples": false
  },
  "_options_help": {
    "env": "Set to 'venv' to use pip/python in the generated Makefile.",
    "test_framework": "Choose catch2, gtest, or none to disable native harness.",
    "build_examples": "Flip to true to compile the CLI helper that embeds Python."
  },
  "_cmake_help": [
    "The flags below are what the render bakes in. They are recorded here so",
    "you can reproduce the same configuration from a bare `cmake` invocation;",
    "scikit-build-core does not read them from this file."
  ],
  "cmake_options": [
    "-DBUILD_CPP_TESTS=<options.build_cpp_tests>",
    "-DTEST_FRAMEWORK=<options.test_framework>",
    "-DBUILD_EMBEDDED_CLI=<options.build_examples>"
  ]
}
