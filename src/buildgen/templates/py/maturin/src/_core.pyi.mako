<%!
from buildgen.skbuild.maturin import resolve
%>\
<%
_m = resolve(context.get("options"))
%>\
% if _m.bindings == "cffi":
# maturin generates this module at build time. It wraps the C ABI in src/lib.rs.
from typing import Any

ffi: Any
lib: Any
% else:
% if _m.generated_module:
# maturin generates this module at build time. Keep in step with src/lib.rs.
% endif
def add(a: int, b: int) -> int: ...
def greet(name: str) -> str: ...
% endif
