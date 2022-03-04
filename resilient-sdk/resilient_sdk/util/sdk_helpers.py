#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Common Helper Functions for the resilient-sdk"""
import logging
import keyword
import re
import os
import sys
import io
import copy
import json
import datetime
import importlib
import hashlib
import time
import uuid
import shlex
import subprocess
import ast
import pkg_resources
import tempfile
import shutil
import xml.etree.ElementTree as ET
from jinja2 import Environment, PackageLoader
from zipfile import ZipFile, is_zipfile, BadZipfile
import requests.exceptions
from resilient import ArgumentParser, get_config_file, get_client
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.resilient_objects import DEFAULT_INCIDENT_TYPE, DEFAULT_INCIDENT_FIELD, ResilientTypeIds, ResilientFieldTypes, ResilientObjMap
from resilient_sdk.util.jinja2_filters import add_filters_to_jinja_env
from resilient_sdk.util import constants

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    # JSONDecodeError is not available in PY2.7 so we set it to None
    JSONDecodeError = None
else:
    # Handle PY 3 specific imports
    # reload(package) in PY2.7, importlib.reload(package) in PY3.6
    reload = importlib.reload
    from json.decoder import JSONDecodeError

# Temp fix to handle the resilient module logs
logging.getLogger("resilient.co3").addHandler(logging.StreamHandler())
# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)


def get_resilient_client(path_config_file=None):
    """
    Return a SimpleClient for Resilient REST API using configurations
    options from provided path_config_file or from ~/.resilient/app.config

    :param path_config_file: Path to app.config file to use
    :return: SimpleClient for Resilient REST API
    :rtype: SimpleClient
    """

    if not path_config_file:
        path_config_file = get_config_file()

    LOG.debug("Using app.config file at: %s", path_config_file)

    config_parser = ArgumentParser(config_file=path_config_file)
    opts = config_parser.parse_known_args()[0]

    LOG.info("Connecting to IBM Security SOAR at: %s", opts.get("host"))

    return get_client(opts)


def setup_jinja_env(relative_path_to_templates):
    """
    Returns a Jinja2 Environment with Jinja templates found in resilient_sdk/<<relative_path_to_templates>>
    """
    jinja_env = Environment(
        loader=PackageLoader("resilient_sdk", relative_path_to_templates),  # Loads Jinja Templates in resilient_sdk/<<relative_path_to_templates>>
        trim_blocks=True,  # First newline after a block is removed
        lstrip_blocks=True,  # Leading spaces and tabs are stripped from the start of a line to a block
        keep_trailing_newline=True  # Preserve the trailing newline when rendering templates
    )

    # Add custom filters to our jinja_env
    add_filters_to_jinja_env(jinja_env)

    return jinja_env


def setup_env_and_render_jinja_file(relative_path_to_template, filename, *args, **kwargs):
    """
    Creates a Jinja env and returns the rendered string from a jinja template of a given filename.
    Passes on args and kwargs to the render function
    """

    # instantiate Jinja2 Environment with path to Jinja2 templates
    jinja_env = setup_jinja_env(relative_path_to_template)

    # Load the Jinja2 Template from filename + jinja2 ext
    file_template = jinja_env.get_template(filename + ".jinja2")

    # render the template with the required variables and return the string value
    return file_template.render(*args, **kwargs)


def write_file(path, contents):
    """Writes the String contents to a file at path"""

    if sys.version_info[0] < 3 and isinstance(contents, str):
        contents = unicode(contents, "utf-8")

    with io.open(path, mode="wt", encoding="utf-8", newline="\n") as the_file:
        the_file.write(contents)


def read_file(path):
    """Returns all the lines of a file at path as a List"""
    file_lines = []
    with io.open(path, mode="rt", encoding="utf-8") as the_file:
        file_lines = the_file.readlines()
    return file_lines


def read_json_file(path):
    """
    If the contents of the file at path is valid JSON,
    returns the contents of the file as a dictionary

    :param path: Path to JSON file to read
    :type path: str
    :return: File contents as a dictionary
    :rtype: dict
    """
    file_contents = None
    with io.open(path, mode="rt", encoding="utf-8") as the_file:
        try:
            file_contents = json.load(the_file)
        # In PY2.7 it raises a ValueError and in PY3.6 it raises
        # a JSONDecodeError if it cannot load the JSON from the file
        except (ValueError, JSONDecodeError) as err:
            raise SDKException("Could not read corrupt JSON file at {0}\n{1}".format(path, err))
    return file_contents


def read_zip_file(path, pattern):
    """Returns unzipped contents of file whose name matches a pattern
    in zip file at path.

    :param path: Path to zip file.
    :param pattern: File pattern to match in the zip file.
    :return: file_content: Return unzipped file content.
    """
    file_content = None
    try:
        with ZipFile((path), 'r') as zobj:
            # Get all file names matching 'pattern'.
            file_matches = [f for f in zobj.namelist() if pattern.lower() in f.lower()]
            if len(file_matches):
                if len(file_matches) > 1:
                    raise SDKException("More than one file matching pattern {0} found in zip file: {1}"
                                       .format(pattern, path))
                else:
                    file_name = file_matches.pop()
                    # Extract the file.
                    f = zobj.open(file_name)
                    # Read file and convert content from bytes to string.
                    file_content = f.read().decode('utf8', 'ignore')
            else:
                raise SDKException("A file matching pattern {0} was not found in zip file: {1}"
                                   .format(pattern, path))
    except BadZipfile:
        raise SDKException("Bad zip file {0}.".format(path))

    except SDKException as err:
        raise err

    except Exception as err:
        # An an unexpected error trying to read a zipfile.
        raise SDKException("Got an error '{0}' attempting to read zip file {1}".format(err, path))

    return file_content


