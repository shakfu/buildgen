#include <gtest/gtest.h>
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

TEST(${name}_module, add) {
    py::scoped_interpreter guard{};
    EXPECT_EQ(python_add(10, 5), 15);
}

TEST(${name}_module, greet) {
    py::scoped_interpreter guard{};
    EXPECT_EQ(python_greet("GTest"), "Hello, GTest!");
}
