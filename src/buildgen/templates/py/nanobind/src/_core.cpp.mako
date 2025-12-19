#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <string>

namespace nb = nanobind;

int add(int a, int b) {
    return a + b;
}

std::string greet(const std::string& name) {
    return "Hello, " + name + "!";
}

NB_MODULE(_core, m) {
    m.doc() = "${name} extension module";

    m.def("add", &add, "Add two integers",
          nb::arg("a"), nb::arg("b"));

    m.def("greet", &greet, "Return a greeting string",
          nb::arg("name"));
}
