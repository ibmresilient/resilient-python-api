# -*- coding: utf-8 -*

from resilient_circuits import ResilientComponent, handler, app_function, StatusMessage, FunctionResult
from resilient_lib import ResultPayload, RequestsCommon, IntegrationError, validate_fields
from tests import mock_constants

PACKAGE_NAME = mock_constants.MOCK_PACKAGE_NAME


class AppFunctionMockComponent(ResilientComponent):

    def __init__(self, opts):
        super(AppFunctionMockComponent, self).__init__(opts)
        self.PACKAGE_NAME = PACKAGE_NAME
        self.app_configs = validate_fields([], opts.get(PACKAGE_NAME, {}))
        self.rc = RequestsCommon(opts=self.opts, function_opts=self.app_configs)

    @handler("reload")
    def _reload(self, event, opts):
        self.app_configs = validate_fields([], opts.get(PACKAGE_NAME, {}))

    @app_function(mock_constants.MOCK_APP_FN_NAME_ONE)
    def _app_function_mock_one(self, fn_inputs, **kwargs):
        yield self.status_message(u"Mock զ է ը թ ժ ի լ StatusMessage 1")
        yield self.status_message(u"Mock StatusMessage 2")
        yield self.status_message(fn_inputs.input_one)
        yield FunctionResult({"malware": True})

    @app_function(mock_constants.MOCK_APP_FN_NAME_EX)
    def _app_function_mock_raise_exception(self, fn_inputs, **kwargs):
        raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")
