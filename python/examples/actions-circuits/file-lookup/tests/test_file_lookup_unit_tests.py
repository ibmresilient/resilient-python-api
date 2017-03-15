"""Tests for FileLookup component"""
from __future__ import print_function

import os.path
import json
import pytest
from resilient_circuits.actions_test_component import SubmitTestAction
import file_lookup.components.file_lookup

config_data = file_lookup.components.file_lookup.config_section_data()

resilient_mock = os.path.join("tests", "resilient_filelookup_mock.MyResilientMock")

class TestFileLookupUnitTests:
    """ System tests for the File Lookup component """

    def test_success(self, circuits_app):
        """ Successful value lookup """
        log_dir = circuits_app.logs

        # Load saved Action Message
        saved_data_file = os.path.join("tests",
                                       "responses",
                                       "ActionMessage_Lookup Value_2017-01-30T11-09-38.489498")
        with open(saved_data_file) as data_file:
            msg = json.loads(data_file.read())
            msg["incident"]["properties"]["custom1"] = "value1"
            msg["incident"]["properties"]["custom2"] = ""
        circuits_app.app.action_component.fire(SubmitTestAction(queue="filelookup",
                                                                 msg_id="test_success",
                                                                 message=msg))
        event = circuits_app.watcher.wait("lookup_value_success", timeout=4, channel="actions.filelookup")
        assert event
        pytest.wait_for(event, "complete", True)
        applog = os.path.join(circuits_app.logs.strpath, "app.log")
        with open(applog) as applog_file:
            app_log = applog_file.read()
            assert "READ custom1:value1  STORED custom2:some details about value 1" in app_log
        inc = circuits_app.app.action_component.rest_client().get("/incidents/2314")
        assert inc['properties']['custom2'] == "some details about value 1"

    def test_missing_value(self, circuits_app):
        """ Field custom1 has a value not present in the CSV data """
        log_dir = circuits_app.logs

        # Load saved Action Message
        saved_data_file = os.path.join("tests",
                                       "responses",
                                       "ActionMessage_Lookup Value_2017-01-30T11-09-38.489498")
        with open(saved_data_file) as data_file:
            msg = json.loads(data_file.read())
            msg["incident"]["properties"]["custom1"] = "invalid"
            msg["incident"]["properties"]["custom2"] = None

        circuits_app.app.action_component.fire(SubmitTestAction(queue="filelookup",
                                                                msg_id="test_missing_value",
                                                                message=msg))
        event = circuits_app.watcher.wait("lookup_value_success", timeout=4, channel="actions.filelookup")
        assert event
        pytest.wait_for(event, "complete", True)

        applog = os.path.join(circuits_app.logs.strpath, "app.log")
        with open(applog) as applog_file:
            app_log = applog_file.read()
            assert "No entry for [invalid] in [" in app_log
