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

DATATABLE_TYPE_ID = 8

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


def list_message_destinations(client):
    """List all the message destinations"""
    try:
        message_destination_defs = client.cached_get("/message_destinations?handle_format=names")
    except SimpleHTTPException as exc:
        if exc.response.status_code == 500:
            LOG.error(u"ERROR: Message destinations are not available on this Resilient appliance.")
            return
        else:
            raise

    print(u"Available message destinations:")
    for message_destination_def in message_destination_defs["entities"]:
        print(u"    {}".format(message_destination_def["programmatic_name"]))


def list_incident_fields(client):
    """List all the custom incident fields"""
    field_defs = client.cached_get("/types/incident/fields?handle_format=names")
    print(u"Available incident fields:")
    for field_def in field_defs:
        if field_def.get("prefix") == "properties":
            print(u"    {}".format(field_def["name"]))


def list_datatables(client):
    """List all the datatables"""
    datatable_defs = client.cached_get("/types?handle_format=names")
    print(u"Available datatables:")
    for datatable_name, datatable_def in datatable_defs.items():
        if datatable_def["type_id"] == DATATABLE_TYPE_ID:
            print(u"    {}".format(datatable_name))


def list_automatic_tasks(client):
    """List all the tasks (built-in and custom are not distinguished)"""
    task_defs = client.cached_get("/automatic_tasks?handle_format=names")
    print(u"Available tasks:")
    for task_def in task_defs:
        print(u"    {}".format(task_def["programmatic_name"]))


def list_scripts(client):
    """List all the scripts"""
    script_defs = client.cached_get("/scripts?handle_format=names")
    print(u"Available scripts:")
    for script_def in script_defs["entities"]:
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
        for function_name in function_names or []:
            if function_name not in available_names:
                LOG.error(u"ERROR: Function '%s' not found on this Resilient appliance.", function_name)
                list_functions(client)
                return

        # Check that the named message destination is available
        for message_destination_name in message_destination_names or []:
            if message_destination_name not in all_destinations:
                LOG.error(u"ERROR: Message destination '%s' not found on this Resilient appliance.", message_destination_name)
                list_message_destinations(client)
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
            action_field_names = [item.get("content")
                                  for item in action_def["view_items"]
                                  if "content" in item]
            fields = []
            for field_name in action_field_names:
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

    function_fields = dict(
        (field["uuid"], field) for field in
        client.cached_get("/types/__function/fields?text_content_output_format=objects_no_convert")
    )

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

    incident_fields = {}
    if field_names:
        # Get definitions for custom incident fields
        for field_name in field_names:
            try:
                field = client.cached_get("/types/incident/fields/{}?handle_format=names".format(field_name))
                if field.get("prefix") != "properties":
                    # NB we only include custom fields (others are built-in so don't include customization)
                    LOG.error(u"Field '%s' is built-in, not included in customization.", field_name)
                    list_incident_fields(client)
                    return
                clean(field, INCIDENT_FIELD_ATTRIBUTES)
                for template in field.get("templates", []):
                    clean(template, TEMPLATE_ATTRIBUTES)
                for value in field.get("values", []):
                    clean(value, VALUE_ATTRIBUTES)
                incident_fields[field["uuid"]] = field
            except SimpleHTTPException as exc:
                if exc.response.status_code == 404:
                    LOG.error(u"ERROR: Field '%s' not found on this Resilient appliance.", field_name)
                    list_incident_fields(client)
                    return
                else:
                    raise

    datatables = {}
    if datatable_names:
        # Get datatable definitions
        for datatable_name in datatable_names:
            try:
                datatable_fields = {}
                for field in client.cached_get("/types/{}/fields?handle_format=names".format(datatable_name)):
                    clean(field, DATATABLE_FIELD_ATTRIBUTES)
                    for template in field.get("templates", []):
                        clean(template, TEMPLATE_ATTRIBUTES)
                    for value in field.get("values", []):
                        clean(value, VALUE_ATTRIBUTES)
                    datatable_fields[field["uuid"]] = field
                datatables[datatable_name] = datatable_fields
            except SimpleHTTPException as exc:
                if exc.response.status_code == 404:
                    LOG.error(u"ERROR: Datatable '%s' not found on this Resilient appliance.", datatable_name)
                    list_datatables(client)
                    return
                else:
                    raise

    # Automtic tasks determine the list of phases
    phase_names = set()
    automatic_tasks = {}
    if task_names:
        # Get task definitions
        for task_name in task_names:
            try:
                task = client.cached_get("/automatic_tasks/{}?handle_format=names".format(task_name))
                clean(task, AUTOMATIC_TASK_ATTRIBUTES)
                automatic_tasks[task_name] = task
                phase_names.add(task["phase_id"])
            except SimpleHTTPException as exc:
                if exc.response.status_code == 404:
                    LOG.error(u"ERROR: Task '%s' not found on this Resilient appliance.", task_name)
                    list_automatic_tasks(client)
                    return
                else:
                    raise

    phases = {}
    if phase_names:
        # Get phase definitions
        all_phases = dict((phase["name"], phase)
                          for phase in client.cached_get("/phases?handle_format=names")["entities"])
        for phase_name in phase_names:
            # Assume phase-name is found.  It was derived from the automatic task.
            phase = all_phases[phase_name]
            clean(phase, PHASE_ATTRIBUTES)
            phases[phase_name] = phase

    scripts = {}
    if script_names:
        # Get script definitions
        for script_name in script_names:
            try:
                script = client.cached_get("/scripts/{}?handle_format=names".format(script_name))
                clean(script, SCRIPT_ATTRIBUTES)
                scripts[script_name] = script
            except SimpleHTTPException as exc:
                if exc.response.status_code == 404:
                    LOG.error(u"ERROR: Script '%s' not found on this Resilient appliance.", script_name)
                    list_scripts(client)
                    return
                else:
                    raise

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
