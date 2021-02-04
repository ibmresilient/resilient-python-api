# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to import customizations"""

from __future__ import print_function
import logging
import json
import base64
from distutils.util import strtobool
import pkg_resources
import resilient
from resilient_circuits.app import AppArgumentParser
from resilient_circuits import helpers
from resilient import (SimpleHTTPException,
                       Definition,
                       TypeDefinition,
                       MessageDestinationDefinition,
                       FunctionDefinition,
                       ActionDefinition,
                       ImportDefinition)

try:
    from builtins import input
except ImportError:
    # Python 2
    from __builtin__ import raw_input as input


LOG = logging.getLogger(__name__)


def get_customization_definitions(package):
    """Read the default configuration-data section from the given package"""
    data = None
    try:
        dist = pkg_resources.get_distribution(package)
        entries = pkg_resources.get_entry_map(dist, "resilient.circuits.customize")
        if entries:
            for entry in iter(entries):
                func = entries[entry].load()
                data = func(client=None)
    except pkg_resources.DistributionNotFound:
        pass
    return data or []


def get_function_definition(package, function_name):
    """Find a function in the default configuration-data section from the given package"""
    for definition in get_customization_definitions(package):
        if isinstance(definition, FunctionDefinition):
            new_functions = definition.value
            if not isinstance(new_functions, (tuple, list)):
                new_functions = [new_functions]
            for func in new_functions:
                if func["name"] == function_name:
                    # Found it!  Success.
                    return func
        elif isinstance(definition, ImportDefinition):
            import_data = json.loads(base64.b64decode(definition.value).decode("utf-8"))
            for func in import_data.get("functions"):
                if func["name"] == function_name:
                    # Found it!  Success.
                    return func




def setdefault(dictionary, defaults):
    """Fill in the blanks"""
    for key in defaults.keys():
        if dictionary.get(key) is None:
            dictionary[key] = defaults[key]


def type_displayname(typename):
    """A readable displayname for a type

        >>> type_displayname('__function')
        'Function'
        >>> type_displayname('my_data_table')
        'MyDataTable'
    """
    return typename.title().replace("_", "")


def customize_resilient(args):
    """import customizations to the resilient server"""
    parser = AppArgumentParser(config_file=resilient.get_config_file())
    (opts, extra) = parser.parse_known_args()
    client = resilient.get_client(opts)

    # Call each of the 'customize' entry points to get type definitions,
    # then apply them to the resilient server
    entry_points = pkg_resources.iter_entry_points('resilient.circuits.customize')
    do_customize_resilient(client, entry_points, args.yflag, args.install_list)


