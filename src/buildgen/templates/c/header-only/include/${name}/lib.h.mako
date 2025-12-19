#ifndef ${name.upper()}_LIB_H
#define ${name.upper()}_LIB_H

#ifdef __cplusplus
extern "C" {
#endif

/* Add two integers */
static inline int ${name}_add(int a, int b) {
    return a + b;
}

#ifdef __cplusplus
}
#endif

#endif  /* ${name.upper()}_LIB_H */