def rename_file(path_current_file, new_name):
    """Renames the file at path_current_file with the new_name"""
    os.rename(path_current_file, os.path.join(os.path.dirname(path_current_file), new_name))


def is_valid_package_name(name):
    """Test if 'name' is a valid identifier for a package or module

       >>> is_valid_package_name("")
       False
       >>> is_valid_package_name(None)
       False
       >>> is_valid_package_name("get")
       False
       >>> is_valid_package_name("bang!")
       False
       >>> is_valid_package_name("_something")
       True
       >>> is_valid_package_name("-something")
       True
    """

    if keyword.iskeyword(name):
        return False
    elif name in dir(__builtins__):
        return False
    elif name is None:
        return False
    return re.match(r"[(_|\-)a-z][(_|\-)a-z0-9]*$", name) is not None


def is_valid_version_syntax(version):
    """
    Returns True if version is valid, else False. Accepted version examples are:
        "1.0.0" "1.1.0" "123.0.123"
    """
    if not version:
        return False

    regex = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')

    return regex.match(version) is not None


def is_valid_url(url):
    """
    Returns True if url is valid, else False. Accepted url examples are:
        "http://www.example.com:8000", "https://www.example.com", "www.example.com", "example.com"
    """

    if not url:
        return False

    regex = re.compile(
        r'^(https?://)?'  # optional http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?)'  # domain/hostname
        r'(?:/?|[/?]\S+)'  # .com etc.
        r'(?::\d{1,5})?$',  # port number
        re.IGNORECASE)

    return regex.search(url) is not None


def is_valid_hash(input_hash):
    """Returns True if the input_hash is a valid SHA256 hash.
    Returns False if;
        -   input_hash is not a str
        -   input_hash is not equal to 64 characters
        -   that all characters in input_hash are base 16 (valid hexadecimal)

    :param input_hash: str to validate if its a SHA256 hash
    :type input_hash: str
    :return: True/False
    """
    if not input_hash:
        return False

    regex = re.compile(r'^[a-f0-9]{64}(:.+)?$')

    return regex.match(input_hash) is not None


def does_url_contain(url, qry):
    """
    Checks if url is a valid url, if it isn't returns False.
    Checks if qry is in url. Returns True if it is
    """
    if not is_valid_url(url):
        return False

    return qry in url


def generate_uuid_from_string(the_string):
    """
    Returns String representation of the UUID of a hex md5 hash of the given string
    """

    # Instansiate new md5_hash
    md5_hash = hashlib.md5()

    # Pass the_string to the md5_hash as bytes
    md5_hash.update(the_string.encode("utf-8"))

    # Generate the hex md5 hash of all the read bytes
    the_md5_hex_str = md5_hash.hexdigest()

    # Return a String repersenation of the uuid of the md5 hash
    return str(uuid.UUID(the_md5_hex_str))


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
            raise SDKException(u"{0}: {1}".format(constants.ERROR_NOT_FIND_FILE, path_to_file))

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
            raise SDKException(u"{0}: {1}".format(constants.ERROR_NOT_FIND_DIR, path_to_dir))

        if permissions:
            # Check we have the correct permissions
            has_permissions(permissions, path_to_dir)


def get_resilient_server_info(res_client, keys_to_get=[]):
    """
    Calls the const/ endpoint and returns the info specified in keys_to_get

    **Example:**

    .. code-block:: python

        server_version = get_resilient_server_info(res_client, ["server_version"])

    :param res_client: required for communication back to resilient
    :type res_client: sdk_helpers.get_resilient_client()
    :param keys_to_get: list of strings of the keys to return from the const/ endpoint. If ``None``
    returns the whole response
    :type keys_to_get: list
    :return: response from const/
    :rtype: dict
    """
    LOG.debug("Getting server info")
    server_info = res_client.get("/const/", is_uri_absolute=True)

    if keys_to_get:
        server_info = {k: server_info.get(k, {}) for k in keys_to_get}

    return server_info


def get_resilient_server_version(res_client):
    """
    Uses get_resilient_server_info to get the "server_version"
    and converts it into a float of ``major.minor`` and returns it

    :param res_client: required for communication back to resilient
    :type res_client: sdk_helpers.get_resilient_client()
    :return: the server_version in the form ``major.minor``
    :rtype: float
    """
    LOG.debug("Getting server version")

    if constants.CURRENT_SOAR_SERVER_VERSION:
        return constants.CURRENT_SOAR_SERVER_VERSION

    server_version = get_resilient_server_info(res_client, ["server_version"]).get("server_version", {})

    constants.CURRENT_SOAR_SERVER_VERSION = float("{0}.{1}".format(server_version.get("major", 0), server_version.get("minor", 0)))

    LOG.info("IBM Security SOAR version: v%s", constants.CURRENT_SOAR_SERVER_VERSION)

    return constants.CURRENT_SOAR_SERVER_VERSION


