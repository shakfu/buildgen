#include <pybind11/pybind11.h>
#include <string>

namespace py = pybind11;

int add(int a, int b) {
    return a + b;
}

std::string greet(const std::string& name) {
    return "Hello, " + name + "!";
}

PYBIND11_MODULE(_core, m) {
    m.doc() = "${name} extension module";

    m.def("add", &add, "Add two integers",
          py::arg("a"), py::arg("b"));

    m.def("greet", &greet, "Return a greeting string",
          py::arg("name"));
}
