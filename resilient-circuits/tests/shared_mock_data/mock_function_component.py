# -*- coding: utf-8 -*-

from resilient_circuits import (FunctionError, FunctionResult,
                                ResilientComponent, StatusMessage, function)
from resilient_lib import ResultPayload, IntegrationError
from tests import mock_constants

PACKAGE_NAME = mock_constants.MOCK_PACKAGE_NAME


class MockFunctionComponent(ResilientComponent):

    def __init__(self, opts):
        super(MockFunctionComponent, self).__init__(opts)
        self.options = opts.get(PACKAGE_NAME, {})

    @function(mock_constants.MOCK_FN_NAME_ONE)
    def _fn_mock_fn_one(self, event, *args, **kwargs):
        try:
            rp = ResultPayload(mock_constants.MOCK_FN_NAME_ONE, **kwargs)
            yield StatusMessage(u"Mock զ է ը թ ժ ի լ StatusMessage 1")
            yield StatusMessage(u"Mock StatusMessage 2")
            yield FunctionResult(rp.done(True, {"malware": True}))
        except Exception as e:
            yield FunctionError(e)

    @function(mock_constants.MOCK_FN_NAME_EX)
    def _fn_mock_raise_exception(self, event, *args, **kwargs):
        try:
            raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")
        except Exception as e:
            yield FunctionError(e)
