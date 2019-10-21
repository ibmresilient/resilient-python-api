#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Common Helper Functions for the resilient-sdk"""

import logging
import keyword
import re
import os
import sys
import io
import copy
from jinja2 import Environment, PackageLoader
from resilient import ArgumentParser, get_config_file, get_client
from resilient_sdk.util.resilient_types import ResilientTypeIds, ResilientFieldTypes
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.default_resilient_objects import DEFAULT_INCIDENT_TYPE, DEFAULT_INCIDENT_FIELD
from resilient_sdk.util.jinja2_filters import add_filters_to_jinja_env

# Temp fix to handle the resilient module logs
logging.getLogger("resilient.co3").addHandler(logging.StreamHandler())
# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


def get_resilient_client():
    """
    Return a connection to Resilient Appliance using configurations
    from app.config file
    """
    config_parser = ArgumentParser(config_file=get_config_file())
    opts = config_parser.parse_known_args()[0]
    return get_client(opts)


def setup_jinja_env(relative_path_to_templates):
    """
    Returns a Jinja2 Environment with Jinja templates found in resilient_sdk/<<relative_path_to_templates>>
    """
    jinja_env = Environment(
        loader=PackageLoader("resilient_sdk", relative_path_to_templates),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )

    # Add custom filters to our jinja_env
    add_filters_to_jinja_env(jinja_env)

    return jinja_env


def write_file(path, contents):
    """Writes the String contents to a file at path"""

    if sys.version_info[0] < 3 and isinstance(contents, str):
        contents = unicode(contents, "utf-8")

    with io.open(path, mode="wt", encoding="utf-8") as the_file:
        the_file.write(contents)


def is_valid_package_name(name):
    """Test if 'name' is a valid identifier for a package or module

       >>> is_valid_package_name("")
       False
       >>> is_valid_package_name("get")
       False
       >>> is_valid_package_name("bang!")
       False
       >>> is_valid_package_name("_something")
       True
    """

    if keyword.iskeyword(name):
        return False
    if name in dir(__builtins__):
        return False
    return re.match("[_A-Za-z][_a-zA-Z0-9]*$", name) is not None


def has_permissions(permissions, path):
    """
    Raises an exception if the user does not have the given permissions to path
    """

    LOG.debug("checking if: %s has correct permissions", path)

    if not os.access(path, permissions):

        if permissions is os.R_OK:
            permissions = "READ"
        elif permissions is os.W_OK:
            permissions = "WRITE"

        raise SDKException("User does not have {0} permissions for: {1}".format(permissions, path))


def validate_file_paths(permissions, *args):
    """
    Check the given *args paths exist and has the given permissions, else raises an Exception
    """

    # For each *args
    for path_to_file in args:
        # Check the file exists
        if not os.path.isfile(path_to_file):
            raise SDKException("Could not find file: {0}".format(path_to_file))

        if permissions:
            # Check we have the correct permissions
            has_permissions(permissions, path_to_file)


def validate_dir_paths(permissions, *args):
    """
    Check the given *args paths are Directories and have the given permissions, else raises an Exception
    """

    # For each *args
    for path_to_dir in args:
        # Check the dir exists
        if not os.path.isdir(path_to_dir):
            raise SDKException("Could not find directory: {0}".format(path_to_dir))

        if permissions:
            # Check we have the correct permissions
            has_permissions(permissions, path_to_dir)


def get_latest_org_export(res_client):
    """
    Generates a new Export on the Resilient Appliance.
    Returns the POST response
    """
    LOG.debug("Generating new organization export")
    latest_export_uri = "/configurations/exports/"
    return res_client.post(latest_export_uri, {"layouts": True, "actions": True, "phases_and_tasks": True})


def get_obj_from_list(identifer, obj_list, condition=lambda o: True):
    """
    Return a dict the name of the object as its Key
    e.g. {
        "fn_mock_function_1": {...},
        "fn_mock_function_2": {...}
    }
    :param identifer: The attribute of the object we use to identify it e.g. "programmatic_name"
    :type identifer: str
    :param obj_list: List of Resilient Objects
    :type obj_list: List
    :param condition: A lambda function to evaluate each object
    :type condition: function
    :return: Dictionary of each found object like the above example
    :rtype: Dict
    """
    return dict((o[identifer], o) for o in obj_list if condition(o))


