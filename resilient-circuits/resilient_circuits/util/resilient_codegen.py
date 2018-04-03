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
import datetime
from resilient_circuits import template_functions


LOG = logging.getLogger("__name__")


# Template files that drive codegen
FUNCTION_TEMPLATE_PATH = "data/template_function.jinja2"
PACKAGE_TEMPLATE_PATH = "data/template_package.jinja2"

INCIDENT_TYPE_ID = 0
ACTION_TYPE_ID = 6
DATATABLE_TYPE_ID = 8
FUNCTION_TYPE_ID = 11

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
INCIDENT_FIELD_ATTRIBUTES = FUNCTION_FIELD_ATTRIBUTES
DATATABLE_FIELD_ATTRIBUTES = FUNCTION_FIELD_ATTRIBUTES

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

AUTOMATIC_TASK_ATTRIBUTES = [
    "uuid",  # note - workflows reference tasks by uuid
    "due_date_offset",
    "due_date_units",
    "name",
    "enabled",
    "task_layout",
    "programmatic_name",
    "phase_id",
    "optional",
    "instructions"
]

AUTOMATIC_TASK_LAYOUT_ATTRIBUTES = [
    "show_if",
    "field_type",
    "show_link_header",
    "element",
    "content",
    "step_label"
]

PHASE_ATTRIBUTES = [
    "uuid",
    "name",
    "enabled",
    "order"
]

