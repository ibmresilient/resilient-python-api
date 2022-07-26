# -*- coding: utf-8 -*

from resilient_circuits import (AppFunctionComponent, FunctionResult,
                                app_function)
from resilient_lib import IntegrationError
from tests import mock_constants

PACKAGE_NAME = mock_constants.MOCK_PACKAGE_NAME
REQUIRED_APP_CONFIGS = mock_constants.MOCK_REQUIRED_APP_CONFIGS


class AppFunctionMockComponent(AppFunctionComponent):

    def __init__(self, opts, package_name="", required_app_configs=[]):
        if not package_name:
            package_name = PACKAGE_NAME

        if not required_app_configs:
            required_app_configs = REQUIRED_APP_CONFIGS

        super(AppFunctionMockComponent, self).__init__(opts, package_name, required_app_configs)

    @app_function(mock_constants.MOCK_APP_FN_NAME_ONE)
    def _app_function_mock_one(self, fn_inputs):
        yield self.status_message(u"Mock զ է ը թ ժ ի լ StatusMessage 1")
        yield self.status_message(u"Mock StatusMessage 2")
        yield self.status_message(fn_inputs.input_one)

        fn_msg = self.get_fn_msg()

        yield self.status_message(u"Function name: {0}".format(fn_msg.get("function", {}).get("name", "Unknown")))
        yield FunctionResult({"malware": True})

    @app_function(mock_constants.MOCK_APP_FN_NAME_CUSTOM_RESULT)
    def _app_function_mock_custom_result(self, fn_inputs):
        yield FunctionResult({"custom_key": "custom_value"}, custom_results=True)

    @app_function(mock_constants.MOCK_APP_FN_NAME_EX)
    def _app_function_mock_raise_exception(self, fn_inputs):
        raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")