def get_latest_org_export(res_client):
    """
    Generates a new Export on the Resilient Appliance.
    Returns the POST response
    """
    LOG.debug("Generating new organization export")
    latest_export_uri = "/configurations/exports/"

    customizations_to_get = {
        "layouts": True,
        "actions": True,
        "phases_and_tasks": True
    }
    server_version = get_resilient_server_version(res_client)

    if server_version >= constants.MIN_SOAR_SERVER_VERSION_PLAYBOOKS:
        customizations_to_get.update({"playbooks": True})

    return res_client.post(latest_export_uri, customizations_to_get)


def add_configuration_import(new_export_data, res_client):
    """
    Makes a REST request to add a configuration import.

    After the request is made, the configuration import is set at a pending state and needs to be confirmed.
    If the configuration state is not reported as pending, raise an SDK Exception.


    :param new_export_data: A dict representing a configuration import DTO
    :type result: dict
    :param import_id: The ID of the configuration import to confirm
    :type import_id: int
    :param res_client: An instantiated res_client for making REST calls
    :type res_client: SimpleClient()
    :raises SDKException: If the confirmation request fails raise an SDKException
    """
    try:
        result = res_client.post(constants.IMPORT_URL, new_export_data)
    except requests.RequestException as upload_exception:
        LOG.debug(new_export_data)
        raise SDKException(upload_exception)
    else:
        assert isinstance(result, dict)
    if result.get("status", '') == "PENDING":
        confirm_configuration_import(result, result.get("id"), res_client)
    else:
        raise SDKException(
            "Could not import because the server did not return an import ID")


def confirm_configuration_import(result, import_id, res_client):
    """
    Makes a REST request to confirm a pending configuration import as accepted.

    Takes 3 params
    The result of a configuration import request
    The ID of the configuration import request
    A res_client to perform the request

    :param result: Result of the configuration import request
    :type result: dict
    :param import_id: The ID of the configuration import to confirm
    :type import_id: int
    :param res_client: An instantiated res_client for making REST calls
    :type res_client: SimpleClient()
    :raises SDKException: If the confirmation request fails raise an SDKException
    """

    result["status"] = "ACCEPTED"      # Have to confirm changes
    uri = "{}/{}".format(constants.IMPORT_URL, import_id)
    try:
        res_client.put(uri, result)
        LOG.info("Imported configuration changes successfully to the Resilient Appliance")
    except requests.RequestException as import_exception:
        raise SDKException(repr(import_exception))

def read_local_exportfile(path_local_exportfile):
    """
    Read export from given path
    Return res export as dict
    """
    # Get absolute path
    path_local_exportfile = os.path.abspath(path_local_exportfile)

    # Validate we can read it
    validate_file_paths(os.R_OK, path_local_exportfile)

    # Read the export file content.
    if is_zipfile(path_local_exportfile):
        # File is a zip file get unzipped content.
        export_content = read_zip_file(path_local_exportfile, constants.RES_EXPORT_SUFFIX)
    else:
        # File is a assumed to be a text file read the export file content.
        export_content = ''.join(read_file(path_local_exportfile))

    if not export_content:
        raise SDKException("Failed to read {0}".format(path_local_exportfile))

    return json.loads(export_content)


def get_object_api_names(api_name, list_objs):
    """
    Return a list of object api_names from list_objs
    """
    if list_objs:
        return [o.get(api_name) for o in list_objs]
    else:
        return []


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
    if obj_list:
        return dict((o[identifer].strip(), o) for o in obj_list if condition(o))
    return {}


