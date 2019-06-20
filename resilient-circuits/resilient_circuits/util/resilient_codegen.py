# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to codegen a resilient-circuits component or package"""

from __future__ import print_function
import os
import sys
import io
import json
import logging
import keyword
import re
import datetime
import uuid
import time
import copy
import pkg_resources
from zipfile import ZipFile
from resilient_circuits import template_functions

if sys.version_info.major == 2:
    import imp
else:
    import importlib.util

LOG = logging.getLogger("__name__")


# A (const, random) namespace for import
UUID_CODEGEN = uuid.UUID('bfeec2d4-3770-11e8-ad39-4a0004044aa0')

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

ARTIFACT_TYPE_ATTRIBUTES = [
    "uuid",
    "desc",
    "name",
    "programmatic_name",
    "file",
    "system",
    "multi_aware",
    "use_for_relationships",
    "parse_for_csv",
    "enabled"
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

def list_artifact_types(artifact_type_defs):
    """List all the artifact types"""
    print(u"Available artifact types:")
    for artifact_type_def in artifact_type_defs:
        print(u"    {}".format(artifact_type_def["name"]))


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
                LOG.warning(exc)
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

            # Handle if the file is a .png
            if os.path.splitext(source_file)[1] == ".png":
                with io.open(source_file, 'rb') as source:
                    png_as_bytes = source.read()
                with io.open(target_file, mode="wb") as outfile:
                    outfile.write(png_as_bytes)

            else:
                with io.open(source_file, mode='r', encoding="utf-8") as source:
                    source_template = source.read()
                    source_rendered = template_functions.render(source_template, data)
                with io.open(target_file, mode="w", encoding="utf-8") as outfile:
                    outfile.write(source_rendered)


def codegen_from_template(cmd, client, export_file, template_file_path, package,
                          message_destination_names, function_names, workflow_names, action_names,
                          field_names, datatable_names, task_names, script_names, artifact_type_names,
                          output_dir, output_file, zip):
    """Based on a template-file, produce the generated file or package.

       To codegen a single file, the template will be a JSON dict with just one entry,
       such as {"file_to_generate.py": "path/to/template.jinja2"}
       To codegen a whole directory, the template dict can have multiple values,
       including nested subdirectories.

       Each source ("path/to/template.jinja2") will be rendered using jinja2,
       then written to the target ("file_to_generate.py").

       :param cmd: 'codegen' or 'extract'
       :param client: the REST client
       :param export_file: file containing customization exports (default is to use the server's latest)
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
       :param artifact_type_names: lists of custom artifact groups to include
       :param output_dir: output location
       :param output_file: output file name, also .res file produced for 'extract'
       :param zip: True if resulting file(s) should be zipped up
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
    artifact_types = {}

    if export_file:
        with io.open(export_file, 'r', encoding="utf-8") as export:
            export_data = json.loads(export.read())
        LOG.info(u"{} is based on the organization export from '{}'.".format(cmd, export_file))
    else:
        # Force a recent export
        latest_export_uri = "/configurations/exports/"
        client.post(latest_export_uri, {"layouts": True, "actions": True, "phases_and_tasks": True})

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
        LOG.info(u"{} is based on the organization export from {}.".format(cmd, dt))
        export_uri = "/configurations/exports/{}".format(last_id)
        export_data = client.get(export_uri)

    # Get definitions for custom incident fields - used in multiple areas
    all_fields = dict((field["name"], field)
                      for field in export_data.get("fields")
                      if field["type_id"] == INCIDENT_TYPE_ID and field.get("prefix") == "properties")

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

    # ensure empty lists as we may dynamically add to them
    if not task_names:
        task_names = []
    if not script_names:
        script_names = []
    if not artifact_type_names:
        artifact_type_names = []
    if not field_names:
        field_names = []

    if action_names:
        # Check that 'actions' are available. actions are rules
        action_defs = export_data.get("actions")
        if not action_defs:
            LOG.error(u"ERROR: Rules are not available in this export.")
            return

        # Check that each named action is available
        actions = {action_def["name"]: clean(copy.deepcopy(action_def), ACTION_ATTRIBUTES)
                   for action_def in action_defs
                   if action_def["name"] in action_names}
        all_action_fields = dict((field["uuid"], field)
                                 for field in export_data.get("fields")
                                 if field["type_id"] == ACTION_TYPE_ID)
        all_action_fields_2 = dict((field["name"], field)
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
                                  if "content" in item and item.get("field_type")]
            fields = []
            for field_uuid in action_field_uuids:
                field = copy.deepcopy(all_action_fields.get(field_uuid))
                if field is None:
                    # v29-style export where layout indexed by field name
                    field = copy.deepcopy(all_action_fields_2.get(field_uuid))
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

            # Get the task(s) for this rule (if any)
            for automation in action_def["automations"]:
                if automation.get("tasks_to_create"):
                    for task_name in automation["tasks_to_create"]:
                        if task_name not in task_names:
                            task_names.append(task_name)

                elif automation.get("scripts_to_run"):
                    script_name = automation["scripts_to_run"]
                    if script_name not in script_names:
                        script_names.append(script_name)

                elif automation.get("field"):
                    field_name = automation["field"]
                    if field_name not in field_names and field_name in all_fields:
                        field_names.append(field_name)

            # Get the message destination(s) for this rule (if any)
            dest_names = action_def["message_destinations"]
            for dest_name in dest_names:
                if dest_name not in message_destinations:
                    dest = copy.deepcopy(all_destinations_2[dest_name])
                    clean(dest, MESSAGE_DESTINATION_ATTRIBUTES)
                    message_destinations[dest_name] = dest

    all_functions = dict((function["name"], function)
                         for function in export_data.get("functions") or [])
    all_function_fields = dict((field["uuid"], field)
                               for field in export_data.get("fields")
                               if field["type_id"] == FUNCTION_TYPE_ID)

    for function_name in (function_names or []):
        # Get the function definition
        function_def = copy.deepcopy(all_functions.get(function_name))
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
            param = copy.deepcopy(all_function_fields[param_name])
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
            dest = copy.deepcopy(all_destinations[dest_name])
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
                workflow = clean(copy.deepcopy(workflow_def), WORKFLOW_ATTRIBUTES)
                clean(workflow["content"], WORKFLOW_CONTENT_ATTRIBUTES)
                workflows[workflow_name] = workflow
            else:
                LOG.error(u"ERROR: Workflow '%s' not found in this export.", workflow_name)
                list_workflows(export_data.get("workflows"))
                return

    if field_names:
        for field_name in field_names:
            fielddef = all_fields.get(field_name)
            if fielddef:
                field = clean(copy.deepcopy(fielddef), INCIDENT_FIELD_ATTRIBUTES)
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
                    field = clean(copy.deepcopy(fielddef), DATATABLE_FIELD_ATTRIBUTES)
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

    # Automatic tasks determine the list of phases
    phase_names = set()
    if task_names:
        # Get task definitions
        all_tasks = dict((task["programmatic_name"], task)
                          for task in export_data.get("automatic_tasks"))
        for task_name in task_names:
            task = all_tasks.get(task_name)
            if task:
                automatic_tasks[task_name] = clean(copy.deepcopy(task), AUTOMATIC_TASK_ATTRIBUTES)
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
            phases[phase_name] = clean(copy.deepcopy(phase), PHASE_ATTRIBUTES)

    if script_names:
        # Get script definitions
        all_scripts = dict((script["name"], script)
                           for script in export_data.get("scripts"))
        for script_name in script_names:
            script = all_scripts.get(script_name)
            if script:
                scripts[script_name] = clean(copy.deepcopy(script), SCRIPT_ATTRIBUTES)
            else:
                LOG.error(u"ERROR: Script '%s' not found in this export.", script_name)
                list_scripts(export_data.get("scripts", []))
                return

    if artifact_type_names:
        # get custom artifact types
        all_artifact_types = dict((artifact_type["programmatic_name"], artifact_type)
                          for artifact_type in export_data.get("incident_artifact_types"))

        for artifact_type_name in artifact_type_names:
            for artifact_name in all_artifact_types:
                artifact = all_artifact_types[artifact_name]
                if artifact["programmatic_name"] == artifact_type_name:
                    artifact_types[artifact["programmatic_name"]] = clean(copy.deepcopy(artifact), ARTIFACT_TYPE_ATTRIBUTES)

        # confirm we got all the custom artifact types
        for artifact_name in artifact_type_names:
            if artifact_name not in artifact_types:
                LOG.error(u"ERROR: Artifact Type '%s' not found in this export.", artifact_name)
                list_artifact_types(export_data.get("incident_artifact_types", []))
                return

    # Minify the export_data
    fields_list = []
    if len(incident_fields) == 0:
        # import requires at least one, use placeholder
        fields_list.extend(["incident/inc_training"])
    else:
        fields_list.extend(["incident/{}".format(fld["name"]) for fld in incident_fields.values()])
    fields_list.extend(["actioninvocation/{}".format(fld["name"]) for fld in action_fields.values()])
    fields_list.extend(["__function/{}".format(fld["name"]) for fld in function_params.values()])
    keep_keys = [
        "export_date",
        "export_format_version",
        "id",
        "server_version"
    ]
    minify_keys = {
        "actions": {"name": actions.keys()},
        "automatic_tasks": {"programmatic_name": automatic_tasks.keys()},
        "fields": {"export_key": fields_list},
        "functions": {"name": functions.keys()},
        "message_destinations": {"programmatic_name": message_destinations.keys()},
        "phases": {"name": phases.keys()},
        "scripts": {"name": scripts.keys()},
        "types": {"type_name": datatables.keys()},
        "workflows": {"programmatic_name": workflows.keys()},
        "incident_artifact_types": {"programmatic_name": artifact_types.keys()}
    }
    for key in export_data.keys():
        if key in keep_keys:
            pass
        elif key in minify_keys.keys():
            name = list(minify_keys[key].keys())[0]   # The property we match on
            values = minify_keys[key][name]           # These are the names of the things to keep
            for data in list(export_data[key]):
                if not data.get(name):
                    LOG.warning("No %s in %s", name, key)
                if not data.get(name) in values:
                    export_data[key].remove(data)
        elif isinstance(export_data[key], list):
            export_data[key] = []
        elif isinstance(export_data[key], dict):
            export_data[key] = {}
        else:
            export_data[key] = None
    # Incident types are special, add one for this specific package
    # (because not enabled, this doesn't actually get loaded into the destination)
    t0 = int(time.time()*1000)
    export_data["incident_types"] = [{
        "update_date": t0,
        "create_date": t0,
        "uuid": str(UUID_CODEGEN),
        "description": "Customization Packages (internal)",
        "export_key": "Customization Packages (internal)",
        "name": "Customization Packages (internal)",
        "enabled": False,
        "system": False,
        "parent_id": None,
        "hidden": False,
        "id": 0
    }]

    # if an extract, write the file and return
    if cmd == "extract":
        do_extract(output_file, export_data, zip)
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
        "actions": actions,
        "export_data": export_data,
        "incident_artifact_types": artifact_types
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

def do_extract(output_file, export_data, zip):
    """
    either create the export file in clear text or zip up
    :param output_file:
    :param export_data:
    :param zip: True if zipping up file
    :return: None
    """
    if sys.version_info.major >= 3:
        res_data = json.dumps(export_data, ensure_ascii=False)
    else:
        res_data = unicode(json.dumps(export_data, ensure_ascii=False))

    if zip:
        # get the base name of the file to create so we know what to call our file inside the zip file
        if not output_file.endswith(".zip"):
            output_file = "".join((output_file, ".zip"))
        print (u"Writing {}".format(output_file))

        base = os.path.basename(output_file)
        filename = os.path.splitext(base)
        while '.' in filename[0]:
            filename = os.path.splitext(filename[0])
        # name internal to zip file
        filename = "".join((filename[0], ".res"))

        with ZipFile(output_file, 'w') as myZip:
            myZip.writestr(filename, res_data)
    else:
        print (u"Writing {}".format(output_file))
        with io.open(output_file, 'w', encoding="utf-8") as extract_fh:
            extract_fh.write(res_data)

    return

def codegen_package(client, export_file, package,
                    message_destination_names, function_names, workflow_names, action_names,
                    field_names, datatable_names, task_names, script_names, artifact_type_names,
                    output_dir):
    """Generate a an installable python package"""
    if not valid_identifier(package):
        LOG.error(u"ERROR: %s is not a valid package name.", package)
        return

    # Make the output directory (usually a new subdirectory of cwd)
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        LOG.warning(u"%s", exc)

    template_file_path = pkg_resources.resource_filename("resilient_circuits", PACKAGE_TEMPLATE_PATH)
    return codegen_from_template('codegen', client, export_file, template_file_path, package,
                                 message_destination_names, function_names, workflow_names, action_names,
                                 field_names, datatable_names, task_names, script_names, artifact_type_names,
                                 output_dir, None, False)


def codegen_functions(client, export_file, function_names, workflow_names, action_names, artifact_type_names,
                      output_dir, output_file):
    """Generate a python file that implements one or more functions"""
    message_destination_names = None
    template_file_path = pkg_resources.resource_filename("resilient_circuits", FUNCTION_TEMPLATE_PATH)
    return codegen_from_template('codegen', client, export_file, template_file_path, None,
                                 message_destination_names, function_names, workflow_names, action_names,
                                 None, None, None, None, artifact_type_names,
                                 output_dir, output_file, False)

def extract_to_res(client, export_file,
                     message_destination_names, function_names, workflow_names, action_names,
                     field_names, datatable_names, task_names, script_names, artifact_types,
                     output_file, zip):
    """
    extract portions of a .res file as directed by the parameters below and save to a specified file
    :param client:
    :param export_file: .res to use otherwise the most recent one produced will be used
    :param message_destination_names:
    :param function_names:
    :param workflow_names:
    :param action_names:
    :param field_names:
    :param datatable_names:
    :param task_names:
    :param script_names:
    :param artifact_types:
    :param output_file: file to produce or overwrite
    :param zip: true if resulting file should be zipped
    :return: None
    """
    return codegen_from_template('extract', client, export_file, None, None,
                                 message_destination_names, function_names, workflow_names, action_names,
                                 field_names, datatable_names, task_names, script_names, artifact_types,
                                 None, output_file, zip)

def get_customize_file_path(package):
    """Get the location of current customize.py for this package"""
    output_base = os.path.join(os.getcwd(), package)
    customize_dir = os.path.join(output_base, package, "util")
    customize_file = os.path.join(customize_dir, "customize.py")
    return customize_file, output_base, customize_dir

def get_codegen_reload_data(package):
    """Read the default codegen_reload_data section from the given package"""

    # Get the file path of the customize file for the package
    customize_file, base_dir, customize_dir = get_customize_file_path(package)

    # Check if customize.py exits.  We need to get the reload commands
    # from the current customize.py and if it's not there then exit.
    if not os.path.isfile(customize_file):
        raise Exception(u"{} does not exist. Run resilient_circuits codegen without --reload option to create it.".format(customize_file))

    data = None

    # Dynamically load the customize module and call the codegen_reload_date routine.
    # Different pacakges are used in Python 2 and Python 3.
    if sys.version_info.major == 2:      # Python 2
        try:
            customize_module = imp.load_source("customize", customize_file)
            data = customize_module.codegen_reload_data()
        except Exception as e:
            LOG.error(u"Error loading codegen_reload_data: %s", e)
    else:                                # Python 3
        try:
            spec = importlib.util.spec_from_file_location("codegen_reload_data", customize_file)
            customize_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(customize_module)
            data = customize_module.codegen_reload_data()
        except Exception as e:
            LOG.error(u"Error loading codegen_reload_data for package %s", e)
    return data or []


def merge_codegen_params(reload_list, arg_list):
    """Merge the codegen reload params list additional arguments list with no duplicates"""

    if reload_list:
        new_reload_list = reload_list
    else:
        new_reload_list = []

    if arg_list:
        new_arg_list = arg_list
    else:
        new_arg_list = []

    # Combine the reload and new argument list without duplicates
    combined_args_list = list(set(new_reload_list).union(set(new_arg_list)))

    return combined_args_list



def codegen_reload_package(client, args):
    """Generate a package using previous codegen parameters and add any new ones from the commandline."""

    # Get the previous params for codegen from the customize.py
    # codegen_reload_data function.
    codegen_params = get_codegen_reload_data(args.reload)

    if codegen_params == None or codegen_params == []:
        raise Exception(u"codegen_reload_data entry point returned empty list")

    # Rename the old customize.py file to customize-yyyymmdd-hhmmss.bak
    customize_file, output_base, customize_dir = get_customize_file_path(args.reload)

    # Get time now.
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    old_customize_file = os.path.join(customize_dir, "customize-{}.bak".format(now))
    LOG.info(u"Renaming customize.py to %s", old_customize_file)
    os.rename(customize_file, old_customize_file)

    try:
        # If there are new commandline parameters, append them to the old commandline
        # list for each param type.
        message_destinations = merge_codegen_params(codegen_params.get("message_destinations", []), args.messagedestination)
        functions            = merge_codegen_params(codegen_params.get("functions", []), args.function)
        rules                = merge_codegen_params(codegen_params.get("actions", []), args.rule)
        workflows            = merge_codegen_params(codegen_params.get("workflows", []), args.workflow)
        incident_fields      = merge_codegen_params(codegen_params.get("incident_fields", []), args.field)
        datatables           = merge_codegen_params(codegen_params.get("datatables", []), args.datatable)
        automatic_tasks      = merge_codegen_params(codegen_params.get("automatic_tasks", []), args.task)
        scripts              = merge_codegen_params(codegen_params.get("scripts", []), args.script)
        artifact_types       = merge_codegen_params(codegen_params.get("incident_artifact_types", []), args.artifacttype)

        # Print the codegen --reload command with all arguments.
        print_codegen_reload_commandline(args.reload, args.exportfile,
                                         message_destinations,
                                         functions,
                                         workflows,
                                         rules,
                                         incident_fields,
                                         datatables,
                                         automatic_tasks,
                                         scripts,
                                         artifact_types)

        # Call codegen to recreate package with the new parameter list.
        codegen_package(client,
                    args.exportfile,
                    args.reload,
                    message_destinations,
                    functions,
                    workflows,
                    rules,
                    incident_fields,
                    datatables,
                    automatic_tasks,
                    scripts,
                    artifact_types,
                    output_base)
    except Exception as e:
        LOG.error(u"Error running codegen --reload %s", e)
    finally:
        # If no customize.py was created an error occurred somewhere in codegen.
        # Rename the saved off version back to customize.py
        if not os.path.isfile(customize_file):
            LOG.info(u"Renaming %s back to %s", old_customize_file, customize_file)
            os.rename(old_customize_file, customize_file)

def create_command(command, params, quotes):
    """Create commandline substring for codegen --reload commandline """
    result_command = command
    if len(params) > 0:
        for item in params:
            if quotes:
                result_command = result_command + u' "{}"'.format(item)
            else:
                result_command = result_command + u" {}".format(item)
    else:
        result_command = u""
    return result_command

def print_codegen_reload_commandline(package, export_file, message_destinations, functions, workflows,
                                     rules, incident_fields, datatables, tasks, scripts, artifact_types):
    """Print the resilient-circuits codegen --reload commandline for a given package"""

    # Build the commandline string
    commandline = u"resilient-circuits codegen --reload {}".format(package)
    if export_file:
        commandline = commandline + u" --export {}".format(export_file)
    commandline = commandline + create_command(u" --messagedestination", message_destinations, False)
    commandline = commandline + create_command(u" --rule", rules, True)
    commandline = commandline + create_command(u" --workflow", workflows, False)
    commandline = commandline + create_command(u" --function", functions, False)
    commandline = commandline + create_command(u" --field", incident_fields, False)
    commandline = commandline + create_command(u" --datatable", datatables, False)
    commandline = commandline + create_command(u" --task", tasks, False)
    commandline = commandline + create_command(u" --script", scripts, True)
    commandline = commandline + create_command(u" --artifacttype", artifact_types, True)

    print (commandline)