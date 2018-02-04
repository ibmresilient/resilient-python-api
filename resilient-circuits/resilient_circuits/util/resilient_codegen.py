# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to codegen a resilient-circuits component or package"""

from __future__ import print_function

import os
import io
import json
import logging
import pkg_resources
from resilient import SimpleHTTPException
from resilient_circuits import template_functions


LOG = logging.getLogger("__name__")


# Template files that drive codegen
FUNCTION_TEMPLATE_PATH = "data/template_function.jinja2"
PACKAGE_TEMPLATE_PATH = "data/template_package.jinja2"


# The attributes we want to keep from the object definitions
TEMPLATE_ATTRIBUTES = [
    "template",
    "name"
]

VALUE_ATTRIBUTES = [
    "label"
]

PARAMETER_ATTRIBUTES = [
    "templates",
    "text",
    "tooltip",
    "rich_text",
    "values",
    "blank_option",
    "input_type",
    "placeholder",
    "name"
]

VIEW_ITEM_ATTRIBUTES = [
    "content"
]

FUNCTION_ATTRIBUTES = [
    "display_name",
    "view_items",
    "name",
    "description",
    "destination_handle"
]

MESSAGE_DESTINATION_ATTRIBUTES = [
    "programmatic_name",
    "name",
    "expect_ack",
    "destination_type"
]


def list_functions(client):
    """List all the functions"""
    try:
        function_defs = client.get("/functions?handle_format=names")
    except SimpleHTTPException as exc:
        if exc.response.status_code == 500:
            LOG.error(u"ERROR: Functions are not available on this Resilient appliance.")
            return
        else:
            raise

    print(u"Available functions:")
    for function_def in function_defs["entities"]:
        print(u"    {}".format(function_def["name"]))


def clean(dictionary, keep):
    """Remove attributes that are not in the 'keep' list"""
    for key in dictionary.keys():
        if key not in keep:
            dictionary.pop(key)
    return dictionary


def render_file_mapping(file_mapping_dict, data, source_dir, target_dir):
    """
    Walk each value in the "rendered" file-mapping dictionary, and create the target files.

    Nesting in the 'target' dictionary represents the target directory structure.
    Source values are the full path to a source file.
    Each source file is treated as a JINJA2 template, and rendered using the data provided.

    :param file_mapping_dict: {"target": "source"...}
    :param data: the data for JINJA rendering of each source file
    :param source_dir: path to the root of the source files
    :param target_dir: path where the target files and directories should be written
    """
    for (key, value) in file_mapping_dict.items():
        if not key:
            LOG.error(u"Cannot render empty target for %s", value)
            continue
        # The key is a directory-name or filename,
        # optionally followed by a '@xxx" where 'xxx' is a variable tha the
        # template needs, such as a loop-variable.  Split this out if present.
        loopvar = None
        if "@" in key:
            split = key.split("@", 1)
            key = split[0]
            loopvar = split[1]
        data["loopvar"] = loopvar
        #
        if isinstance(value, dict):
            # This is a subdirectory
            subdir = os.path.join(target_dir, key)
            try:
                os.mkdir(subdir)
            except OSError as exc:
                LOG.warn(exc)
            render_file_mapping(value, data, source_dir, subdir)
        else:
            target_file = os.path.join(target_dir, key)
            source_file = os.path.join(source_dir, value)
            if os.path.exists(target_file):
                LOG.error(u"Not writing %s: file exists.", target_file)
                continue
            # Render the source file as a JINJA template
            LOG.debug(u"Writing %s from template %s", target_file, source_file)
            LOG.info(u"Writing %s", target_file)
            with io.open(source_file, 'r', encoding="utf-8") as source:
                source_template = source.read()
                source_rendered = template_functions.render(source_template, data)
            with io.open(target_file, mode="w", encoding="utf-8") as outfile:
                outfile.write(source_rendered)


