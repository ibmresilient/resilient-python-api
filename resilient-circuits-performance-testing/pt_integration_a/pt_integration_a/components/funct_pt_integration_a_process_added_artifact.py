# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_lib import validate_fields, ResultPayload
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError

PACKAGE_NAME = "pt_integration_a"


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'pt_integration_a_process_added_artifact"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get(PACKAGE_NAME, {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get(PACKAGE_NAME, {})

    @function("pt_integration_a_process_added_artifact")
    def _pt_integration_a_process_added_artifact_function(self, event, *args, **kwargs):
        """Function: Processes the Artifact added. Just returns a success = True"""
        try:

            log = logging.getLogger(__name__)

            # Instansiate ResultPayload
            rp = ResultPayload(PACKAGE_NAME, **kwargs)

            mandatory_fields = [
                "pt_int_artifact_id",
                "pt_int_artifact_description",
                "pt_int_artifact_value"
            ]

            # Get the function inputs:
            fn_inputs = validate_fields(mandatory_fields, kwargs)

            log.info("Processing Artifact: %s", fn_inputs.get("pt_int_artifact_id"))

            results_content = {
                "artifact_description": fn_inputs.get("pt_int_artifact_description")
            }

            results = rp.done(True, results_content)

            log.info("Returning results to post-process script")

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()
