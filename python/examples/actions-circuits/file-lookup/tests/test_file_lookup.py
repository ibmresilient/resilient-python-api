"""Tests for FileLookup component"""

import os.path
import pytest
from circuits_fixture import circuits_app, new_incident
from resilient_circuits.actions_test_component import SubmitTestAction

config_data = """
[lookup]
queue=filelookup

reference_file=sample.csv
source_field=custom1
dest_field=custom2
"""

@pytest.fixture(scope="module")
def resilient_configured():
    """ Create the custom fields, msg dest, and action if missing """
    # TODO: Configure vanilla Resilient instance
    pass

@pytest.mark.usefixtures("resilient_configured")
class TestFileLookup:
    def test_success(self, circuits_app, new_incident):
        """ Successful value lookup """
        log_dir = circuits_app.logs

        # Create an incident to test with
        inc = circuits_app.app.action_component.rest_client().post("/incidents", new_incident)
        inc_id = inc.get('id')
        assert inc_id
        inc["properties"]["custom1"] = "value1"
        circuits_app.app.action_component.fire(SubmitTestAction(queue="filelookup",
                                                                 msg_id="test_success",
                                                                 message={"incident": inc}))
        assert circuits_app.watcher.wait("_success", timeout=4)
        applog = os.path.join(circuits_app.logs.strpath, "app.log")

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
        test_event = SubmitTestAction(queue="filelookup",
                                      msg_id="test_missing_value",
                                      message={"incident": inc})
        circuits_app.app.fire(test_event)
        assert circuits_app.watcher.wait("_success", timeout=4, channel="actions.filelookup")
        pytest.wait_for(test_event, "complete", True)

        applog = os.path.join(circuits_app.logs.strpath, "app.log")
        with open(applog) as applog_file:
            app_log = applog_file.read()
            assert "No entry for [unexpected] in [sample.csv]" in app_log

        inc = circuits_app.app.action_component.rest_client().get("/incidents/%d" % inc_id)
        assert inc['properties']['custom2'] is None
