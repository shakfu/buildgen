<%page args="name, options={}" />
<%!
from buildgen.skbuild.maturin import resolve
%>\
<%
_m = resolve(options)
_label = {"pyo3": "PyO3", "cffi": "cffi", "uniffi": "UniFFI"}[_m.bindings]
%>\
<%include file="/common/pyproject.base.toml.mako" args="
    name=name,
    framework=_m.bindings,
    framework_pkg=None,
    description='A Python extension module written in Rust with ' + _label,
    lang_classifier='Rust',
    maturin=True,
    options=options
"/>
