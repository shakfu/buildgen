#include <stdio.h>
#include "${name}/lib.h"

int main(void) {
    int result = ${name}_add(2, 3);
    if (result != 5) {
        fprintf(stderr, "Test failed: expected 5, got %d\n", result);
        return 1;
    }
    printf("All tests passed!\n");
    return 0;
}
