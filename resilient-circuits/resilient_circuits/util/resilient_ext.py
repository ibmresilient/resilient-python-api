#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Python Module to handle resilient-circuits ext: commands"""

import logging
import os
import json
import re
import shutil
from setuptools import sandbox as use_setuptools

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
    def __validate_directory__(path_to_extension_dir, path_to_setup_py_file):
        """Function that validates the dir exists and that the user has WRITE access"""

        # Check the path is absolute
        if not os.path.isabs(path_to_extension_dir):
            raise ExtException("The path to the package directory must be an absolute path: {0}".format(path_to_extension_dir))

        # Check the directory exists
        if not os.path.isdir(path_to_extension_dir):
            raise ExtException("The path does not exist: {0}".format(path_to_extension_dir))

        # Check user has WRITE permissions
        if not os.access(path_to_extension_dir, os.W_OK):
            raise ExtException("User does not have WRITE permissions for: {0}".format(path_to_extension_dir))

        # Check setup.py exists
        if not os.path.isfile(path_to_setup_py_file):
            raise ExtException("Could not find setup.py in: {0}".format(path_to_extension_dir))

    @staticmethod
    def __is_setup_attribute__(line):

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
            LOG.warning("WARNING: '{0}' is not a valid attribute name in the provided setup.py file: {1}".format(attribute_name, path_to_setup_py))

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

    @classmethod
    def package_extension(cls, path_to_extension):

        LOG.info("Packaging extension. args: %s", path_to_extension)

        # Generate path to setup.py
        path_setup_py_file = os.path.join(path_to_extension, "setup.py")

        # Ensure the directory exists and we have WRITE access
        cls.__validate_directory__(path_to_extension, path_setup_py_file)

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

        # Generate the 'main' name for the extension
        extension_name = "{0}-{1}".format(setup_py_attributes.get("name"), setup_py_attributes.get("version"))

        # Generate all paths to the directories and files we will use
        path_dist = os.path.join(path_to_extension, "dist")
        path_extension_zip = os.path.join(path_dist, "ext-{0}".format(extension_name))
        path_build = os.path.join(path_dist, "build")
        path_extension_json = os.path.join(path_build, "extension.json")
        path_export_res = os.path.join(path_build, "export.res")
        path_executables = os.path.join(path_build, "executables")
        path_executable_zip = os.path.join(path_executables, "exe-{0}".format(extension_name))
        path_executable_json = os.path.join(path_executable_zip, "executable.json")
        path_executable_dockerfile = os.path.join(path_executable_zip, "Dockerfile")

        # TODO: Remove this after development
        # shutil.rmtree(os.path.join(path_to_extension, "dist"))

        # Create the directories for the path "./dist/build/executables/exe-<package-name>/"
        os.makedirs(path_executable_zip)

        # Generate the contents for the executable.json file
        the_executable_json_file_contents = {
            "name": extension_name
        }

        # Write the executable.json file
        cls.__write_file__(path_executable_json, json.dumps(the_executable_json_file_contents, sort_keys=True, indent=4))

        # Generate the contents for the Dockerfile
        the_dockerfile_contents = """FROM resilient:v32_1\n
COPY *.tar.gz /app/data\n
RUN pip install -U {0}.tar.gz \\\n  && resilient-circuits config -u -l {1}""".format(extension_name, setup_py_attributes.get("name").replace("_", "-"))

        # Write the Dockerfile
        cls.__write_file__(path_executable_dockerfile, the_dockerfile_contents)

        # Generate the tar.gz
        use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist"])

        # Copy the tar.gz to the executable_zip dir
        shutil.copy(os.path.join(path_dist, "{0}.tar.gz".format(extension_name)), path_executable_zip)

        # zip the executable_zip dir
        shutil.make_archive(base_name=path_executable_zip, format="zip", root_dir=path_executable_zip)

        # Remove the executable_zip dir
        shutil.rmtree(path_executable_zip)

        # Generate the contents for the extension.json file
        # TODO: icons?
        # TODO: author website?
        # TODO: tag?
        # TODO: uuid?
        # TODO: min version - customize.py?
        the_extension_json_file_contents = {
            "author": {
                "name": setup_py_attributes.get("author"),
                "website": setup_py_attributes.get("author_email"),
                "icon": {
                    "data": "TODO",
                    "media_type": "TODO"
                }
            },
            "description": {
                "content": setup_py_attributes.get("description"),
                "format": "text"
            },
            "display_name": setup_py_attributes.get("name"),
            "icon": {
                "data": "TODO",
                "media_type": "TODO"
            },
            "long_description": {
                "content": "<div>{0}</div>".format(setup_py_attributes.get("long_description")),
                "format": "html"
            },
            "minimum_resilient_version": {
                "major": 0,
                "minor": 0,
                "build_number": 0,
                "version": "0.0.0"
            },
            "name": setup_py_attributes.get("name"),
            "tag": {
                "prefix": "TODO",
                "name": "TODO",
                "display_name": "TODO",
                "uuid": "TODO"
            },
            "uuid": "TODO",
            "version": setup_py_attributes.get("version")
        }

        # Write the executable.json file
        cls.__write_file__(path_extension_json, json.dumps(the_extension_json_file_contents, sort_keys=True, indent=4))

        # Generate the contents for the export.res file 
        # TODO: get the content of export.res from customize.py
        the_export_res_contents = {"test": "value"}
        
        # Write the export.res file
        cls.__write_file__(path_export_res, json.dumps(the_export_res_contents, sort_keys=True, indent=4))

        # zip the build dir
        shutil.make_archive(base_name=path_extension_zip, format="zip", root_dir=path_build)

        # Remove the executable_zip dir
        shutil.rmtree(path_build)
