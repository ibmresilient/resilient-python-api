#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""Common Helper Functions for the resilient-sdk"""
import ast
import copy
import datetime
import hashlib
import importlib
import io
import json
import keyword
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from argparse import SUPPRESS
from collections import OrderedDict
from zipfile import BadZipfile, ZipFile, is_zipfile

import pkg_resources
import requests
import requests.exceptions
from jinja2 import Environment, PackageLoader
from packaging.version import parse as parse_version
from resilient_sdk.util import constants
from resilient_sdk.util.jinja2_filters import add_filters_to_jinja_env
from resilient_sdk.util.resilient_objects import (DEFAULT_INCIDENT_FIELD,
                                                  DEFAULT_INCIDENT_TYPE,
                                                  SCRIPT_TYPE_MAP,
                                                  ResilientFieldTypes,
                                                  ResilientObjMap,
                                                  ResilientTypeIds)
from resilient_sdk.util.sdk_exception import SDKException

from resilient import ArgumentParser
from resilient import constants as res_constants
from resilient import get_client, get_config_file
from resilient.helpers import remove_tag

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

    retry_args = {
        res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES: opts.get(res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES),
        res_constants.APP_CONFIG_REQUEST_MAX_RETRIES: opts.get(res_constants.APP_CONFIG_REQUEST_MAX_RETRIES),
        res_constants.APP_CONFIG_REQUEST_RETRY_DELAY: opts.get(res_constants.APP_CONFIG_REQUEST_RETRY_DELAY),
        res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF: opts.get(res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF)
    }

    return get_client(opts, **retry_args)


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


def write_latest_pypi_tmp_file(latest_version, path_sdk_tmp_pypi_version):
    """
    Writes the ``latest_version`` and the ts of the current time
    to ``path_sdk_tmp_pypi_version``

    If ``latest_version`` is a ``pkg_resources.Version``, get its ``base_version``.
    Note: this is actually a different Version type - we would have to import extra
    dependencies to correctly use isinstance(latest_version, Version) - so just checking
    if it has the attribute
    """
    # Try get the 'base_version' if this is a Version object
    if isinstance(latest_version, object):
        latest_version = getattr(latest_version, "base_version", latest_version)

    saved_version_data = {
        "ts": int(time.time()),
        "version": latest_version
    }

    write_file(path_sdk_tmp_pypi_version, json.dumps(saved_version_data))


def read_file(path):
    """Returns all the lines of a file at path as a List"""
    file_lines = []
    with io.open(path, mode="rt", encoding="utf-8") as the_file:
        file_lines = the_file.readlines()
    return file_lines


def read_json_file(path, section=None):
    """
    If the contents of the file at path is valid JSON,
    returns the contents of the file as a dictionary

    :param path: Path to JSON file to read
    :type path: str
    :param section: Section name in JSON file (eg. commands in resilient-sdk)
    :type section: str
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
    if section:
        if section in file_contents:
            return file_contents.get(section, {})
        else: 
            LOG.debug("Section {} not found in provided JSON.".format(section))
            return {}
    else:
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

    # added in v51.0 the ability to have more than three numbers in the version
    # (min still 3) since new versioning scheme has 5(!!) numbers
    regex = re.compile(r'^\d+\.\d+\.\d+(?:\.\d+)*$')

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
    and converts it into a Version object and returns it

    :param res_client: required for communication back to resilient
    :type res_client: sdk_helpers.get_resilient_client()
    :return: the server_version.version value
    :rtype: Version object
    """
    LOG.debug("Getting server version")

    if constants.CURRENT_SOAR_SERVER_VERSION:
        return constants.CURRENT_SOAR_SERVER_VERSION

    server_version = get_resilient_server_info(res_client, ["server_version"]).get("server_version", {})

    constants.CURRENT_SOAR_SERVER_VERSION = parse_version(server_version.get("version", "0.0.0.0"))

    LOG.info("IBM Security SOAR version: v%s", constants.CURRENT_SOAR_SERVER_VERSION)

    return constants.CURRENT_SOAR_SERVER_VERSION


