#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject* ${name}_add(PyObject* self, PyObject* args) {
    int a, b;
    if (!PyArg_ParseTuple(args, "ii", &a, &b)) {
        return NULL;
    }
    return PyLong_FromLong(a + b);
}

static PyObject* ${name}_greet(PyObject* self, PyObject* args) {
    const char* name;
    if (!PyArg_ParseTuple(args, "s", &name)) {
        return NULL;
    }
    return PyUnicode_FromFormat("Hello, %s!", name);
}

static PyMethodDef ${name}_methods[] = {
    {"add", ${name}_add, METH_VARARGS, "Add two integers."},
    {"greet", ${name}_greet, METH_VARARGS, "Return a greeting string."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef ${name}_module = {
    PyModuleDef_HEAD_INIT,
    "_core",
    "${name} C extension module",
    -1,
    ${name}_methods
};

PyMODINIT_FUNC PyInit__core(void) {
    return PyModule_Create(&${name}_module);
}
