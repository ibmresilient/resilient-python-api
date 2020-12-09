#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""
Common Helper Functions specific to customize.py, config.py and setup.py files for the resilient-sdk
"""
import logging
import re
import sys
import importlib
import os
import json
import base64
import shutil
import struct
import tempfile
import pkg_resources
from resilient import ImportDefinition
from resilient_sdk.util.resilient_objects import DEFAULT_INCIDENT_TYPE_UUID
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers

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
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)

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

PREFIX_EXTENSION_ZIP = "app-"

PATH_DEFAULT_ICON_EXTENSION_LOGO = pkg_resources.resource_filename("resilient_sdk", "data/ext/icons/app_logo.png")
PATH_DEFAULT_ICON_COMPANY_LOGO = pkg_resources.resource_filename("resilient_sdk", "data/ext/icons/company_logo.png")
PATH_DEFAULT_SCREENSHOT = pkg_resources.resource_filename("resilient_sdk", "data/codegen/templates/package_template/doc/screenshots/main.png")

PATH_SETUP_PY = "setup.py"
PATH_CUSTOMIZE_PY = os.path.join("util", "customize.py")
PATH_CONFIG_PY = os.path.join("util", "config.py")
PATH_UTIL_DATA_DIR = os.path.join("util", "data")
PATH_LOCAL_EXPORT_RES = os.path.join("data", BASE_NAME_LOCAL_EXPORT_RES)
PATH_DOC_DIR = "doc"
PATH_SCREENSHOTS = os.path.join(PATH_DOC_DIR, "screenshots")
PATH_README = "README.md"
PATH_DEFAULT_README = pkg_resources.resource_filename("resilient_sdk", "data/codegen/templates/package_template/README.md.jinja2")

MIN_SETUP_PY_VERSION = "1.0.0"

SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES = (
    "author", "name", "display_name", "version",
    "description", "long_description", "url",
    "install_requires", "entry_points"
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
    "resilient.circuits.apphost.configsection",
    "resilient.circuits.configsection"
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

def parse_setup_py(path, attribute_names):
    """Parse the values of the given attribute_names and return a Dictionary attribute_name:attribute_value

    :param path: Path to setup.py for a package.
    :param attribute_names: List of attribute names to extract from setup.py.
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
        result = eval(setup_callable, {'__builtins__':built_ins}, {"setup": setup})
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
            return_dict[attribute_name] = result.get(attribute_name)

    return return_dict

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
    apikey_permissions = [p.strip() for p in apikey_permissions_lines if not p.lstrip().startswith("#")]

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
        raise SDKException("Icon resolution is {0}x{1}. Resolution must be {2}x{3}\nIcon File:{4}".format(icon_width, icon_height, width_accepted, height_accepted, path_icon_to_use))

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
                     output_dir, path_built_distribution=None, path_extension_logo=None, path_company_logo=None,
                     custom_display_name=None, repository_name=None, keep_build_dir=False):
    """
    TODO: update this docstring to new standard format
    Function that creates The App.zip file from the given setup.py, customize and config files
    and copies it to the output_dir. Returns the path to the App.zip
    - path_setup_py_file [String]: abs path to the setup.py file
    - path_apikey_permissions_file [String]: abs path to the apikey_permissions.txt file
    - output_dir [String]: abs path to the directory the App.zip should be produced
    - path_built_distribution [String]: abs path to a tar.gz Built Distribution
        - if provided uses that .tar.gz
        - else looks for it in the output_dir. E.g: output_dir/package_name.tar.gz
    - path_extension_logo [String]: abs path to the app_logo.png. Has to be 200x72 and a .png file
        - if not provided uses default icon
    - path_company_logo [String]: abs path to the company_logo.png. Has to be 100x100 and a .png file
        - if not provided uses default icon
    - custom_display_name [String]: will give the App that display name. Default: name from setup.py file
    - repository_name [String]: will over-ride the container repository name for the App. Default: 'ibmresilient'
    - keep_build_dir [Boolean]: if True, build/ will not be remove. Default: False
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
        # No 'customize.py' file found generate import definition with just mimimum server version.
        import_definition = {
            'server_version':
                IMPORT_MIN_SERVER_VERSION
        }

    # Add the tag to the import defintion
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
            width_accepted=200,
            height_accepted=72,
            default_path_to_icon=PATH_DEFAULT_ICON_EXTENSION_LOGO)

        company_logo = get_icon(
            icon_name=os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO),
            path_to_icon=path_company_logo,
            width_accepted=100,
            height_accepted=100,
            default_path_to_icon=PATH_DEFAULT_ICON_COMPANY_LOGO)

        # Get the display name
        # Use --display-name if passed
        # If not use 'display_name' attribute in setup.py
        # If not set use the 'name' attribute in setup.py
        display_name = custom_display_name or setup_py_attributes.get("display_name") or setup_py_attributes.get("name")

        # Image string is all lowercase on quay.io
        image_name = "{0}/{1}:{2}".format(repository_name, setup_py_attributes.get("name"), setup_py_attributes.get("version"))
        image_name = image_name.lower()

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
                "content": "<div>{0}</div>".format(setup_py_attributes.get("long_description")),
                "format": "html"
            },
            "minimum_resilient_version": {
                "major": import_definition.get("server_version").get("major", None),
                "minor": import_definition.get("server_version").get("minor", None),
                "build_number": import_definition.get("server_version").get("build_number", None),
                "version": import_definition.get("server_version").get("version", None)
            },
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

        # Write the customize ImportDefinition to the app*.zip export.res file
        sdk_helpers.write_file(path_export_res, json.dumps(import_definition, sort_keys=True))

        # Copy the built distribution to the build dir, enforce rename to .tar.gz
        shutil.copy(path_built_distribution, os.path.join(path_build, "{0}.tar.gz".format(extension_name)))

        # create The Extension Zip by zipping the build directory
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
