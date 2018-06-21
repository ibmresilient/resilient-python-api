# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'utilities_resilient_search"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get("fn_utilities", {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get("fn_utilities", {})

    @function("utilities_resilient_search")
    def _utilities_resilient_search_function(self, event, *args, **kwargs):
        """Function: Searches Resilient for incident data.
NOTE: The results may include data from incidents that the current user cannot access.  Use with caution, to avoid information disclosure."""
        try:
            # Get the function parameters:
            resilient_search_template = self.get_textarea_param(kwargs.get("resilient_search_template"))  # textarea
            resilient_search_query = kwargs.get("resilient_search_query")  # text

            log = logging.getLogger(__name__)
            log.info("resilient_search_template: %s", resilient_search_template)
            log.info("resilient_search_query: %s", resilient_search_query)

            # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE
            #  yield StatusMessage("starting...")
            #  yield StatusMessage("done...")

            results = {
                "value": "xyz"
            }

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()