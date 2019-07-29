#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
# pylint: disable=line-too-long

""" Python Module that exposes the ExtCreate class """

import logging
import os
import io
import json
import re
import shutil
import sys
import base64
import importlib
import struct
import pkg_resources
from jinja2 import Environment, PackageLoader
from resilient_circuits.util.resilient_customize import ImportDefinition
from resilient_circuits.util.ext.Ext import Ext
from resilient_circuits.util.ext.ExtException import ExtException

# Handle import of ConfigParser + importlib.reload() for PY 2 + 3
if sys.version_info.major < 3:
    import ConfigParser as configparser
else:
    import configparser

    # reload(package) in PY2.7, importlib.reload(package) in PY3.6
    reload = importlib.reload

# Get the same logger object that is used in resilient_circuits_cmd.py
LOG = logging.getLogger("resilient_circuits_cmd_logger")

# Constants
BASE_NAME_BUILD = "build"
BASE_NAME_EXTENSION_JSON = "extension.json"
BASE_NAME_EXPORT_RES = "export.res"
BASE_NAME_EXECUTABLES = "executables"
BASE_NAME_EXECUTABLE_JSON = "executable.json"
BASE_NAME_EXECUTABLE_DOCKERFILE = "Dockerfile"

PREFIX_EXECUTABLE_ZIP = "exe-"
PREFIX_EXTENSION_ZIP = "ext-"

JINJA_TEMPLATE_DOCKERFILE = "docker_file_template.jinja2"

PATH_DEFAULT_ICON_EXTENSION_LOGO = pkg_resources.resource_filename("resilient_circuits", "data/ext/icons/extension_logo.png")
PATH_DEFAULT_ICON_COMPANY_LOGO = pkg_resources.resource_filename("resilient_circuits", "data/ext/icons/company_logo.png")

# Default incident_type to remove from customize.py (if found)
DEFAULT_INCIDENT_TYPE_UUID = u'bfeec2d4-3770-11e8-ad39-4a0004044aa0'


