# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to install customizations"""

from __future__ import print_function
import logging
import json
from distutils.util import strtobool
import pkg_resources
import resilient
from resilient import SimpleHTTPException
from resilient_circuits.app import AppArgumentParser
from requests_toolbelt.multipart.encoder import MultipartEncoder

try:
    from builtins import input
except ImportError:
    # Python 2
    from __builtin__ import raw_input as input


LOG = logging.getLogger(__name__)


class Definition(object):
    """A definition that can be loaded by this helper."""
    def __init__(self, value):
        self.value = value


class TypeDefinition(Definition):
    """Definition of a type with fields"""
    pass


class MessageDestinationDefinition(Definition):
    """Definition of a message destination"""
    pass


class ActionDefinition(Definition):
    """Definition of an action"""
    pass


class FunctionDefinition(Definition):
    """Definition of a function"""
    pass


class WorkflowDefinition(Definition):
    """Definition of a workflow"""
    pass


def setdefault(dictionary, defaults):
    """Fill in the blanks"""
    for key in defaults.keys():
        if dictionary.get(key) is None:
            dictionary[key] = defaults[key]


def customize_resilient(args):
    """install customizations to the resilient server"""
    parser = AppArgumentParser(config_file=resilient.get_config_file())
    (opts, extra) = parser.parse_known_args()
    client = resilient.get_client(opts)

    # Call each of the 'customize' entry points to get type definitions,
    # then apply them to the resilient server
    entry_points = pkg_resources.iter_entry_points('resilient.circuits.customize')
    do_customize_resilient(client, entry_points, args.yflag)


def do_customize_resilient(client, entry_points, yflag):
    """install customizations to the resilient server"""
    ep_count = 0
    customizations = Customizations(client, yflag)
    for entry in entry_points:
        ep_count = ep_count + 1
        def_count = 0
        dist = entry.dist

        try:
            func = entry.load()
        except ImportError:
            LOG.exception(u"Customizations for module '%s' cannot be loaded.", repr(dist))
            continue

        # The entrypoint function should be a generator
        # that produces Definitions in the sequence required:
        # usually that means:
        # - fields first,
        # - then message destinations,
        # - then actions, functions, etc

        LOG.info(u"Module '%s'", dist)
        definitions = func()
        for definition in definitions:
            def_count = def_count + 1
            if not isinstance(definition, Definition):
                pass
            try:
                if isinstance(definition, TypeDefinition):
                    customizations.load_types(definition)
                elif isinstance(definition, MessageDestinationDefinition):
                    customizations.load_message_destinations(definition)
                elif isinstance(definition, ActionDefinition):
                    customizations.load_actions(definition)
                elif isinstance(definition, FunctionDefinition):
                    customizations.load_functions(definition)
                elif isinstance(definition, WorkflowDefinition):
                    customizations.load_workflows(definition)
                else:
                    LOG.error(u"Not implemented: %s", type(definition))
            except SimpleHTTPException:
                LOG.error(u"Failed, %s", customizations.doing)
                raise
        LOG.info(u"Module '%s' applied %s customizations", dist, def_count)

    if ep_count == 0:
        LOG.info(u"No customizations are defined by installed packages.")


