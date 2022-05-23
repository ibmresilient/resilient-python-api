# -*- coding: utf-8 -*-

"""AppFunction implementation"""

from resilient_circuits import AppFunctionComponent, app_function, FunctionResult
from resilient_lib import IntegrationError, validate_fields

PACKAGE_NAME = "fn_main_mock_integration"
FN_NAME = "mock_function_one"


class FunctionComponent(AppFunctionComponent):
    """Component that implements function 'mock_function_one'"""

    def __init__(self, opts):
        super(FunctionComponent, self).__init__(opts, PACKAGE_NAME)

    @app_function(FN_NAME)
    def _app_function(self, fn_inputs):
        """
        Function: A mock description of mock_function_one with unicode:  ล ฦ ว ศ ษ ส ห ฬ อ
        Inputs:
            -   fn_inputs.mock_input_date_picker
            -   fn_inputs.mock_input_number
            -   fn_inputs.mock_input_multiselect
            -   fn_inputs.mock_input_text_with_value_string
            -   fn_inputs.mock_input_date_time_picker
            -   fn_inputs.mock_input_select
            -   fn_inputs.mock_input_boolean
            -   fn_inputs.mock_input_text
        """

        yield self.status_message("Starting App Function: '{0}'".format(FN_NAME))

        yield self.status_message("Mock Input Text: '{0}'".format(fn_inputs.mock_input_text))

        # Example validating app_configs
        # validate_fields([
        #     {"name": "api_key", "placeholder": "<your-api-key>"},
        #     {"name": "base_url", "placeholder": "<api-base-url>"}],
        #     self.app_configs)

        # Example validating required fn_inputs
        # validate_fields(["required_input_one", "required_input_two"], fn_inputs)

        # Example accessing optional attribute in fn_inputs (this is similiar for app_configs)
        # optional_input = fn_inputs.optional_input if hasattr(fn_inputs, "optional_input") else "Default Value"

        # Example getting access to self.get_fn_msg()
        # fn_msg = self.get_fn_msg()
        # self.LOG.info("fn_msg: %s", fn_msg)

        # Example interacting with REST API
        # res_client = self.rest_client()
        # function_details = res_client.get("/functions/{0}?handle_format=names".format(FN_NAME))

        # Example raising an exception
        # raise IntegrationError("Example raising custom error")

        ##############################################
        # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE #
        ##############################################

        # Call API implemtation example:
        # params = {
        #     "api_key": self.app_configs.api_key,
        #     "ip_address": fn_inputs.artifact_value
        # }
        #
        # response = self.rc.execute(
        #     method="get",
        #     url=self.app_configs.api_base_url,
        #     params=params
        # )
        #
        # results = response.json()
        #
        # yield self.status_message("Endpoint reached successfully and returning results for App Function: '{0}'".format(FN_NAME))
        #
        # yield FunctionResult(results)
        ##############################################

        yield self.status_message("Finished running App Function: '{0}'".format(FN_NAME))

        # Note this is only used for demo purposes! Put your own key/value pairs here that you want to access on the Platform
        results = {"note_text": fn_inputs.mock_input_text}

        yield FunctionResult(results)
        # yield FunctionResult({}, success=False, reason="Bad call")
