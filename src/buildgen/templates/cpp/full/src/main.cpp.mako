#include <iostream>
#include "${name}/lib.hpp"

int main(int argc, char* argv[]) {
    int result = ${name}::add(2, 3);
    std::cout << "${name}: 2 + 3 = " << result << std::endl;
    return 0;
}
