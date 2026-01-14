{
  "_notes": [
    "Configurable recipe produced by py/pybind11-flex.",
    "1. Edit the options block.",
    "2. Run `buildgen render project.flex.json`."
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
  "compile_options": [
    "-Wall",
    "-Wextra",
    "-O2"
  ],
  "cmake_options": [
    "-DBUILD_CPP_TESTS=ON",
    "-DTEST_FRAMEWORK=<options.test_framework>",
    "-DBUILD_EMBEDDED_CLI=<options.build_examples>"
  ],
  "dependencies": [
    "pybind11",
    "Threads",
    "Catch2",
    "GTest"
  ],
  "targets": [
    {
      "name": "${name}_core",
      "type": "shared",
      "sources": ["src/${name}/_core.cpp"],
      "include_dirs": ["src/${name}"],
      "install": true
    },
    {
      "name": "${name}_tests",
      "type": "executable",
      "sources": [
        "tests/native/test_module.catch2.cpp"
      ],
      "link_libraries": [
        "${name}_core",
        "Catch2::Catch2WithMain"
      ],
      "compile_options": [
        "-DTEST_FRAMEWORK=<options.test_framework>"
      ]
    },
    {
      "name": "${name}_cli",
      "type": "executable",
      "sources": [
        "examples/cli/main.cpp"
      ],
      "link_libraries": [
        "pybind11::embed"
      ]
    }
  ]
}
