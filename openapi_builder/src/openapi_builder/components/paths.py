# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

import copy
import json
import re

from typing import Union, Tuple
from urllib.parse import urlparse, ParseResult
from xmltodict import parse as xmlparse
from xml.parsers.expat import ExpatError

from jsonschema_to_openapi.convert import convert
from json2schema import json2schema

from . import constants
from . import common
from .auth import Authentication
from .interfaces import SpecificationSection
from .servers import Servers
from .headers import Headers
from .parameters import Parameters
from .tags import Tags

class Paths(SpecificationSection):
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict = None):
        super().__init__(is_soar,
                         is_terse,
                         constants.SPEC_PATHS_PATH,
                         spec_default={},
                         spec=spec
                         )
        self.is_soar = is_soar
        self.is_terse = is_terse
        self._schemas = common.navigate_dict(spec, constants.SPEC_SCHEMAS_PATH)

    def export_schemas(self):
        """export the path schemas to be used in the openapi spec file. This data
            is retained in a different section from the paths sections

        :return: schema section of the openapi spec document
        :rtype: dict
        """
        return self._schemas

    def prep(self,
             auth: Authentication,
             servers: Servers,
             headers: Headers,
             parameters: Parameters,
             tags: Tags) -> None:
        """ initialize other classes needed for a path """

        self.auth = auth
        self.servers = servers
        self.headers = headers
        self.parameters = parameters
        self.tags = tags

    # override from SpecificationSection
    def display_existing_section(self) -> list:
        """ build the list of existing paths which include the methods used.
            Ex. /query_incidents (get, put, post) 
        """
        display_paths = []
        for key, methods in self.section.items():
            all_methods = methods.keys()
            all_methods = list(set(all_methods) & set(constants.VALID_API_CALL_METHODS))
            display_paths.append(f"{key} ({' | '.join(all_methods)})")
        return display_paths

    # implementation from SpecificationSection
    def prompt_section(self):
        """prompt the user for additional endpoint paths to be added to the openapi spec file.
        """

        while True:
            path_schemas, path = self._get_path(common.make_another(self.section, default="an "))
            if not path:
                if not self.section:
                    common.print_error("At least one path is required.")
                else:
                    break
            else:
                # merge the new paths with the existing paths, mindful of paths to overwrite
                endpoint = list(path.keys())[0]
                endpoint_method = list(path.values())[0]
                # duplicate?
                if endpoint in self.section:
                    endpoint_method_key = list(endpoint_method.keys())[0] # get, put, etc.
                    # remove case in comparison
                    if endpoint_method_key in [key.upper() for key in self.section[endpoint]]:
                        for key in self.section[endpoint]:
                            if key.upper() == endpoint_method_key:
                                del self.section[endpoint][key]
                                break

                        # add back the method
                        self.section[endpoint][endpoint_method_key] = list(endpoint_method.values())[0]
                    else:
                        self.update_section(endpoint, {**self.section[endpoint], **endpoint_method})
                else:
                    self.update_section(endpoint, endpoint_method)

                # merge the new schema with the existing schemas
                for schema_key, schema in path_schemas.items():
                    self._schemas[schema_key] = schema

    def _get_path(self,
                  another: str) -> Tuple[Union[dict, None], Union[dict, None]]:
        """collect all the information for one path. A path can contain:
            - uri information
            - HTTP method
            - headers used
            - path parameters
            - query parameters
            - output schemas
            - example output data

        :param another: label for prompting
        :type another: str
        :param headers: any headers collected
        :type headers: Headers
        :param authentication: the authentication information
        :type authentication: Auth
        :param servers: any server(s) collected
        :type servers: Servers
        :param parameters: any query and path parameters(s) collected
        :type servers: Parameters
        :return: schema and path information
        :rtype: Tuple[Union[dict, None], Union[dict, None]]
        """
        prompt = [f"* Enter {another}API endpoint path starting with '/'."]
        if not self.is_terse:
            prompt += ["Include any query parameters if present. Prompts will follow to enter additional query parameters separately."]
        uri = common.prompt_input(prompt,
                                  example="/threats/{threatId}?deep=true",
                                  required=False)
        if not uri:
            return None, None

        # all paths must start with '/'
        if uri[0] != "/":
            uri = f"/{uri}"

        parsed_uri: ParseResult = urlparse(uri)

        path_server = None
        if len(self.servers.section) > 1:
            # chose server
            path_server = common.prompt_input("More than one server URL is specified. Choose this path server.",
                                              choices=self.servers.display_existing_section())

        description = common.prompt_input("Enter a description helpful to understand the functionality of this API call.",
                                          default="",
                                          required=False)

        api_method = common.prompt_input("Enter the HTTP method.", choices=constants.API_CALL_METHODS)
        api_method = api_method.lower() # OpenAPI spec uses lower case methods

        # determine if this combination of uri and api_method already exists
        if self.section.get(uri, {}).get(api_method):
            prompt_result = common.prompt_input(f"This endpoint already exists: {uri} ({api_method}). Continue to overwrite?",
                                                choices=[constants.CHOICE_YES, constants.CHOICE_NO], required=True)
            if prompt_result == constants.CHOICE_NO:
                return None, None

        operation_id = common.make_operation_id(parsed_uri.path, api_method)
        prompt = "Enter the API call label."
        if not self.is_terse:
            prompt = " ".join([prompt,
                               "This will be the connector name."
                               "It must be unique."])

        operation_id = common.prompt_input(prompt,
                                           default=operation_id,
                                           example="get computers")

        tag_list = []
        if self.tags.display_existing_section():
            tag_list = auth_choice = common.prompt_input("Identify any optional tags to apply to this path as a comma separated list.",
                                                         multi_select=True,
                                                         choices=self.tags.display_existing_section(),
                                                         required=False)

        # get authentication
        auth_types: list = self.auth.display_existing_section()
        auth_choice = []
        if auth_types:
            auth_types.append("None")
            auth_choice = common.prompt_input("Which authentication should be used?",
                                              choices=auth_types)
            # if format "<label> (<location>)", only use <label>
            auth_choice = [] if auth_choice == "None" else auth_choice.split(" ")[0]

        parameter_list = []
        # path parameters
        parameter_list.extend(self.get_path_parameters(parsed_uri.path, operation_id))
        # query parameters on the path uri
        query_names, query_parameters = self.parameters.parse_query_parameters(parsed_uri.query, operation_id)
        parameter_list.extend(query_parameters)

        # additional query parameters
        parameter_list.extend(self.parameters.prompt_parameters("query",
                                                                parsed_uri.path,
                                                                operation_id,
                                                                query_names))

        if self.headers.export_section():
            parameter_list.extend(self.headers.prompt_existing_headers(operation_id))

        request_body = request_body_required = None
        if api_method != constants.API_CALL_METHOD_GET.lower():
            request_body_required, request_body = self.get_request_body(operation_id)

        # collect the path responses as examples or schemas
        responses = PathResponses(self.is_soar, self.is_terse)
        responses.prompt_responses(operation_id)

        response_schemas, path_responses = responses.export_section()

        result = {
            parsed_uri.path: {
                api_method: {
                    "operationId": operation_id,
                    "description": description,
                    "parameters": parameter_list,
                    "responses": path_responses,
                    "security": [],
                    "tags": tag_list
                }
            }
        }

        # identify the authentication method to use
        if auth_choice:
            result[parsed_uri.path][api_method]["security"] = [
                {
                    auth_choice: []
                }
            ]

        if path_server:
            result[parsed_uri.path][api_method]["servers"] = [{
                "url": path_server
            }]

        if request_body:
            result[parsed_uri.path][api_method]["requestBody"] = {
                "required": request_body_required,
                "content": request_body
            }

        return response_schemas, result

    def get_path_parameters(self, uri: str, operation_id: str) -> list:
        """The input path may contain path parameters. Parse them out and prompt for
            valid type format

        :param uri: uri of path
        :type uri: str
        :param operation_id: label derived or prompted for this endpoint
        :type operation_id: str
        :return: list of path parameters
        :rtype: list
        """
        params = []
        matches = re.findall(constants.PATH_PARAMS_REXEG, uri) # look for '{}' variable names
        for match in matches:
            param_type = common.prompt_input(f"({operation_id}): Found the path parameter: '{match}'. Enter parameter type.", choices=constants.VALUE_TYPES)
            params.append({
                "in": "path",
                "name": match,
                "required": True,
                "schema": {
                "type": param_type
                }
            })

        return params

    def get_request_body(self, operation_id: str) -> Tuple[str, dict]:
        """collect the request body data for an endpoint path

        :param operation_id: label derived or prompted for this endpoint
        :type operation_id: str
        :return: required flag and request body
        :rtype: Tuple[str, dict]
        """
        required = None
        request_body_content = {}

        prompt = ["Request Body"]
        if not self.is_terse:
            prompt += ["Many API calls allow for request body data, such as json-encoded API parameters.",
                       "The following prompts will guide you through request data specification."]

        common.multiline_output(prompt)

        # multiple request bodies are possible
        request_body_list = common.prompt_input(f"({operation_id}) Enter the request body content types supported as comma separated list.",
                                                choices=constants.CONTENT_TYPES,
                                                multi_select=True,
                                                required=False)

        if request_body_list and not isinstance(request_body_list, list):
            request_body_list = [request_body_list]

        if request_body_list:
            required = common.prompt_input([f"({operation_id}) Is the request body data required?"], choices=constants.API_PARAMETER_REQUIRED)

            # visit all content types for schema information
            for content_type in request_body_list:
                if content_type == constants.CONTENT_TYPE_SPECIFY:
                    content_type = common.prompt_input(f"({operation_id}) Enter a new response content media format.")

                request_schema, _request_example = get_schema(f"{operation_id}", True, content_type)

                request_body_content[content_type] = {
                    "schema": request_schema
                }

        return required, request_body_content

