<%!
from buildgen.skbuild.maturin import resolve
%>\
<%
_m = resolve(context.get("options"))
_label = {"pyo3": "[PyO3](https://pyo3.rs)", "cffi": "[cffi](https://cffi.readthedocs.io)", "uniffi": "[UniFFI](https://mozilla.github.io/uniffi-rs/)"}[_m.bindings]
%>\
# ${name}

A Python extension module written in Rust with ${_label},
built by [maturin](https://www.maturin.rs).

${"##"} Requirements

- [uv](https://docs.astral.sh/uv/)
- A Rust toolchain (`cargo`), e.g. from [rustup](https://rustup.rs)

${"##"} Quick Start

```bash
uv sync
uv run pytest
% if _m.rust_tests:
cargo test --no-default-features
% endif
uv build
```

`uv sync` rebuilds the extension when `src/lib.rs` or `Cargo.toml` changes.
Keep `src/${name}/_core.pyi` in step with the Rust signatures.
% if _m.generated_module:
maturin generates `src/${name}/_core/` on each build; it is not tracked.
% endif

Use `make help` for additional targets (wheel, sdist, clean, etc.).
