#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""
Common Helper Functions specific to customize.py, config.py and setup.py files for the resilient-sdk
"""
import logging
import re
import sys
import importlib
import os
import io
import json
import base64
from resilient import ImportDefinition
from resilient_sdk.util.resilient_objects import DEFAULT_INCIDENT_TYPE_UUID
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.helpers import (load_py_module,
                                        read_file,
                                        rename_to_bak_file,
                                        write_file,
                                        rename_file)

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    import ConfigParser as configparser
else:
    # Handle PY 3 specific imports
    import configparser

    # reload(package) in PY2.7, importlib.reload(package) in PY3.6
    reload = importlib.reload

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES = (
    "author", "name", "version",
    "description", "long_description", "url",
    "install_requires"
)


def _is_setup_attribute(line):
    """Use RegEx to check if the given file line starts with (for example) 'long_description='.
    Will also handle if the attribute has been commented out: '# long_description='.
    Returns True if something like 'long_description=' is at the start of the line, else False"""

    any_attribute_regex = re.compile(r'^#?\s*[a-z_]+=')

    if re.match(pattern=any_attribute_regex, string=line) is not None:
        return True

    return False


def _parse_setup_attribute(path_to_setup_py, setup_py_lines, attribute_name):
    """Returns the attribute value from setup.py given the attribute name"""

    # Generate the regex to find the attribute line
    the_attribute_regex = re.compile("^{0}=".format(attribute_name))

    # Store the contents of the attribute
    the_attribute_found, the_attribute_value = False, []

    # Loop the setup_py lines
    for i in range(len(setup_py_lines)):
        the_attribute_line = setup_py_lines[i]

        # Check if this line contains the attribute_name
        if re.match(pattern=the_attribute_regex, string=the_attribute_line):

            # If found, flip flag + append the line to the_attribute_value
            the_attribute_found = True
            the_attribute_value.append(re.split(pattern=the_attribute_regex, string=the_attribute_line)[1])

            # Check preceding lines to see if this attribute value is multiline string
            for preceding_line in setup_py_lines[i + 1:]:
                if _is_setup_attribute(preceding_line):
                    break

                # Append the line if it is not a new attribute
                the_attribute_value.append(preceding_line)

            break

    # If we could not find an attribute with attribute_name, log a warning
    if not the_attribute_found:
        LOG.warning("WARNING: '%s' is not a defined attribute name in the provided setup.py file: %s", attribute_name, path_to_setup_py)

    # Create single string and trim (" , ' )
    the_attribute_value = " ".join(the_attribute_value)
    the_attribute_value = the_attribute_value.strip("\",'.")

    return the_attribute_value


def parse_setup_py(path, attribute_names):
    """Parse the values of the given attribute_names and return a Dictionary attribute_name:attribute_value"""

    # Read the setup.py file into a List
    setup_py_lines = read_file(path)

    # Raise an error if nothing found in the file
    if not setup_py_lines:
        raise SDKException(u"No content found in provided setup.py file: {0}".format(path))

    setup_regex_pattern = r"setup\("
    setup_defined, index_of_setup, return_dict = False, None, dict()

    for i in range(len(setup_py_lines)):

        if re.match(pattern=setup_regex_pattern, string=setup_py_lines[i]) is not None:
            setup_defined = True
            index_of_setup = i
            break

    # Raise an error if we can't find 'setup()' in the file
    if not setup_defined:
        raise SDKException(u"Could not find 'setup()' defined in provided setup.py file: {0}".format(path))

    # Get sublist containing lines from 'setup(' to EOF + trim whitespaces
    setup_py_lines = setup_py_lines[index_of_setup:]
    setup_py_lines = [file_line.strip() for file_line in setup_py_lines]

    # Foreach attribute_name, get its value and add to return_dict
    for attribute_name in attribute_names:
        return_dict[attribute_name] = _parse_setup_attribute(path, setup_py_lines, attribute_name)

    return return_dict


def get_dependency_from_install_requires_str(install_requires_str, dependency_name):
    """Returns the String of the dependency_name specified in the setup.py file by
    using the install_requires_str parsed from the setup.py file with utils.parse_setup_py()
    to return the name and version of dependency_name

    - install_requires_str: String  "['resilient_circuits>=31.0.0', 'resilient_lib']"
    - dependency_name: String "resilient_circuits"
    - Return: 'resilient_circuits>=31.0.0' """

    # Remove first + last character if they are [ or ]
    if install_requires_str[0] == "[":
        install_requires_str = install_requires_str[1:]

    if install_requires_str[-1] == "]":
        install_requires_str = install_requires_str[:-1]

    # Remove start + trailing whitespace
    install_requires_str = install_requires_str.strip()

    # Convert str to list on comma
    dependencies = install_requires_str.split(",")

    # Remove start + trailing whitespace, ' or " for each dependency
    dependencies = [d.strip(" '\"") for d in dependencies]

    # Get the dependency if it includes dependency_name
    dependency = next((d for d in dependencies if dependency_name in d), None)

    return dependency


def load_customize_py_module(path_customize_py):
    """
    Return the path_customize_file as a Python Module.
    We can then access it methods like:
        > result = customize_py_module.codegen_reload_data()

    Raises an SDKException if we fail to load the module

    :param path_customize_py: Path to the customize.py file that contains the module
    :return: The customize Python Module, if found
    :rtype: module
    """
    LINE_TO_REPLACE = u"from resilient_circuits"
    REPLACE_TEXT = u"from resilient import ImportDefinition\n"

    # Try to load the customize.py module.
    # Some customize.py files (older) have a dependency on resilient_circuits.
    # In this case, the import will fail.
    # So if it does, we try replace the line of code in customize.py
    # that starts with "from resilient_circuits" with "from resilient import ImportDefinition".
    try:
        customize_py_module = load_py_module(path_customize_py, "customize")
    except ImportError as err:
        LOG.warning("WARNING: Failed to load customize.py\n%s", err)

        new_lines, path_backup_customize_py = [], ""
        current_customize_py_lines = read_file(path_customize_py)

        # Loop lines
        for i, line in enumerate(current_customize_py_lines):
            if line.startswith(LINE_TO_REPLACE):
                new_lines = current_customize_py_lines[:i] + [REPLACE_TEXT] + current_customize_py_lines[i + 1:]
                break

        # if new_lines means we have replaced some old lines
        if new_lines:

            # Create backup!
            path_backup_customize_py = rename_to_bak_file(path_customize_py)

            try:
                # Write the new customize.py
                write_file(path_customize_py, u"".join(new_lines))

                # Try loading again customize module
                customize_py_module = load_py_module(path_customize_py, "customize")

            except Exception as err:
                # TODO: move this rename to a finally block in case user uses keyboard interrupt...
                # If an error trying to load the module again and customize.py does not exist
                # rename the backup file to original
                if not os.path.isfile(path_customize_py):
                    LOG.info(u"An error occurred. Renaming customize.py.bak to customize.py")
                    rename_file(path_backup_customize_py, "customize.py")

                raise SDKException(u"Failed to load customize.py module\n{0}".format(err))

        # Else we did not match resilient_circuits, file corrupt.
        # We only support one instance of "from resilient_circuits"
        # If different means developer modified customize.py manually
        else:
            raise SDKException(u"Failed to load customize.py module. The file is corrupt\n{0}".format(err))

    return customize_py_module


def get_import_definition_from_customize_py(path_customize_py_file):
    """Return the base64 encoded ImportDefinition in a customize.py file as a Dictionary"""

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

    # Get reference to incident_types if there are any
    incident_types = customize_py_import_definition.get("incident_types", [])

    if incident_types:

        incident_type_to_remove = None

        # Loop through and remove this custom one (that is originally added using codegen)
        for incident_type in incident_types:
            if incident_type.get("uuid") == DEFAULT_INCIDENT_TYPE_UUID:
                incident_type_to_remove = incident_type
                break

        if incident_type_to_remove:
            incident_types.remove(incident_type_to_remove)

    return customize_py_import_definition


def get_configs_from_config_py(path_config_py_file):
    """Returns a tuple (config_str, config_list). If no configs found, return ("", []).
    Raises Exception if it fails to parse configs
    - config_str: is the full string found in the config.py file
    - config_list: is a list of dict objects that contain each un-commented config
        - Each dict object has the attributes: name, placeholder, env_name, section_name
    """

    config_str, config_list = "", []

    try:
        # Import the config module
        config_py = load_py_module(path_config_py_file, "config")

        # Call config_section_data() to get the string containing the configs
        config_str = config_py.config_section_data()

        # Instansiate a new configparser
        config_parser = configparser.ConfigParser()

        # Read and parse the configs from the config_str
        if sys.version_info < (3, 2):
            # config_parser.readfp() was deprecated and replaced with read_file in PY3.2
            config_parser.readfp(io.StringIO(config_str))

        else:
            config_parser.read_file(io.StringIO(config_str))

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

    except Exception as err:
        raise SDKException(u"Failed to parse configs from config.py file\nThe config.py file may be corrupt. Visit the App Exchange to contact the developer\nReason: {0}".format(err))

    return (config_str, config_list)
