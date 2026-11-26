{
  "_notes": [
    "Configurable recipe produced by py/maturin-flex.",
    "1. Edit the options block below.",
    "2. Run `buildgen render project.flex.json`.",
    "To try a different combination, edit this file and render again."
  ],
  "name": "${name}",
  "version": "0.1.0",
  "recipe": "py/maturin-flex",
  "options": {
    "env": "${options.get('env', 'uv')}",
    "bindings": "${options.get('bindings', 'pyo3')}",
    "abi3": ${"true" if options.get("abi3", True) else "false"},
    "rust_tests": ${"true" if options.get("rust_tests", True) else "false"}
  },
  "_options_help": {
    "env": "Set to 'venv' to use pip/python in the generated Makefile.",
    "bindings": "pyo3 (Python C API), cffi (C ABI), or uniffi (UniFFI proc-macros).",
    "abi3": "pyo3 only: build one stable-ABI wheel per platform instead of one per CPython version.",
    "rust_tests": "Add Rust unit tests, `make test-rust`, and a CI step running `cargo test`."
  }
}
