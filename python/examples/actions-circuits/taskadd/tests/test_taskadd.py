"""System Integration Tests for AddTaskAction component"""
from __future__ import print_function

import os.path
import json
import pytest
from resilient_circuits.actions_test_component import SubmitTestAction

config_data = """
[task_add]
queue=add_task
"""

@pytest.mark.usefixtures("configure_resilient")
class TestTaskAddIntegrationTests:
    """ System tests for the AddTask component """
    # Appliance Configuration Requirements
    destinations = ("add_task",)
    action_fields = {"task_name": ("text", "Task Name", None),
                     "task_instructions": ("text", "Task Instructions", None),
                     "task_phase": ("select", "Task Phase",
                                    ("Engage", "Detect/Analyze"))}
    manual_actions = {"Add Task": ("add_task", "Incident", ("task_name",
                                                            "task_instructions",
                                                            "task_phase"))}

    def test_success(self, circuits_app, new_incident):
        """ Successful value lookup """
        log_dir = circuits_app.logs

        # Create an incident to test with
        inc = circuits_app.app.action_component.rest_client().post("/incidents", new_incident)
        inc_id = inc.get('id')
        assert inc_id

        # Find Action ID
        actions = circuits_app.app.action_component.rest_client().get("/actions")["entities"]
        action_id = None
        for action in actions:
            if action["name"] == "Add Task":
                action_id = action["id"]
                #print("THE ACTION!!\n%s"% json.dumps(action, indent=2))
                break
        assert action_id

        # Find Action Field task_phase ID
        task_phase_id_values = circuits_app.app.action_component.rest_client().get("/types/actioninvocation/fields/task_phase")["values"]
        task_phase_id = None
        for value_obj in task_phase_id_values:
            print("FOUND TASK PHASE:\n", json.dumps(value_obj))
            if value_obj["label"] == "Engage":
                task_phase_id = value_obj["value"]
                break
        assert task_phase_id

        # Find Phase ID
        phase_id_values = circuits_app.app.action_component.rest_client().get("/types/incident/fields/phase_id")["values"]
        phase_id = None
        for value_obj in phase_id_values:
            print("FOUND PHASE:\n", json.dumps(value_obj))
            if value_obj["label"] == "Engage":
                phase_id = value_obj["value"]
                break
        assert phase_id

        # Post action
        action_data = {"action_id": action_id,
                       "properties": {"task_name": "test task",
                                      "task_instructions": "test instructions",
                                      "task_phase": task_phase_id}
        }
        circuits_app.app.action_component.rest_client().post("/incidents/%d/action_invocations" % inc_id,
                                                             action_data)

        event = circuits_app.watcher.wait("add_task_success", timeout=4, channel='actions.add_task')
        assert event
        pytest.wait_for(event, "complete", True)

        applog = os.path.join(circuits_app.logs.strpath, "app.log")
        with open(applog) as applog_file:
            app_log = applog_file.read()
            assert "Task Posted: {" in app_log

        tasks = circuits_app.app.action_component.rest_client().get("/incidents/%d/tasks" % inc_id)
        found_task = False
        for task in tasks:
            if (task["name"] == "test task"):
                print(json.dumps(task, indent=2))
            if ((task["name"] == "test task") and
                (task["instr_text"] == "test instructions") and
                (task["phase_id"] == phase_id)):
                found_task = True
                break
        assert found_task
