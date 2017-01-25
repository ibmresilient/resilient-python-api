"""Pytest Fixture for Testing Resilient Circuits Components"""

import os
import sys
import time
import calendar
import json
import traceback
import pytest
from circuits import Event
from conftest import manager, watcher
import co3
from co3.co3 import SimpleHTTPException, _raise_if_error

#LOG = logging.getLogger(__name__)
#LOG.addHandler(logging.StreamHandler())
#LOG.setLevel(logging.DEBUG)

class ConfiguredAppliance:
    """ configure resilient org with specs from the test module """
    def __init__(self, request):
        # TODO: Add support for phases, tasks, incident types
        host = os.environ.get("RESILIENT_APPLIANCE", "192.168.56.101")
        url = "https://%s:443" % host
        org = os.environ.get("RESILIENT_ORG", "No Actions")
        user = os.environ.get("RESILIENT_USER", "kchurch@us.ibm.com")
        password = os.environ.get("RESILIENT_PASSWORD", "Pass4Admin")

        # Connect to Resilient
        self.client = co3.SimpleClient(org_name=org, base_url=url, verify=False)
        session = self.client.connect(user, password)

        # Retrieve constants from appliance
        constants = self._get_constants()["actions_framework"]
        # Invert the dictionaries so they are {"name": id,...}
        action_object_types = {value:int(key) for key, value in constants["action_object_types"].iteritems()}
        action_types = {value:int(key) for key, value in constants["action_types"].iteritems()}
        destination_types = {value:int(key) for key, value in constants["destination_types"].iteritems()}

        # Delete all existing configuration items
        self._clear_org()

        # Create all required configuration items for this class of tests
        action_fields = getattr(request.cls, "action_fields", None)
        if action_fields:
            for field_name, info in action_fields.iteritems():
                success = self._create_action_field(field_name,
                                                    info[0], info[1])
                assert success
        custom_fields = getattr(request.cls, "custom_fields", None)
        if custom_fields:
            for field_name, info in custom_fields.iteritems():
                success = self._create_custom_field(field_name,
                                                    info[0], info[1])
                assert success
        destinations = getattr(request.cls, "destinations", None)
        if destinations:
            for queue_name in destinations:
                success = self._create_destination(queue_name,
                                                   destination_types["Queue"])
                assert success

        destinations = self.client.get("/message_destinations")["entities"]
        destinations = {dest["programmatic_name"]:int(dest["id"]) for dest in destinations}
        manual_actions = getattr(request.cls, "manual_actions", None)
        if manual_actions:
            for action_name, info in manual_actions.iteritems():
                success = self._create_manual_action(action_name,
                                                     destinations[info[0]],
                                                     action_object_types[info[1]],
                                                     action_types["Manual"],
                                                     info[2])
                assert success
        automatic_actions = getattr(request.cls, "automatic_actions", None)
        if automatic_actions:
            for action_name, info in automatic_actions.iteritems():
                success = self._create_automatic_action(action_name,
                                                        destinations[info[0]],
                                                        action_object_types[info[1]],
                                                        action_types["Automatic"],
                                                        info[2])
                assert success
    # end __init__

    def _clear_org(self):
        """ Delete all existing destinations, actions, fields, etc from org """

        actions = self.client.get("/actions")["entities"]
        if actions:
            for action in actions:
                self.client.delete("/actions/%s" % action['id'])

        destinations = self.client.get("/message_destinations")["entities"]
        if destinations:
            for destination in destinations:
                print "/message_destinations/%s" % destination['id']
                self.client.delete("/message_destinations/%s" % destination['id'])

        fields = self.client.get("/types/actioninvocation/fields")
        if fields:
            for field in fields:
                self.client.delete("/types/actioninvocation/fields/%s" % field['id'])

        fields = self.client.get("/types/incident/fields")
        if fields:
            fields = [field for field in fields if field['prefix'] == "properties"]
            for field in fields:
                print "URL IS /types/incident/fields/%s" % field['id']
                self.client.delete("/types/incident/fields/%s" % field['id'])
    # end _clear_org

    def _get_constants(self):
        """ get data from /rest/const """
        url = "{0}/rest/const".format(self.client.base_url)
        response = self.client._execute_request(self.client.session.get,
                                                url,
                                                proxies=self.client.proxies,
                                                cookies=self.client.cookies,
                                                headers=self.client._SimpleClient__make_headers())
        _raise_if_error(response)
        return json.loads(response.text)
    # end _get_constants

    def _create_action_field(self, programmatic_name, field_type, display_name):
        """ Create action field in resilient """
        endpoint = "/types/actioninvocation/fields"
        action_field = {"text": display_name,
                        "required": "always",
                        "tooltip": display_name,
                        "blank_option": False,
                        "input_type": field_type,
                        "name": programmatic_name}
        try:
            field_def = self.client.post(endpoint, action_field)
            if not field_def:
                return False
            #LOG.error("Failed to create action field %s" % programmatic_name)
            print "Failed to create action field %s" % programmatic_name
        except Exception, e:
            # LOG.error("Failed to create action field %s" % programmatic_name)
            print "Failed to create action field %s" % programmatic_name
            traceback.print_exc()
            return False
        return True
    # end _create_action_field

    def _create_custom_field(self, programmatic_name, field_type, display_name):
        """ Create custom field in resilient """
        endpoint = "/types/incident/fields"
        custom_field = {"text": display_name,
                        "input_type": field_type,
                        "name": programmatic_name}
        response = self.client.post(endpoint, custom_field)
        return True if response else False
    # end _create_custom_field

    def _create_destination(self, name, destination_type):
        """ Create destination queue """
        user_id = self.client.user_id
        endpoint = "/message_destinations"
        destination_obj = {"name": name,
                           "expect_ack": True,
                           "destination_type": destination_type,
                           "programmatic_name": name,
                           "users": [user_id]}
        try:
            destination = self.client.post(endpoint, destination_obj)
            if not destination:
                #LOG.error("Failed to create destination %s", name)
                print "Failed to create destination %s" % name
                return False
        except Exception, e:
            #LOG.error("Failed to create destination %s", name)
            print "Failed to create destination %s" % name
            traceback.print_exc()
            return False
        return True
    # end _create_destination

    def _create_manual_action(self, action_name, destination_id, object_type_id, action_type_id, fields):
        """ Create and configure a manual action """
        endpoint = "/actions"
        action = {"name": action_name,
                  "type": action_type_id,
                  "object_type": object_type_id,
                  "message_destinations": [destination_id],
                  "view_items": [{"field_type": "actioninvocation",
                                  "element": "field",
                                  "content": fieldname} for fieldname in fields]
        }
        try:
            action_obj = self.client.post(endpoint, action)
            if not action_obj:
                #LOG.error("Failed to create action %s" % action_name)
                print "Failed to create action %s" % action_name
                return False
        except Exception, e:
            #LOG.error("Failed to create action %s" % action_name)
            print "Failed to create action %s" % action_name
            traceback.print_exc()
            return False

        return True
    # end _create_manual_action

    def _create_automatic_action(self, action_name, destination_id, object_type_id, action_type_id, conditions):
        """ Create and configure automatic action """
        endpoint = "/actions"
        action = {"name": action_name,
                  "type": action_type_id,
                  "object_type": object_type_id,
                  "message_destinations": [destination_id]
        }
        if conditions:
            action["conditions"] = conditions

        try:
            action_obj = self.client.post(endpoint, action)
            if not action_obj:
                #LOG.error("Failed to create action %s" % action_name)
                print "Failed to create action %s" % action_name
                return False
        except Exception, e:
            #LOG.error("Failed to create action %s" % action_name)
            print "Failed to create action %s" % action_name
            traceback.print_exc()
            return False

        return True
    # end _create_automatic_action