SCRIPT_ATTRIBUTES = [
    "uuid",  # note - workflows reference scripts by uuid
    "description",
    "language",
    "object_type",
    "name",
    "script_text"
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


def list_functions(function_defs):
    """List all the functions"""
    print(u"Available functions:")
    for function_def in function_defs:
        print(u"    {}".format(function_def["name"]))


def list_workflows(workflow_defs):
    """List all the workflows"""
    print(u"Available workflows:")
    for workflow_def in workflow_defs:
        print(u"    {}".format(workflow_def["programmatic_name"]))


def list_actions(action_defs):
    """List all the actions (rules)"""
    print(u"Available rules:")
    for action_def in action_defs:
        print(u"    {}".format(action_def["name"]))


def list_message_destinations(message_destination_defs):
    """List all the message destinations"""
    print(u"Available message destinations:")
    for message_destination_def in message_destination_defs:
        print(u"    {}".format(message_destination_def["programmatic_name"]))


def list_incident_fields(field_defs):
    """List all the custom incident fields"""
    print(u"Available incident fields:")
    for field_def in field_defs:
        if field_def["type_id"] == INCIDENT_TYPE_ID and field_def.get("prefix") == "properties":
            print(u"    {}".format(field_def["name"]))


def list_datatables(datatable_defs):
    """List all the datatables"""
    print(u"Available datatables:")
    for datatable_def in datatable_defs:
        if datatable_def["type_id"] == DATATABLE_TYPE_ID:
            print(u"    {}".format(datatable_def["type_name"]))


def list_automatic_tasks(task_defs):
    """List all the tasks (built-in and custom are not distinguished)"""
    print(u"Available tasks:")
    for task_def in task_defs:
        print(u"    {}".format(task_def["programmatic_name"]))


def list_scripts(script_defs):
    """List all the scripts"""
    print(u"Available scripts:")
    for script_def in script_defs:
        print(u"    {}".format(script_def["name"]))


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
                          field_names, datatable_names, task_names, script_names,
                          output_dir, output_file):
    """Based on a template-file, produce the generated file or package.

       To codegen a single file, the template will be a JSON dict with just one entry,
       such as {"file_to_generate.py": "path/to/template.jinja2"}
       To codegen a whole directory, the template dict can have multiple values,
       including nested subdirectories.

       Each source ("path/to/template.jinja2") will be rendered using jinja2,
       then written to the target ("file_to_generate.py").

       :param client: the REST client
       :param template_file_path: location of templates
       :param package: name of the package to be generated
       :param message_destination_names: list of message desctinations; generate all the functions that use them
       :param function_names: list of named functions to be generated
       :param workflow_names: list of workflows whose customization def should be included in the package
       :param action_names: list of actions (rules) whose customization def should be included in the package
       :param field_names: list of incident fields whose customization def should be included in the package
       :param datatable_names: list of data tables whose customization def should be included in the package
       :param task_names: list of automatic tasks whose customization def should be included in the package
       :param script_names: list of scripts whose customization def should be included in the package
       :param output_dir: output location
       :param output_file: output file name
    """
    functions = {}
    function_params = {}
    message_destinations = {}
    incident_fields = {}
    action_fields = {}
    datatables = {}
    datatable_fields = {}
    phases = {}
    automatic_tasks = {}
    scripts = {}
    workflows = {}
    actions = {}

    # Get the most recent org export that includes actions and tasks
    export_uri = "/configurations/exports/history"
    export_list = client.get(export_uri)["histories"]
    last_date = 0
    last_id = 0
    for export in export_list:
        if export["options"]["actions"] and export["options"]["phases_and_tasks"]:
            if export["date"] > last_date:
                last_date = export["date"]
                last_id = export["id"]
    if last_date == 0:
        LOG.error(u"ERROR: No suitable export is available.  "
                  u"Create an export for code generation. (Administrator Settings -> Organization -> Export).")
        return
    dt = datetime.datetime.utcfromtimestamp(last_date/1000.0)
    LOG.info(u"Codegen is based on the organization export from {}.".format(dt))
    export_uri = "/configurations/exports/{}".format(last_id)
    export_data = client.get(export_uri)

    all_destinations = dict((dest["programmatic_name"], dest)
                            for dest in export_data.get("message_destinations", []))
    all_destinations_2 = dict((dest["name"], dest)
                              for dest in export_data.get("message_destinations", []))

    if function_names or message_destination_names:
        # Check that 'functions' are available (v30 onward)
        function_defs = export_data.get("functions")
        if not function_defs:
            LOG.error(u"ERROR: Functions are not available in this export.")
            return
        function_names = function_names or []
        available_names = [function_def["name"] for function_def in function_defs]
        if message_destination_names:
            # Build a list of all the functions that use the specified message destination(s)
            for function_def in function_defs:
                if function_def["destination_handle"] in message_destination_names:
                    function_names.append(function_def["name"])

        # Check that each named function is available
        for function_name in function_names or []:
            if function_name not in available_names:
                LOG.error(u"ERROR: Function '%s' not found in this export.", function_name)
                list_functions(function_defs)
                return

        # Check that the named message destination is available
        for message_destination_name in message_destination_names or []:
            if message_destination_name not in all_destinations:
                LOG.error(u"ERROR: Message destination '%s' not found in this export.", message_destination_name)
                list_message_destinations(export_data.get("message_destinations"))
                return

    if workflow_names:
        # Check that 'workflows' are available (v28 onward)
        workflow_defs = export_data.get("workflows")
        if not workflow_defs:
            LOG.error(u"ERROR: Workflows are not available in this export.")
            return
    else:
        workflow_names = []

    if action_names:
        # Check that 'actions' are available
        action_defs = export_data.get("actions")
        if not action_defs:
            LOG.error(u"ERROR: Rules are not available in this export.")
            return

        # Check that each named action is available
        actions = {action_def["name"]: clean(action_def.copy(), ACTION_ATTRIBUTES)
                   for action_def in action_defs
                   if action_def["name"] in action_names}
        all_action_fields = dict((field["uuid"], field)
                                 for field in export_data.get("fields")
                                 if field["type_id"] == ACTION_TYPE_ID)

        for action_name in action_names:
            if action_name not in actions:
                LOG.error(u"ERROR: Rule '%s' not found in this export.", action_name)
                list_actions(action_defs)
                return
            action_def = actions[action_name]

            # Get the activity-fields for this action (if any)
            action_field_uuids = [item.get("content")
                                  for item in action_def["view_items"]
                                  if "content" in item]
            fields = []
            for field_uuid in action_field_uuids:
                field = all_action_fields.get(field_uuid).copy()
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
                    dest = all_destinations_2[dest_name].copy()
                    clean(dest, MESSAGE_DESTINATION_ATTRIBUTES)
                    message_destinations[dest_name] = dest

    all_functions = dict((function["name"], function)
                         for function in export_data.get("functions"))
    all_function_fields = dict((field["uuid"], field)
                               for field in export_data.get("fields")
                               if field["type_id"] == FUNCTION_TYPE_ID)

    for function_name in (function_names or []):
        # Get the function definition
        function_def = all_functions.get(function_name).copy()
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
            param = all_function_fields[param_name].copy()
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
            dest = all_destinations[dest_name].copy()
            clean(dest, MESSAGE_DESTINATION_ATTRIBUTES)
            message_destinations[dest_name] = dest

    if workflow_names:
        all_workflows = dict((workflow["programmatic_name"], workflow)
                             for workflow in export_data.get("workflows"))
        for workflow_name in workflow_names:
            # Get the workflow definition
            workflow_def = all_workflows.get(workflow_name)
            if workflow_def:
                # Remove the attributes we don't want to serialize
                workflow = clean(workflow_def.copy(), WORKFLOW_ATTRIBUTES)
                clean(workflow["content"], WORKFLOW_CONTENT_ATTRIBUTES)
                workflows[workflow_name] = workflow
            else:
                LOG.error(u"ERROR: Workflow '%s' not found in this export.", workflow_name)
                list_workflows(export_data.get("workflows"))
                return

    if field_names:
        # Get definitions for custom incident fields
        all_fields = dict((field["name"], field)
                          for field in export_data.get("fields")
                          if field["type_id"] == INCIDENT_TYPE_ID and field.get("prefix") == "properties")
        for field_name in field_names:
            fielddef = all_fields.get(field_name)
            if fielddef:
                field = clean(fielddef.copy(), INCIDENT_FIELD_ATTRIBUTES)
                for template in field.get("templates", []):
                    clean(template, TEMPLATE_ATTRIBUTES)
                for value in field.get("values", []):
                    clean(value, VALUE_ATTRIBUTES)
                incident_fields[field["uuid"]] = field
            else:
                LOG.error(u"ERROR: Custom incident field '%s' not found in this export.", field_name)
                list_incident_fields(export_data.get("fields"))
                return

    if datatable_names:
        # Get datatable definitions
        all_datatables = dict((table["type_name"], table)
                              for table in export_data.get("types")
                              if table["type_id"] == DATATABLE_TYPE_ID)
        for datatable_name in datatable_names:
            datatable = all_datatables.get(datatable_name)
            if datatable:
                for (fieldname, fielddef) in datatable["fields"].items():
                    field = clean(fielddef.copy(), DATATABLE_FIELD_ATTRIBUTES)
                    for template in field.get("templates", []):
                        clean(template, TEMPLATE_ATTRIBUTES)
                    for value in field.get("values", []):
                        clean(value, VALUE_ATTRIBUTES)
                    datatable_fields[field["uuid"]] = field
                datatables[datatable_name] = datatable
            else:
                LOG.error(u"ERROR: Datatable '%s' not found in this export.", datatable_name)
                list_datatables(export_data.get("types", []))
                return

    # Automtic tasks determine the list of phases
    phase_names = set()
    if task_names:
        # Get task definitions
        all_tasks = dict((task["programmatic_name"], task)
                          for task in export_data.get("automatic_tasks"))
        for task_name in task_names:
            task = all_tasks.get(task_name)
            if task:
                automatic_tasks[task_name] = clean(task.copy(), AUTOMATIC_TASK_ATTRIBUTES)
                phase_names.add(task["phase_id"])
            else:
                LOG.error(u"ERROR: Task '%s' not found in this export.", task_name)
                list_automatic_tasks(export_data.get("automatic_tasks", []))
                return

    if phase_names:
        # Get phase definitions
        all_phases = dict((phase["name"], phase)
                          for phase in export_data.get("phases"))
        for phase_name in phase_names:
            # Assume phase-name is found.  It was derived from the automatic task.
            phase = all_phases[phase_name]
            phases[phase_name] = clean(phase.copy(), PHASE_ATTRIBUTES)

    if script_names:
        # Get script definitions
        all_scripts = dict((script["name"], script)
                           for script in export_data.get("scripts"))
        for script_name in script_names:
            script = all_scripts.get(script_name)
            if script:
                scripts[script_name] = clean(script.copy(), SCRIPT_ATTRIBUTES)
            else:
                LOG.error(u"ERROR: Script '%s' not found in this export.", script_name)
                list_scripts(export_data.get("scripts", []))
                return

    # Prepare the dictionary of substitution values for jinja2
    # (includes all the configuration elements related to the functions)
    data = {
        "package": package,
        "function_names": function_names,
        "output_dir": output_dir,
        "output_file": output_file,
        "functions": functions,
        "function_params": function_params,
        "message_destinations": message_destinations,
        "incident_fields": incident_fields,
        "action_fields": action_fields,
        "datatables": datatables,
        "datatable_fields": datatable_fields,
        "phases": phases,
        "automatic_tasks": automatic_tasks,
        "scripts": scripts,
        "workflows": workflows,
        "actions": actions
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
                    field_names, datatable_names, task_names, script_names,
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
                                 field_names, datatable_names, task_names, script_names,
                                 output_dir, None)


def codegen_functions(client, function_names, workflow_names, action_names, output_dir, output_file):
    """Generate a python file that implements one or more functions"""
    message_destination_names = None
    template_file_path = pkg_resources.resource_filename("resilient_circuits", FUNCTION_TEMPLATE_PATH)
    return codegen_from_template(client, template_file_path, None,
                                 message_destination_names, function_names, workflow_names, action_names,
                                 None, None, None, None,
                                 output_dir, output_file)
