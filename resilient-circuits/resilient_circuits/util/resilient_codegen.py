# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to codegen a resilient-circuits component or package"""

from __future__ import print_function
import os
import io
import json
import logging
import keyword
import re
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

FUNCTION_FIELD_ATTRIBUTES = [
    "uuid",  # note - workflows reference function inputs by uuid
    "templates",
    "text",
    "tooltip",
    "rich_text",
    "values",
    "blank_option",
    "input_type",
    "placeholder",
    "required",
    "name"
]

ACTION_FIELD_ATTRIBUTES = FUNCTION_FIELD_ATTRIBUTES

VIEW_ITEM_ATTRIBUTES = [
    "element",
    "content",
    "field_type"
]

FUNCTION_ATTRIBUTES = [
    "uuid",  # note - workflows reference functions by uuid
    "display_name",
    "view_items",
    "name",
    "description",
    "destination_handle"
]

WORKFLOW_ATTRIBUTES = [
    "programmatic_name",
    "object_type",
    "content"
]

WORKFLOW_CONTENT_ATTRIBUTES = [
    "xml"
]

MESSAGE_DESTINATION_ATTRIBUTES = [
    "programmatic_name",
    "name",
    "expect_ack",
    "destination_type"
]

ACTION_ATTRIBUTES = [
    "logic_type",
    "name",
    "view_items",
    "type",
    "workflows",
    "object_type",
    "timeout_seconds",
    "automations",
    "conditions",
    "message_destinations"
]


def valid_identifier(name):
    """Test if 'name' is a valid identifier for a package or module

       >>> valid_identifier("")
       False
       >>> valid_identifier("get")
       False
       >>> valid_identifier("bang!")
       False
       >>> valid_identifier("_something")
       True
    """
    if keyword.iskeyword(name):
        return False
    if name in dir(__builtins__):
        return False
    return re.match("[_A-Za-z][_a-zA-Z0-9]*$", name) is not None


def list_functions(client):
    """List all the functions"""
    try:
        function_defs = client.cached_get("/functions?handle_format=names")
    except SimpleHTTPException as exc:
        if exc.response.status_code == 500:
            LOG.error(u"ERROR: Functions are not available on this Resilient appliance.")
            return
        else:
            raise

    print(u"Available functions:")
    for function_def in function_defs["entities"]:
        print(u"    {}".format(function_def["name"]))


def list_workflows(client):
    """List all the workflows"""
    try:
        workflow_defs = client.cached_get("/workflows?handle_format=names")
    except SimpleHTTPException as exc:
        if exc.response.status_code == 500:
            LOG.error(u"ERROR: Workflows are not available on this Resilient appliance.")
            return
        else:
            raise

    print(u"Available workflows:")
    for workflow_def in workflow_defs["entities"]:
        print(u"    {}".format(workflow_def["programmatic_name"]))


def list_actions(client):
    """List all the actions (rules)"""
    try:
        action_defs = client.cached_get("/actions?handle_format=names")
    except SimpleHTTPException as exc:
        if exc.response.status_code == 500:
            LOG.error(u"ERROR: Rules are not available on this Resilient appliance.")
            return
        else:
            raise

    print(u"Available rules:")
    for action_def in action_defs["entities"]:
        print(u"    {}".format(action_def["name"]))


def clean(dictionary, keep):
    """Remove attributes that are not in the 'keep' list"""
    for key in dictionary.copy().keys():
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
    for (key, value) in sorted(file_mapping_dict.items()):
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


