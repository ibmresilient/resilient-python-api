# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError

PACKAGE_NAME = "fn_main_mock_integration"


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'a_mock_function_with_no_unicode_characters_in_name''"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get(PACKAGE_NAME, {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get(PACKAGE_NAME, {})

    @function("a_mock_function_with_no_unicode_characters_in_name")
    def _a_mock_function_with_no_unicode_characters_in_name_function(self, event, *args, **kwargs):
        """Function: A mock description of 'A Mock Function with No Unicode Characters in Name' with unicode:  ล ฦ ว ศ ษ ส ห ฬ อ"""
        try:

            # Get the wf_instance_id of the workflow this Function was called in
            wf_instance_id = event.message["workflow_instance"]["workflow_instance_id"]

            yield StatusMessage("Starting 'a_mock_function_with_no_unicode_characters_in_name' running in workflow '{0}'".format(wf_instance_id))

            # Get the function parameters:
            mock_input_text = kwargs.get("mock_input_text")  # text

            log = logging.getLogger(__name__)
            log.info("mock_input_text: %s", mock_input_text)

            ##############################################
            # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE #
            ##############################################

            yield StatusMessage("Finished 'a_mock_function_with_no_unicode_characters_in_name' that was running in workflow '{0}'".format(wf_instance_id))

            results = {
                "content": "xyz"
            }

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()