# end ConfiguredAppliance

class ResilientCircuits:
    def __init__(self, tmpdir_factory, manager, watcher, request):
        resilient_config_data = """
[resilient]
logfile = app.log
loglevel = DEBUG
cafile = false
stomp_port = 65001
componentsdir = components
no_prompt_password = True
port = 443
test_actions = True
"""
        os.chdir(getattr(request.module, "base_dir", "."))
        self.config_file = tmpdir_factory.mktemp('data').join("apptest.config")
        print self.config_file.strpath
        self.logs = tmpdir_factory.mktemp("logs")
        config_data = getattr(request.module, "config_data", "")
        self.config_file.write(resilient_config_data)
        host = os.environ.get("RESILIENT_APPLIANCE", "192.168.56.101")
        self.config_file.write("host = %s\n" % host, mode='a')
        org = os.environ.get("RESILIENT_ORG", "Test")
        self.config_file.write("org = %s\n" % org, mode='a')
        user = os.environ.get("RESILIENT_USER", "kchurch@us.ibm.com")
        self.config_file.write("email = %s\n" % user, mode='a')
        password = os.environ.get("RESILIENT_PASSWORD", "Pass4Admin")
        self.config_file.write("password = %s\n" % password, mode='a')
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
    # end __init__
# end ResilientCircuits

@pytest.fixture(scope="class")
def circuits_app(tmpdir_factory, manager, watcher, request):
    return ResilientCircuits(tmpdir_factory, manager, watcher, request)

@pytest.fixture(scope="class")
def configure_resilient(request):
    """ Create necessary destinations, actions, fields, etc in Resilient """
    return ConfiguredAppliance(request)
# end configure_resilient

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
# end new_incident