def get_res_obj(obj_name, obj_identifer, obj_display_name, wanted_list, export, condition=lambda o: True, include_api_name=True):
    """
    Return a List of Resilient Objects that are in the 'wanted_list' and meet the 'condition'

    :param obj_name: Name of the Object list in the Export
    :type obj_name: str
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
    :param include_api_name: Whether or not to return the objects API name as a field.
    :type include_api_name: bool
    :return: List of Resilient Objects
    :rtype: List
    """
    return_list = []

    # This loops wanted_list
    # If an entry is dict format, it will have value and identifier attributes
    # We use those to get the 'programmatic_name' or 'api_name'
    # Example: For message_destinations referenced in actions, they are referenced by display name
    # This allows us to get their 'programmatic_name'
    for index, obj in enumerate(wanted_list):
        if isinstance(obj, dict):
            temp_obj_identifier = obj.get("identifier", "")
            obj_value = obj.get("value", "")
            full_obj = get_obj_from_list(temp_obj_identifier,
                                         export.get(obj_name, ""),
                                         lambda wanted_obj, i=temp_obj_identifier, v=obj_value: True if wanted_obj.get(i) == v else False)

            wanted_list[index] = full_obj.get(obj_value).get(obj_identifer)

    if wanted_list:
        ex_obj = get_obj_from_list(obj_identifer, export.get(obj_name, ""), condition)

        for o in set(wanted_list):
            stripped_o = o.strip()
            if stripped_o not in ex_obj:
                raise SDKException(u"{0}: '{1}' not found in this export.\n{0}s Available:\n\t{2}".format(obj_display_name, stripped_o, "\n\t".join(ex_obj.keys())))

            # Add x_api_name to each object, so we can easily reference. This avoids needing to know if
            # obj attribute is 'name' or 'programmatic_name' etc.
            obj = ex_obj.get(stripped_o)
            if include_api_name:
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
                    incident_types=[],
                    datatables=[],
                    tasks=[],
                    scripts=[],
                    playbooks=[],
                    get_related_objects=True):
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
    :param incident_types: List of Custom Incident Type API Names
    :param datatables: List of Data Table API Names
    :param tasks: List of Custom Task API Names
    :param scripts: List of Script Display Names
    :param playbooks: List of Playbook API Names
    :param get_related_objects: Whether or not to hunt for related action objects, defaults to True
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
    incident_types = incident_types if incident_types else []
    datatables = datatables if datatables else []
    tasks = tasks if tasks else []
    scripts = scripts if scripts else []
    playbooks = playbooks if playbooks else []

    # Dict to return
    return_dict = {
        "all_fields": []
    }

    # Get Rules
    return_dict["rules"] = get_res_obj("actions", ResilientObjMap.RULES, "Rule", rules, export)

    if get_related_objects:
        # For Rules we attempt to locate related workflows and message_destinations
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
            # Message Destinations in Rules are identified by their Display Name
            for m in r.get("message_destinations", []):
                message_destinations.append({"identifier": "name", "value": m})

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
    if get_related_objects:
        # For functions we attempt to locate related message destinations
        # Get Function names that use 'wanted' Message Destinations
        for f in export.get("functions", []):
            if f.get("destination_handle") in message_destinations:
                functions.append(f.get(ResilientObjMap.FUNCTIONS))

    return_dict["functions"] = get_res_obj("functions", ResilientObjMap.FUNCTIONS, "Function", functions, export)

    for f in return_dict.get("functions"):
        # Get Function Inputs
        view_items = f.get("view_items", [])
        function_input_uuids = [v.get("content") for v in view_items if "content" in v and v.get("field_type") == ResilientFieldTypes.FUNCTION_INPUT]
        f["inputs"] = get_res_obj("fields", "uuid", "Function Input", function_input_uuids, export)

        return_dict["all_fields"].extend([u"__function/{0}".format(fld.get("name")) for fld in f.get("inputs")])

        # Get Function's Message Destination name
        message_destinations.append(f.get("destination_handle", ""))

    # Get Workflows
    return_dict["workflows"] = get_res_obj("workflows", ResilientObjMap.WORKFLOWS, "Workflow", workflows, export)

    if get_related_objects:
        # For workflows we attempt to locate related functions
        # Get Functions in Workflow
        for workflow in return_dict["workflows"]:
            # This gets all the Functions in the Workflow's XML
            wf_functions = get_workflow_functions(workflow)

            # Add the Display Name and Name to each wf_function
            for wf_fn in wf_functions:
                for fn in return_dict["functions"]:
                    if wf_fn.get("uuid", "a") == fn.get("uuid", "b"):
                        wf_fn["name"] = fn.get("name")
                        wf_fn["display_name"] = fn.get("display_name")
                        wf_fn["message_destination"] = fn.get("destination_handle", "")
                        break

            workflow["wf_functions"] = wf_functions

    # Get Message Destinations
    return_dict["message_destinations"] = get_res_obj("message_destinations", ResilientObjMap.MESSAGE_DESTINATIONS, "Message Destination", message_destinations, export)

    # Get Incident Fields (Custom and Internal)
    return_dict["fields"] = get_res_obj("fields", ResilientObjMap.FIELDS, "Field", fields, export,
                                        condition=lambda o: True if o.get("type_id") == ResilientTypeIds.INCIDENT else False)

    return_dict["all_fields"].extend([u"incident/{0}".format(fld.get("name")) for fld in return_dict.get("fields")])

    # Get Custom Artifact Types
    return_dict["artifact_types"] = get_res_obj("incident_artifact_types", ResilientObjMap.INCIDENT_ARTIFACT_TYPES, "Custom Artifact", artifact_types, export)

    # Get Incident Types
    return_dict["incident_types"] = get_res_obj("incident_types", ResilientObjMap.INCIDENT_TYPES, "Custom Incident Type", incident_types, export)

    # Get Data Tables
    return_dict["datatables"] = get_res_obj("types", ResilientObjMap.DATATABLES, "Datatable", datatables, export,
                                            condition=lambda o: True if o.get("type_id") == ResilientTypeIds.DATATABLE else False)

    # Get Custom Tasks
    return_dict["tasks"] = get_res_obj("automatic_tasks", ResilientObjMap.TASKS, "Custom Task", tasks, export)

    # Get related Phases for Tasks
    phase_ids = [t.get("phase_id") for t in return_dict.get("tasks")]
    return_dict["phases"] = get_res_obj("phases", ResilientObjMap.PHASES, "Phase", phase_ids, export)

    # Get Scripts
    return_dict["scripts"] = get_res_obj("scripts", ResilientObjMap.SCRIPTS, "Script", scripts, export)

    # Get Playbooks
    if playbooks and constants.CURRENT_SOAR_SERVER_VERSION and constants.CURRENT_SOAR_SERVER_VERSION < constants.MIN_SOAR_SERVER_VERSION_PLAYBOOKS:
        raise SDKException("Playbooks are only supported in {0} for SOAR >= {1}. Current version: {2}.".format(constants.SDK_RESOURCE_NAME, constants.MIN_SOAR_SERVER_VERSION_PLAYBOOKS, constants.CURRENT_SOAR_SERVER_VERSION))
    else:
        return_dict["playbooks"] = get_res_obj("playbooks", ResilientObjMap.PLAYBOOKS, "Playbook", playbooks, export)

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
                  scripts=[],
                  incident_types=[],
                  playbooks=[]):
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
    :param incident_types: List of Custom Incident Type Names
    :param playbooks: List of Playbook API Names
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

    # some incident types are parent/child. This routine will return all the parent incident types
    parent_child_incident_types = find_parent_child_types(export, "incident_types", "name", incident_types)

    # Setup the keys_to_minify dict
    keys_to_minify = {
        "message_destinations": {ResilientObjMap.MESSAGE_DESTINATIONS: message_destinations},
        "functions": {ResilientObjMap.FUNCTIONS: functions},
        "workflows": {ResilientObjMap.WORKFLOWS: workflows},
        "actions": {ResilientObjMap.RULES: rules},
        "fields": {"export_key": fields},
        "incident_artifact_types": {ResilientObjMap.INCIDENT_ARTIFACT_TYPES: artifact_types},
        "types": {ResilientObjMap.DATATABLES: datatables},
        "automatic_tasks": {ResilientObjMap.TASKS: tasks},
        "phases": {ResilientObjMap.PHASES: phases},
        "scripts": {ResilientObjMap.SCRIPTS: scripts},
        "incident_types": {ResilientObjMap.INCIDENT_TYPES: parent_child_incident_types},
        "playbooks": {ResilientObjMap.PLAYBOOKS: playbooks}
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
            # strip out extra spaces from the attribute (ie Display name for Rules, Scripts, etc.)
            values = [name.strip() for name in values]

            obj = minified_export.get(key)

            if obj:
                for data in list(obj):

                    if not data.get(attribute_name):
                        LOG.warning("No %s in %s", attribute_name, key)

                    # strip out extra spaces from the attribute (ie Display name for Rules, Scripts, etc.)
                    # If this Resilient Object is not in our minify list, remove it
                    if not data.get(attribute_name, "").strip() in values:
                        minified_export[key].remove(data)

        elif isinstance(minified_export[key], list):
            minified_export[key] = []

        elif isinstance(minified_export[key], dict):
            minified_export[key] = {}

        else:
            minified_export[key] = None

    # Add default incident_type. Needed for every Import
    if minified_export.get("incident_types"):
        minified_export["incident_types"].append(DEFAULT_INCIDENT_TYPE)
    else:
        minified_export["incident_types"] = [DEFAULT_INCIDENT_TYPE]

    # If no Custom Incident Fields are in the export, add this default.
    # An import needs at least 1 Incident Field
    if "incident/" not in fields:
        minified_export["fields"].append(DEFAULT_INCIDENT_FIELD)

    return minified_export

def find_parent_child_types(export, object_type, attribute_name, name_list):
    """[get all parent objects (like incident_types)]

    Args:
        export ([dict]): [export file to parse]
        object_type ([str]): [heirarchy of objects to parse]
        attribute_name ([str]): [name of field to check for]
        name_list ([list]): [list of objects to same]
    """

    extended_name_list = name_list[:]

    if export.get(object_type):
        section = export.get(object_type)
        for name in name_list:
            for item in section:
              if item.get(attribute_name) == name:
                  if item.get('parent_id'):
                      # add the parent hierarchy
                      parent_list = find_parent_child_types(export, object_type, attribute_name, [item.get('parent_id')])
                      extended_name_list.extend(parent_list)

    return list(set(extended_name_list))


def load_py_module(path_python_file, module_name):
    """
    Return the path_python_file as a Python Module.
    We can then access it methods like:

        > result = py_module.some_method_in_module()

    :param path_python_file: Path to the file that contains the module
    :param module_name: Is normally the file name without the .py
    :return: The Python Module found
    :rtype: module
    """
    # Insert the parent dir of path_python_file to the start of our Python PATH at runtime
    path_parent_dir = os.path.dirname(path_python_file)
    sys.path.insert(0, path_parent_dir)

    # Import the module
    py_module = importlib.import_module(module_name)

    # Reload the module so we get the latest one
    # If we do not reload, can get stale results if
    # this method is called more then once
    reload(py_module)

    # Remove the path from PYTHONPATH
    sys.path.remove(path_parent_dir)

    return py_module


def rename_to_bak_file(path_current_file, path_default_file=None):
    """Renames path_current_file with a postfixed timestamp.
    If path_default_file is provided, path_current_file is only
    renamed if the default and current file are different"""
    if not os.path.isfile(path_current_file):
        LOG.warning("No backup file created due to file missing: %s", path_current_file)
        return path_current_file

    if path_default_file is not None and not os.path.isfile(path_default_file):
        raise IOError("Default file to compare to does not exist at: {0}".format(path_default_file))

    new_file_name = "{0}-{1}.bak".format(os.path.basename(path_current_file), get_timestamp())

    # If default file provided, compare to current file
    if path_default_file is not None:
        # Read the default file + the current file
        default_file_contents = read_file(path_default_file)
        current_file_contents = read_file(path_current_file)

        # If different, rename
        if default_file_contents != current_file_contents:
            LOG.debug("Creating a backup of: %s", path_current_file)
            rename_file(path_current_file, new_file_name)

    else:
        LOG.debug("Creating a backup of: %s", path_current_file)
        rename_file(path_current_file, new_file_name)

    return os.path.join(os.path.dirname(path_current_file), new_file_name)


def generate_anchor(header):
    """
    Converts header to lowercase, removes all characters except a-z, 0-9, -,
    unicode charaters that are used in words and spaces then replaces
    all spaces with -

    An anchor is used in Markdown Templates to link certain parts of the document.

    :param header: String to create anchor from
    :type header: str
    :return: header formatted as an anchor
    :rtype: str
    """
    anchor = header.lower()

    regex = re.compile(r"[^\w\-\s]", re.U)

    anchor = re.sub(regex, "", anchor)
    anchor = re.sub(r"[\s]", "-", anchor)

    return anchor


def simplify_string(the_string):
    """
    Simplifies the_string by converting it to lowercases and
    removing all characters except a-z, 0-9, - and spaces then
    replaces all spaces with -

    :param the_string: String to simplify
    :type the_string: str
    :return: the_string formatted
    :rtype: str
    """
    the_string = the_string.lower()

    regex = re.compile(r"[^a-z0-9\-\s_]")

    the_string = re.sub(regex, "", the_string)
    the_string = re.sub("_", "-", the_string)
    the_string = re.sub(r"[\s]", "-", the_string)

    return the_string


def get_workflow_functions(workflow, function_uuid=None):
    """Parses the XML of the Workflow Object and returns
    a List of all Functions found. If function_uuid is defined
    returns all occurrences of that function.

    A Workflow Function can have the attributes:
    - uuid: String
    - inputs: Dict
    - post_processing_script: String
    - pre_processing_script: String
    - result_name: String"""

    return_functions = []

    # Workflow XML text
    wf_xml = workflow.get("content", {}).get("xml", None)

    if wf_xml is None:
        raise SDKException("Could not load xml content from Workflow: {0}".format(workflow))

    # Get the root element + endode in utf8 in order to handle Unicode
    root = ET.fromstring(wf_xml.encode("utf8"))

    # Get the prefix for each element's tag
    tag_prefix = root.tag.replace("definitions", "")

    xml_path = "./{0}process/{0}serviceTask/{0}extensionElements/*".format(tag_prefix)
    the_function_elements = []

    if function_uuid is not None:
        xml_path = "{0}[@uuid='{1}']".format(xml_path, function_uuid)

        # Get all elements at xml_path that have the uuid of the function
        the_function_elements = root.findall(xml_path)

    else:
        the_extension_elements = root.findall(xml_path)
        for extension_element in the_extension_elements:
            if "function" in extension_element.tag:
                the_function_elements.append(extension_element)

    # Foreach element found, load it as a dictionary and append to return list
    for fn_element in the_function_elements:
        return_function = json.loads(fn_element.text)
        return_function["uuid"] = fn_element.attrib.get("uuid", "")
        return_function["result_name"] = return_function.get("result_name", None)
        return_function["post_processing_script"] = return_function.get("post_processing_script", None)
        return_function["pre_processing_script"] = return_function.get("pre_processing_script", None)

        return_functions.append(return_function)

    return return_functions


def get_main_cmd():
    """
    Return the "main" command from the command line.

    E.g. with command line: '$ resilient-sdk codegen -p abc'
    this function will return 'codegen'
    """
    cmd_line = sys.argv

    if len(cmd_line) > 1:
        return cmd_line[1]

    return None


def get_timestamp(timestamp=None):
    """
    Returns a string of the current time
    in the format YYYY-MM-DD-hh:mm:ss

    If `timestamp` is defined, it will return that timestamp in
    the format YYYY-MM-DD-hh:mm:ss

    :param timestamp: Dictionary whose keys are file names
    :type timestamp: float

    :return: Timestamp string
    :rtype: str
    """
    TIME_FORMAT = "%Y%m%d%H%M%S"

    if timestamp:
        return datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)

    return datetime.datetime.now().strftime(TIME_FORMAT)