class Customizations(object):
    """Main class for managing customizations"""

    def __init__(self, client, yflag):
        super(Customizations, self).__init__()

        self.client = client
        self.prompt = not yflag
        self.doing = ""

    def confirm(self, activity):
        """Prompt, if self.prompt"""
        yes = True
        self.doing = u"creating {}".format(activity)
        if self.prompt:
            yes = False
            inp = input(u"OK to create {}? (y/n):".format(activity))
            try:
                yes = strtobool(inp)
            except ValueError:
                pass
        if not yes:
            print(u"Not creating {}".format(activity))
        return yes

    def load_message_destinations(self, definition):
        """Load one or more message destinations"""
        new_destinations = definition.value
        if not isinstance(new_destinations, (tuple, list)):
            new_destinations = [new_destinations]
        uri = "/message_destinations"
        existing_destinations = self.client.get(uri)["entities"]
        existing_destination_names = [dest["programmatic_name"] for dest in existing_destinations]
        existing_destination_dnames = [dest["name"] for dest in existing_destinations]
        for dest in new_destinations:
            if dest["programmatic_name"] in existing_destination_names:
                LOG.info(u"Message destination exists: %s", dest["programmatic_name"])
            elif dest["name"] in existing_destination_dnames:
                LOG.info(u"Message destination exists: %s", dest["name"])
            else:
                setdefault(dest, {
                    "name": dest["programmatic_name"],
                    "expect_ack": True,
                    "destination_type": 0
                })
                # Set this API account to be a user of the message destination
                dest["users"] = [self.client.user_id]
                # Don't re-use id
                if "id" in dest:
                    dest.remove("id")
                # Create the message destination
                if self.confirm(u"message destination '{}'".format(dest["programmatic_name"])):
                    self.client.post(uri, dest)
                    LOG.info(u"Message destination created: %s ('%s')", dest["programmatic_name"], dest["name"])

    def load_types(self, definition):
        """Load a type definition (action fields, incident fields, data table, etc)"""
        new_types = definition.value
        type_name = new_types["type_name"]
        new_fields = new_types["fields"]
        uri = "/types/{0}".format(type_name)
        try:
            existing_types = self.client.get(uri)
        except SimpleHTTPException:
            # There is no type (data-table) of this name.
            # So let's create it.
            uri = "/types"
            if self.confirm("type '{}'".format(new_types["type_name"])):
                self.client.post(uri, new_types)
                LOG.info(u"Type created: %s ('%s')", new_types["type_name"], new_types["display_name"])
            return
        existing_fields = existing_types["fields"]
        for fieldname in new_fields:
            field = new_fields[fieldname]
            if fieldname in existing_fields.keys():
                # Merge the field values and update
                LOG.info(u"Field exists: %s", fieldname)
                new_values = field.get("values", [])
                # Remove any ids from the new stuff
                for value in new_values:
                    if "id" in value:
                        value.remove("id")
                new_ids = [value["label"] for value in new_values]
                old_values = existing_fields[fieldname].get("values", [])
                old_ids = [value["label"] for value in old_values]
                # If there are any old values that are not in the new values (by id),
                # add them to the end of the list, and mark as no longer enabled.
                for old_id in set(old_ids) - set(new_ids):
                    old_value = [value for value in old_values if value["label"] == old_id][0]
                    if old_value.get("enabled", True):
                        old_value["enabled"] = False
                        new_values.append(old_value)
                        new_ids.append(old_id)
                # If there are any old values that are in the new values (by label),
                # set their id.
                for value in new_values:
                    label = value["label"]
                    old_values = [value for value in old_values if value["label"] == label]
                    if len(old_values) > 0:
                        value["value"] = old_values[0]["value"]
                    elif "value" in value:
                        value.pop("value", None)
                if new_ids != old_ids:
                    # Post the update
                    LOG.debug(json.dumps(field, indent=2))
                    existing_id = existing_fields[fieldname]["id"]
                    if self.confirm("values for field '{}'".format(fieldname)):
                        uri = "/types/{0}/fields/{1}".format(type_name, existing_id)
                        self.client.put(uri, field)
                        LOG.info(u"Field updated: %s ('%s')", fieldname, field["text"])
            else:
                # Don't re-use id
                if "id" in field:
                    field.remove("id")
                # Create the field
                fields_uri = "/types/{0}/fields".format(type_name)
                if self.confirm("field '{}'".format(fieldname)):
                    self.client.post(fields_uri, field)
                    LOG.info(u"Field created: %s ('%s')", fieldname, field["text"])

    def load_actions(self, definition):
        """Load custom actions"""
        new_actions = definition.value
        if not isinstance(new_actions, (tuple, list)):
            new_actions = [new_actions]
        uri = "/actions"
        existing_actions = self.client.get(uri)["entities"]
        existing_action_names = [action["name"] for action in existing_actions]
        for action in new_actions:
            if action["name"] in existing_action_names:
                LOG.info(u"Action exists: %s", action["name"])
            else:
                # Don't re-use id
                if "id" in action:
                    action.pop("id", None)
                # Create the action
                if self.confirm("action '{}'".format(action["name"])):
                    self.client.post(uri, action)
                    LOG.info(u"Action created: %s", action["name"])

    def load_functions(self, definition):
        """Load custom functions"""
        new_functions = definition.value
        if not isinstance(new_functions, (tuple, list)):
            new_functions = [new_functions]
        uri = "/functions"
        existing_functions = self.client.get(uri)["entities"]
        existing_function_names = [function["name"] for function in existing_functions]
        for function in new_functions:
            if function["name"] in existing_function_names:
                LOG.info(u"Function exists: %s", function["name"])
            else:
                setdefault(function, {
                    "display_name": function["name"]
                })
                # Don't re-use id
                if "id" in function:
                    function.pop("id", None)
                # Create the function
                if self.confirm("function '{}'".format(function["name"])):
                    self.client.post(uri, function)
                    LOG.info(u"Function created: %s", function["name"])

    def load_workflows(self, definition):
        """Load workflows"""
        new_workflows = definition.value
        if not isinstance(new_workflows, (tuple, list)):
            new_workflows = [new_workflows]
        uri = "/workflows"
        existing_workflows = self.client.get(uri)["entities"]
        existing_workflow_names = [workflow["programmatic_name"] for workflow in existing_workflows]
        for workflow in new_workflows:
            if workflow["programmatic_name"] in existing_workflow_names:
                LOG.info(u"Workflow exists: %s", workflow["programmatic_name"])
            else:
                # Create the workflow
                if self.confirm("workflow '{}'".format(workflow["programmatic_name"])):
                    # Post multi-part MIME with the workflow XML as a mime part
                    url = u"{0}/rest/orgs/{1}{2}".format(self.client.base_url, self.client.org_id, uri)
                    multipart_data = {
                        "file": workflow["content"]["xml"],
                        "object_type": workflow.get("object_type", 0)
                    }
                    encoder = MultipartEncoder(fields=multipart_data)
                    headers = self.client.make_headers(None,
                                                       additional_headers={'content-type': encoder.content_type})
                    response = self.client._execute_request(self.client.session.post,
                                                            url,
                                                            data=encoder,
                                                            proxies=self.client.proxies,
                                                            cookies=self.client.cookies,
                                                            headers=headers,
                                                            verify=self.client.verify)
                    if response.status_code != 200:
                        raise SimpleHTTPException(response)
                    LOG.info(u"Workflow created: %s", workflow["programmatic_name"])
