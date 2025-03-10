# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError

PACKAGE_NAME = "fn_main_mock_integration"


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'mock_function__three''"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get(PACKAGE_NAME, {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get(PACKAGE_NAME, {})

    @function("mock_function__three")
    def _mock_function__three_function(self, event, *args, **kwargs):
        """Function: mock function ล ฦ ว ศ ษ ส ห ฬ อ three description"""
        try:

            # Get the wf_instance_id of the workflow this Function was called in
            wf_instance_id = event.message["workflow_instance"]["workflow_instance_id"]

            yield StatusMessage("Starting 'mock_function__three' running in workflow '{0}'".format(wf_instance_id))

            # Get the function parameters:
            mock_input_boolean = kwargs.get("mock_input_boolean")  # boolean

            log = logging.getLogger(__name__)
            log.info("mock_input_boolean: %s", mock_input_boolean)

            ##############################################
            # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE #
            ##############################################

            yield StatusMessage("Finished 'mock_function__three' that was running in workflow '{0}'".format(wf_instance_id))

            results = {
                "content": "xyz"
            }

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()