class PathResponses():
    def __init__(self, is_soar: bool, is_terse: bool):
        self.is_sour = is_soar
        self.is_terse = is_terse
        self._schemas = {}
        self.responses = {}

    def export_section(self) -> Tuple[dict, dict]:
        """export the parts of path comprising the schema and/or response sample data

        :return: _description_
        :rtype: Tuple[dict, dict]
        """
        return (self._schemas, self.responses)

    def prompt_responses(self, operation_id: str) -> None:
        """collect different responses for a give path endpoint. These responses will
            be either undefined, a schema or a sample response. The schema is used to validate the response data.

        :param operation_id: label for the endpoint, used in the SOAR connector
        :type operation_id: str
        """
        prompt = ["Responses"]
        if not self.is_terse:
            prompt += ["API calls have different expected responses based on the API call's status code, such as '200'.",
                       "The following prompts will guide you through response data specification.",
                       "At least one response needs to be specified."]
        common.multiline_output(prompt)

        required = True
        while True:
            response_example = None
            another = common.make_another(self.responses, default="a ")
            response_code = common.prompt_input(f"* ({operation_id}) Enter {another}response code. Specify a range as: 2XX.",
                                                example="200",
                                                required=required)

            if not response_code:
                break

            # make upper case: 2xx -> 2XX
            response_code = response_code.upper()

            if not validate_response_code(response_code):
                common.print_error(f"Response code is invalid: {response_code}. Please reenter.")
                continue

            # create a derived operation_id used to reference within the openapi spec
            response_operation_id = f"{operation_id.replace(' ', '_')}_{response_code}"

            response_description = common.prompt_input(f"({operation_id}) Enter description for response '{response_code}'",
                                                        default='OK' if response_code[0] == "2" else None,
                                                        required=True)


            # this is the minimum response
            self.responses[response_code] = {
                "description": response_description
            }

            prompt_header = f"{operation_id}:{response_code}"

            # json, xml, etc. data formats
            response_content_format = common.prompt_input(f"({prompt_header}) Enter the response content media format.",
                                                          default=constants.CONTENT_TYPE_APPLICATION_JSON,
                                                          choices=constants.CONTENT_TYPES)

            if response_content_format == constants.CONTENT_TYPE_SPECIFY:
                response_content_format = common.prompt_input(f"({prompt_header}) Enter a new response content media format.")

            # undefined responses are empty definitions
            if response_content_format != constants.CONTENT_TYPE_UNDEFINED:
                response_content_openapi_schema, response_example = get_schema(prompt_header, False, response_content_format)

                # save the schema in openAPI format
                if response_content_openapi_schema:
                    self._schemas[response_operation_id] = response_content_openapi_schema

                    response_data = {
                            "schema": {
                                constants.INTERNAL_REF: common.make_ref(constants.SPEC_SCHEMAS_PATH, response_operation_id)
                            }
                        }

                    if response_example:
                        response_data["example"] = response_example

                    self.responses[response_code]["content"] = {
                        response_content_format: response_data
                    }

            required = False