def get_res_obj(obj_name, obj_identifer, obj_display_name, wanted_list, export, condition=lambda o: True):
    """
    Return a List of Resilient Objects that are in the 'wanted_list' and meet the 'condition'

    :param obj_name: Name of the Object list in the Export
    :type identifer: str
    :param obj_identifer: The attribute of the object we use to identify it e.g. "programmatic_name"
    :type obj_identifer: str
    :param obj_display_name: The Display Name we want to use for this object in our Logs
    :type obj_display_name: str
    :param wanted_list: List of identifers for objects we want to return
    :type wanted_list: List of str
    :param export: The result of calling get_latest_org_export()
    :type export: Dict
    :param condition: A lambda function to evaluate each object
    :type condition: function
    :return: List of Resilient Objects
    :rtype: List
    """
    return_list = []

    if wanted_list:
        ex_obj = get_obj_from_list(obj_identifer, export[obj_name], condition)

        for o in set(wanted_list):
            if o not in ex_obj:
                raise SDKException(u"{0}: '{1}' not found in this export.\n{0}s Available:\n\t{2}".format(obj_display_name, o, "\n\t".join(ex_obj.keys())))

            # Add x_api_name to each object, so we can easily reference. This avoids needing to know if
            # obj attribute is 'name' or 'programmatic_name' etc.
            obj = ex_obj.get(o)
            obj["x_api_name"] = obj[obj_identifer]
            return_list.append(obj)

    return return_list


def get_from_export(export,
                    message_destinations=[],
                    functions=[],
                    workflows=[],
                    rules=[],
                    fields=[],
                    artifact_types=[],
                    datatables=[],
                    tasks=[],
                    scripts=[]):
    """
    Return a Dictionary of Resilient Objects that are found in the Export.
    The parameters are Lists of the Objects you want

    :param export: The result of calling get_latest_org_export()
    :type export: Dict
    :param message_destinations: List of Message Destination API Names
    :param functions: List of Function API Names
    :param workflows: List of Workflow API Names
    :param rules: List of Rule Display Names
    :param fields: List of Field API Names
    :param artifact_types: List of Custom Artifact Type API Names
    :param datatables: List of Data Table API Names
    :param tasks: List of Custom Task API Names
    :param scripts: List of Script Display Names
    :return: Return a Dictionary of Resilient Objects
    :rtype: Dict
    """

    # Create a deepcopy of the export, so we don't overwrite the original
    export = copy.deepcopy(export)

    # Set paramaters to Lists if falsy
    message_destinations = message_destinations if message_destinations else []
    functions = functions if functions else []
    workflows = workflows if workflows else []
    rules = rules if rules else []
    fields = fields if fields else []
    artifact_types = artifact_types if artifact_types else []
    datatables = datatables if datatables else []
    tasks = tasks if tasks else []
    scripts = scripts if scripts else []

    # Dict to return
    return_dict = {
        "all_fields": []
    }

    # Get Rules
    return_dict["rules"] = get_res_obj("actions", "name", "Rule", rules, export)

    for r in return_dict.get("rules"):

        # Get Activity Fields for Rules
        view_items = r.get("view_items", [])
        activity_field_uuids = [v.get("content") for v in view_items if "content" in v and v.get("field_type") == ResilientFieldTypes.ACTIVITY_FIELD]
        r["activity_fields"] = get_res_obj("fields", "uuid", "Activity Field", activity_field_uuids, export)
        return_dict["all_fields"].extend([u"actioninvocation/{0}".format(fld.get("name")) for fld in r.get("activity_fields")])

        # Get names of Workflows that are related to Rule
        for w in r.get("workflows", []):
            workflows.append(w)

        # Get names of Message Destinations that are related to Rule
        for m in r.get("message_destinations", []):
            message_destinations.append(m)

        # Get names of Tasks/Scripts/Fields that are related to Rule
        automations = r.get("automations", [])
        for a in automations:
            if a.get("tasks_to_create"):
                for t in a["tasks_to_create"]:
                    tasks.append(t)

            elif a.get("scripts_to_run"):
                scripts.append(a.get("scripts_to_run"))

            elif a.get("field"):
                fields.append(a.get("field"))

    # Get Functions
    # Get Function names that use 'wanted' Message Destinations
    for f in export.get("functions", []):
        if f.get("destination_handle") in message_destinations:
            functions.append(f.get("export_key"))

    return_dict["functions"] = get_res_obj("functions", "export_key", "Function", functions, export)

    for f in return_dict.get("functions"):
        # Get Function Inputs
        view_items = f.get("view_items", [])
        function_input_uuids = [v.get("content") for v in view_items if "content" in v and v.get("field_type") == ResilientFieldTypes.FUNCTION_INPUT]
        f["inputs"] = get_res_obj("fields", "uuid", "Function Input", function_input_uuids, export)

        return_dict["all_fields"].extend([u"__function/{0}".format(fld.get("name")) for fld in f.get("inputs")])

        # Get Function's Message Destination name
        message_destinations.append(f.get("destination_handle", ""))

    # Get Workflows
    return_dict["workflows"] = get_res_obj("workflows", "programmatic_name", "Workflow", workflows, export)

    # Get Message Destinations
    return_dict["message_destinations"] = get_res_obj("message_destinations", "programmatic_name", "Message Destination", message_destinations, export)

    for m in return_dict.get("message_destinations"):
        LOG.info(m)

    # Get Custom Fields
    return_dict["fields"] = get_res_obj("fields", "name", "Field", fields, export,
                                        condition=lambda o: True if o.get("prefix") == "properties" and o.get("type_id") == ResilientTypeIds.INCIDENT else False)

    return_dict["all_fields"].extend([u"incident/{0}".format(fld.get("name")) for fld in return_dict.get("fields")])

    # Get Custom Artifact Types
    return_dict["artifact_types"] = get_res_obj("incident_artifact_types", "programmatic_name", "Custom Artifact", artifact_types, export)

    # Get Data Tables
    return_dict["datatables"] = get_res_obj("types", "type_name", "Datatable", datatables, export,
                                            condition=lambda o: True if o.get("type_id") == ResilientTypeIds.DATATABLE else False)

    # Get Custom Tasks
    return_dict["tasks"] = get_res_obj("automatic_tasks", "programmatic_name", "Custom Task", tasks, export)

    # Get related Phases for Tasks
    phase_ids = [t.get("phase_id") for t in return_dict.get("tasks")]
    return_dict["phases"] = get_res_obj("phases", "export_key", "Phase", phase_ids, export)

    # Get Scripts
    return_dict["scripts"] = get_res_obj("scripts", "export_key", "Script", scripts, export)

    return return_dict


