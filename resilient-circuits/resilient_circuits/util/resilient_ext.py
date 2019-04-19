#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Python Module to handle resilient-circuits ext: commands"""

import logging
import os
import json
import re
import shutil
import hashlib
import uuid
import sys
import base64
import importlib
from setuptools import sandbox as use_setuptools
from resilient_circuits.util.resilient_customize import ImportDefinition

# TODO: Investigate using LOG.setLevel value from app.config file
# Setup logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())


# Custom Extensions Exception
class ExtException(Exception):
    def __init__(self, message):
        self.message = message

        # Call the base class
        super(ExtException, self).__init__(message)

    def __str__(self):
        return "\nresilient-circuits %s FAILED\nERROR: %s" % (ExtCommands.get_command_ran(), self.message)


class ExtCommands(object):

    # Class var to store what command was run
    command_ran = None

    def __init__(self, command_ran, path_to_extension):
        self.command_ran = command_ran

        if command_ran == "ext:package":
            self.package_extension(path_to_extension)

        elif command_ran == "ext:convert":
            # TODO
            pass

        else:
            raise ExtException("Unsupported command: {0}. Supported commands are: (ext:package, ext:convert)")

    @classmethod
    def get_command_ran(cls):
        """Returns the name of the command ran"""
        return cls.command_ran

    @staticmethod
    def __write_file__(path, contents):
        """Writes the String contents to a file at path"""
        with open(path, "wb") as the_file:
            the_file.write(contents)

    @staticmethod
    def __read_file__(path):
        """Returns all the lines of a file at path as a List"""
        file_lines = []
        with open(path, "r") as the_file:
            file_lines = the_file.readlines()
        return file_lines

    @staticmethod
    def __generate_md5_uuid_from_file__(path_to_file):
        """Returns String representation of the UUID of a hex md5 hash of the given file"""

        # Instansiate new md5_hash
        md5_hash = hashlib.md5()

        # Open a stream to the file. Read 4096 bytes at a time. Pass these bytes to md5_hash object
        with open(path_to_file, mode="rb") as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)

        # Generate the hex md5 hash of all the read bytes
        the_md5_hex_str = md5_hash.hexdigest()

        # Return a String repersenation of the uuid of the md5 hash
        return str(uuid.UUID(the_md5_hex_str))

    @staticmethod
    def __validate_directory_and_files__(path_to_extension_dir, **kwargs):
        """Function that validates the dir exists and the user has WRITE access to it.
        Also validates the file paths that are passed as **kwargs exists and the user has READ access"""

        # Check the path is absolute
        if not os.path.isabs(path_to_extension_dir):
            raise ExtException("The path to the package directory must be an absolute path: {0}".format(path_to_extension_dir))

        # Check the directory exists
        if not os.path.isdir(path_to_extension_dir):
            raise ExtException("The path does not exist: {0}".format(path_to_extension_dir))

        # Check user has WRITE permissions
        if not os.access(path_to_extension_dir, os.W_OK):
            raise ExtException("User does not have WRITE permissions for: {0}".format(path_to_extension_dir))

        # For each file in kwargs
        for file_name, path_to_file in kwargs.items():
            # Check the file exists
            if not os.path.isfile(path_to_file):
                raise ExtException("Could not find {0} file at: {1}".format(file_name.replace("_", "."), path_to_file))

            # Check user has READ permissions
            if not os.access(path_to_extension_dir, os.R_OK):
                raise ExtException("User does not have READ permissions for: {0}".format(path_to_file))


    @staticmethod
    def __is_setup_attribute__(line):
        """Use RegEx to check if the given file line starts with (for example) 'long_description='
        Returns true if something like 'long_description=' is at the start of the line, else false"""

        any_attribute_regex = r"^[a-z_]+="

        if re.match(pattern=any_attribute_regex, string=line) is not None:
            return True

        return False

    @classmethod
    def __parse_setup_attribute__(cls, path_to_setup_py, setup_py_lines, attribute_name):
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
                for preceding_line in setup_py_lines[i+1:]:
                    if cls.__is_setup_attribute__(preceding_line):
                        break

                    # Append the line if it is not a new attribute
                    the_attribute_value.append(preceding_line)

                break

        # If we could not find an attribute with attribute_name, raise an Exception
        if not the_attribute_found:
            # raise ExtException("{0} is not a valid attribute name in the provided setup.py file: {1}".format(attribute_name, path_to_setup_py))
            LOG.warning("WARNING: '%s' is not a valid attribute name in the provided setup.py file: %s", attribute_name, path_to_setup_py)

        # Create single string and trim (" , ' )
        the_attribute_value = " ".join(the_attribute_value)
        the_attribute_value = the_attribute_value.strip("\",'.")

        return the_attribute_value

    @classmethod
    def __parse_setup_py__(cls, path, attribute_names):
        """Parse the values of the given attribute_names and return a Dictionary attribute_name:attribute_value"""

        # Read the setup.py file into a List
        setup_py_lines = cls.__read_file__(path)

        # Raise an error is nothing found in the file
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
            return_dict[attribute_name] = cls.__parse_setup_attribute__(path, setup_py_lines, attribute_name)

        return return_dict

    @staticmethod
    def __get_import_definition_from_customize_py__(path_to_base_dir):
        """Return the base64 encoded ImportDefinition in a customize.py file as a Dictionary"""

        # Insert the path_to_base_dir to the start of our Python PATH at runtime so we can import the customize module from within it
        sys.path.insert(0, path_to_base_dir)

        # TODO: investigate why customize.py has to "from resilient_circuits.util import *"??
        # Import the customize module
        customize_py = importlib.import_module("util.customize")

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

        return customize_py_import_definitions[0]

    @classmethod
    def package_extension(cls, path_to_extension):

        LOG.info("Packaging extension. args: %s", path_to_extension)

        # Generate path to setup.py, util dir and customize.py
        path_setup_py_file = os.path.join(path_to_extension, "setup.py")
        path_to_base_dir = os.path.join(path_to_extension, os.path.basename(path_to_extension))
        path_customize_py_file = os.path.join(path_to_base_dir, "util", "customize.py")

        # Ensure the directory exists, we have WRITE access and ensure we can READ setup.py and customize.py
        cls.__validate_directory_and_files__(path_to_extension, **{
            "setup_py": path_setup_py_file,
            "customize_py": path_customize_py_file
        })

        # Parse the setup.py file
        setup_py_attributes = cls.__parse_setup_py__(path_setup_py_file, [
            "author",
            "author_email",
            "name",
            "version",
            "description",
            "long_description",
            "license",
            "url"
        ])

        # Get ImportDefinition from customize.py
        customize_py_import_definition = cls.__get_import_definition_from_customize_py__(path_to_base_dir)

        # Generate the 'main' name for the extension
        extension_name = "{0}-{1}".format(setup_py_attributes.get("name"), setup_py_attributes.get("version"))

        # Generate all paths to the directories and files we will use
        path_dist = os.path.join(path_to_extension, "dist")
        path_python_tar_package = os.path.join(path_dist, "{0}.tar.gz".format(extension_name))
        path_extension_zip = os.path.join(path_dist, "ext-{0}".format(extension_name))
        path_build = os.path.join(path_dist, "build")
        path_extension_json = os.path.join(path_build, "extension.json")
        path_export_res = os.path.join(path_build, "export.res")
        path_executables = os.path.join(path_build, "executables")
        path_executable_zip = os.path.join(path_executables, "exe-{0}".format(extension_name))
        path_executable_json = os.path.join(path_executable_zip, "executable.json")
        path_executable_dockerfile = os.path.join(path_executable_zip, "Dockerfile")

        # Create the directories for the path "./dist/build/executables/exe-<package-name>/"
        os.makedirs(path_executable_zip)

        # Generate the contents for the executable.json file
        the_executable_json_file_contents = {
            "name": extension_name
        }

        # Write the executable.json file
        # TODO: remove the indent formatting so the file is minified when written
        cls.__write_file__(path_executable_json, json.dumps(the_executable_json_file_contents, sort_keys=True, indent=4))

        # TODO: Render this String from from a JINJA Template
        # Generate the contents for the Dockerfile
        the_dockerfile_contents = """FROM resilient:v32_1\n
COPY *.tar.gz /app/data\n
RUN pip install -U {0}.tar.gz \\\n  && resilient-circuits config -u -l {1}""".format(extension_name, setup_py_attributes.get("name").replace("_", "-"))

        # Write the Dockerfile
        cls.__write_file__(path_executable_dockerfile, the_dockerfile_contents)

        # Generate the tar.gz
        use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist"])

        # Copy the tar.gz to the executable_zip dir
        shutil.copy(path_python_tar_package, path_executable_zip)

        # zip the executable_zip dir
        shutil.make_archive(base_name=path_executable_zip, format="zip", root_dir=path_executable_zip)

        # Remove the executable_zip dir
        shutil.rmtree(path_executable_zip)

        # Generate the contents for the extension.json file
        # TODO: icons?

        the_extension_json_file_contents = {
            "author": {
                "name": setup_py_attributes.get("author"),
                "website": setup_py_attributes.get("url"),
                "icon": {
                    "data": "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",
                    "media_type": "image/png"
                }
            },
            "description": {
                "content": setup_py_attributes.get("description"),
                "format": "text"
            },
            "display_name": setup_py_attributes.get("name"),
            "icon": {
                "data": "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",
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
                "prefix": setup_py_attributes.get("name"),
                "name": setup_py_attributes.get("name"),
                "display_name": setup_py_attributes.get("name"),
                "uuid": cls.__generate_md5_uuid_from_file__(path_python_tar_package)
            },
            "uuid": cls.__generate_md5_uuid_from_file__("{0}.zip".format(path_executable_zip)),
            "version": setup_py_attributes.get("version")
        }

        # Write the executable.json file
        # TODO: remove the indent formatting so the file is minified when written
        cls.__write_file__(path_extension_json, json.dumps(the_extension_json_file_contents, sort_keys=True, indent=4))

        # Write the customize ImportDefinition to the export.res file
        # TODO: remove the indent formatting so the file is minified when written
        cls.__write_file__(path_export_res, json.dumps(customize_py_import_definition, sort_keys=True, indent=4))

        # zip the build dir
        shutil.make_archive(base_name=path_extension_zip, format="zip", root_dir=path_build)

        # Remove the executable_zip dir
        shutil.rmtree(path_build)