def validate_response_code(response_code: str) -> bool:
    """ Ensure that the response code is validate, such as 200 or 2XX"""
    # must be 3 characters starting with a number
    if len(response_code) != 3 or not response_code[0].isdigit():
        return False
    # Assisted by watsonx Code Assistant :
    for char in response_code:
        if not (char.isdigit() or char == 'X'):
            return False
    return True


def get_schema(prompt_header: str, request: bool, content_type: str=None) -> Tuple[dict, Union[dict, None]]:
    request_response = "request" if request else "response"
    if content_type == constants.CONTENT_TYPE_APPLICATION_JSON:
        choices = [constants.RESPONSE_FORMAT_JSON, constants.RESPONSE_FORMAT_SCHEMA, constants.NONE_TYPE]
        default = constants.RESPONSE_FORMAT_JSON
    elif content_type == constants.CONTENT_TYPE_APPLICATION_XML:
        choices = [constants.RESPONSE_FORMAT_XML, constants.RESPONSE_FORMAT_SCHEMA, constants.NONE_TYPE]
        default = constants.RESPONSE_FORMAT_XML
    else:
        choices = [constants.NONE_TYPE, constants.RESPONSE_FORMAT_JSON, constants.RESPONSE_FORMAT_XML, constants.RESPONSE_FORMAT_SCHEMA]
        default = constants.NONE_TYPE

    while True:
        response_content = common.prompt_input(f"({prompt_header}:{content_type}) Is there formatted example or schema data for the {request_response}?",
                                                choices=choices,
                                                default=default)

        if response_content == constants.RESPONSE_FORMAT_JSON:
            try:
                response_content = json_loads(f"({prompt_header}) Paste the JSON formatted example {request_response} or specify a file path. End with Return/Enter.")
                return convert_example_to_schema(response_content)

            except json.decoder.JSONDecodeError as err:
                common.print_error(f"Unable to convert example to JSON. Try again: {str(err)}")
                continue

        elif response_content == constants.RESPONSE_FORMAT_SCHEMA:
            response_content = common.prompt_input(f"({prompt_header}) Paste the JSON formatted schema {request_response} or specify a file path. {constants.END_WITH_EMPTY_LINE}",
                                            multiline=True)
            try:
                response_content_schema = json_loads(response_content)

                return convert(response_content_schema), None
            except json.decoder.JSONDecodeError as err:
                common.print_error(f"Unable to convert schema to JSON. Try again: {str(err)}")
                continue
        elif response_content == constants.RESPONSE_FORMAT_XML:
            response_content = xml_loads(f"({prompt_header}) Paste the XML formatted example {request_response} or specify a file path. End with Return/Enter.")
            return convert_example_to_schema(response_content)
        elif response_content != constants.NONE_TYPE:
            return (get_undefined_schema(), None)
        else:
            return ({}, None)