class ExtCreate(Ext):
    """ ExtCreate is a subclass of Ext. It is inherited by
    ExtPackage and ExtConvert. It exposes one method: create_extension() """

    # Tuple of the setup.py attributes we use
    supported_setup_py_attribute_names = (
        "author", "name", "version",
        "description", "long_description", "url"
    )

    # Tuple of all Resilient Object Names we support when packaging/converting
    supported_res_obj_names = (
        "actions", "automatic_tasks", "fields",
        "functions", "incident_artifact_types",
        "incident_types", "message_destinations",
        "phases", "roles", "scripts",
        "types", "workflows", "workspaces"
    )

    # Instansiate Jinja2 Environment with path to Jinja2 templates
    jinja_env = Environment(
        loader=PackageLoader("resilient_circuits", "data/ext/templates"),
        trim_blocks=True
    )

    @staticmethod
    def __get_import_definition_from_customize_py__(path_customize_py_file):
        """Return the base64 encoded ImportDefinition in a customize.py file as a Dictionary"""

        # Insert the customize.py parent dir to the start of our Python PATH at runtime so we can import the customize module from within it
        path_to_util_dir = os.path.dirname(path_customize_py_file)
        sys.path.insert(0, path_to_util_dir)

        # Import the customize module
        customize_py = importlib.import_module("customize")

        # Reload the module so we get the latest one
        # If we do not reload, can get stale results if
        # this method is called more then once
        reload(customize_py)

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
            raise ExtException("No ImportDefinition found in the customize.py file")

        # If more than 1 found
        elif len(customize_py_import_definitions) > 1:
            raise ExtException("Multiple ImportDefinitions found in the customize.py file. There must only be 1 ImportDefinition defined")

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

        # Remove the path from PYTHONPATH
        sys.path.remove(path_to_util_dir)

        return customize_py_import_definition

    @staticmethod
    def __get_configs_from_config_py__(path_config_py_file):
        """Returns a tuple (config_str, config_list). If no configs found, return ("", []).
        Raises Exception if it fails to parse configs
        - config_str: is the full string found in the config.py file
        - config_list: is a list of dict objects that contain each un-commented config
            - Each dict object has the attributes: name, placeholder, env_name, section_name
        """

        config_str, config_list = "", []

        # Insert the customize.py parent dir to the start of our Python PATH at runtime so we can import the customize module from within it
        path_to_util_dir = os.path.dirname(path_config_py_file)
        sys.path.insert(0, path_to_util_dir)

        try:
            # Import the config module
            config_py = importlib.import_module("config")

            # Reload the module so we get the latest one
            # If we do not reload, can get stale results if
            # this method is called more then once
            reload(config_py)

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
            raise ExtException("Failed to parse configs from config.py file\nThe config.py file may be corrupt. Visit the App Exchange to contact the developer\nReason: {0}".format(err))

        finally:
            # Remove the path from PYTHONPATH
            sys.path.remove(path_to_util_dir)

        return (config_str, config_list)

    @staticmethod
    def __is_setup_attribute__(line):
        """Use RegEx to check if the given file line starts with (for example) 'long_description='.
        Will also handle if the attribute has been commented out: '# long_description='.
        Returns True if something like 'long_description=' is at the start of the line, else False"""

        any_attribute_regex = re.compile(r'^#?\s*[a-z_]+=')

        if re.match(pattern=any_attribute_regex, string=line) is not None:
            return True

        return False

    @staticmethod
    def __parse_setup_attribute__(path_to_setup_py, setup_py_lines, attribute_name):
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
                    if ExtCreate.__is_setup_attribute__(preceding_line):
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

    @staticmethod
    def __parse_setup_py__(path, attribute_names):
        """Parse the values of the given attribute_names and return a Dictionary attribute_name:attribute_value"""

        # Read the setup.py file into a List
        setup_py_lines = ExtCreate.__read_file__(path)

        # Raise an error if nothing found in the file
        if not setup_py_lines:
            raise ExtException("No content found in provided setup.py file: {0}".format(path))

        setup_regex_pattern = r"setup\("
        setup_defined, index_of_setup, return_dict = False, None, dict()

        for i in range(len(setup_py_lines)):

            if re.match(pattern=setup_regex_pattern, string=setup_py_lines[i]) is not None:
                setup_defined = True
                index_of_setup = i
                break

        # Raise an error if we can't find 'setup()' in the file
        if not setup_defined:
            raise ExtException("Could not find 'setup()' defined in provided setup.py file: {0}".format(path))

        # Get sublist containing lines from 'setup(' to EOF + trim whitespaces
        setup_py_lines = setup_py_lines[index_of_setup:]
        setup_py_lines = [file_line.strip() for file_line in setup_py_lines]

        # Foreach attribute_name, get its value and add to return_dict
        for attribute_name in attribute_names:
            return_dict[attribute_name] = ExtCreate.__parse_setup_attribute__(path, setup_py_lines, attribute_name)

        return return_dict

    @staticmethod
    def __get_icon__(icon_name, path_to_icon, width_accepted, height_accepted, default_path_to_icon):
        """Returns the icon at path_to_icon as a base64 encoded string if it is a valid .png file with the resolution
        width_accepted x height_accepted. If path_to_icon does not exist, default_path_to_icon is returned as a base64
        encoded string"""

        path_icon_to_use = path_to_icon

        # Use default_path_to_icon if path_to_icon does not exist
        if not path_icon_to_use or not os.path.isfile(path_icon_to_use):
            LOG.warning("WARNING: Default Extension Icon will be used\nProvided custom icon path for %s is invalid: %s\nNOTE: %s should be placed in the /icons directory", icon_name, path_icon_to_use, icon_name)
            path_icon_to_use = default_path_to_icon

        else:
            LOG.info("INFO: Using custom %s icon: %s", icon_name, path_icon_to_use)

        # Validate path_icon_to_use and ensure we have READ permissions
        try:
            ExtCreate.__validate_file_paths__(os.R_OK, path_icon_to_use)
        except ExtException as err:
            raise OSError("Could not find valid icon file. Looked at two locations:\n{0}\n{1}\n{2}".format(path_to_icon, default_path_to_icon, err.message))

        # Get the extension of the file. os.path.splitext returns a Tuple with the file extension at position 1 and can be an empty string
        split_path = os.path.splitext(path_icon_to_use)
        file_extension = split_path[1]

        if not file_extension:
            raise ExtException("Provided icon file does not have an extension. Icon file must be .png\nIcon File: {0}".format(path_icon_to_use))

        elif file_extension != ".png":
            raise ExtException("{0} is not a supported icon file type. Icon file must be .png\nIcon File: {1}".format(file_extension, path_icon_to_use))

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
                raise ExtException("Failed to read icon's resolution. Icon file corrupt. Icon file must be .png\nIcon File: {0}".format(path_icon_to_use))

        # Raise exception if resolution is not accepted
        if icon_width != width_accepted or icon_height != height_accepted:
            raise ExtException("Icon resolution is {0}x{1}. Resolution must be {2}x{3}\nIcon File:{4}".format(icon_width, icon_height, width_accepted, height_accepted, path_icon_to_use))

        # If we get here all validations have passed. Open the file in Bytes mode and encode it as base64 and decode to a utf-8 string
        with open(path_icon_to_use, "rb") as icon_file:
            encoded_icon_string = base64.b64encode(icon_file.read()).decode("utf-8")

        return encoded_icon_string

    @staticmethod
    def __add_tag__(tag_name, list_of_objs):
        """Returns list_of_objs with tag_name added to each object"""

        # Create tag_to_add
        tag_to_add = {
            "tag_handle": tag_name,
            "value": None
        }

        err_msg = "Error adding tag '{0}'. '{1}' (printed above) is not a {2}. Instead a {3} was provided.\nProvided ImportDefinition in the customize.py file may be corrupt"

        # Check list_of_objs is a List
        if not isinstance(list_of_objs, list):
            LOG.error("Error adding tag.\n'list_of_objs': %s", list_of_objs)
            raise ExtException(err_msg.format(tag_name, "list_of_objs", "List", type(list_of_objs)))

        # Loop each object in the List
        for obj in list_of_objs:

            # If its not a dict, error
            if not isinstance(obj, dict):
                LOG.error("Error adding tag.\n'list_of_objs': %s\n'obj': %s", list_of_objs, obj)
                raise ExtException(err_msg.format(tag_name, "obj", "Dictionary", type(obj)))

            # Try get current_tags
            current_tags = obj.get("tags")

            # If None, create new empty List
            if current_tags is None:
                current_tags = []

            # If current_tags is not a list, error
            if not isinstance(current_tags, list):
                LOG.error("Error adding tag.\n'current_tags': %s", current_tags)
                raise ExtException(err_msg.format(tag_name, "current_tags", "List", type(current_tags)))

            # Append our tag_to_add to current_tags
            current_tags.append(tag_to_add)

            # Set the obj's 'tags' value to current_tags
            obj["tags"] = current_tags

        # Return the updated list_of_objs
        return list_of_objs

    @staticmethod
    def __add_tag_to_import_definition__(tag_name, supported_res_obj_names, import_definition):
        """Returns import_definition with tag_name added to each supported_res_object_name found
        in the import_definition"""

        for obj_name in supported_res_obj_names:

            res_object_list = import_definition.get(obj_name)

            if res_object_list:
                res_object_list = ExtCreate.__add_tag__(tag_name, res_object_list)

                # A 'function' object has a list of 'workflows' which also need the tag added to
                if obj_name == "functions":
                    res_functions_list = import_definition.get("functions")

                    for fn in res_functions_list:
                        fn_workflows_list = fn.get("workflows")

                        if fn_workflows_list:
                            fn_workflows_list = ExtCreate.__add_tag__(tag_name, fn_workflows_list)

        return import_definition

    @classmethod
    def create_extension(cls, path_setup_py_file, path_customize_py_file, path_config_py_file, output_dir,
                         path_built_distribution=None, path_extension_logo=None, path_company_logo=None, custom_display_name=None, keep_build_dir=False):
        """ Function that creates The Extension.zip file from the given setup.py, customize.py and config.py files
        and copies it to the output_dir. Returns the path to the Extension.zip
        - path_setup_py_file [String]: abs path to the setup.py file
        - path_customize_py_file [String]: abs path to the customize.py file
        - path_config_py_file [String]: abs path to the config.py file
        - output_dir [String]: abs path to the directory the Extension.zip should be produced
        - path_built_distribution [String]: abs path to a tar.gz Built Distribution
            - if provided uses that .tar.gz
            - else looks for it in the output_dir. E.g: output_dir/package_name.tar.gz
        - path_extension_logo [String]: abs path to the extension_logo.png. Has to be 200x72 and a .png file
            - if not provided uses default icon
        - path_company_logo [String]: abs path to the extension_logo.png. Has to be 100x100 and a .png file
            - if not provided uses default icon
        - custom_display_name [String]: will give the Extension that display name. Default: name from setup.py file
        - keep_build_dir [Boolean]: if True, build/ will not be remove. Default: False
        """

        LOG.info("Creating Extension")

        # Ensure the output_dir exists, we have WRITE access and ensure we can READ setup.py and customize.py
        cls.__validate_directory__(os.W_OK, output_dir)
        cls.__validate_file_paths__(os.R_OK, path_setup_py_file, path_customize_py_file)

        # Parse the setup.py file
        setup_py_attributes = cls.__parse_setup_py__(path_setup_py_file, cls.supported_setup_py_attribute_names)

        # Validate setup.py attributes

        # Validate the name attribute. Raise exception if invalid
        if not cls.__is_valid_package_name__(setup_py_attributes.get("name")):
            raise ExtException("'{0}' is not a valid Extension name. The name attribute must be defined and can only include 'a-z and _'.\nUpdate this value in the setup.py file located at: {1}".format(setup_py_attributes.get("name"), path_setup_py_file))

        # Validate the version attribute. Raise exception if invalid
        if not cls.__is_valid_version_syntax__(setup_py_attributes.get("version")):
            raise ExtException("'{0}' is not a valid Extension version syntax. The version attribute must be defined. Example: version=\"1.0.0\".\nUpdate this value in the setup.py file located at: {1}".format(setup_py_attributes.get("version"), path_setup_py_file))

        # Validate the url supplied in the setup.py file, set to an empty string if not valid
        if not cls.__is_valid_url__(setup_py_attributes.get("url")):
            LOG.warning("WARNING: '%s' is not a valid url. Ignoring.", setup_py_attributes.get("url"))
            setup_py_attributes["url"] = ""

        # Get ImportDefinition from customize.py
        customize_py_import_definition = cls.__get_import_definition_from_customize_py__(path_customize_py_file)

        # Get the tag name
        tag_name = setup_py_attributes.get("name")

        # Add the tag to the import defintion
        customize_py_import_definition = cls.__add_tag_to_import_definition__(tag_name, cls.supported_res_obj_names, customize_py_import_definition)

        # Parse the app.configs from the config.py file
        app_configs = cls.__get_configs_from_config_py__(path_config_py_file)

        # Generate the name for the extension
        extension_name = "{0}-{1}".format(setup_py_attributes.get("name"), setup_py_attributes.get("version"))

        # Generate paths to the directories and files we will use in the build directory
        path_build = os.path.join(output_dir, BASE_NAME_BUILD)
        path_extension_json = os.path.join(path_build, BASE_NAME_EXTENSION_JSON)
        path_export_res = os.path.join(path_build, BASE_NAME_EXPORT_RES)
        path_executables = os.path.join(path_build, BASE_NAME_EXECUTABLES)
        path_executable_zip = os.path.join(path_executables, "{0}{1}".format(PREFIX_EXECUTABLE_ZIP, extension_name))
        path_executable_json = os.path.join(path_executable_zip, BASE_NAME_EXECUTABLE_JSON)
        path_executable_dockerfile = os.path.join(path_executable_zip, BASE_NAME_EXECUTABLE_DOCKERFILE)

        try:
            # If there is an old build directory, remove it first
            if os.path.exists(path_build):
                shutil.rmtree(path_build)

            # Create the directories for the path "/build/executables/exe-<package-name>/"
            os.makedirs(path_executable_zip)

            # If no path_built_distribution is given, use the default: "<output_dir>/<package-name>.tar.gz"
            if not path_built_distribution:
                path_built_distribution = os.path.join(output_dir, "{0}.tar.gz".format(extension_name))

            # Validate the built distribution exists and we have READ access
            cls.__validate_file_paths__(os.R_OK, path_built_distribution)

            # Copy the built distribution to the executable_zip dir and  enforce rename to .tar.gz
            shutil.copy(path_built_distribution, os.path.join(path_executable_zip, "{0}.tar.gz".format(extension_name)))

            # Generate the contents for the executable.json file
            the_executable_json_file_contents = {
                "name": extension_name
            }

            # Write the executable.json file
            cls.__write_file__(path_executable_json, json.dumps(the_executable_json_file_contents, sort_keys=True))

            # NOTE: Dockerfile creation commented out for this release
            '''
            # Load Dockerfile template
            docker_file_template = cls.jinja_env.get_template(JINJA_TEMPLATE_DOCKERFILE)

            # Render Dockerfile template with required variables
            the_dockerfile_contents = docker_file_template.render({
                "extension_name": extension_name,
                "installed_package_name": setup_py_attributes.get("name").replace("_", "-"),
                "app_configs": app_configs[1]
            })

            # Write the Dockerfile
            cls.__write_file__(path_executable_dockerfile, the_dockerfile_contents)
            '''

            # zip the executable_zip dir
            shutil.make_archive(base_name=path_executable_zip, format="zip", root_dir=path_executable_zip)

            # Remove the executable_zip dir
            shutil.rmtree(path_executable_zip)

            # Get the extension_logo (icon) and company_logo (author.icon) as base64 encoded strings
            extension_logo = cls.__get_icon__(
                icon_name=os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO),
                path_to_icon=path_extension_logo,
                width_accepted=200,
                height_accepted=72,
                default_path_to_icon=PATH_DEFAULT_ICON_EXTENSION_LOGO)

            company_logo = cls.__get_icon__(
                icon_name=os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO),
                path_to_icon=path_company_logo,
                width_accepted=100,
                height_accepted=100,
                default_path_to_icon=PATH_DEFAULT_ICON_COMPANY_LOGO)

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
                "display_name": custom_display_name if custom_display_name is not None else setup_py_attributes.get("name"),
                "icon": {
                    "data": extension_logo,
                    "media_type": "image/png"
                },
                "long_description": {
                    "content": "<div>{0}</div>".format(setup_py_attributes.get("long_description")),
                    "format": "html"
                },
                "minimum_resilient_version": {
                    "major": customize_py_import_definition.get("server_version").get("major"),
                    "minor": customize_py_import_definition.get("server_version").get("minor"),
                    "build_number": customize_py_import_definition.get("server_version").get("build_number"),
                    "version": customize_py_import_definition.get("server_version").get("version")
                },
                "name": setup_py_attributes.get("name"),
                "tag": {
                    "prefix": tag_name,
                    "name": tag_name,
                    "display_name": tag_name,
                    "uuid": cls.__generate_uuid_from_string__(tag_name)
                },
                "uuid": cls.__generate_uuid_from_string__("{0}-{1}".format(setup_py_attributes.get("name"), setup_py_attributes.get("version"))),
                "version": setup_py_attributes.get("version"),
                # TODO: discuss with Sasquatch. Can add the app_config_str here, but will not install
                # TODO: get 'Unrecognized field "app_config_str"' error
                # "app_config_str": app_configs[0]
            }

            # Write the executable.json file
            cls.__write_file__(path_extension_json, json.dumps(the_extension_json_file_contents, sort_keys=True))

            # Write the customize ImportDefinition to the export.res file
            cls.__write_file__(path_export_res, json.dumps(customize_py_import_definition, sort_keys=True))

            # Copy the built distribution to the build dir, enforce rename to .tar.gz
            shutil.copy(path_built_distribution, os.path.join(path_build, "{0}.tar.gz".format(extension_name)))

            # create The Extension Zip by zipping the build directory
            extension_zip_base_path = os.path.join(output_dir, "{0}{1}".format(PREFIX_EXTENSION_ZIP, extension_name))
            extension_zip_name = shutil.make_archive(base_name=extension_zip_base_path, format="zip", root_dir=path_build)
            path_the_extension_zip = os.path.join(extension_zip_base_path, extension_zip_name)

        except ExtException as err:
            raise err

        except Exception as err:
            raise ExtException(err)

        finally:
            # Remove the executable_zip dir. Keep it if user passes --keep-build-dir
            if not keep_build_dir:
                shutil.rmtree(path_build)

        LOG.info("Extension %s created", "{0}{1}".format(PREFIX_EXTENSION_ZIP, extension_name))

        # Return the path to the extension zip
        return path_the_extension_zip
