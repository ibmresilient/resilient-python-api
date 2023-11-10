#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""
Common Helper Functions specific to customize.py, config.py and setup.py files for the resilient-sdk
"""
import base64
import importlib
import json
import logging
import os
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from collections import defaultdict

import pkg_resources
from resilient import ImportDefinition
from resilient_sdk.util import constants, sdk_helpers
from resilient_sdk.util.resilient_objects import (DEFAULT_INCIDENT_TYPE_UUID,
                                                  ResilientObjMap)
from resilient_sdk.util.sdk_exception import SDKException

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    import ConfigParser as configparser
    from StringIO import StringIO
else:
    # Handle PY 3 specific imports
    import configparser
    from io import StringIO

    # reload(package) in PY2.7, importlib.reload(package) in PY3.6
    reload = importlib.reload

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)

# Constants
BASE_NAME_BUILD = "build"
BASE_NAME_CUSTOMIZE_PY = "customize.py"
BASE_NAME_EXTENSION_JSON = "app.json"
BASE_NAME_EXPORT_RES = "export.res"
BASE_NAME_LOCAL_EXPORT_RES = "export.res"
BASE_NAME_SETUP_PY = "setup.py"
BASE_NAME_DIST_DIR = "dist"
BASE_NAME_DOCKER_FILE = "Dockerfile"
BASE_NAME_ENTRY_POINT = "entrypoint.sh"
BASE_NAME_APIKEY_PERMS_FILE = "apikey_permissions.txt"
BASE_NAME_DOC_DIR = "doc"
BASE_NAME_README = "README.md"
BASE_NAME_VALIDATE_REPORT = "validate_report.md"
BASE_NAME_POLLER_CREATE_CASE_TEMPLATE = "soar_create_case.jinja"
BASE_NAME_POLLER_UPDATE_CASE_TEMPLATE = "soar_update_case.jinja"
BASE_NAME_POLLER_CLOSE_CASE_TEMPLATE = "soar_close_case.jinja"
BASE_NAME_PAYLOAD_SAMPLES_DIR = "payload_samples"
BASE_NAME_PAYLOAD_SAMPLES_SCHEMA = "output_json_schema.json"
BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE = "output_json_example.json"
BASE_NAME_PAYLOAD_SAMPLES_EX_SUCCESS = "mock_json_expectation_success.json"
BASE_NAME_PAYLOAD_SAMPLES_EP_SUCCESS = "mock_json_endpoint_success.json"
BASE_NAME_PAYLOAD_SAMPLES_EX_FAIL = "mock_json_expectation_fail.json"
BASE_NAME_PAYLOAD_SAMPLES_EP_FAIL = "mock_json_endpoint_fail.json"

PATH_DEFAULT_ICON_EXTENSION_LOGO = pkg_resources.resource_filename("resilient_sdk", "data/ext/icons/app_logo.png")
PATH_DEFAULT_ICON_COMPANY_LOGO = pkg_resources.resource_filename("resilient_sdk", "data/ext/icons/company_logo.png")
PATH_DEFAULT_README = pkg_resources.resource_filename("resilient_sdk", "data/codegen/templates/package_template/README.md.jinja2")
PATH_DEFAULT_SCREENSHOT = pkg_resources.resource_filename("resilient_sdk", "data/codegen/templates/package_template/doc/screenshots/main.png")
PATH_DEFAULT_POLLER_CREATE_TEMPLATE = pkg_resources.resource_filename("resilient_sdk",
                    "data/codegen/templates/package_template/package/poller/data/soar_create_case.jinja2")
PATH_DEFAULT_POLLER_CLOSE_TEMPLATE = pkg_resources.resource_filename("resilient_sdk",
                    "data/codegen/templates/package_template/package/poller/data/soar_close_case.jinja2")
PATH_DEFAULT_POLLER_UPDATE_TEMPLATE = pkg_resources.resource_filename("resilient_sdk", 
                    "data/codegen/templates/package_template/package/poller/data/soar_update_case.jinja2")


PATH_TEMPLATE_PAYLOAD_SAMPLES = "payload_samples/function_name"

PATH_CUSTOMIZE_PY = os.path.join("util", BASE_NAME_CUSTOMIZE_PY)
PATH_CONFIG_PY = os.path.join("util", "config.py")
PATH_UTIL_DATA_DIR = os.path.join("util", "data")
PATH_SELFTEST_PY = os.path.join("util", "selftest.py")
PATH_LOCAL_EXPORT_RES = os.path.join("data", BASE_NAME_LOCAL_EXPORT_RES)
PATH_SCREENSHOTS = os.path.join(BASE_NAME_DOC_DIR, "screenshots")
PATH_ICON_EXTENSION_LOGO = os.path.join("icons", "app_logo.png")
PATH_ICON_COMPANY_LOGO = os.path.join("icons", "company_logo.png")
PATH_VALIDATE_REPORT = os.path.join(BASE_NAME_DIST_DIR, BASE_NAME_VALIDATE_REPORT)

PREFIX_EXTENSION_ZIP = "app-"
MIN_SETUP_PY_VERSION = "1.0.0"

SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES = (
    "display_name", "name", "version", "author",
    "author_email", "install_requires", "description",
    "long_description", "url", "entry_points", "python_requires"
)

# Tuple of all Resilient Object Names we support when packaging/converting to ext
SUPPORTED_RES_OBJ_NAMES = (
    "actions", "automatic_tasks", "fields",
    "functions", "incident_artifact_types",
    "incident_types", "message_destinations",
    "phases", "roles", "scripts",
    "types", "workflows", "workspaces"
)

# Base set of api key permissions needed by an app to communicate with the resilient platform.
BASE_PERMISSIONS = [
    "read_data", "read_function"
]
# List of supported entry points.
SUPPORTED_EP = [
    "resilient.circuits.customize",
    "resilient.circuits.configsection",
    "resilient.circuits.selftest"
]
# Minimum server version for import if no customize.py defined.
IMPORT_MIN_SERVER_VERSION = {
    'major': 36,
    'minor': 2,
    'build_number': 0000,
    'version': "36.2.0000"
}

# The default app container repository name.
REPOSITORY_NAME = "ibmresilient"

# Color dict for printing in color
COLORS = {
    "PASS": '\033[92m',
    "GREEN": '\033[92m',
    "DEBUG": '\033[92m',
    "FAIL": '\033[91m',
    "RED": '\033[91m',
    "CRITICAL": '\033[91m',
    "WARNING": '\033[93m',
    "INFO": '\033[94m',
    "SKIPPED": '\033[94m',
    "BLUE": '\033[94m',
    "END": '\033[0m'
}


def get_setup_callable(content):
    """ Parse the setup.py file, returning just the callable setup() section.
    Any embedded function will have the entire line commented out.

    :param content: Content of setup.py as a list of lines.
    :return: Return callable section of section from setup.py as a string.
    """
    regex = re.compile(r'[a-zA-Z0-9_]+\(.*\)')
    sanitized_content = []

    start = False
    for line in content:
        if ('setup(' in line.replace(' ', '')):
            start = True

        if start:
            # comment out lines with embedded functions
            if regex.search(line):
                sanitized_content.append(u'#'+line)
            else:
                sanitized_content.append(line)

    return '\n'.join(sanitized_content)

def parse_setup_py(path, attribute_names, the_globals={}):
    """Parse the values of the given attribute_names and return a Dictionary attribute_name:attribute_value

    :param path: Path to setup.py for a package.
    :param attribute_names: List of attribute names to extract from setup.py.
    :param the_globals: Dict of extra variables required to invoke the setup.py file successfully.
    :return return_dict: Dict of properties from setup.py.
    """
    return_dict = {}
    # Define "True" = bool(True) as value for eval built_ins if using python 2.
    if sys.version_info.major < 3:
        built_ins = {
            "True": bool(True),
            "False": bool(False)
        }
    else:
        built_ins = {}

    the_globals.update({"__builtins__": built_ins})

    # Define a dummy setup function to get the dictionary of parameters returned from evaled setup.py callable.
    def setup(*args, **kwargs):
        return kwargs

    # Read the setup.py content.
    setup_content = sdk_helpers.read_file(path)

    # Raise an error if nothing found in the file.
    if not setup_content:
        raise SDKException(u"No content found in provided setup.py file: {0}".format(path))

    # Get the callable section from contents of setup.py.
    setup_callable = get_setup_callable(setup_content)

    # Run eval on callable content to retrieve attributes.
    try:
        result = eval(setup_callable, the_globals, {"setup": setup})
    except Exception as err:
        raise SDKException(u"Failed to eval setup callable {0}".format(err))

    # Foreach attribute_name, get/calculate its value and add to return_dict
    for attribute_name in attribute_names:
        if attribute_name == "entry_points":
            entry_point_paths = {}
            # Get the path of the top level for the package.
            path_package = os.path.dirname(path)
            for ep in SUPPORTED_EP:
                if result['entry_points'].get(ep):
                    # Extract the relative dotted module reference from entry point values of following types:
                    #      ["customize = fn_func.util.customize:customization_data"]
                    #      ["gen_config = fn_func.util.config:apphost_config_section_data"]
                    #      ["gen_config = fn_func.util.config:config_section_data"]
                    # e.g. Extract ["customize = fn_func.util.customize:customization_data"] -> fn_func.util.customize
                    parsed_ep = ''.join(result['entry_points'].get(ep)).split('=')[1].split(':')[0].strip()
                    # Convert a dotted module reference to an actual python module path:
                    # e.g. Convert fn_func.util.customize -> /path_to_package/fn_func/fn_func/util/customize.py
                    entry_point_paths.update({ep: os.path.join(path_package, parsed_ep
                                                                       .replace(".", os.path.sep)) + ".py"})
            return_dict[attribute_name] = entry_point_paths
        else:
            if result.get(attribute_name):
                value = result.get(attribute_name)

                # clean out spaces in install_requires for better formatting
                if attribute_name == constants.SETUP_PY_INSTALL_REQ_NAME:
                    value = [" ".join(v.split()) for v in value]
                return_dict[attribute_name] = value

    return return_dict


def get_package_name(path_package):
    """
    Using the path to a package, gets the path to the setup.py file
    and validates it. Then parses the file and returns the ``name`` attribute

    :return: the ``name`` attribute in the package's setup.py file or ""
    :rtype: str
    """
    # Generate path to setup.py file + validate we have permissions to read it
    path_setup_py_file = os.path.join(path_package, BASE_NAME_SETUP_PY)
    sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)

    # Parse the setup.py file
    setup_py_attributes = parse_setup_py(path_setup_py_file, SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

    return setup_py_attributes.get("name", "")


def get_dependency_from_install_requires(install_requires, dependency_name):
    """Returns the String of the dependency_name specified in the setup.py file by
    using the install_requires_list parsed from the setup.py file with utils.parse_setup_py()
    to return the name and version of dependency_name

    - install_requires: List  "['resilient_circuits>=31.0.0', 'resilient_lib']"
    - dependency_name: String "resilient_circuits"
    - Return: 'resilient_circuits>=31.0.0'
    """

    # Get the dependency if it includes dependency_name
    dependency = next((d for d in install_requires if dependency_name in d), None)

    if not dependency:
        # pip allows for dependencies to have either "-" or "_" in their names so create a
        # version that is the swapped of what was given to make this method resilient in handling
        # both options
        # eg: both "resilient-circuits" and "resilient_circuits" are allowed as depedencies in
        # the install_requires list
        dependency_name = dependency_name.replace("_", "-") if "_" in dependency_name else dependency_name.replace("-", "_")
        dependency = next((d for d in install_requires if dependency_name in d), None)

    return dependency


def load_customize_py_module(path_customize_py, warn=True):
    """
    Return the path_customize_file as a Python Module.
    We can then access it methods like:
        > result = customize_py_module.codegen_reload_data()

    Raises an SDKException if we fail to load the module

    :param path_customize_py: Path to the customize.py file that contains the module
    :param warn: Boolean to indicate warning should happen, for codegen usage warning not required.
    :return: The customize Python Module, if found
    :rtype: module
    """
    LINE_TO_REPLACE = u"from resilient_circuits"
    REPLACE_TEXT = u"from resilient import ImportDefinition"

    new_lines = []
    current_customize_py_lines = sdk_helpers.read_file(path_customize_py)

    # Check if customize.py has dependencies on resilient-circuits
    for i, line in enumerate(current_customize_py_lines):
        if line.startswith(LINE_TO_REPLACE):
            new_lines = current_customize_py_lines[:i] + [REPLACE_TEXT] + current_customize_py_lines[i + 1:]
            if warn:
                LOG.warning("WARNING: Import References to resilient-circuits are deprecated in v35.0.195. For newer "
                            "versions of resilient-circuits, replace '%s', with '%s' in %s", line.strip(), REPLACE_TEXT,
                            path_customize_py)
            break


    if new_lines:
        # The customize.py has a reference to a deprecated resilient-circuits import. Save the customize.py
        # file as a temporary file with deprecated resilient-circuits import altered then attempt to load
        # the module from the temporary location.
        temp_customize = u"".join(new_lines)

        if sys.version_info.major == 3:
            temp_file_obj = tempfile.NamedTemporaryFile('w', suffix=".py", encoding="utf8", delete=False)
        else:
            temp_customize = temp_customize.encode('utf-8')
            temp_file_obj = tempfile.NamedTemporaryFile('w+b', suffix=".py", delete=False)

        try:
            # Write the new temporary customize.py (with resilient-circuits replaced with resilient)
            with temp_file_obj as temp_file:
                temp_file.write(temp_customize)
                temp_file.flush()
                module_name = os.path.basename(temp_file.name)[:-3]

            # Attempt to import the module from the temporary file location.
            customize_py_module = sdk_helpers.load_py_module(temp_file.name, module_name)

        except IOError as ioerr:
            raise IOError("Unexpected IO error '{0}' for file '{1}".format(ioerr, temp_file.name))

        except Exception as err:
            # An an unexpected error trying to load the module temporary customize module.
            raise SDKException(u"Got an error attempting to load temporary customize.py module\n{0}".format(err))

        finally:
            os.unlink(temp_file.name)

    else:
        try:
            customize_py_module = sdk_helpers.load_py_module(path_customize_py, "customize")
        except Exception as err:
            raise SDKException(u"Failed to load customize.py module\n{0}".format(err))

    return customize_py_module

def remove_default_incident_type_from_import_definition(import_definition):
    """
      Take ImportDefinition as input and remove the DEFAULT_INCIDENT_TYPE added by
       codegen in minify_export.
    :param import_definition dictionary
    :return: import_definition dictionary
    """
    # Get reference to incident_types if there are any
    incident_types = import_definition.get("incident_types", [])

    if incident_types:

        incident_type_to_remove = None

        # Loop through and remove this custom one (that is originally added using codegen)
        for incident_type in incident_types:
            if incident_type.get("uuid") == DEFAULT_INCIDENT_TYPE_UUID:
                incident_type_to_remove = incident_type
                break

        if incident_type_to_remove:
            incident_types.remove(incident_type_to_remove)
    return import_definition

def get_import_definition_from_customize_py(path_customize_py_file):
    """
       Return the ImportDefinition in a customize.py or /util/data/export.res file as a Dictionary.
       :param path_customize_py_file: Path to the customize.py file
       :return import definition dict from /util/data/export.res if the file exists. Otherwise,
               get it from customize.py
    """

    # If there is a /util/data/export.res then get the import definition from there.
    path_src = os.path.dirname(path_customize_py_file)
    path_local_export_res = os.path.join(path_src, PATH_LOCAL_EXPORT_RES)
    if os.path.isfile(path_local_export_res):
        import_definition = get_import_definition_from_local_export_res(path_local_export_res)
        return import_definition

    customize_py = load_customize_py_module(path_customize_py_file)

    # Call customization_data() to get all ImportDefinitions that are "yielded"
    customize_py_import_definitions_generator = customize_py.customization_data()
    customize_py_import_definitions = []

    # customization_data() returns a Generator object with all yield statements, so we loop them
    for definition in customize_py_import_definitions_generator:
        if isinstance(definition, ImportDefinition):
            customize_py_import_definitions.append(json.loads(base64.b64decode(definition.value)))
        else:
            LOG.warning("WARNING: Unsupported data found in customize.py file. Expected an ImportDefinition. Got: '%s'", definition)

    # If no ImportDefinition found
    if not customize_py_import_definitions:
        raise SDKException("No ImportDefinition found in the customize.py file")

    # If more than 1 found
    elif len(customize_py_import_definitions) > 1:
        raise SDKException("Multiple ImportDefinitions found in the customize.py file. There must only be 1 ImportDefinition defined")

    # Get the import defintion as dict
    customize_py_import_definition = customize_py_import_definitions[0]

    # Remove the incident type that was added by codegen that allows the data to import
    customize_py_import_definition = remove_default_incident_type_from_import_definition(customize_py_import_definition)

    return customize_py_import_definition

def get_import_definition_from_local_export_res(path_export_res_file):
    """Return ImportDefinition from a local (/util/data) export.res file as a Dictionary"""

    # Read /util/data/export.res file
    import_definition = sdk_helpers.read_json_file(path_export_res_file)

    # Remove the incident type that was added by codegen that allows the data to import
    import_definition = remove_default_incident_type_from_import_definition(import_definition)

    return import_definition

def get_export_from_zip(path_zip, format_str="zip"):
    """
    Given a path to an export.resz (zip file), extract the export.res file from within.
    This applies to System exports from the UI or Playbook exports from the UI.

    :param path_zip: absolute path to the .resz file
    :type path_zip: str
    :param format: format of the .resz file, always "zip", defaults to "zip"
    :type format: str, optional (other options are "tar", "gztar", "bztar", "xztar")
    :raises SDKException: if given file is not a zip file or if the zip file doesn't have an export.res in it
    :return: the contents of the export.res file within the zip
    :rtype: dict
    """
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(path_zip, "r") as myzip:
            myzip.extractall(temp_dir)
    except zipfile.BadZipfile as err:
        raise SDKException(str(err))

    for file_path in os.listdir(temp_dir):
        if file_path.endswith(".res"):
            export_file_path = os.path.join(temp_dir, file_path)
            break
    else:
        raise SDKException("No export.res found in {0}".format(path_zip))
    export_content = get_import_definition_from_local_export_res(export_file_path)

    shutil.rmtree(temp_dir)

    return export_content

def get_configs_from_config_py(path_config_py_file):
    """Returns a tuple (config_str, config_list). If no configs found, return ("", []).
    Raises Exception if it fails to parse configs
    - config_str: is the full string found in the config file
    - apphost_config_str: is the full string found in the app host config file
    - config_list: is a list of dict objects that contain each un-commented config
        - Each dict object has the attributes: name, placeholder, env_name, section_name
    """

    config_str, config_list = "", []

    try:
        # Get the module name from the config file path by getting basename and stripping '.py'
        # from the rhs of the resulting string.
        config_module = os.path.basename(path_config_py_file)[:-3]
        # Import the config module
        config_py = sdk_helpers.load_py_module(path_config_py_file, config_module)

        # Call config_section_data() to get the string containing the configs
        config_str = config_py.config_section_data()
        # Call apphost_config_section_data available to get app host config settings
        try:
            apphost_config_str = config_py.apphost_config_section_data()
        except AttributeError:
            # An app host config may not exist
            apphost_config_str = None

        # concatenate the config sections
        clean_cfg_list = list(filter(None, [apphost_config_str, config_str]))
        concat_cfg_str = '\n'.join(clean_cfg_list)
        # Iterate over config sections and parse settings.
        for cfg_str in clean_cfg_list:
            # Instansiate a new configparser
            config_parser = configparser.ConfigParser()

            # Read and parse the configs from the config_str or apphost_config_str
            if sys.version_info < (3, 2):
                # config_parser.readfp() was deprecated and replaced with read_file in PY3.2
                config_parser.readfp(StringIO(cfg_str))
            else:
                config_parser.read_file(StringIO(cfg_str))

            # Get the configs from each section
            for section_name in config_parser.sections():
                parsed_configs = config_parser.items(section_name)

                for config in parsed_configs:
                    config_list.append({
                        "name": config[0],
                        "placeholder": config[1],
                        "env_name": "{0}_{1}".format(section_name.upper(), config[0].upper()),
                        "section_name": section_name
                    })

    except ImportError as err:
        raise SDKException(u"Failed to load module '{0}' got error '{1}'".format(config_module, err.__repr__()))

    except Exception as err:
        raise SDKException(u"Failed to parse configs from the config file\nThe config file may be corrupt. Visit "
                           u"the App Exchange to contact the developer\nReason: {0}".format(err))

    return (concat_cfg_str, config_list)

def get_apikey_permissions(path):
    """
    Returns a list of api keys to allow an integration to run.
    :param path: Location to file with api keys one per line.
    :return apikey_permissions: Return list of api keys.
    """

    try:
        # Read the apikey_permissions.txt file into a List
        apikey_permissions_lines = sdk_helpers.read_file(path)

    except Exception as err:
        raise SDKException(u"Failed to parse configs from apikey_permissions.txt file\nThe apikey_permissions.txt file may "
                           u"be corrupt. Visit the App Exchange to contact the developer\nReason: {0}".format(err))

    # Raise an error if nothing found in the file
    if not apikey_permissions_lines:
        raise SDKException(u"No content found in provided apikey_permissions.txt file: {0}".format(path))

    # Get permissions. Ignore comments where 1st non-whitespace character is a '#'.
    apikey_permissions = [p.strip() for p in apikey_permissions_lines if not p.lstrip().startswith("#") and p.strip() != ""]

    # Do basic check on api keys to see if they are in correct format.
    for p in apikey_permissions:
        if not re.match("[_a-zA-Z]*$", p):
            raise SDKException(u"Value '{0}' in file '{1}' is not a valid api key value.".format(p, path))

    # Ensure that the permissions includes at minimum the set of base permissions.
    if not all(p in apikey_permissions for p in BASE_PERMISSIONS):
        raise SDKException(u"'The file '{0}' is missing one of the base api key permissions.".format(path))

    return apikey_permissions

def get_icon(icon_name, path_to_icon, width_accepted, height_accepted, default_path_to_icon):
    """
    TODO: update docstring with correct standard
    Returns the icon at path_to_icon as a base64 encoded string if it is a valid .png file with the resolution
    width_accepted x height_accepted. If path_to_icon does not exist, default_path_to_icon is returned as a base64
    encoded string
    """

    path_icon_to_use = path_to_icon

    # Use default_path_to_icon if path_to_icon does not exist
    if not path_icon_to_use or not os.path.isfile(path_icon_to_use):
        LOG.warning("WARNING: Default icon will be used\nProvided custom icon path for %s is invalid: %s\nNOTE: %s should be placed in the /icons directory", icon_name, path_icon_to_use, icon_name)
        path_icon_to_use = default_path_to_icon

    # Validate path_icon_to_use and ensure we have READ permissions
    try:
        sdk_helpers.validate_file_paths(os.R_OK, path_icon_to_use)
    except SDKException as err:
        raise OSError("Could not find valid icon file. Looked at two locations:\n{0}\n{1}\n{2}".format(path_to_icon, default_path_to_icon, err.message))

    # Get the extension of the file. os.path.splitext returns a Tuple with the file extension at position 1 and can be an empty string
    split_path = os.path.splitext(path_icon_to_use)
    file_extension = split_path[1]

    if not file_extension:
        raise SDKException("Provided icon file does not have an extension. Icon file must be .png\nIcon File: {0}".format(path_icon_to_use))

    elif file_extension != ".png":
        raise SDKException("{0} is not a supported icon file type. Icon file must be .png\nIcon File: {1}".format(file_extension, path_icon_to_use))

    # Open the icon_file in Bytes mode to validate its resolution
    with open(path_icon_to_use, mode="rb") as icon_file:
        # According to: https://en.wikipedia.org/wiki/Portable_Network_Graphics#File_format
        # First need to seek 16 bytes:
        #   8 bytes: png signature
        #   4 bytes: IDHR Chunk Length
        #   4 bytes: IDHR Chunk type
        icon_file.seek(16)

        try:
            # Bytes 17-20 = image width. Use struct to unpack big-endian encoded unsigned int
            icon_width = struct.unpack(">I", icon_file.read(4))[0]

            # Bytes 21-24 = image height. Use struct to unpack big-endian encoded unsigned int
            icon_height = struct.unpack(">I", icon_file.read(4))[0]
        except Exception as err:
            raise SDKException("Failed to read icon's resolution. Icon file corrupt. Icon file must be .png\nIcon File: {0}".format(path_icon_to_use))

    # Raise exception if resolution is not accepted
    if icon_width != width_accepted or icon_height != height_accepted:
        raise SDKException("Icon resolution is {0}x{1}. Resolution must be {2}x{3}\nIcon File: {4}".format(icon_width, icon_height, width_accepted, height_accepted, path_icon_to_use))

    # If we get here all validations have passed. Open the file in Bytes mode and encode it as base64 and decode to a utf-8 string
    with open(path_icon_to_use, "rb") as icon_file:
        encoded_icon_string = base64.b64encode(icon_file.read()).decode("utf-8")

    return encoded_icon_string


def add_tag(tag_name, list_of_objs):
    """
    Returns list_of_objs with tag_name added to each object.
    Replaces any tags that were there originally to address bug INT-3077

    :param tag_name: The name of the tag to add
    :param list_of_objs: A list of all the objects you want to add the tag too
    :raise: SDKException: if list_of_objs is corrupt
    :return: list_of_objs with tag_name added to each object
    :rtype: list of dicts
    """
    # Create tag_to_add
    tag_to_add = {
        "tag_handle": tag_name,
        "value": None
    }

    err_msg = "Error adding tag '{0}'. '{1}' (printed above) is not a {2}. Instead a {3} was provided.\nProvided ImportDefinition in the customize.py file may be corrupt"

    # Check list_of_objs is a List
    if not isinstance(list_of_objs, list):
        LOG.error("Error adding tag.\n'list_of_objs': %s", list_of_objs)
        raise SDKException(err_msg.format(tag_name, "list_of_objs", "List", type(list_of_objs)))

    # Loop each object in the List
    for obj in list_of_objs:

        # If its not a dict, error
        if not isinstance(obj, dict):
            LOG.error("Error adding tag.\n'list_of_objs': %s\n'obj': %s", list_of_objs, obj)
            raise SDKException(err_msg.format(tag_name, "obj", "Dictionary", type(obj)))

        # Set the obj's 'tags' value to tag_to_add
        obj["tags"] = [tag_to_add]

    # Return the updated list_of_objs
    return list_of_objs


def add_tag_to_import_definition(tag_name, supported_res_obj_names, import_definition):
    """
    TODO: update this docsting to correct standard
    Returns import_definition with tag_name added to each supported_res_object_name found
    in the import_definition
    """

    for obj_name in supported_res_obj_names:

        res_object_list = import_definition.get(obj_name)

        if res_object_list:
            res_object_list = add_tag(tag_name, res_object_list)

            # A 'function' object has a list of 'workflows' which also need the tag added to
            if obj_name == "functions":
                res_functions_list = import_definition.get("functions")

                for fn in res_functions_list:
                    fn_workflows_list = fn.get("workflows")

                    if fn_workflows_list:
                        fn_workflows_list = add_tag(tag_name, fn_workflows_list)

    return import_definition

def get_configuration_py_file_path(file_type, setup_py_attributes):
    """  Get the location of configuration file config or customize for a package.

    If file_type == "customize" check that entry point 'resilient.circuits.apphost.customize' (SUPPORTED_EP[0])
    is defined in setup.py of the package.
    If file_type == "config" check that entry point 'resilient.circuits.apphost.configsection' (SUPPORTED_EP[1]) is
    defined in setup.py of the package, else check 'resilient.circuits.configsection' (SUPPORTED_EP[2]) was detected in
    setup.py of the package.

    Note: For some packages neither of these files may exist not exist.

    :param file_type: File whose location is required should be 'customize' or 'config'.
    :param setup_py_attributes: Parsed setup.py content.
    :return path_py_file: The customize or config file location for the package.
    """
    path_py_file = None

    if file_type == "customize":
        if SUPPORTED_EP[0] in setup_py_attributes["entry_points"]:
            path_py_file = setup_py_attributes["entry_points"][SUPPORTED_EP[0]]
    elif file_type == "config":
        for ep in SUPPORTED_EP[1:]:
            if ep in setup_py_attributes["entry_points"]:
                path_py_file = setup_py_attributes["entry_points"][ep]
                break
    else:
        raise SDKException("Unknown option '{}'.".format(file_type))

    if path_py_file:
        # If configuration file defined in setup.py but does not exist raise an error.
        try:
            sdk_helpers.validate_file_paths(os.R_OK, path_py_file)
        except SDKException:
            LOG.info("Configuration File '%s' defined as an entry point in 'setup.py' not found at location '%s'.",
                     file_type, path_py_file)
            if not sdk_helpers.validate_file_paths(os.R_OK, path_py_file):
                raise SDKException("Configuration File '{0}' defined as an entry point in 'setup.py' not found at "
                                   "location '{1}'.".format(file_type, path_py_file))
    else:
        # For certain packages or threat-feeds these files may not exist.
        # Warn user if file not found.
        LOG.warning("WARNING: Configuration File of type '%s' not defined in 'setup.py'. Ignoring and continuing.",
                    file_type)

    return path_py_file

def create_extension(path_setup_py_file, path_apikey_permissions_file,
                     output_dir, path_built_distribution=None, path_extension_logo=None, path_company_logo=None, path_payload_samples=None, path_validate_report=None,
                     custom_display_name=None, repository_name=None, image_hash=None, keep_build_dir=False):
    """
    Function that creates The App.zip file from the given setup.py, customize and config files
    and copies it to the output_dir. Returns the path to the app.zip

    :param path_setup_py_file: abs path to the setup.py file
    :type path_setup_py_file: str
    :param path_apikey_permissions_file: abs path to the apikey_permissions.txt file
    :type path_apikey_permissions_file: str
    :param output_dir: abs path to the directory the App.zip should be produced
    :type output_dir: str
    :param path_built_distribution: abs path to a tar.gz Built Distribution
        - if provided uses that .tar.gz
        - else looks for it in the output_dir. E.g: output_dir/package_name.tar.gz
    :type path_built_distribution: str
    :param path_extension_logo: abs path to the app_logo.png. Has to be 200x72 and a .png file
        - if not provided uses default icon
    :type path_extension_logo: str
    :param path_company_logo: abs path to the company_logo.png. Has to be 100x100 and a .png file
        - if not provided uses default icon
    :type path_company_logo: str
    :param path_payload_samples: abs path to directory containing the files with a JSON schema and example output of the functions
    :type path_payload_samples: str
    :param path_validate_report: abs path to directory containing the validation report - to be copied to the build directory that will be zipped
    :type path_validate_report: str
    :param custom_display_name: will give the App that display name. Default: name from setup.py file
    :type custom_display_name: str
    :param repository_name: will over-ride the container repository name for the App. Default: 'ibmresilient'
    :type repository_name: str
    :param image_hash: if defined will append the hash to the image_name in the app.json file e.g. <repository_name>/<package_name>@sha256:<image_hash>. Default: <repository_name>/<package_name>:<version>
    :type image_hash: str
    :param keep_build_dir: if True, build/ will not be removed. Default: False
    :type keep_build_dir: bool
    :return: Path to new app.zip
    :rtype: str
    """

    LOG.info("Creating App")
    # Variables to hold path of files for customize and config as defined in setup.py.
    # Set initially default to 'None', actual paths will be calculated later.
    path_customize_py_file = None
    path_config_py_file = None

    # Ensure the output_dir exists, we have WRITE access and ensure we can READ setup.py and apikey_permissions.txt
    # files.
    sdk_helpers.validate_dir_paths(os.W_OK, output_dir)
    sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file, path_apikey_permissions_file)

    # Parse the setup.py file
    setup_py_attributes = parse_setup_py(path_setup_py_file, SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

    # Validate setup.py attributes

    # Validate the name attribute. Raise exception if invalid
    if not sdk_helpers.is_valid_package_name(setup_py_attributes.get("name")):
        raise SDKException("'{0}' is not a valid App name. The name attribute must be defined and can only include 'a-z and _'.\nUpdate this value in the setup.py file located at: {1}".format(setup_py_attributes.get("name"), path_setup_py_file))

    # Validate the version attribute. Raise exception if invalid
    if not sdk_helpers.is_valid_version_syntax(setup_py_attributes.get("version")):
        raise SDKException("'{0}' is not a valid App version syntax. The version attribute must be defined. Example: version=\"1.0.0\".\nUpdate this value in the setup.py file located at: {1}".format(setup_py_attributes.get("version"), path_setup_py_file))

    # Validate the url supplied in the setup.py file, set to an empty string if not valid
    if not sdk_helpers.is_valid_url(setup_py_attributes.get("url")):
        LOG.warning("WARNING: '%s' is not a valid url. Ignoring.", setup_py_attributes.get("url"))
        setup_py_attributes["url"] = ""

    # Get the tag name
    tag_name = setup_py_attributes.get("name")

    # Get the customize file location.
    path_customize_py_file = get_configuration_py_file_path("customize", setup_py_attributes)

    # Get the config file location.
    path_config_py_file = get_configuration_py_file_path("config", setup_py_attributes)

    # Get ImportDefinition from the discovered customize file.
    if path_customize_py_file:
        import_definition = get_import_definition_from_customize_py(path_customize_py_file)
    else:
        # No 'customize.py' file found generate import definition with just minimum server version.
        import_definition = {
            'server_version':
                IMPORT_MIN_SERVER_VERSION
        }

    # Add the tag to the import definition
    import_definition = add_tag_to_import_definition(tag_name, SUPPORTED_RES_OBJ_NAMES, import_definition)

    # Parse the app.configs from the discovered config file
    if path_config_py_file:
        app_configs = get_configs_from_config_py(path_config_py_file)
    else:
        # No config file file found generate an empty definition.
        app_configs = ("", [])

    # Parse the api key permissions from the apikey_permissions.txt file
    apikey_permissions = get_apikey_permissions(path_apikey_permissions_file)

    # Generate the name for the extension
    extension_name = "{0}-{1}".format(setup_py_attributes.get("name"), setup_py_attributes.get("version"))

    # Generate the uuid
    uuid = sdk_helpers.generate_uuid_from_string(setup_py_attributes.get("name"))

    # Set the container repository name to default if value not passed in as argument.
    if not repository_name:
        repository_name = REPOSITORY_NAME

    # Generate paths to the directories and files we will use in the build directory
    path_build = os.path.join(output_dir, BASE_NAME_BUILD)
    path_extension_json = os.path.join(path_build, BASE_NAME_EXTENSION_JSON)
    path_export_res = os.path.join(path_build, BASE_NAME_EXPORT_RES)

    try:
        # If there is an old build directory, remove it first
        if os.path.exists(path_build):
            shutil.rmtree(path_build)

        # Create the directories for the path "/build/"
        os.makedirs(path_build)

        # If no path_built_distribution is given, use the default: "<output_dir>/<package-name>.tar.gz"
        if not path_built_distribution:
            path_built_distribution = os.path.join(output_dir, "{0}.tar.gz".format(extension_name))

        # Validate the built distribution exists and we have READ access
        sdk_helpers.validate_file_paths(os.R_OK, path_built_distribution)

        # Copy the built distribution to the build dir and enforce rename to .tar.gz
        shutil.copy(path_built_distribution, os.path.join(path_build, "{0}.tar.gz".format(extension_name)))

        # Get the extension_logo (icon) and company_logo (author.icon) as base64 encoded strings
        extension_logo = get_icon(
            icon_name=os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO),
            path_to_icon=path_extension_logo,
            width_accepted=constants.ICON_APP_LOGO_REQUIRED_WIDTH,
            height_accepted=constants.ICON_APP_LOGO_REQUIRED_HEIGHT,
            default_path_to_icon=PATH_DEFAULT_ICON_EXTENSION_LOGO)

        company_logo = get_icon(
            icon_name=os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO),
            path_to_icon=path_company_logo,
            width_accepted=constants.ICON_COMPANY_LOGO_REQUIRED_WIDTH,
            height_accepted=constants.ICON_COMPANY_LOGO_REQUIRED_HEIGHT,
            default_path_to_icon=PATH_DEFAULT_ICON_COMPANY_LOGO)

        # Get the display name
        # Use --display-name if passed
        # If not use 'display_name' attribute in setup.py
        # If not set use the 'name' attribute in setup.py
        display_name = custom_display_name or setup_py_attributes.get("display_name") or setup_py_attributes.get("name")

        # Image string is all lowercase on quay.io
        image_name = "{0}/{1}:{2}".format(repository_name, setup_py_attributes.get("name"), setup_py_attributes.get("version"))

        if image_hash:

            if not sdk_helpers.is_valid_hash(image_hash):
                raise SDKException(u"image_hash '{0}' is not a valid SHA256 hash\nIt must be a valid hexadecimal and 64 characters long".format(image_hash))

            # If image_hash is defined append to image name e.g. <repository_name>/<package_name>@sha256:<image_hash>
            image_name = "{0}/{1}@sha256:{2}".format(repository_name, setup_py_attributes.get("name"), image_hash)

        image_name = image_name.lower()

        LOG.debug("image_name generated: %s", image_name)

        # Generate the contents for the extension.json file
        the_extension_json_file_contents = {
            "author": {
                "name": setup_py_attributes.get("author"),
                "website": setup_py_attributes.get("url"),
                "icon": {
                    "data": company_logo,
                    "media_type": "image/png"
                }
            },
            "description": {
                "content": setup_py_attributes.get("description"),
                "format": "text"
            },
            "display_name": display_name,
            "icon": {
                "data": extension_logo,
                "media_type": "image/png"
            },
            "long_description": {
                "content": u"<div>{0}</div>".format(setup_py_attributes.get("long_description")),
                "format": "html"
            },
            "minimum_resilient_version": import_definition.get("server_version", {}),
            "name": setup_py_attributes.get("name"),
            "tag": {
                "prefix": tag_name,
                "name": tag_name,
                "display_name": tag_name,
                "uuid": uuid
            },
            "uuid": uuid,
            "version": setup_py_attributes.get("version"),
            "current_installation": {
                "executables": [
                    {
                        "name": setup_py_attributes.get("name"),
                        "image": image_name,
                        "config_string": app_configs[0],
                        "permission_handles": apikey_permissions,
                        "uuid": uuid
                    }
                ]
            }
        }

        # Write the executable.json file
        sdk_helpers.write_file(path_extension_json, json.dumps(the_extension_json_file_contents, sort_keys=True))

        # Gather payload_samples file for each function and add to export.res file if exists
        if not path_payload_samples:
            LOG.warning("WARNING: No path for 'payload_samples' provided. Skipping adding them to the export.res file")

        else:
            for fn in import_definition.get("functions"):

                # Get paths to payload_samples
                fn_name = fn.get(ResilientObjMap.FUNCTIONS)
                path_payload_samples_fn = os.path.join(path_payload_samples, fn_name)
                path_payload_samples_schema = os.path.join(path_payload_samples_fn, BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)
                path_payload_samples_example = os.path.join(path_payload_samples_fn, BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)

                try:
                    # Validate payload_files, add custom error message if we can't
                    sdk_helpers.validate_file_paths(os.R_OK, path_payload_samples_schema, path_payload_samples_example)
                except SDKException as err:
                    err.message += ("\nWARNING: could not access JSON file to add payload_samples. Continuing to create package.\n"
                                    "Add '--no-samples' flag to avoid looking for them and avoid this warning message.\n")
                    LOG.warning(err.message)
                    continue

                # Read in schema payload and add to function import definition
                payload_samples_schema_contents_dict = sdk_helpers.read_json_file(path_payload_samples_schema)
                LOG.debug("Adding JSON output schema to '%s' from file: %s", fn_name, path_payload_samples_schema)
                json_schema_key = os.path.splitext(BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)[0]
                fn[json_schema_key] = json.dumps(payload_samples_schema_contents_dict)

                # Read in example payload and add to function import definition
                payload_samples_example_contents_dict = sdk_helpers.read_json_file(path_payload_samples_example)
                LOG.debug("Adding JSON output example to '%s' from file: %s", fn_name, path_payload_samples_example)
                json_example_key = os.path.splitext(BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)[0]
                fn[json_example_key] = json.dumps(payload_samples_example_contents_dict)

        if path_validate_report:
            path_zipped_validate_report = os.path.join(path_build, os.path.basename(path_validate_report))
            shutil.copy(path_validate_report, path_zipped_validate_report)
        else:
            LOG.warn("WARNING: If a validation report is not included with your submission, it will get rejected. Run this command with the '--validate' flag to include validations.")

        # Write the customize ImportDefinition to the app*.zip export.res file
        sdk_helpers.write_file(path_export_res, json.dumps(import_definition, sort_keys=True))

        # Copy the built distribution to the build dir, enforce rename to .tar.gz
        shutil.copy(path_built_distribution, os.path.join(path_build, "{0}.tar.gz".format(extension_name)))

        # Create the app.zip (Extension Zip) by zipping the build directory
        extension_zip_base_path = os.path.join(output_dir, "{0}{1}".format(PREFIX_EXTENSION_ZIP, extension_name))
        extension_zip_name = shutil.make_archive(base_name=extension_zip_base_path, format="zip", root_dir=path_build)
        path_the_extension_zip = os.path.join(extension_zip_base_path, extension_zip_name)

    except SDKException as err:
        raise err

    except Exception as err:
        raise SDKException(err)

    finally:
        # Remove the build dir. Keep it if user passes --keep-build-dir
        if not keep_build_dir:
            shutil.rmtree(path_build)

    LOG.info("App %s.zip created", "{0}{1}".format(PREFIX_EXTENSION_ZIP, extension_name))

    # Return the path to the extension zip
    return path_the_extension_zip

def get_required_python_version(python_requires_str):
    """
    Given a value from the 'python_requires' attribute of setup.py, parse out the
    numerical value given for the version required.

    :param python_requires_str: str representation of the value assosciated with the 'python_requires' attr in setup.py
    :raise SDKException: if format of python_requires is not correct (i.e. in '>=<version>' format)
    :return: return the minimum required python version or None if not found
    :rtype: tuple with (<major>, <minor>) version format
    """
    try:
        version_str = re.match(r"(?:>=)([0-9]+[\.0-9]*)", python_requires_str).groups()[0]
        version = pkg_resources.parse_version(version_str)
        
        return sdk_helpers.parse_version_object(version)
    except AttributeError as e:
        raise SDKException("'python_requires' version not given in correct format.")

def check_package_installed(package_name):
    """
    Uses pkg_resources.require to certify that a package is installed
    
    :param package_name: name of package
    :type package_name: str
    :return: boolean value whether or not package is installed in current python env
    :rtype: bool
    """
    try:
        pkg_resources.require(package_name)
    except pkg_resources.DistributionNotFound:
        return False

    return True

def color_output(s, level, do_print=False):
    """
    Uses class COLORS to color given string. 'level' maps to values in COLORS dict.
    If do_print is set, logs out 's'

    :param s: value to be wrapped in color
    :type s: str
    :param level: map to COLORS dict defined as constant above
    :type level: str
    :param do_print: If True, logs the string to the stdout
    :type do_print: bool
    :return: colored output of 's'
    :rtype: str
    """
    text = u"{0}{1}{2}".format(COLORS.get(level), s, COLORS.get("END"))

    if do_print:
        LOG.info(text)

    return text

def color_diff_output(diff):
    """
    Colors output of a diff iterator.
    Makes lines that are '-' red and '+' green.

    :param diff: generator of diffs
    :type diff: Iterator[str]
    :return: colored generator of diffs
    :rtype: Iterator[str]
    """

    key_pairs = [
        ("+++", COLORS.get("GREEN")),
        ("+", COLORS.get("GREEN")),
        ("---", COLORS.get("RED")),
        ("-", COLORS.get("RED")),
        ("^", COLORS.get("BLUE")),
    ]

    for line in diff:
        for key, color in key_pairs:
            if line.startswith(key):
                yield  color + line[0:len(key)] + COLORS.get("END") + line[len(key):]
                break
        else:
            yield line

def parse_file_paths_from_readme(readme_line_list):
    """
    Takes a list of strings and looks through to find the links characters in markdown: 
    ![<fall_back_name>](<link_to_screenshot>)
    The method will raise an SDKException if there is a link started without the provided parenthetical
    link in correct syntax.
    If no exception is raised, it returns a list of filepaths for linked images in the readme.

    :param readme_line_list: list of readme lines that will have the comment lines removed
    :type readme_line_list: list[str]
    :raises: SDKException if link given in invalid syntax
    :return: list of paths to linked files
    :rtype: list[str]
    """

    paths = []

    # first, filter out any comments as those might contain invalid screenshot paths
    readme_line_list = re.sub(r"(<!--.*?-->)", "", "".join(readme_line_list), flags=re.DOTALL).splitlines()

    # loop through the lines of the readme
    for line in readme_line_list:

        line = line.strip() # strip any leading and trailing whitespace

        # check if the line starts with the Markdown syntax for a linked file
        if line.startswith("!["):
            if "(" in line and ")" in line:
                # look to find the linked file between ( )
                paths.append(line[line.rfind("(")+1:line.rfind(")")])
            else:
                # incorrect syntax for line starting with "![" but not including "( ... )"
                raise SDKException(u"Line '{0}' in README has invalid link syntax".format(line))

    return paths


def check_validate_report_exists():
    """
    Goes into the dist directory and looks for the validate_report.md. If it exists, returns the path.
    If it doesn't exists, returns None

    :return: path of the validate_report.md if it exists else None
    :rtype: str
    """

    return PATH_VALIDATE_REPORT if os.path.exists(PATH_VALIDATE_REPORT) else None


def parse_dockerfile(path):
    """ 
    Reads through a Dockerfile line by line and adds commands to a dictionary
    The dictionary has the following format - {"COMMAND":[list_of_arguments]}.
    This means that if line 1 is "RUN yum clean" and line 2 is "RUN yum install", the resulting dictionary would be
    {"RUN":["yum clean","yum install"]}
    
    Does not yet support multi-line commands

    :param path: Path to dockerfile
    """

    found_commands = defaultdict(lambda: [])
    lines = sdk_helpers.read_file(path)
    for line in lines: 
        # split the line into the command and the argument, and strip any extra characters
        split_line = line.strip().split(" ")
        if split_line[0] == "#" or split_line[0] == "": # skip comments
            continue
        found_commands[split_line[0]].append(' '.join(split_line[1:])) # makes a list of arguments per command i.e. maps "RUN" to all RUN commands

    return found_commands


def color_lines(log_level, lines):
    """
    Takes a list of strs and adds the given log_level
    color to the str. Then returns the list of ``colored_lines``

    Note: colored_lines[0] will always be a ``constants.LOG_DIVIDER``

    See ``print_latest_version_warning`` method for an example usage

    :param log_level: map to COLORS dict defined as constant above
    :type log_level: str
    :param lines: list of strings to add color to
    :type lines: [str]
    :return: List of colored_lines or an empty list if ``lines`` is falsy
    :rtype: [str] | None
    """

    colored_lines = []

    if not lines:
        return colored_lines

    colored_lines.append(color_output(constants.LOG_DIVIDER, log_level))

    for l in lines:
        colored_lines.append(color_output(l, log_level))

    return colored_lines


def print_latest_version_warning(current_version, latest_available_version):
    """
    Convert all text to yellow and LOG a warning message
    with current_version and latest_available_version
    """

    log_level = "WARNING"

    colored_lines = color_lines(log_level, [
        "{0}:".format(log_level),
        "'{0}' is not the latest version of the resilient-sdk. 'v{1}' is available on https://pypi.org/project/resilient-sdk/".format(current_version, latest_available_version),
        "To update run:",
        "$ pip install -U resilient-sdk"
    ])

    w = "{0}\n{1}\n{2}\n\n{3}\n\t{4}\n{0}".format(colored_lines[0], colored_lines[1], colored_lines[2], colored_lines[3], colored_lines[4])

    LOG.warning(w)

def make_list_of_dicts_unique(list_of_dicts):
    """
    Creates temporary dictionary of schema str(dict):dict
    for each dict in the list, then captures the values
    of the temporary dictionary (just the dict side) and
    returns that list. The crucial part of this is that the
    temporary dictionary keys are unique -- thus guaranteeing
    that any two dictionaries whose str() cast would be the same,
    won't appear more than once in the temporary object.

    :param list_of_dicts: List of dictionaries to make unique
    :type list_of_dicts: list[dict]
    :return: same list as started with with any extra duplicates removed
    :rtype: list[dict]
    """

    # .values() only grabs each x from the unique, temporary dictionary created in-line
    unique_list = list({str(x): x for x in list_of_dicts}.values())
    return unique_list
