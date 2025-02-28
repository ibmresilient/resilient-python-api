# -*- coding: utf-8 -*

from resilient_circuits import (AppFunctionComponent, LowCodeResult, low_code_function)
from resilient_lib import IntegrationError
from tests import mock_constants

PACKAGE_NAME = mock_constants.MOCK_PACKAGE_NAME
REQUIRED_APP_CONFIGS = mock_constants.MOCK_REQUIRED_APP_CONFIGS


class LowCodeMockComponent(AppFunctionComponent):

    def __init__(self, opts, package_name="", required_app_configs=[]):
        if not package_name:
            package_name = PACKAGE_NAME

        if not required_app_configs:
            required_app_configs = REQUIRED_APP_CONFIGS

        super(LowCodeMockComponent, self).__init__(opts, package_name, required_app_configs)

    @low_code_function("xyz.201.connectors.my_app")
    def _low_code_function_mock_one(self, low_code_request):
        yield self.status_message(u"Mock զ է ը թ ժ ի լ StatusMessage 1")
        yield self.status_message(u"Mock StatusMessage 2")
        yield self.status_message(low_code_request.get("server_url"))

        fn_msg = self.get_fn_msg()

        yield self.status_message(u"Function name: {0}".format(fn_msg.get("function", {}).get("name", "Unknown")))
        yield LowCodeResult({"status_code": 200, "content": {"malware": True}})  # TODO

    @low_code_function(mock_constants.MOCK_LOW_CODE_APP_FN_NAME_EX)
    def _app_function_mock_raise_exception(self, low_code_request):
        raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")
    