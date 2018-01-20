#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility to codegen a resilient-circuits component or package"""

from __future__ import print_function

import logging
import resilient
from resilient_circuits import template_functions


# JINJA template for the generated code
CODE_TEMPLATE = '''# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits.actions_component import ResilientComponent, function


class MyComponent(ResilientComponent):
    """Component that implements Resilient function(s)"""
{%for function in functions%}
    @function("{{function.name|js}}")
    def _{{function.name}}_function(self, event, *args, **kwargs):
        """Function: {{function.description}}"""

        # Get the function parameters:
        function_parameters = event.message.get("inputs", {}){%for p in function.parameters%}
        {{p.name}} = function_parameters.get("{{p.name}}"){%endfor%}

        # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE
        logging.getLogger(__name__).info("this function was called!")

        # Return a string or dictionary
        return "That's all, folks!"
{%endfor%}'''

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
    "description"
]


class CodegenArgumentParser(resilient.ArgumentParser):
    """Commandline arguments"""
    def __init__(self, config_file=None):
        super(CodegenArgumentParser, self).__init__(config_file=config_file)

        self.add_argument('function',
                          nargs="*",
                          help="Name of the function.")


def list_functions(client):
    """List all the functions"""
    function_defs = client.get("/functions?handle_format=names")

    print("Available functions:")
    for function_def in function_defs["entities"]:
        print("    {}".format(function_def["name"]))


def clean(dictionary, keep):
    """Remove attributes that are not in the 'keep' list"""
    for key in dictionary.keys():
        if key not in keep:
            dictionary.pop(key)
    return dictionary


def codegen_function(client, function_names):
    """Generate a code template for a function"""
    functions = []

    for function_name in function_names:
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

        # Write out the template
        function_def["parameters"] = params
        functions.append(function_def)

    data = {
        "functions": functions,
    }
    print(template_functions.render(CODE_TEMPLATE, data))


def main():
    """main"""
    parser = CodegenArgumentParser(config_file=resilient.get_config_file())
    opts = parser.parse_args()

    # Create SimpleClient for a REST connection to the Resilient services
    client = resilient.get_client(opts)

    function_names = opts.get("function")
    if function_names:
        codegen_function(client, function_names)
    else:
        list_functions(client)


if __name__ == "__main__":
    # logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARN)
    main()
