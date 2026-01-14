#include <catch2/catch_test_macros.hpp>
#include <pybind11/embed.h>

namespace py = pybind11;

static int python_add(int a, int b) {
    py::module module = py::module::import("${name}");
    return module.attr("add")(a, b).cast<int>();
}

static std::string python_greet(const std::string& target) {
    py::module module = py::module::import("${name}");
    return module.attr("greet")(target).cast<std::string>();
}

TEST_CASE("pybind11 module round-trips", "[native]") {
    py::scoped_interpreter guard{};

    REQUIRE(python_add(3, 4) == 7);
    REQUIRE(python_greet("Catch2") == "Hello, Catch2!");
}
