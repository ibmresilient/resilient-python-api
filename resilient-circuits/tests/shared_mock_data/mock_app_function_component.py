# -*- coding: utf-8 -*

from resilient_circuits import ResilientComponent, handler, app_function, StatusMessage, FunctionResult
from resilient_lib import ResultPayload, RequestsCommon, IntegrationError, validate_fields
from tests import mock_constants

PACKAGE_NAME = mock_constants.MOCK_PACKAGE_NAME
APP_FUNCTION_PREFIX = "app_function_mock_"


class AppFunctionMockComponent(ResilientComponent):

    def __init__(self, opts):
        super(AppFunctionMockComponent, self).__init__(opts)
        self.PACKAGE_NAME = PACKAGE_NAME
        self.app_configs = validate_fields([], opts.get(PACKAGE_NAME, {}))
        self.rc = RequestsCommon(opts=self.opts, function_opts=self.app_configs)

    @handler("reload")
    def _reload(self, event, opts):
        self.app_configs = validate_fields([], opts.get(PACKAGE_NAME, {}))

    @app_function(APP_FUNCTION_PREFIX + "one")
    def _app_function_mock_one(self, fn_inputs, **kwargs):

        yield self.status_message("Custom message with unicode լ խ ծ կ հ ձ ղ ճ ")
        yield FunctionResult({"response": "yes"})
