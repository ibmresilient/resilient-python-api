# -*- coding: utf-8 -*-
"""Tests using pytest_resilient_circuits"""

from __future__ import print_function
import pytest
from resilient_circuits.util import get_config_data, get_function_definition
from resilient_circuits import SubmitTestFunction, FunctionResult

PACKAGE_NAME = "pt_integration_b"
FUNCTION_NAME = "pt_integration_b_run"

# Read the default configuration-data section from the package
config_data = get_config_data(PACKAGE_NAME)

# Provide a simulation of the Resilient REST API (uncomment to connect to a real appliance)
resilient_mock = "pytest_resilient_circuits.BasicResilientMock"


def call_pt_integration_b_run_function(circuits, function_params, timeout=10):
    # Fire a message to the function
    evt = SubmitTestFunction("pt_integration_b_run", function_params)
    circuits.manager.fire(evt)
    event = circuits.watcher.wait("pt_integration_b_run_result", parent=evt, timeout=timeout)
    assert event
    assert isinstance(event.kwargs["result"], FunctionResult)
    pytest.wait_for(event, "complete", True)
    return event.kwargs["result"].value


class TestPtIntegrationBRun:
    """ Tests for the pt_integration_b_run function"""

    def test_function_definition(self):
        """ Test that the package provides customization_data that defines the function """
        func = get_function_definition(PACKAGE_NAME, FUNCTION_NAME)
        assert func is not None

    @pytest.mark.parametrize("pt_int_num_artifacts, pt_int_num_runs, pt_int_delay, pt_int_sample_data, expected_results", [
        (123, 123, 123, "text", {"value": "xyz"}),
        (123, 123, 123, "text", {"value": "xyz"})
    ])
    def test_success(self, circuits_app, pt_int_num_artifacts, pt_int_num_runs, pt_int_delay, pt_int_sample_data, expected_results):
        """ Test calling with sample values for the parameters """
        function_params = { 
            "pt_int_num_artifacts": pt_int_num_artifacts,
            "pt_int_num_runs": pt_int_num_runs,
            "pt_int_delay": pt_int_delay,
            "pt_int_sample_data": pt_int_sample_data
        }
        results = call_pt_integration_b_run_function(circuits_app, function_params)
        assert(expected_results == results)