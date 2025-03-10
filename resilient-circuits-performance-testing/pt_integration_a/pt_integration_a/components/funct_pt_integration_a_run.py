# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
import time
from resilient_lib import validate_fields, ResultPayload
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError

PACKAGE_NAME = "pt_integration_a"


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'pt_integration_a_run"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get(PACKAGE_NAME, {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get(PACKAGE_NAME, {})

    @function("pt_integration_a_run")
    def _pt_integration_a_run_function(self, event, *args, **kwargs):
        """Function: Function that:
- Sleeps for delay
- Generates list of num_artifacts
- Returns list of Artifacts to add, remaining number of runs and sample data"""
        try:

            log = logging.getLogger(__name__)

            # Instansiate ResultPayload
            rp = ResultPayload(PACKAGE_NAME, **kwargs)

            mandatory_fields = [
                "pt_int_num_artifacts",
                "pt_int_num_runs",
                "pt_int_delay"
            ]

            # Get the function inputs:
            fn_inputs = validate_fields(mandatory_fields, kwargs)
            num_artifacts = fn_inputs.get("pt_int_num_artifacts")
            num_runs = fn_inputs.get("pt_int_num_runs")
            delay = fn_inputs.get("pt_int_delay")
            sample_data = fn_inputs.get("pt_int_sample_data")
            log.info("Got fn_inputs: %s", fn_inputs)

            if delay:
                log.info("Delay set. Sleeping for %s ms", delay)
                time.sleep(delay / 1000)

            log.info("Generating list of %s Artifacts", num_artifacts)
            artifacts_to_create = []
            for num in range(num_artifacts):
                artifacts_to_create.append({
                    "value": u"PT Artifact {0}".format(num),
                    "description": u"PT Artifact Description"
                })

            remaining_runs = num_runs - 1
            log.info("Remaining runs changed to: %s", remaining_runs)

            results_content = {
                "remaining_runs": remaining_runs,
                "artifacts_to_create": artifacts_to_create,
                "sample_data": sample_data
            }

            results = rp.done(True, results_content)

            log.info("Returning results to post-process script")

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()
