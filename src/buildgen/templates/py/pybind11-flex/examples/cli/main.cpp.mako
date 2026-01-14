#include <pybind11/embed.h>
#include <iostream>
#include <stdexcept>

namespace py = pybind11;

int main(int argc, char** argv) {
    py::scoped_interpreter guard{};

    auto module = py::module::import("${name}");

    const int lhs = argc > 1 ? std::stoi(argv[1]) : 1;
    const int rhs = argc > 2 ? std::stoi(argv[2]) : 2;

    const int result = module.attr("add")(lhs, rhs).cast<int>();

    std::cout << lhs << " + " << rhs << " = " << result << std::endl;
    std::cout << module.attr("greet")("CLI user").cast<std::string>() << std::endl;
    return 0;
}
