#include <iostream>
#include "${name}/lib.hpp"

int main() {
    int result = ${name}::add(2, 3);
    if (result != 5) {
        std::cerr << "Test failed: expected 5, got " << result << std::endl;
        return 1;
    }
    std::cout << "All tests passed!" << std::endl;
    return 0;
}
