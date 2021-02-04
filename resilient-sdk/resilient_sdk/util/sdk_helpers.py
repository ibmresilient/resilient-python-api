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
import uuid
import xml.etree.ElementTree as ET
from jinja2 import Environment, PackageLoader
from zipfile import ZipFile, is_zipfile, BadZipfile
import requests.exceptions
from resilient import ArgumentParser, get_config_file, get_client
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.resilient_objects import DEFAULT_INCIDENT_TYPE, DEFAULT_INCIDENT_FIELD, ResilientTypeIds, ResilientFieldTypes, ResilientObjMap
from resilient_sdk.util.jinja2_filters import add_filters_to_jinja_env

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    # JSONDecodeError is not available in PY2.7 so we set it to None
    JSONDecodeError = None
else:
    # Handle PY 3 specific imports
    # reload(package) in PY2.7, importlib.reload(package) in PY3.6
    reload = importlib.reload
    from json.decoder import JSONDecodeError

LOGGER_NAME = "resilient_sdk_log"
ENV_VAR_DEV = "RES_SDK_DEV"

# Temp fix to handle the resilient module logs
logging.getLogger("resilient.co3").addHandler(logging.StreamHandler())
# Get the same logger object that is used in app.py
LOG = logging.getLogger(LOGGER_NAME)

# Resilient export file suffix.
RES_EXPORT_SUFFIX = ".res"
# Endpoint url for importing a configuration
IMPORT_URL = "/configurations/imports"


def get_resilient_client(path_config_file=None):
    """
    Return a SimpleClient for Resilient REST API using configurations
    options from provided path_config_file or from ~/.resilient/app.config

    :param path_config_file: Path to app.config file to use
    :return: SimpleClient for Resilient REST API
    :rtype: SimpleClient
    """
    LOG.info("Connecting to Resilient Appliance...")

    if not path_config_file:
        path_config_file = get_config_file()

    config_parser = ArgumentParser(config_file=path_config_file)
    opts = config_parser.parse_known_args()[0]

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


def write_file(path, contents):
    """Writes the String contents to a file at path"""

    if sys.version_info[0] < 3 and isinstance(contents, str):
        contents = unicode(contents, "utf-8")

    with io.open(path, mode="wt", encoding="utf-8") as the_file:
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
        result = res_client.post(IMPORT_URL, new_export_data)
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
    uri = "{}/{}".format(IMPORT_URL, import_id)
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
        export_content = read_zip_file(path_local_exportfile, RES_EXPORT_SUFFIX)
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
    return [o.get(api_name) for o in list_objs]


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
    :param export: Whether or not to return the objects API name as a field.
    :type export: bool
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
                                         export[obj_name],
                                         lambda wanted_obj, i=temp_obj_identifier, v=obj_value: True if wanted_obj.get(i) == v else False)

            wanted_list[index] = full_obj.get(obj_value).get(obj_identifer)

    if wanted_list:
        ex_obj = get_obj_from_list(obj_identifer, export[obj_name], condition)

        for o in set(wanted_list):
            if o not in ex_obj:
                raise SDKException(u"{0}: '{1}' not found in this export.\n{0}s Available:\n\t{2}".format(obj_display_name, o, "\n\t".join(ex_obj.keys())))

            # Add x_api_name to each object, so we can easily reference. This avoids needing to know if
            # obj attribute is 'name' or 'programmatic_name' etc.
            obj = ex_obj.get(o)
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
                    datatables=[],
                    tasks=[],
                    scripts=[],
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
    :param datatables: List of Data Table API Names
    :param tasks: List of Custom Task API Names
    :param scripts: List of Script Display Names
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
    datatables = datatables if datatables else []
    tasks = tasks if tasks else []
    scripts = scripts if scripts else []

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
            LOG.info("Creating a backup of: %s", path_current_file)
            rename_file(path_current_file, new_file_name)

    else:
        LOG.info("Creating a backup of: %s", path_current_file)
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