def json_loads(prompt) -> dict:
    """load string encoded data as a dictionary from either a literal or a file path.
       Errors to convert data to a dictionary will reprompt for data entry.

    :param prompt: prompt to present for data input
    :type prompt: str
    :return: converted json
    :rtype: dict
    """
    while True:
        sample_content = common.prompt_input(prompt, multiline=True)
        try:
            if sample_content.strip().startswith("{"):
                return json.loads(sample_content)

            with open(sample_content, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.decoder.JSONDecodeError as e:
            common.print_error(f"Unable to convert string to JSON. Try again: {str(e)}")
        except FileNotFoundError as ee:
            common.print_error(f"File {sample_content} not found. Try again: {str(ee)}")

def xml_loads(prompt: str) -> dict:
    """convert xml format to a dictionary for schema generation.
      Errors to convert the data to a dictionary will re-prompt for the data.

    :param prompt: prompt for the string encoded XML data (literal or file path)
    :type prompt: str
    :return: XML data converted as a dictionary
    :rtype: dict
    """
    while True:
        sample_content = common.prompt_input(prompt, multiline=True)
        try:
            if sample_content.strip().startswith("<"):
                return xmlparse(sample_content)

            with open(sample_content, "r", encoding="utf-8") as f:
                return xmlparse(f.read())
        except ExpatError as e:
            common.print_error(f"Unable to convert XML to JSON. Try again: {str(e)}")

def convert_example_to_schema(response_content: dict) -> dict:
    """ Convert example data already in dictionary format in openapi schema
        The raw schema data is 'corrected' so it can be imported into SOAR.

    :param response_content: data to convert
    :type response_content: dict
    :return: schema representation of data
    :rtype: dict
    """
    # convert example json to schema
    response_content_schema = json2schema(response_content, required_all=False)
    response_content_schema = fix_sample(response_content_schema)

    # convert json schema to openAPI schema
    response_content_openapi_schema = convert(response_content_schema)
    return correct_schema(response_content_openapi_schema), response_content


def correct_schema(schema: dict) -> dict:
    """schema data for SOAR's validation needs to be 'fixed' in order to be imported

    :param schema: schema of response data
    :type schema: dict
    :return: corrected schema
    :rtype: dict
    """
    schema_copy = copy.deepcopy(schema)
    for key, value in schema.items():
        if key == "type" and value == "array" and not schema.get("items"):
            # if items is empty, it will untyped. For now, we will indicate that it's an object
            schema_copy["items"] = {
                "type": constants.OBJECT_TYPE
            }
        elif key == "items" and isinstance(value, list):
            schema_copy[key] = correct_schema(value[0])
        elif isinstance(value, dict):
            schema_copy[key] = correct_schema(schema_copy[key])
        elif key == "additionalProperties":
            del schema_copy[key]

    return schema_copy

def fix_sample(response_content_schema: dict, default_type="string") -> dict:
    """common method to take a json example file for a given response and ensure it has correct data.
        for instance, null response need to be converted to some primitive value (default is 'string')

    :param response_content_schema: schema of example json response
    :type response_content_schema: dict
    :return: _description_
    :rtype: dict
    """

    for key, value in response_content_schema.items():
        if key == "type" and (value in (None, "null")):
            response_content_schema[key] = default_type
        elif isinstance(value, dict):
            response_content_schema[key] = fix_sample(value) # recursive walk the hierarchy
        elif isinstance(value, list):
            list_results = []
            for item in value:
                list_results.append(fix_sample(item)) # recursive walk the list ent

            response_content_schema[key] = list_results

    return response_content_schema

def get_undefined_schema():
    """ This is needed when the schema is no defined in order to have some schema definition """
    return {
        "nullable": False,
        "type": "object"
    }