def get_latest_org_export(res_client):
    """
    Generates a new Export on SOAR.
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
        LOG.info("Imported configuration changes successfully to SOAR")
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


def get_script_info(each_script_in_playbook, scripts_in_location, script_type):
    '''
    Extracts script related information for playbooks. Scripts can be of 2 types: local or global.
    Local scripts live within the playbook itself, while global scripts are stored in the global_export dict.
    
    Note: The scripts are passed by reference. They need not be returned. They are directly updated.
    :param each_script_in_playbook: Individual scripts found in the playbook
    :type each_script_in_playbook: dict
    :param scripts_in_location: All scripts in the location (global or local). Global scripts are pulled directly from the global_export dict. Local scripts are pulled from the playbook
    :type scripts_in_location: list
    :param script_type: The type of script (global or local)
    :type script_type: str
    '''
    found_script = False
    for sc in scripts_in_location:
        if each_script_in_playbook.get("uuid", "uuid_not_found_pb") == sc.get("uuid", "uuid_not_found_sc"):
            each_script_in_playbook["name"] = sc.get("name")
            each_script_in_playbook["script_type"] = script_type
            each_script_in_playbook["description"] = sc.get("description")
            each_script_in_playbook["object_type"] = sc.get("object_type")
            each_script_in_playbook["script_text"] = sc.get("script_text", "")
            found_script = True
            break
    return found_script


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
                    apps=[],
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

    # Get Apps
    return_dict["apps"] = get_res_obj("apps", ResilientObjMap.APPS, "Apps", apps, export)

    # Get Playbooks
    if playbooks and constants.CURRENT_SOAR_SERVER_VERSION and constants.CURRENT_SOAR_SERVER_VERSION < constants.MIN_SOAR_SERVER_VERSION_PLAYBOOKS:
        raise SDKException(constants.ERROR_PLAYBOOK_SUPPORT)
    else:
        return_dict["playbooks"] = get_res_obj("playbooks", ResilientObjMap.PLAYBOOKS, "Playbook", playbooks, export)

        if get_related_objects:
            # For Playbooks we attempt to locate related functions and scripts
            # Get Functions in Playbooks
            for playbook in return_dict.get("playbooks", []):
                # This gets all the functions and scripts in the Playbooks's XML
                pb_objects = get_playbook_objects(playbook)

                # Add the Display Name and Name to each wf_function
                for pb_fn in pb_objects.get("functions", []):
                    for fn in return_dict["functions"]:
                        if pb_fn.get("uuid", "uuid_not_found_pb") == fn.get("uuid", "uuid_not_found_fn"):
                            pb_fn["name"] = fn.get("name")
                            pb_fn["display_name"] = fn.get("display_name")
                            pb_fn["message_destination"] = fn.get("destination_handle", "")
                            break

                # If a playbook script is local, its information can be directly extracted from the playbook,
                # if not, the script's information has to be extracted from the global scripts
                for pb_sc in pb_objects.get("scripts", []):
                    # If the script is a local script, then we need to find the script in the Playbook
                    found_script = get_script_info(pb_sc, playbook.get("local_scripts"), SCRIPT_TYPE_MAP.get("local"))

                    # If script not found in playbook, searching Global Scripts
                    found_script = get_script_info(pb_sc, return_dict["scripts"], SCRIPT_TYPE_MAP.get("global")) if not found_script else True

                    # If the script is not found in the Playbook or Global Scripts, then its UUID is used to find the script form the org export
                    if not found_script:
                        _unfound_scripts = get_res_obj("scripts", "uuid", "Script", [pb_sc.get("uuid")], export)
                        for script in _unfound_scripts:
                            # Renaming the x_api_name to name. Since the script was fetched with UUID, the x_api_name is the UUID
                            script["x_api_name"] = script["name"]
                        found_script = get_script_info(pb_sc, _unfound_scripts, SCRIPT_TYPE_MAP.get("global"))
                        # Adding script to return_dict. This is to make sure that its included in the export.res and customize.py
                        return_dict["scripts"].extend(_unfound_scripts)

                # add name to each sub playbook input
                for pb_sub_pb in pb_objects.get("sub_pbs", []):
                    replace_uuids_in_subplaybook_data(pb_sub_pb, export)

                activation_type = playbook.get("activation_type", "")
                if playbook.get("type") == "subplaybook":
                    playbook["activation_type"] = "Sub-playbook"
                else:
                    playbook["activation_type"] = activation_type.capitalize()

                if activation_type.lower() == "manual":
                    activation_conditions = playbook.get("manual_settings", {}).get("activation_conditions", {})
                else:
                    activation_conditions = playbook.get("activation_details", {}).get("activation_conditions", {})
                playbook["conditions"] = str_repr_activation_conditions(activation_conditions) or "-"
                playbook["pb_functions"] = pb_objects.get("functions")
                playbook["pb_scripts"]   = pb_objects.get("scripts")
                playbook["pb_sub_pbs"]   = pb_objects.get("sub_pbs")

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
    :param keys_to_keep: Keys that should remain unchanged from the original export
    :type keys_to_keep: Dict
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
    # keys_to_keep is used to keep values from the original export
    # without being minified
    if not keys_to_keep:
        keys_to_keep = [
            "export_date",
            "export_format_version",
            "id",
            "server_version"
        ]

    # certain keys need to be cleared, rather than set to empty objects
    # so as not to process a delete or update on the platform when the
    # export is modified and POSTed back to SOAR
    keys_to_clear = [
        "overrides"
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

        elif key in keys_to_clear:
            minified_export[key] = None

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

    # Clean out any pii values with keys included in pii_key_list
    pii_key_list = ["creator", "creator_id"]
    minified_export = rm_pii(pii_key_list, minified_export)

    minified_export = remove_tag(minified_export)

    return minified_export


def rm_pii(pii_key_list, export):
    """
    Remove any keys from 'export' that are in 'pii_key_list'.
    Recursively searches the export object.
    
    :param pii_key_list: list of str keys to be removed from 'export'. ex: ["creator", "creator_id"]
    :type pii_key_list: [str]
    :param export: the result of calling get_latest_org_export() or minified_export from calling minify_export()
    :type export: Dict
    :return: modified export with any pii keys removed
    :rtype: Dict
    """

    if export:
        export_copy = export.copy()

        for key in list(export_copy.keys()):
            content = export_copy[key]

            # if key is in pii_list to remove, delete entry in payload_result
            if key in pii_key_list:
                del export_copy[key]
                continue

            # if key wasn't in pii_list, continue searching recursively for dictionaries and scrubbing pii
            if isinstance(content, dict):
                export_copy[key] = rm_pii(pii_key_list, content)
            elif isinstance(content, list):
                # recreates the list where any dict elements of the list are recursively scrubbed
                # if list item is not a dictionary, don't 
                export_copy[key] = [rm_pii(pii_key_list, list_content) if isinstance(list_content, dict) else list_content for list_content in content]

        return export_copy
    else:
        return export


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


def get_playbook_objects(playbook, function_uuid=None):
    """Parses the XML of the Playbook Object and returns
    a List of all Functions and Scripts found. The scripts
    returned only has the uuid attribute. This can later
    be used to extract all script-related information either
    form the playbook export or from global scripts. If
    function_uuid is defined returns all occurrences of that
    function only.

    Function Attributes:
    - uuid: String
    - inputs: Dict
    - pre_processing_script: String
    - result_name: String

    Script Attributes:
    - uuid: String
    """
    playbook_elements = {"functions": [], "scripts": [], "sub_pbs": []}

    # Playbook XML text
    pb_xml = playbook.get("content", {}).get("xml", None)

    if pb_xml is None:
        raise SDKException("Could not load xml content from Playbooks: {0}".format(playbook))

    # Get the root element + encoded in utf8 in order to handle Unicode
    root = ET.fromstring(pb_xml.encode("utf8"))

    # Get the prefix for each element's tag
    tag_prefix = root.tag.replace("definitions", "")

    xml_function_path = "./{0}process/{0}serviceTask/{0}extensionElements/*".format(tag_prefix)
    xml_script_path = "./{0}process/{0}scriptTask/{0}extensionElements/*".format(tag_prefix)
    xml_sub_playbook_path = "./{0}process/{0}callActivity/{0}extensionElements/*".format(tag_prefix)

    if function_uuid is not None:
        xml_function_path = "{0}[@uuid='{1}']".format(xml_function_path, function_uuid)

        # Get all elements at xml_path that have the uuid of the function
        playbook_elements += root.findall(xml_function_path)
    else:
        # Paths to functions, scripts, and subplaybooks in the XML
        the_extension_elements  = root.findall(xml_function_path)
        the_extension_elements += root.findall(xml_script_path)
        the_extension_elements += root.findall(xml_sub_playbook_path)

        for extension_element in the_extension_elements:
            return_function = {}
            # Extracting Function related data from the XML
            if "function" in extension_element.tag:
                return_function = json.loads(extension_element.text)
                return_function["uuid"] = extension_element.attrib.get("uuid", "")
                return_function["result_name"] = return_function.get("result_name", None)
                return_function["pre_processing_script"] = return_function.get("pre_processing_script", None)
                playbook_elements["functions"].append(return_function)

            # Extracting Script related data from the XML
            if "script" in extension_element.tag:
                return_function["uuid"] = extension_element.get("uuid", "")
                playbook_elements["scripts"].append(return_function)

            # Extracting Subplaybook related data from the XML
            if "sub-playbook" in extension_element.tag:
                sub_pb = json.loads(extension_element.text)
                sub_pb["uuid"] = extension_element.attrib.get("uuid", "")
                playbook_elements["sub_pbs"].append(sub_pb)

    return playbook_elements


def replace_uuids_in_subplaybook_data(playbook_data, export):
    """
    When processing a subplaybook within a playbook, it is possible that there are
    references to objects only through UUIDs. Those are not useful for
    generating Markdown files where a user wants to read through in plain text
    the values of the objects referenced. This function replaces any relevant
    UUIDs with their true value from the export. The replacement is in place

    :param playbook_data: sub playbook to process
    :type playbook_data: dict
    :param export: full export data
    :type export: dict
    """

    # add name to each sub playbook input
    for sub_pb in export.get("playbooks", []):
        if playbook_data.get("uuid", "uuid_not_found_pb") == sub_pb.get("uuid", "uuid_not_found_fn"):
            fields = sub_pb.get("fields_type", {}).get("fields", {})

            # update sub playbook's name
            playbook_data["name"] = sub_pb.get("display_name")
            for field_name, field in fields.items():
                if field.get("uuid", "uuid_not_found") in playbook_data.get("inputs", {}):
                    # convert input uuid to input_name
                    playbook_data["inputs"][field.get("uuid")]["input_name"] = field.get("text")
                    playbook_data["inputs"][field.get("uuid")]["input_api_name"] = field_name
                    # add input type
                    playbook_data["inputs"][field.get("uuid")]["input_type_name"] = field.get("input_type")
                    # selects and multiselects reference their UUID in the data extracted from xml,
                    # so we need to replace that with the true value found in the sub_pb
                    if field.get("input_type") == "select":
                        select_input_uuid = playbook_data["inputs"][field.get("uuid")]["static_input"]["select_value"]
                        playbook_data["inputs"][field.get("uuid")]["static_input"]["select_value"] = next(value.get("label") for value in field.get("values") if value.get("uuid") == select_input_uuid)
                    elif field.get("input_type") == "multiselect":
                        select_input_uuids = playbook_data["inputs"][field.get("uuid")]["static_input"]["multiselect_value"]
                        playbook_data["inputs"][field.get("uuid")]["static_input"]["multiselect_value"] = ", ".join(value.get("label") for value in field.get("values") if value.get("uuid") in select_input_uuids)

    # make input easier to get in jinja2
    for _, input in playbook_data.get("inputs", {}).items():
        input_str_repr = ""
        if "expression_input" in input:
            input_str_repr = input.get("expression_input", {}).get("expression", "UNKNOWN")
        elif "static_input" in input:
            in_content = input.get("static_input")
            # there's only one item ever in in_content so we can use ``next()``
            # on the generator below to get the item's value
            input_str_repr = next(value for _, value in in_content.items())
        input["input_as_str"] = input_str_repr

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

    :param package_name: name of the package to get version of
    :type package_name: str
    :return: a Version object representing the version of the given package or None
    :rtype: Version or None
    """
    try:
        return pkg_resources.parse_version(pkg_resources.require(package_name)[0].version)
    except pkg_resources.DistributionNotFound:
        return None