def str_to_bool(value):
    """
    Represents value as boolean.
    :param value:
    :rtype: bool
    """
    value = str(value).lower()
    return value in ('1', 'true', 'yes')


def is_env_var_set(env_var):
    """
    :return: True/False if env_var is set in environment
    :rtype: bool
    """
    return str_to_bool(os.getenv(env_var))


def get_resilient_libraries_version_to_use():
    """
    :return: Version of resilient-circuits to use depending on ENV_VAR_DEV set
    :rtype: str
    """
    if is_env_var_set(constants.ENV_VAR_DEV):
        return constants.RESILIENT_LIBRARIES_VERSION_DEV
    else:
        return constants.RESILIENT_LIBRARIES_VERSION


def get_resilient_sdk_version():
    """
    wrapper method to call get_package_version on constant SDK_PACKAGE_NAME

    :return: a Version object
    """
    return get_package_version(constants.SDK_PACKAGE_NAME)


def get_package_version(package_name):
    """
    Uses pkg_resources to parse the version of a package if installed in the environment.
    If not installed, return None

    :param package_name: name of the packge to get version of
    :type package_name: str
    :return: a Version object representing the version of the given package or None
    :rtype: Version or None
    """
    try:
        return pkg_resources.parse_version(pkg_resources.require(package_name)[0].version)
    except pkg_resources.DistributionNotFound:
        return None