def codegen_from_template(client, template_file_path, package, function_names, output_dir, output_file):
    """Based on a template-file, produce the generated file or package.

       To codegen a single file, the template will be a JSON dict with just one entry,
       such as {"file_to_generate.py": "path/to/template.jinja2"}
       To codegen a whole directory, the template dict can have multiple values,
       including nested subdirectories.

       Each source ("path/to/template.jinja2") will be rendered using jinja2,
       then written to the target ("file_to_generate.py").

       :param template_file_path: a file that defines the item(s) to be codegenned.
       :param package: name of the package to be generated
       :param function_names: list of named functions to be generated

    """
    if function_names:
        # Check that 'functions' are available (v30 onward)
        try:
            function_defs = client.get("/functions?handle_format=names")
        except SimpleHTTPException as exc:
            if exc.response.status_code == 500:
                LOG.error(u"ERROR: Functions are not available on this Resilient appliance.")
                return
            else:
                raise

    # Prepare the dictionary of substitution values for jinja2
    # (includes all the configuration elements related to the functions)
    functions = {}
    function_fields = {}
    all_destinations = dict((dest["programmatic_name"], dest) for dest in client.get("/message_destinations")["entities"])
    message_destinations = {}
    for function_name in (function_names or []):
        # Get the function definition
        function_def = client.get("/functions/{}?handle_format=names".format(function_name))
        # Remove the attributes we don't want to serialize
        clean(function_def, FUNCTION_ATTRIBUTES)
        for view_item in function_def.get("view_items", []):
            clean(view_item, VIEW_ITEM_ATTRIBUTES)

        # Get the parameters (input fields)
        param_names = [item["content"] for item in function_def["view_items"]]
        params = []
        for param_name in param_names:
            param = client.get("/types/__function/fields/{}?handle_format=names".format(param_name))
            clean(param, PARAMETER_ATTRIBUTES)
            for template in param.get("templates", []):
                clean(template, TEMPLATE_ATTRIBUTES)
            for value in param.get("values", []):
                clean(value, VALUE_ATTRIBUTES)
            params.append(param)
            function_fields[param["name"]] = param

        # Get the message destination
        dest_name = function_def["destination_handle"]
        if dest_name not in message_destinations:
            dest = all_destinations[dest_name]
            clean(dest, MESSAGE_DESTINATION_ATTRIBUTES)
            message_destinations[dest_name] = dest

        # Write out the template values
        function_def["parameters"] = params
        functions[function_name] = function_def

    data = {
        "package": package,
        "function_names": function_names,
        "output_dir": output_dir,
        "output_file": output_file,
        "functions": functions,
        "function_fields": function_fields,
        "message_destinations": message_destinations
    }
    LOG.debug(u"Configuration data:\n%s", json.dumps(data, indent=2))

    # Read the files/package template and render it
    # to produce the file-mapping dictionary from template-files to generated-files
    with io.open(template_file_path, 'r', encoding="utf-8") as template_file:
        file_mapping_template = template_file.read()
        file_mapping = template_functions.render_json(file_mapping_template, data)

    LOG.debug(u"Codegen template:\n%s", json.dumps(file_mapping, indent=2))

    # Write all the files defined in the mapping definition
    src_dir = os.path.dirname(template_file_path)
    render_file_mapping(file_mapping, data, src_dir, output_dir)


def codegen_package(client, package, function_names, output_dir):
    """Generate a an installable python package"""
    # Make the output directory (usually a new subdirectory of cwd)
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        LOG.warn("%s", exc)

    template_file_path = pkg_resources.resource_filename("resilient_circuits", PACKAGE_TEMPLATE_PATH)
    return codegen_from_template(client, template_file_path, package, function_names, output_dir, None)


def codegen_functions(client, function_names, output_dir, output_file):
    """Generate a python file that implements one or more functions"""
    template_file_path = pkg_resources.resource_filename("resilient_circuits", FUNCTION_TEMPLATE_PATH)
    return codegen_from_template(client, template_file_path, None, function_names, output_dir, output_file)
