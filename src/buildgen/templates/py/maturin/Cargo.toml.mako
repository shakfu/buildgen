<%!
from buildgen.common import versions as V
from buildgen.skbuild.maturin import resolve
%>\
<%
_m = resolve(context.get("options"))
_defaults = context.get("defaults") or {}
# One abi3 wheel per platform covers every CPython from the requires-python floor.
_floor = _defaults.get("python_version", str(V.PYTHON["floor"]))
_pyo3_features = ['"abi3-py%s"' % _floor.replace(".", "")] if _m.abi3 else []
%>\
[package]
name = "${name}"
version = "0.1.0"
edition = "2024"

[lib]
# Must match the last component of [tool.maturin] module-name in pyproject.toml.
name = "_core"
# cdylib produces the shared library Python imports.
crate-type = ["cdylib"]
% if _m.bindings == "uniffi":

[[bin]]
# maturin runs this to generate the Python bindings, so their version always
# matches the uniffi crate.
name = "uniffi-bindgen"
path = "uniffi-bindgen.rs"
required-features = ["uniffi-cli"]

[features]
uniffi-cli = ["uniffi/cli"]
% elif _m.bindings == "pyo3" and _m.rust_tests:

[features]
# `cargo test --no-default-features` drops pyo3, so the test binary does not
# need to link libpython. maturin builds with default features.
default = ["python"]
python = ["dep:pyo3"]
% endif

[dependencies]
% if _m.bindings == "pyo3":
pyo3 = { version = "${V.CRATES['pyo3']}"${', optional = true' if _m.rust_tests else ''}, features = [${", ".join(_pyo3_features)}] }
% elif _m.bindings == "uniffi":
uniffi = "${V.CRATES['uniffi']}"
% endif