def minify_export(export,
                  keys_to_keep=[],
                  message_destinations=[],
                  functions=[],
                  workflows=[],
                  rules=[],
                  fields=[],
                  artifact_types=[],
                  datatables=[],
                  tasks=[],
                  phases=[],
                  scripts=[]):
    """
    Return a 'minified' version of the export.
    All parameters are a list of api_names of objects to include in the export.
    Anything not mentioned in passed Lists are set to empty or None.

    :param export: The result of calling get_latest_org_export()
    :type export: Dict
    :param message_destinations: List of Message Destination API Names
    :param functions: List of Function API Names
    :param workflows: List of Workflow API Names
    :param rules: List of Rule Display Names
    :param fields: List of Field export_keys e.g. ['incident/custom_field', 'actioninvocation/custom_activity_field', '__function/custom_fn_input']
    :param artifact_types: List of Custom Artifact Type API Names
    :param datatables: List of Data Table API Names
    :param tasks: List of Custom Task API Names
    :param tasks: List of Phases API Names
    :param scripts: List of Script Display Names
    :return: Return a Dictionary of Resilient Objects
    :rtype: Dict
    """
    # Deep copy the export, so we don't overwrite anything
    minified_export = copy.deepcopy(export)

    # If no keys_to_keep are specified, use these defaults
    if not keys_to_keep:
        keys_to_keep = [
            "export_date",
            "export_format_version",
            "id",
            "server_version"
        ]

    # Setup the keys_to_minify dict
    keys_to_minify = {
        "message_destinations": {"programmatic_name": message_destinations},
        "functions": {"name": functions},
        "workflows": {"programmatic_name": workflows},
        "actions": {"name": rules},
        "fields": {"export_key": fields},
        "incident_artifact_types": {"programmatic_name": artifact_types},
        "types": {"type_name": datatables},
        "automatic_tasks": {"programmatic_name": tasks},
        "phases": {"name": phases},
        "scripts": {"name": scripts}
    }

    for key in minified_export.keys():

        # If we keep this one, skip
        if key in keys_to_keep:
            continue

        # If we are to minify it
        elif key in keys_to_minify.keys():

            # Get the attribute_name to match on (normally 'name'/'programmatic_name'/'export_key')
            attribute_name = list(keys_to_minify[key].keys())[0]

            values = keys_to_minify[key][attribute_name]

            for data in list(minified_export[key]):

                if not data.get(attribute_name):
                    LOG.warning("No %s in %s", attribute_name, key)

                # If this Resilient Object is not in our minify list, remove it
                if not data.get(attribute_name) in values:
                    minified_export[key].remove(data)

        elif isinstance(minified_export[key], list):
            minified_export[key] = []

        elif isinstance(minified_export[key], dict):
            minified_export[key] = {}

        else:
            minified_export[key] = None

    # Add default incident_type. Needed for every Import
    minified_export["incident_types"] = [DEFAULT_INCIDENT_TYPE]

    # If no Custom Incident Fields are in the export, add this default.
    # An import needs at least 1 Incident Field
    if "incident/" not in fields:
        minified_export["fields"].append(DEFAULT_INCIDENT_FIELD)

    return minified_export
