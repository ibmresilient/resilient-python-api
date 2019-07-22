# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import pytest
from resilient_circuits.action_message import *

class TestErrors(object):
    def test_errors_subclass_value_error(self):
        assert issubclass(FunctionException_, ValueError)
        assert issubclass(FunctionError_, ValueError)

    def test_function_exception_returned_after_exception(self):
        try:
            raise ValueError("hello")
        except ValueError:
            assert issubclass(FunctionError().__class__, FunctionException_)

    def test_function_error_returned_outside_try(self):
        assert issubclass(FunctionError().__class__, FunctionError_)

    def test_function_error_returned_after_handled_exception(self):
        """
        Different behavior in Python 2.7 and 3
        In 3, after the try..catch sys.exc_info is empty, in 2.7 it's not
        """
        import sys
        PY2 = sys.version_info[0] == 2

        try:
            raise ValueError("hello")
        except ValueError:
            pass
        if PY2:
            assert issubclass(FunctionError().__class__, FunctionException_)
        else:
            assert issubclass(FunctionError().__class__, FunctionError_)

    def test_message_passed_in_error_preserved(self):
        err = FunctionError("error")
        assert str(err) == "error"

    def test_trace_is_included_unless_otherwise_said(self):
        try:
            raise ValueError("trace_included")
        except:
            err = FunctionError("message_included")
            message = str(err)
            assert "trace_included" in message
    """
    --------------------------------
    Section testing new capabilities
    --------------------------------
    """
    def test_message_passed_in_exception_preserved_no_trace(self):
        try:
            raise ValueError("value_error")
        except:
            err = FunctionError("error", trace=False)
            assert str(err) == "error"

    def test_trace_and_message_preserved(self):
        try:
            raise ValueError("trace_included")
        except:
            err = FunctionError("message_included")
            message = str(err)
            assert "trace_included" in message
            assert "message_included" in message