def get_latest_version_on_pypi():
    """
    Uses requests to call 'https://pypi.org/pypi/resilient-sdk/json'
    to get a JSON dict of all the available versions on PyPi.
    Sorts the dict into a list, then gets the latest

    :raises HTTPError: if a problem occurs reaching pypi.org
    :return: the latest available version of this library on PyPi
    :rtype: pkg_resources.extern.packaging.version.Version
    """
    r = requests.get(constants.URL_PYPI_VERSION, timeout=5)
    r.raise_for_status()

    res_json = r.json()

    available_versions = []

    for the_version in res_json.get("releases", {}):

        v = pkg_resources.parse_version(the_version)

        if not isinstance(v, pkg_resources.extern.packaging.version.LegacyVersion):
            available_versions.append(v)

    available_versions = sorted(available_versions)

    return available_versions[-1]


def get_latest_available_version():
    """
    Sees if the latest version is stored in a tmp file
    and if the file is missing or the timestamp is older
    than 3 days, gets the latest version from PyPi

    :return: the latest available version of this library on PyPi
    :rtype: pkg_resources.Version
    """
    latest_available_version = None

    sdk_tmp_dir = get_sdk_tmp_dir()
    path_sdk_tmp_pypi_version = os.path.join(sdk_tmp_dir, constants.TMP_PYPI_VERSION)

    if os.path.isfile(path_sdk_tmp_pypi_version):
        pypi_version_data = read_json_file(path_sdk_tmp_pypi_version)

        now = datetime.datetime.now()
        ts = datetime.datetime.fromtimestamp(pypi_version_data.get("ts", ""))
        refresh_pypi_date = ts + datetime.timedelta(days=3)

        if now > refresh_pypi_date:
            latest_available_version = get_latest_version_on_pypi()
            write_latest_pypi_tmp_file(latest_available_version, path_sdk_tmp_pypi_version)

        else:
            return pkg_resources.parse_version(pypi_version_data.get("version", ""))

    else:
        latest_available_version = get_latest_version_on_pypi()
        write_latest_pypi_tmp_file(latest_available_version, path_sdk_tmp_pypi_version)

    return latest_available_version


