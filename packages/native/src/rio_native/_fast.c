#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>

static PyObject *fnv1a64(PyObject *self, PyObject *arg) {
    Py_buffer view;
    if (PyObject_GetBuffer(arg, &view, PyBUF_SIMPLE) != 0) return NULL;
    uint64_t h = 14695981039346656037ULL;
    const unsigned char *p = (const unsigned char *)view.buf;
    for (Py_ssize_t i = 0; i < view.len; i++) { h ^= p[i]; h *= 1099511628211ULL; }
    PyBuffer_Release(&view);
    return PyLong_FromUnsignedLongLong(h);
}

static PyMethodDef methods[] = {
    {"fnv1a64", fnv1a64, METH_O, "64-bit FNV-1a hash of a bytes-like object."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef mod = {PyModuleDef_HEAD_INIT, "_fast", NULL, -1, methods};
PyMODINIT_FUNC PyInit__fast(void) { return PyModule_Create(&mod); }
