<%!
from buildgen.skbuild.maturin import resolve
%>\
<%
_m = resolve(context.get("options"))
%>\
% if _m.bindings == "uniffi":
uniffi::setup_scaffolding!();

% elif _m.bindings == "cffi":
use std::ffi::{CStr, CString, c_char};

% endif
/// Add two integers.
% if _m.bindings == "uniffi":
#[uniffi::export]
% endif
pub fn add(a: i64, b: i64) -> i64 {
    a + b
}

/// Return a greeting.
% if _m.bindings == "uniffi":
#[uniffi::export]
pub fn greet(name: String) -> String {
    format!("Hello, {name}!")
}
% else:
pub fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}
% endif
% if _m.bindings == "pyo3":

/// The module name must match `[lib] name` in Cargo.toml.
% if _m.rust_tests:
#[cfg(feature = "python")]
% endif
#[pyo3::pymodule]
mod _core {
    use pyo3::prelude::*;

    #[pyfunction]
    fn add(a: i64, b: i64) -> i64 {
        super::add(a, b)
    }

    #[pyfunction]
    fn greet(name: &str) -> String {
        super::greet(name)
    }
}
% elif _m.bindings == "cffi":

// C ABI for cffi. maturin generates the C header and the Python module.

#[unsafe(no_mangle)]
pub extern "C" fn core_add(a: i64, b: i64) -> i64 {
    add(a, b)
}

/// Free the result with `core_free_string`.
///
/// # Safety
/// `name` must be a valid NUL-terminated string.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn core_greet(name: *const c_char) -> *mut c_char {
    let name = unsafe { CStr::from_ptr(name) }.to_string_lossy();
    CString::new(greet(&name)).map_or(std::ptr::null_mut(), CString::into_raw)
}

/// # Safety
/// `s` must come from `core_greet` and must not be used afterwards.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn core_free_string(s: *mut c_char) {
    if !s.is_null() {
        drop(unsafe { CString::from_raw(s) });
    }
}
% endif
% if _m.rust_tests:

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds() {
        assert_eq!(add(1, 2), 3);
        assert_eq!(add(-1, 1), 0);
    }

    #[test]
    fn greets() {
        assert_eq!(greet("World".into()), "Hello, World!");
    }
}
% endif