def create_tmp_dir(sdk_tmp_dir_name=constants.SDK_RESOURCE_NAME, tmp_dir=tempfile.gettempdir()):
    """
    Checks if user has correct permissions then creates
    the sdk_tmp_dir

    :param sdk_tmp_dir_name: the name for the dir to create in the system's /tmp folder
    :type sdk_tmp_dir_name: str
    :param tmp_dir: the path to the temp files location on the system
    :type tmp_dir: str
    :return: path to the sdk_tmp_dir
    :rtype: str
    """
    validate_dir_paths(os.W_OK, tmp_dir)

    path_sdk_tmp_dir = os.path.join(tmp_dir, sdk_tmp_dir_name)

    os.makedirs(path_sdk_tmp_dir)

    return path_sdk_tmp_dir


def get_sdk_tmp_dir(sdk_tmp_dir_name=constants.SDK_RESOURCE_NAME, tmp_dir=tempfile.gettempdir()):
    """
    Gets the path to the sdk_tmp_dir or creates it if it does
    not exist

    :param sdk_tmp_dir_name: the name for the dir normally the name of the package
    :type sdk_tmp_dir_name: str
    :param tmp_dir: the path to the temp files location on the system
    :type tmp_dir: str
    :return: path to the sdk_tmp_dir
    :rtype: str
    """
    path_sdk_tmp_dir = os.path.join(tmp_dir, sdk_tmp_dir_name)

    if not os.path.isdir(path_sdk_tmp_dir):
        path_sdk_tmp_dir = create_tmp_dir(sdk_tmp_dir_name, tmp_dir)

    return path_sdk_tmp_dir


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

        # skipped any suppressed options
        if option.help == SUPPRESS:
            continue

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
        match = regex_line.search(l)

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

