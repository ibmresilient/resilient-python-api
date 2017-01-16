"""Pytest Fixture for Testing Resilient Circuits Components"""

import os
import sys
import time
import calendar
import pytest
from circuits import Event
from conftest import manager, watcher
import co3

class ResilientCircuits:
    def __init__(self, tmpdir_factory, manager, watcher, request):
        resilient_config_data = """
[resilient]
logfile = app.log
loglevel = DEBUG
cafile = false
email = kchurch@us.ibm.com
stomp_port = 65001
host = 192.168.56.101
org = Test
componentsdir = components
password = Pass4Admin
no_prompt_password = True
port = 443
test_actions = True
"""
        self.config_file = tmpdir_factory.mktemp('data').join("apptest.config")
        self.logs = tmpdir_factory.mktemp("logs")
        config_data = getattr(request.module, "config_data", "")
        self.config_file.write(resilient_config_data)
        self.config_file.write("log_http_responses = %s\n" % self.logs, mode='a')
        self.config_file.write("logdir = %s\n" % self.logs, mode='a')
        self.config_file.write(config_data, mode='a')
        os.environ["APP_CONFIG_FILE"] = self.config_file.strpath
        from resilient_circuits.app import App

        self.manager = manager
        self.watcher = watcher

        # Remove the pytest commandline arguments so they don't break ArgParse in co3
        sys.argv=sys.argv[0:1]

        self.app = App().register(manager)
        assert watcher.wait("registered")
        pytest.wait_for(manager, "_running", True)
        assert watcher.wait("load_all_success", timeout=10)
        def finalizer():
            self.app.unregister()

        request.addfinalizer(finalizer)


@pytest.fixture(scope="class")
def circuits_app(tmpdir_factory, manager, watcher, request):
    return ResilientCircuits(tmpdir_factory, manager, watcher, request)

@pytest.fixture(scope="function")
def new_incident(circuits_app):
    """ Create but don't post a minimally populated incident for testing """
    client = circuits_app.app.action_component.rest_client()
    incident = {}
    fields = client.get('/types/incident/fields')
    for field_def  in fields:
        if field_def.get('required', '') != 'always':
            continue
        fieldname = field_def['name']
        field_type = field_def['input_type']

        if field_def['values']:
            # Just use whatever the first valid value is
            value = field_def['values'][0]["value"]
        elif field_type == "boolean":
            value = True
        elif field_type in ("text", "textarea"):
            value = "test"
        elif field_type == "datetimepicker":
            value = int(calendar.timegm(time.gmtime())) *1000
        elif field_type == "number":
            value = 1

        if field_def['prefix']:
            incident[field_def['prefix']][fieldname] = value
        else:
            incident[fieldname] = value
    return incident
