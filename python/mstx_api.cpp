/* -------------------------------------------------------------------------
 * This file is part of the MindStudio project.
 * Copyright (c) 2025 Huawei Technologies Co.,Ltd.
 *
 * MindStudio is licensed under Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *
 *          http://license.coscl.org.cn/MulanPSL2
 *
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
 * EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
 * MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
 * See the Mulan PSL v2 for more details.
 * ------------------------------------------------------------------------- */

#include "mstx/ms_tools_ext.h"
#include "mstx_api.h"

class GILCtrl {
public:
    GILCtrl() : tstate(PyEval_SaveThread()) {} // 释放GIL
    ~GILCtrl()
    {
        PyEval_RestoreThread(tstate);   // 恢复GIL
    }
private:
    PyThreadState* tstate;
};

bool ParseArgs(PyObject *args, PyObject *kwds, const char*& message, PyObject*& py_stream)
{
    message = nullptr;
    py_stream = Py_None;

    static char* kwlist[] = { "message", "stream", nullptr };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|sO", kwlist, &message, &py_stream)) {
        return false;
    }
    return true;
}

PyObject *WrapMstxMarkA(PyObject *self, PyObject *args, PyObject *kwds)
{
    const char *message;
    PyObject *py_stream;

    if (!ParseArgs(args, kwds, message, py_stream)) {
        return NULL;
    }

    aclrtStream stream = nullptr;
    if (py_stream != Py_None) {
        void* ptr = reinterpret_cast<void*>(PyLong_AsVoidPtr(py_stream));
        stream = static_cast<aclrtStream>(ptr);
    }
    if (!mstxMarkA) {
        Py_RETURN_NONE;
    }
    {
        GILCtrl gilCtrl;
        mstxMarkA(message, stream);
    }

    Py_RETURN_NONE;
}

PyObject *WrapMstxRangeStartA(PyObject *self, PyObject *args, PyObject *kwds)
{
    const char* message = nullptr;
    PyObject *py_stream = Py_None;

    if (!ParseArgs(args, kwds, message, py_stream)) {
        return NULL;
    }

    aclrtStream stream = nullptr;
    if (py_stream != Py_None) {
        void* ptr = reinterpret_cast<void*>(PyLong_AsVoidPtr(py_stream));
        stream = static_cast<aclrtStream>(ptr);
    }
    if (!mstxRangeStartA) {
        return Py_BuildValue("I", 0);
    }
    mstxRangeId ret;
    {
        GILCtrl gilCtrl;
        ret = mstxRangeStartA(message, stream);
    }

    return Py_BuildValue("I", ret);
}

PyObject *WrapMstxRangeEnd(PyObject *self, PyObject *args, PyObject *kwds)
{
    uint32_t rangeId = 0;
    static char arg1[] = "rangeId";
    static char *kwlist[] = {arg1, nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|I", kwlist, &rangeId)) {
        return NULL;
    }
    if (!mstxRangeEnd) {
        Py_RETURN_NONE;
    }
    {
        GILCtrl gilCtrl;
        mstxRangeEnd(static_cast<mstxRangeId>(rangeId));
    }

    Py_RETURN_NONE;
}

PyObject *WrapMstxGetToolId(PyObject *self, PyObject *args, PyObject *kwds)
{
    uint64_t id = 0;
    {
        GILCtrl gilCtrl;
        mstxGetToolId(&id);
    }
    return Py_BuildValue("K", id);
}