def str_repr_activation_conditions(activation_conditions):
    """
    Represent "activation conditions" as a string.

    Example:
        activation_conditions = {
            "conditions": [
                {
                    "evaluation_id": None,
                    "field_name": "incident.id",
                    "method": "not_equals",
                    "type": None,
                    "value": 123456
                }
            ],
            "logic_type": "all"
        }
    

    :param activation_conditions: _description_
    :type activation_conditions: _type_
    """
    conditions = OrderedDict()
    for i, condition in enumerate(activation_conditions.get("conditions", []), start=1):
        field_name = condition.get("field_name") or ""
        method = condition.get("method") or ""
        value = condition.get("value") or ""

        # index into the dictionary by the evaluation ID which is only present
        # if the logic_type is "advanced". If not present (i.e. logic_type==any or all),
        # then we just keep track with the index in which it was found in the list
        # NOTE: use ``filter(None, [...items...])`` here to drop any elements that might
        # be None. This would occur in the case that a condition doesn't have
        # all three elements. Example: "incident_created" doesn't have any method or value
        conditions[condition.get("evaluation_id") or i] = u" ".join(filter(None, [str(field_name), str(method), str(value)]))

    if str(activation_conditions.get("logic_type", "")).lower() == "all":
        return u" AND ".join(conditions.values())
    elif str(activation_conditions.get("logic_type", "")).lower() == "any":
        return u" OR ".join(conditions.values())
    else:
        condition_str = activation_conditions.get("custom_condition")
        # here we do two passes to perform a kind of "salting"
        # this is necessary to avoid the condition where in one iteration
        # we replace "1" with "1234" and on the next iteration we replace
        # "2" with something else; in this kind of scenario, we'd be
        # replacing a "2" which we didn't want to
        # So instead, we generate a unique salt and 
        # we replace the original number with that. then on the second pass,
        # we replace the salt with the intended value
        # It is also CRUCIAL that the keys are processed in reverse order
        # to properly handle double digit evaluation IDs
        salts = {}
        for evaluation_id in sorted(conditions.keys(), reverse=True):
            # numbers here are the enemy -- so first we need to map each individual digit to
            # a special string value (I decided to use the corresponding values on the keyboard)
            hashed_eval_id = "".join(constants.SALT_HASH_MAP[id] for id in str(evaluation_id))
            # then add our unique "docgen_{}_salt" prefix to add extra uniqueness
            # NOTE: uniqueness is not guaranteed here from other possible values
            # which we'll be substituting in, but it is unlikely that anyone has
            # "docgen_!@#$_salt" in their system... so uniqueness is practically guaranteed
            salts[evaluation_id] = constants.DOCGEN_SALT_PREFIX.format(hashed_eval_id)
            condition_str = condition_str.replace(str(evaluation_id), salts.get(evaluation_id))
        for evaluation_id in conditions:
            condition_str = condition_str.replace(salts.get(evaluation_id), conditions.get(evaluation_id))
        return condition_str

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
