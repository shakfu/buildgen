#include <stdio.h>
#include "${name}/lib.h"

int main(void) {
    int result = ${name}_add(2, 3);
    printf("${name}: 2 + 3 = %d\n", result);
    return 0;
}