def is_python_min_supported_version(custom_warning=None):
    """
    Logs a WARNING if the current version of Python is not >= MIN_SUPPORTED_PY_VERSION
    :param custom_warning: a custom message you want to log out
    :type custom_warning: str
    :return: a boolean to indicate if current version is supported or not
    :rtype: bool
    """
    if sys.version_info < constants.MIN_SUPPORTED_PY_VERSION:

        if custom_warning:
            LOG.warning("WARNING: %s", custom_warning)

        else:
            LOG.warning("WARNING: this package should only be installed on a Python Environment >= {0}.{1} "
                        "and your current version of Python is {2}.{3}".format(constants.MIN_SUPPORTED_PY_VERSION[0], constants.MIN_SUPPORTED_PY_VERSION[1], sys.version_info[0], sys.version_info[1]))

        return False

    return True


def parse_version_object(version_obj):
    """
    Parses a Version object into a tuple of (major, minor, micro)
    so that it can be compared to other tuples of versions

    Mostly used because .major/.minor/.micro attributes aren't available in py27

    :param version_obj: a Version object to be parsed
    :type version_obj: Version
    :return: (v.major, v.minor, v.micro) tuple
    :rypte: (int, int, int)
    """

    if sys.version_info[0] >= 3: # python 3 
        return (version_obj.major, version_obj.minor, version_obj.micro)
    else: # python 2.7
        major_minor_micro = tuple(int(i) for i in str(version_obj).split("."))
        
        # if version is only one number (i.e. '3'), then add a 0 to the end
        if len(major_minor_micro) == 1:
            major_minor_micro = (major_minor_micro[0], 0, 0)
        elif len(major_minor_micro) == 2:
            major_minor_micro = (major_minor_micro[0], major_minor_micro[1], 0)
        return major_minor_micro

