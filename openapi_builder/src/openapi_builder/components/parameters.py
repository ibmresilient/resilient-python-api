# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from typing import Tuple

from . import constants
from . import common

class Parameters():
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict):
        self.is_soar = is_soar
        self.is_terse = is_terse
        self.params_dict = self.import_spec(spec)

    def import_spec(self, spec: dict, nav_path: list=constants.SPEC_PARAMETERS_PATH) -> dict:
        """From an existing OpenAPI spec document, import the parameters section
        :param spec: original OpenAPI spec document
        :type spec: dict
        :param nav_path: list of directory structure to navigate to find parameters
        :type nav_path: list
        :return: a Parameters object
        :rtype: Parameters
        """
        return common.navigate_dict(spec, nav_path)

    def export_section(self):
        """export the parameters to be used in the openapi spec file

        :return: parameters section of the openapi spec document
        :rtype: dict
        """
        return self.params_dict

    def parse_query_parameters(self,
                               query_parameters: str,
                               operation_id: str) -> Tuple[list, list]:
        """uri can contain query parameters. This function parses those out, if present

        :param query_parameters: string encoded query parameters: key1=value&key2=value
        :type query_parameters: str
        :param operation_id: endpoint reference label for prompting
        :type operation_id: str
        :return list of reference to the parsed query parameters
        """
        # parse out any query parameters on the uri
        new_params = []
        new_query_names = []
        if query_parameters:
            split_params = query_parameters.split("&")
            for split_param in split_params:
                split_query_key_value = split_param.split("=")
                param_name = split_query_key_value[0]

                # does this parameter already exist?
                if param_name not in self.params_dict:
                    param_type = common.prompt_input(f"({operation_id}:{param_name}) Found query parameter: '{param_name}'. Enter parameter type.", choices=constants.VALUE_TYPES)
                    param_required = common.prompt_input(f"({operation_id}:{param_name}) Enter required parameter use.", choices=constants.API_PARAMETER_REQUIRED)
                    param_desc = common.prompt_input(f"({operation_id}:{param_name}) Enter description.", required=False)

                    self.params_dict[param_name] = {
                        "in": "query",
                        "name": param_name,
                        "required": param_required,
                        "description": param_desc,
                        "schema": {
                            "type": param_type
                        }
                    }
                    new_query_names.append(param_name)

                # either $ref or in-line
                if constants.IN_LINE_REFERENCES:
                    new_params.append(self.params_dict[param_name])
                else:
                    new_params.extend([{constants.INTERNAL_REF: common.make_ref(constants.SPEC_PARAMETERS_PATH, param_name)}])

        return (new_query_names, new_params)

    def prompt_parameters(self,
                          parameter_type: str,
                          uri: str = None,
                          operation_id: str = None,
                          exclude_list: list = None) -> list:
        """collect parameters. These parameters may be of type 'query' or 'path'

        :param parameter_type: "query" or "path"
        :type parameter_type: str
        :param uri: endpoint path uri
        :type uri: str
        :param operation_id: label derived or prompted for this endpoint
        :type operation_id: str
        :param query_parameters: string encoded query parameters, key1=value&key2=value
        :return list of parameters to include
        :rtype list
        """
        new_params = []

        common.multiline_output([f"{parameter_type.title()} parameters",
                                 f"API calls may have {parameter_type} parameters. They are optional parameters added to the endpoint URL.",
                                 f"The following prompts will guide you through {parameter_type} parameters common to API calls."])

        # get all existing parameters which can be reused
        existing_parameters = common.get_parameters(self.params_dict, [], {"in": parameter_type})
        existing_parameters = list(set(existing_parameters) - set(exclude_list))
        # existing query parameters
        new_params.extend(self.prompt_existing_parameters(parameter_type, operation_id, existing_parameters))

        # prompt for path parameters
        while True:
            another = common.make_another(self.params_dict, default="a ")
            uri_prompt = ""
            if uri:
                uri_prompt = f" for '{uri}'"
            endpoint_prompt = ""
            if operation_id:
                endpoint_prompt = f"({operation_id}) "

            param_name = common.prompt_input(f"* {endpoint_prompt}Enter {another}{parameter_type} parameter{uri_prompt}.", required=False)
            if not param_name:
                break

            # make sure the query parameter wasn't entered like: key=value
            if parameter_type.lower() == "query" and "=" in param_name:
                param_name = param_name.split("=")[0]

            param_type = common.prompt_input(f"({operation_id}:{param_name}) Enter parameter type.", choices=constants.VALUE_TYPES)
            param_required = common.prompt_input(f"({operation_id}:{param_name}) Enter required parameter use.", choices=constants.API_PARAMETER_REQUIRED)
            param_desc = common.prompt_input(f"({operation_id}:{param_name}) Enter description.", required=False)

            self.params_dict[param_name] = {
                "in": "query",
                "name": param_name,
                "required": param_required,
                "description": param_desc,
                "schema": {
                    "type": param_type
                }
            }

            # either $ref or in-line parameters
            if constants.IN_LINE_REFERENCES:
                new_params.append(self.params_dict[param_name])
            else:
                new_params.extend([{constants.INTERNAL_REF: common.make_ref(constants.SPEC_PARAMETERS_PATH, param_name)}])

        return new_params

    def prompt_existing_parameters(self,
                                   parameter_type: str,
                                   operation_id: str,
                                   existing_parameters: list) -> list:
        """present a list of existing parameters and prompt for a selection to be used

        :param parameter_type: "query" or "path"
        :type parameter_type: str
        :param operation_id: used for prompt
        :type operation_id: str
        :param existing_parameters: list of existing parameters to prompt
        :type existing_parameters: list
        :return: dictionary of references to include with the path information
        :rtype: dict
        """

        if existing_parameters:
            selected_headers = common.prompt_input(f"({operation_id}) Identify any existing {parameter_type} parameters to include as a comma separated list.",
                                                    choices=existing_parameters,
                                                    multi_select=True,
                                                    required=False)
            if selected_headers:
                if constants.IN_LINE_REFERENCES:
                    selected_headers_refs = [self.params_dict[ref] for ref in selected_headers]
                else:
                    selected_headers_refs = [{ constants.INTERNAL_REF: common.make_ref(constants.SPEC_HEADERS_PATH, selected_header) } for selected_header in selected_headers]

                return selected_headers_refs

        return []
