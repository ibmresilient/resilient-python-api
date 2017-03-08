"""System Integration Tests for FileLookup component"""
from __future__ import print_function

import os.path
import pytest
import file_lookup.components.file_lookup

config_data = file_lookup.components.file_lookup.config_section_data()

@pytest.mark.usefixtures("configure_resilient")
class TestFileLookupIntegrationTests:
    """ System tests for the File Lookup component """
    # Appliance Configuration Requirements
    destinations = ("filelookup",)
    action_fields = None
    custom_fields = {"custom1": ("text", "Custom 1", None),
                     "custom2": ("text", "Custom 2", None)}
    automatic_actions = {"Lookup Value": ("filelookup", "Incident", ({u"type": None,
                                                                      u"field_name": u"incident.properties.custom1",
                                                                      u"method": u"changed"},))}
    manual_actions = None

    def test_success(self, circuits_app, new_incident):
        """ Successful value lookup """
        log_dir = circuits_app.logs

        # Create an incident to test with
        inc = circuits_app.app.action_component.rest_client().post("/incidents", new_incident)
        inc_id = inc.get('id')
        assert inc_id
        inc["properties"]["custom1"] = "value1"
        updated_inc = circuits_app.app.action_component.rest_client().put("/incidents/%d" % inc_id, inc)
        event = circuits_app.watcher.wait("lookup_value_success", timeout=4, channel='actions.filelookup')
        assert event
        pytest.wait_for(event, "complete", True)

        applog = os.path.join(circuits_app.logs.strpath, "app.log")
        with open(applog) as applog_file:
            app_log = applog_file.read()
            assert "READ custom1:value1  STORED custom2:some details about value 1" in app_log

        inc = circuits_app.app.action_component.rest_client().get("/incidents/%d" % inc_id)
        assert inc['properties']['custom2'] == "some details about value 1"

    def test_missing_value(self, circuits_app, new_incident):
        """ Field custom1 has a value not present in the CSV data """
        log_dir = circuits_app.logs

        # Create an incident to test with
        inc = circuits_app.app.action_component.rest_client().post("/incidents", new_incident)
        inc_id = inc.get('id')
        assert inc_id
        inc["properties"]["custom1"] = "unexpected"
        updated_inc = circuits_app.app.action_component.rest_client().put("/incidents/%d" % inc_id, inc)
        event = circuits_app.watcher.wait("lookup_value_success", timeout=4, channel="actions.filelookup")
        assert event
        pytest.wait_for(event, "complete", True)

        applog = os.path.join(circuits_app.logs.strpath, "app.log")
        with open(applog) as applog_file:
            app_log = applog_file.read()
            assert "No entry for [unexpected] in [" in app_log

        inc = circuits_app.app.action_component.rest_client().get("/incidents/%d" % inc_id)
        assert inc['properties']['custom2'] is None
