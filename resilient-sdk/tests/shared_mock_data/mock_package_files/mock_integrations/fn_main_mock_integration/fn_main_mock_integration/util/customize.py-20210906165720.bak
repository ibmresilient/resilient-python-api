# -*- coding: utf-8 -*-

"""Generate the Resilient customizations required for fn_main_mock_integration"""

import base64
import os
import io
try:
    from resilient import ImportDefinition
except ImportError:
    # Support Apps running on resilient-circuits < v35.0.195
    from resilient_circuits.util import ImportDefinition

RES_FILE = "data/export.res"


def codegen_reload_data():
    """
    Parameters required reload codegen for the fn_main_mock_integration package
    """
    return {
        "package": u"fn_main_mock_integration",
        "message_destinations": [u"fn_main_mock_integration", u"fn_test_two"],
        "functions": [u"a_mock_function_with_no_unicode_characters_in_name", u"mock_function__three", u"mock_function_one", u"mock_function_two"],
        "workflows": [u"mock_workflow_one", u"mock_workflow_two"],
        "actions": [u"Mock Manual Rule", u"Mock Manual Rule Message Destination", u"Mock Script Rule", u"Mock Task Rule", u"Mock: Auto Rule"],
        "incident_fields": [u"mock_field_number", u"mock_field_text", u"mock_field_text_area"],
        "incident_artifact_types": [u"mock_artifact_2", u"mock_artifact_type_one"],
        "datatables": [u"mock_data_table"],
        "automatic_tasks": [u"initial_triage", u"mock_cusom_task__________two", u"mock_custom_task_one"],
        "scripts": [u"Mock Incident Script", u"Mock Script One"],
    }


def customization_data(client=None):
    """
    Returns a Generator of ImportDefinitions (Customizations).
    Install them using `resilient-circuits customize`

    IBM Resilient Platform Version: 41.0.6783

    Contents:
    - Message Destinations:
        - fn_main_mock_integration
        - fn_test_two
    - Functions:
        - a_mock_function_with_no_unicode_characters_in_name
        - mock_function__three
        - mock_function_one
        - mock_function_two
    - Workflows:
        - mock_workflow_one
        - mock_workflow_two
    - Rules:
        - Mock Manual Rule
        - Mock Manual Rule Message Destination
        - Mock Script Rule
        - Mock Task Rule
        - Mock: Auto Rule
        - Run Mock Function One
    - Incident Fields:
        - mock_field_number
        - mock_field_text
        - mock_field_text_area
    - Custom Artifact Types:
        - mock_artifact_2
        - mock_artifact_type_one
    - Data Tables:
        - mock_data_table
    - Phases:
        - Engage
        - Mock Custom Phase One
        - Mock Custom Phase Two
    - Tasks:
        - initial_triage
        - mock_cusom_task__________two
        - mock_custom_task_one
    - Scripts:
        - Mock Incident Script
        - Mock Script One
    """

    res_file = os.path.join(os.path.dirname(__file__), RES_FILE)
    if not os.path.isfile(res_file):
        raise FileNotFoundError("{} not found".format(RES_FILE))

    with io.open(res_file, mode='rt') as f:
        b64_data = base64.b64encode(f.read().encode('utf-8'))
        yield ImportDefinition(b64_data)