def do_customize_resilient(client, entry_points, yflag, install_list):
    """import customizations to the resilient server"""
    ep_count = 0
    customizations = Customizations(client, yflag)
    for entry in entry_points:
        ep_count = ep_count + 1
        def_count = 0
        dist = entry.dist
        dist_str = entry.dist.project_name

        if install_list is None or dist_str in install_list:
            if install_list is not None:
                install_list.remove(dist_str)
            try:
                func = entry.load()
            except ImportError:
                LOG.exception(u"Customizations for package '%s' cannot be loaded.", repr(dist))
                continue

            # The entrypoint function should be a generator
            # that produces Definitions in the sequence required:
            # usually that means:
            # - fields first,
            # - then message destinations,
            # - then actions, functions, etc

            LOG.info(u"Package '%s':", dist)
            definitions = func(client=client)
            for definition in definitions:
                def_count = def_count + 1
                if not isinstance(definition, Definition):
                    pass
                try:
                    if isinstance(definition, ImportDefinition):
                        customizations.load_import(definition, dist)
                    elif isinstance(definition, TypeDefinition):
                        customizations.load_types(definition)
                    elif isinstance(definition, MessageDestinationDefinition):
                        customizations.load_message_destinations(definition)
                    elif isinstance(definition, ActionDefinition):
                        customizations.load_actions(definition)
                    elif isinstance(definition, FunctionDefinition):
                        customizations.load_functions(definition)
                    else:
                        LOG.error(u"Not implemented: %s", type(definition))
                except SimpleHTTPException:
                    LOG.error(u"Failed, %s", customizations.doing)
                    raise
            LOG.info(u"Package '%s' done.", dist)

    if install_list is not None and len(install_list) > 0:
        LOG.warning("%s not found. Check package name(s)", install_list)

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
        self.doing = u"importing {}".format(activity)
        if self.prompt:
            yes = False
            inp = input(u"    OK to import {}? (y/n):".format(activity))
            try:
                yes = strtobool(inp)
            except ValueError:
                pass
        if not yes:
            print(u"    Not importing {}".format(activity))
        return yes

    def load_import(self, definition, dist):
        """Load an importable block of customizations"""
        import_data = json.loads(base64.b64decode(definition.value).decode("utf-8"))
        import_data = helpers.remove_tag(import_data)
        LOG.debug(json.dumps(import_data, indent=2))
        uri = "/configurations/imports"
        done = False
        if self.confirm(u"customizations from '{}'".format(dist)):
            result = self.client.post(uri, import_data)
            import_id = result["id"]
            LOG.debug(result)
            for message in result.get("messages", []):
                LOG.info(u"    %s: %s", message["type"], message["text"])
            if result["status"] == "PENDING":
                if self.confirm(u""):
                    result["status"] = "ACCEPTED"
                    done = True
                else:
                    result["status"] = "REJECTED"
                uri = "/configurations/imports/{}".format(import_id)
                self.client.put(uri, result)

        if done:
            # For each message destination in the import:
            # Set this API account to be a user of the message destination
            # (otherwise the function won't be able to connect!)

            def update_user(dest):
                # Callback for get/put to update the user list
                if self.client.user_id is None:
                    # We are using API key
                    if self.client.api_key_handle not in dest["api_keys"]:
                        LOG.info(u"    Adding api key to message destination {}".format(dest["programmatic_name"]))
                        dest["api_keys"].append(self.client.api_key_handle)
                else:
                    # We are using user/password to authenticate
                    if self.client.user_id not in dest["users"]:
                        LOG.info(u"    Adding user to message destination {}".format(dest["programmatic_name"]))
                        dest["users"].append(self.client.user_id)
                return dest

            uri = "/message_destinations"
            all_destinations = dict((dest["programmatic_name"], dest) for dest in self.client.get(uri)["entities"])
            [dest.get("programmatic_name") for dest in import_data.get("message_destinations", [])]
            for dest in import_data.get("message_destinations", []):
                dest_name = dest.get("programmatic_name")
                if dest_name in all_destinations:
                    dest_id = all_destinations[dest_name]["id"]
                    uri = "/message_destinations/{}".format(dest_id)
                    self.client.get_put(uri, update_user)

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
                LOG.info(u"    Message destination exists: %s", dest["programmatic_name"])
            elif dest["name"] in existing_destination_dnames:
                LOG.info(u"    Message destination exists: %s", dest["name"])
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
                    LOG.info(u"    Message destination created: %s ('%s')", dest["programmatic_name"], dest["name"])

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
            if self.confirm(u"type '{}'".format(new_types["type_name"])):
                self.client.post(uri, new_types)
                LOG.info(u"    Type created: %s ('%s')", new_types["type_name"], new_types["display_name"])
            return
        existing_fields = existing_types["fields"]
        for fielduuid in new_fields:
            field = new_fields[fielduuid]
            fieldname = field["name"]
            if fieldname in existing_fields.keys():
                # Merge the field values and update
                LOG.info(u"    %s field exists: %s", type_displayname(type_name), fieldname)
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
                    if self.confirm(u"values for {} field '{}'".format(type_displayname(type_name), fieldname)):
                        uri = "/types/{0}/fields/{1}".format(type_name, existing_id)
                        self.client.put(uri, field)
                        LOG.info(u"    %s field updated: %s ('%s')",
                                 type_displayname(type_name), fieldname, field["text"])
            else:
                # Don't re-use id
                if "id" in field:
                    field.remove("id")
                # Create the field
                fields_uri = "/types/{0}/fields".format(type_name)
                if self.confirm(u"{} field '{}'".format(type_displayname(type_name), fieldname)):
                    self.client.post(fields_uri, field)
                    LOG.info(u"    %s field created: %s ('%s')", type_displayname(type_name), fieldname, field["text"])

    def load_actions(self, definition):
        """Load custom actions"""
        new_actions = definition.value
        if not isinstance(new_actions, (tuple, list)):
            new_actions = [new_actions]
        uri = "/actions?handle_format=names"
        existing_actions = self.client.get(uri)["entities"]
        existing_action_names = [action["name"] for action in existing_actions]
        for action in new_actions:
            if action["name"] in existing_action_names:
                LOG.info(u"    Action exists: %s", action["name"])
            else:
                # Don't re-use id
                if "id" in action:
                    action.pop("id", None)
                # Create the action
                if self.confirm(u"action '{}'".format(action["name"])):
                    self.client.post(uri, action)
                    LOG.info(u"    Action created: %s", action["name"])

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
                LOG.info(u"    Function exists: %s", function["name"])
            else:
                setdefault(function, {
                    "display_name": function["name"]
                })
                # Don't re-use id
                if "id" in function:
                    function.pop("id", None)
                # Create the function
                if self.confirm(u"function '{}'".format(function["name"])):
                    self.client.post(uri, function)
                    LOG.info(u"    Function created: %s", function["name"])