def parse_optionals(optionals):
    """
    Returns all optionals as a formatted string
    with the number of tabs used depending
    on the length

    Mainly used to help build our docs

    :param optionals: List of ArgumentParser optionals
    :type optionals: list
    :return: Formatted string
    :rtype: str
    """
    parsed_optionals = []

    for option in optionals:

        option_strings = ", ".join(option.option_strings)

        tabs = "\t\t\t"

        if len(option_strings) >= 16:
            tabs = "\t\t"

        if len(option_strings) >= 22:
            tabs = "\t"

        if len(option_strings) < 10:
            tabs = "\t\t\t\t"

        if len(option_strings) in (8, 9):
            tabs = "\t\t\t"

        parsed_optionals.append("{0}{1}{2}".format(option_strings, tabs, option.help))

    parsed_optionals = " \n ".join(parsed_optionals)
    parsed_optionals = '{0} \n'.format(parsed_optionals)

    return parsed_optionals


def run_subprocess(args, change_dir=None, cmd_name="", log_level_threshold=logging.DEBUG):
    """
    Run a given command as a subprocess. Optionally change directory before running the command (use change_dir parameter)

    :param args: (required) args should be a sequence of program arguments or else a single string (see subprocess.Popen for more details)
    :type args: str | list[str]
    :param change_dir: (optional) path of directory to change to before running command
    :type change_dir: str
    :param cmd_name: (optional) the name of the command to run as a subprocess. will be used to log in the format "Running <cmd_name> ..."
    :type cmd_name: str
    :param log_level_threshold: (optional) the logging level at which to output the stdout/stderr for the subprocess; default is DEBUG
    :type log_level_threshold: int
    :return: the exit code and string details of the run
    :rtype: (int, str)
    """

    LOG.debug("Running {0} as a subprocess".format(args))

    # save starting directory
    current_dir = os.getcwd()

    # if change_dir is set, change to that dir
    if change_dir:
        LOG.debug("Changing directory to {0}".format(change_dir))
        os.chdir(change_dir)

    if isinstance(args, str):
        args = shlex.split(args)

    # run given command as a subprocess
    proc = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, bufsize=0)

    sys.stdout.write("Running {0} (this may take a while) ...".format(cmd_name))
    sys.stdout.flush()

    # if debugging enabled, capture output directly and redirect back to sys.stdout
    # using LOG.log(log_level...)
    if LOG.isEnabledFor(log_level_threshold):
        LOG.debug("")
        details = ""
        while proc.stdout:
            line = proc.stdout.readline()
            if not line:
                break
            LOG.log(log_level_threshold, line.decode("utf-8").strip("\n"))
            details += line.decode("utf-8")

        proc.wait() # additional wait to make sure process is complete
    else:
        # if debugging not enabled, use communicate as that has the
        # greatest ability to deal with large buffers of output 
        # being stored in subprocess.PIPE
        stdout, _ = proc.communicate()
        sys.stdout.write(" {0} complete\n\n".format(cmd_name))
        sys.stdout.flush()
        time.sleep(0.75)
        details = stdout.decode("utf-8")


    # move back to original directory
    # note that this just changes the working directory for the python process,
    # — thus if the subprocess was interrupted and the program quits,
    # the directory of the user's terminal won't be affected
    os.chdir(current_dir)

    return proc.returncode, details


    """ OLD code with a progress bar -- keeping this here for potentially picking it back up later """

    # start_time = time.time()

    # # "waiting bar" that spins while waiting for proc to finish
    # # the waiting bar is only output if the logging threshold is not met
    # waiting_bar = ("-", "\\", "|", "/", "-", "\\", "|", "/")
    # i = 0
    # details = ""
    # while proc.poll() == None and (time.time() - start_time) < timeout:
    #     sys.stdout.write("\r")
    #     sys.stdout.write("Running {0} ... {1}        ".format(cmd_name, waiting_bar[i]))
    #     sys.stdout.flush()
    #     i = (i + 1) % len(waiting_bar)
    #     time.sleep(0.2)


    # # overwrite the last stdout.write of "Running <cmd_name> ..."
    # sys.stdout.write("\r")
    # sys.stdout.write(" "*30+"\n")
    # sys.stdout.flush()


