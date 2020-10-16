# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError

PACKAGE_NAME = "fn_main_mock_integration"


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'mock_function_one''"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get(PACKAGE_NAME, {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get(PACKAGE_NAME, {})

    @function("mock_function_one")
    def _mock_function_one_function(self, event, *args, **kwargs):
        """Function: A mock description of mock_function_one with unicode:  ล ฦ ว ศ ษ ส ห ฬ อ"""
        try:

            # Get the wf_instance_id of the workflow this Function was called in
            wf_instance_id = event.message["workflow_instance"]["workflow_instance_id"]

            yield StatusMessage("Starting 'mock_function_one' running in workflow '{0}'".format(wf_instance_id))

            # Get the function parameters:
            mock_input_number = kwargs.get("mock_input_number")  # number
            mock_input_boolean = kwargs.get("mock_input_boolean")  # boolean
            mock_input_select = self.get_select_param(kwargs.get("mock_input_select"))  # select, values: "select one", "select two", "select  ล ฦ ว ศ ษ ส ห ฬ อ"
            mock_input_date_time_picker = kwargs.get("mock_input_date_time_picker")  # datetimepicker
            mock_input_date_picker = kwargs.get("mock_input_date_picker")  # datepicker
            mock_input_text_with_value_string = self.get_textarea_param(kwargs.get("mock_input_text_with_value_string"))  # textarea
            mock_input_multiselect = self.get_select_param(kwargs.get("mock_input_multiselect"))  # multiselect, values: "value one", "value two", "value  ล ฦ ว ศ ษ ส ห ฬ อ"
            mock_input_text = kwargs.get("mock_input_text")  # text

            log = logging.getLogger(__name__)
            log.info("mock_input_number: %s", mock_input_number)
            log.info("mock_input_boolean: %s", mock_input_boolean)
            log.info("mock_input_select: %s", mock_input_select)
            log.info("mock_input_date_time_picker: %s", mock_input_date_time_picker)
            log.info("mock_input_date_picker: %s", mock_input_date_picker)
            log.info("mock_input_text_with_value_string: %s", mock_input_text_with_value_string)
            log.info("mock_input_multiselect: %s", mock_input_multiselect)
            log.info("mock_input_text: %s", mock_input_text)

            ##############################################
            # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE #
            ##############################################

            yield StatusMessage("Finished 'mock_function_one' that was running in workflow '{0}'".format(wf_instance_id))

            results = {
                "content": "xyz"
            }

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()
