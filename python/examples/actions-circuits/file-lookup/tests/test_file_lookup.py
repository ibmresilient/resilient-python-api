"""Tests for FileLookup component"""

import json
import os.path
import pytest
from circuits_fixture import circuits_app
from resilient_circuits.actions_test_component import SubmitTestAction

config_data = """
[lookup]
queue=filelookup

reference_file=sample.csv
source_field=custom1
dest_field=custom2
"""

def test_one(circuits_app):
    log_dir = circuits_app.logs
    # TODO: replace this hard-coded incident ID with a valid one
    test_msg = {
        "incident": {
            "id": 2233,
            "properties": {
                "custom1": "value1"
            }
        }
    }
    circuits_app.manager.fire(SubmitTestAction(queue="filelookup",
                                         msg_id="test_one",
                                         message=json.dumps(test_msg)))
    assert circuits_app.watcher.wait("_lookup_action_complete")
    applog = os.path.join(circuits_app.logs, "app.log")
    # TODO: inspect log for expected results
    # TODO: Check incident in resilient for expected changes
    