def scrape_results_from_log_file(path_log_file):
    """
    Validate that path_log_file exists, reverse it and look for lines
    containing ``[<fn_name>] Result: {'version': 2.0, 'success': True...``

    Only gets the latest result for each <fn_name> in the log file

    The log file must be in the format of the app.log

    :param path_log_file: (required) absolute path to a app.log file
    :type args: str
    :return: a dictionary in the format {<fn_name>: <fn_results>}
    :rtype: dict
    """
    results_scraped = {}

    validate_file_paths(os.R_OK, path_log_file)

    log_file_contents = read_file(path_log_file)

    regex_line = re.compile(r'\[[\w]+\] Result\:')       # Looking for line that contains [<fn_name>] Result: {'version': 2.0, 'success': True...
    regex_fn_name = re.compile(r'\[([\w]+)\] Result\:')  # Getting <fn_name> from [<fn_name>] Result: {'version': 2.0, 'success': True...

    for l in reversed(log_file_contents):
        match = regex_line.search(l, endpos=120)

        if match:
            fn_name_group_index = 0

            fn_name_match = match.group(fn_name_group_index)
            fn_name_match_endpos = match.end(fn_name_group_index)

            fn_name = regex_fn_name.match(fn_name_match).group(1)

            results_from_l = l[fn_name_match_endpos:].strip("\\n ")

            # Check if this fn_name is already in results_scraped
            if fn_name not in results_scraped.keys():
                # Convert str into dict
                results = ast.literal_eval(results_from_l)
                results_scraped[fn_name] = results

    return results_scraped


def handle_file_not_found_error(e, msg):
    """
    Looks at e's message attribute and if
    it contains ERROR_NOT_FIND_DIR or ERROR_NOT_FIND_FILE
    prints a LOG.warning message else just raises the exception

    :param e: (required) an Exception
    :type e: Exception
    :param msg: (required) the custom error message to print as a WARNING in the logs
    :type msg: str
    :raises: The exception that is passed unless it contains 
    ERROR_NOT_FIND_DIR or ERROR_NOT_FIND_FILE in its e.message
    """
    if constants.ERROR_NOT_FIND_DIR or constants.ERROR_NOT_FIND_FILE in e.message:
        LOG.warning("WARNING: %s", msg)
    else:
        raise e

class ContextMangerForTemporaryDirectory():
    """
    This is a small class for safe use of ``tempfile.mkdtemp()`` which requires cleanup after
    use. The class effectively is the same as ``tempfile.TemporaryDirectory``, however, 
    that class isn't available before python 3 thus the implementation here.
    On enter, ``tempfile.mkdtemp(*args, **kwargs)`` is called and on exit ``shutil.rmtree(path_to_dir)`` is called.
    
    Example:

    .. code-block:: python
        # create the context manager using the 'with ... as:' statement
        # on creation of the 'path_to_tmp_dir' object, the ``__enter__`` method is called

        with sdk_helpers.ContextMangerForTemporaryDirectory() as path_to_tmp_dir:
            # ...
            # do something with path_to_tmp_dir
            # ...

        # on exit of context manager, path_to_tmp_dir will be cleaned up by implicit call of the ``__exit__`` method
    
    :param args: any ordered args that are relevant to calling ``tempfile.mkdtemp()``
    :param kwargs: any keyword arguments relevant to calling ``tempfile.mkdtemp()``
    """

    def __init__(self, *args, **kwargs):
        self.dir = tempfile.mkdtemp(*args, **kwargs)

    def __enter__(self):
        return self.dir

    def __exit__(self, exc_type, exc_value, exc_traceback):
        shutil.rmtree(self.dir)