def codegen_from_template(client, template_file_path, package,
                          message_destination_names, function_names, workflow_names, action_names,
                          output_dir, output_file):
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
       :param workflow_names: list of named workflows to be generated

    """
    actions = {}
    action_fields = {}
    workflows = {}
    functions = {}
    function_params = {}
    message_destinations = {}

    all_destinations = dict((dest["programmatic_name"], dest)
                            for dest in client.cached_get("/message_destinations")["entities"])
    all_destinations_2 = dict((dest["name"], dest)
                            for dest in client.cached_get("/message_destinations")["entities"])

    if function_names or message_destination_names:
        # Check that 'functions' are available (v30 onward)
        try:
            function_defs = client.cached_get("/functions?handle_format=names")
        except SimpleHTTPException as exc:
            if exc.response.status_code == 500:
                LOG.error(u"ERROR: Functions are not available on this Resilient appliance.")
                return
            else:
                raise
        function_names = function_names or []
        available_names = [function_def["name"] for function_def in function_defs["entities"]]
        if message_destination_names:
            # Build a list of all the functions that use the specified message destination(s)
            for function_name in available_names:
                # Get the function definition
                function_def = client.cached_get(
                    "/functions/{}?handle_format=names&text_content_output_format=objects_no_convert"
                    .format(function_name))
                if function_def["destination_handle"] in message_destination_names:
                    function_names.append(function_name)

        # Check that each named function is available
        for function_name in function_names:
            if function_name not in available_names:
                LOG.error(u"ERROR: Function '%s' not found on this Resilient appliance.", function_name)
                list_functions(client)
                return

    if workflow_names:
        # Check that 'workflows' are available (v28 onward)
        try:
            workflow_defs = client.cached_get("/workflows?handle_format=names")
        except SimpleHTTPException as exc:
            if exc.response.status_code == 500:
                LOG.error(u"ERROR: Workflows are not available on this Resilient appliance.")
                return
            else:
                raise
        # Check that each named workflow is available
        available_names = [workflow_def["programmatic_name"] for workflow_def in workflow_defs["entities"]]
        for workflow_name in workflow_names:
            if workflow_name not in available_names:
                LOG.error(u"ERROR: Workflow '%s' not found on this Resilient appliance.", workflow_name)
                list_workflows(client)
                return
    else:
        workflow_names = []

    if action_names:
        # Check that 'actions' are available
        try:
            action_defs = client.cached_get("/actions?handle_format=names")
        except SimpleHTTPException as exc:
            if exc.response.status_code == 500:
                LOG.error(u"ERROR: Rules are not available on this Resilient appliance.")
                return
            else:
                raise
        # Check that each named action is available
        actions = {action_def["name"]: clean(action_def.copy(), ACTION_ATTRIBUTES)
                   for action_def in action_defs["entities"]
                   if action_def["name"] in action_names}
        for action_name in action_names:
            if action_name not in actions:
                LOG.error(u"ERROR: Rule '%s' not found on this Resilient appliance.", action_name)
                list_actions(client)
                return
            action_def = actions[action_name]

            # Get the activity-fields for this action (if any)
            field_names = [item.get("content")
                           for item in action_def["view_items"]
                           if "content" in item]
            fields = []
            for field_name in field_names:
                field = client.cached_get("/types/actioninvocation/fields/{}?handle_format=names".format(field_name))
                clean(field, ACTION_FIELD_ATTRIBUTES)
                for template in field.get("templates", []):
                    clean(template, TEMPLATE_ATTRIBUTES)
                for value in field.get("values", []):
                    clean(value, VALUE_ATTRIBUTES)
                fields.append(field)
                action_fields[field["name"]] = field

            # Get the workflow(s) for this rule (if any)
            wf_names = action_def["workflows"]
            for wf_name in wf_names:
                if wf_name not in workflow_names:
                    workflow_names.append(wf_name)

            # Get the message destination(s) for this rule (if any)
            dest_names = action_def["message_destinations"]
            for dest_name in dest_names:
                if dest_name not in message_destinations:
                    dest = all_destinations_2[dest_name]
                    clean(dest, MESSAGE_DESTINATION_ATTRIBUTES)
                    message_destinations[dest_name] = dest

    function_fields = dict((field["uuid"], field) for field in client.cached_get("/types/__function/fields"))

    for function_name in (function_names or []):
        # Get the function definition
        function_def = client.cached_get(
            "/functions/{}?handle_format=names&text_content_output_format=objects_no_convert".format(function_name)
        )
        # Remove the attributes we don't want to serialize
        clean(function_def, FUNCTION_ATTRIBUTES)
        for view_item in function_def.get("view_items", []):
            clean(view_item, VIEW_ITEM_ATTRIBUTES)
        functions[function_name] = function_def

        # Get the parameters (input fields) for this function
        param_names = [item.get("content")
                       for item in function_def["view_items"]
                       if "content" in item]
        params = []
        for param_name in param_names:
            param = function_fields[param_name]
            clean(param, FUNCTION_FIELD_ATTRIBUTES)
            for template in param.get("templates", []):
                clean(template, TEMPLATE_ATTRIBUTES)
            for value in param.get("values", []):
                clean(value, VALUE_ATTRIBUTES)
            params.append(param)
            function_params[param["uuid"]] = param

        # Get the message destination for this function
        dest_name = function_def["destination_handle"]
        if dest_name not in message_destinations:
            dest = all_destinations[dest_name]
            clean(dest, MESSAGE_DESTINATION_ATTRIBUTES)
            message_destinations[dest_name] = dest

    for workflow_name in (workflow_names or []):
        # Get the workflow definition
        workflow_def = client.cached_get("/workflows/{}?handle_format=names".format(workflow_name))
        # Remove the attributes we don't want to serialize
        clean(workflow_def, WORKFLOW_ATTRIBUTES)
        clean(workflow_def["content"], WORKFLOW_CONTENT_ATTRIBUTES)
        workflows[workflow_name] = workflow_def

    # Prepare the dictionary of substitution values for jinja2
    # (includes all the configuration elements related to the functions)
    data = {
        "package": package,
        "function_names": function_names,
        "output_dir": output_dir,
        "output_file": output_file,
        "functions": functions,
        "function_params": function_params,
        "workflows": workflows,
        "actions": actions,
        "action_fields": action_fields,
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


def codegen_package(client, package,
                    message_destination_names, function_names, workflow_names, action_names,
                    output_dir):
    """Generate a an installable python package"""
    if not valid_identifier(package):
        LOG.error(u"ERROR: %s is not a valid package name.", package)
        return

    # Make the output directory (usually a new subdirectory of cwd)
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        LOG.warn(u"%s", exc)

    template_file_path = pkg_resources.resource_filename("resilient_circuits", PACKAGE_TEMPLATE_PATH)
    return codegen_from_template(client, template_file_path, package,
                                 message_destination_names, function_names, workflow_names, action_names,
                                 output_dir, None)


def codegen_functions(client, function_names, workflow_names, action_names, output_dir, output_file):
    """Generate a python file that implements one or more functions"""
    message_destination_names = None
    template_file_path = pkg_resources.resource_filename("resilient_circuits", FUNCTION_TEMPLATE_PATH)
    return codegen_from_template(client, template_file_path, None,
                                 message_destination_names, function_names, workflow_names, action_names,
                                 output_dir, output_file)
