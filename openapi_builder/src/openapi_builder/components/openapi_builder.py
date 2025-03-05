# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

import copy
import json
import os
import re
import sys
import traceback
import yaml

from argparse import Namespace
from openapi_schema_validator import validate
from jsonschema.exceptions import ValidationError
from typing import Union

from .info import Info
from .tags import Tags
from .externaldocs import ExternalDocs
from .paths import Paths
from .auth import Authentication
from .servers import Servers
from .headers import Headers
from .parameters import Parameters
from . import common
from . import constants

def save_to_spec(save_to: dict,
                 path_list: list,
                 value: Union[dict, list],
                 merge=True) -> Union[dict, None]:
    """build the spec file section by section based on the hierarchy within the openapi spec file

    :param save_to: document where the openapi information is saved
    :type save_to: dict
    :param path_list: list of the hierarchy to have save the openapi spec info (value)
    :type path_list: list
    :param key: path key within the path_list for the data
    :type key: Union[str, None]
    :param value: openapi data to save
    :type value: Union[dict, list]
    :param merge: if data is already present at this path and key, merge the data. defaults to True
    :type merge: bool, optional
    :return: specification document changed
    :rtype: Union[dict, None]
    """
    if not value:
        return save_to

    nav_spec = save_to
    for path in path_list:
        if path not in nav_spec:
            nav_spec[path] = {}
        prev_spec = nav_spec
        nav_spec = nav_spec[path]

    if isinstance(nav_spec, list) and isinstance(value, list) and merge:
        nav_spec.extend(value)
    elif isinstance(nav_spec, dict) and isinstance(value, dict) and merge:
        nav_spec.update(value)
    else:
        prev_spec[path] = value

    return save_to

def save_to_file(spec: dict, file_name: str, confirm_overwrite=True) -> None:
    """Write the specification file to the specified location and file name

    :param spec: openapi spec file to save
    :type spec: dict
    :param file_name: full path of file to save
    :type file_name: str
    """
    continue_write = True
    if os.path.isfile(file_name) and confirm_overwrite:
        answer = common.prompt_input(f"file {file_name} already exists. Overwrite?",
                                    choices=[constants.CHOICE_YES, constants.CHOICE_NO])
        continue_write = bool(answer == constants.CHOICE_YES)

    if continue_write:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(json.dumps(spec, indent=4))

def validate_spec(doc: dict, validate_spec_version: str=constants.VALIDATE_OPENAPI_VERSION) -> bool:
    """validate a spec to make sure it conforms to correct openapi syntax. Error messages
        are displayed if validation fails.

    :param doc: json openapi spec
    :type doc: dict
    :param validate_spec_version: different spec version to validate against, defaults to VALIDATE_OPENAPI_VERSION
    :type validate_spec_version: str, optional
    :return: True if validation was successful
    :rtype: bool
    """
    cwd = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(cwd, constants.DATA_FOLDER, constants.OPENAPI_SPEC_3_0), "r", encoding="utf-8") as f:
        spec = f.read()

    validate_doc = copy.deepcopy(doc)
    validate_doc[constants.SPEC_OPENAPI] = validate_spec_version
    try:
        spec_json = json.loads(spec)
    except json.decoder.JSONDecodeError as err:
        common.print_error(f"Unable to convert the specification to json: {str(err)}")
        spec_json = None

    # change the doc version for validation purposes
    try:
        validate(validate_doc, spec_json) # confirm doc conforms to OpenAPI spec format
        return True
    except ValidationError as err:
        common.print_error(f"Specification file validation failed: {str(err)}")
        return False

def validate_openapi(spec: dict) -> bool:
    """ confirm that this is an openapi formatted document """
    if not spec.get(constants.SPEC_OPENAPI):
        return False

    return bool(re.findall(r"3.[01].[0-9]+", spec.get(constants.SPEC_OPENAPI)))


class OpenAPIBuilder():
    def __init__(self, args: Namespace):
        super().__init__()
        self.spec = {}
        self.spec_file_name = {}

        # argument parser
        self.args = args

    def start(self, version):
        """main function to collect all the openapi information and generate the spec file.
            data can come from cmd line prompts and user input plus an existing spec file which has
            already been started. If a spec file is specified, then existing paths are skipped.
        """
        info = servers = headers = auth = paths = None
        openapi_version = self.args.version
        interrupted = False
        try:
            if self.args.file:
                existing_file = self.args.file
                while not os.path.isfile(existing_file):
                    existing_file = common.prompt_input(f"File '{existing_file}' does not exist. Reenter.")

                self.spec = self.init_spec_from_file(existing_file)
                self.spec_file_name = existing_file

                if not validate_openapi(self.spec):
                    common.print_error(f"Specification file {self.spec_file_name} does not conform to OpenAPI 3.0.X or 3.1.X format. Exiting.")
                    sys.exit()

            init_bundle = (self.args.soar, self.args.terse, self.spec)
            info = Info(*init_bundle)
            tags = Tags(*init_bundle)
            external_docs = ExternalDocs(*init_bundle)
            auth = Authentication(*init_bundle)
            servers = Servers(*init_bundle)
            headers = Headers(*init_bundle)
            parameters = Parameters(*init_bundle)
            paths = Paths(*init_bundle)

            prompts = [f"Welcome to the {constants.TOOL_NAME} ({version})."]
            if not self.args.terse:
                prompts.append( "A series of prompts will guide you through the process of creating a simple OpenAPI spec.")
            if self.args.soar:
                prompts.append("Import the resulting document for use in playbooks using IBM SOAR's low-code connector capability.")

            common.multiline_output(prompts,
                                    prefix=None)

            # start prompts
            info.start(["The following set of prompts define the OpenAPI spec document."])

            external_docs.start(["Reference the API documentation used in this specification document."])

            tag_intro = ["Tags are used for grouping URL Paths and is indented as a UI organizing feature." ]
            if self.args.soar:
                tag_intro.append("IBM QRadar SOAR presently does not use tags in the UI.")

            tags.start(tag_intro)

            servers.start(["The next section prompts for the base URL(s) of the server.",
                           "Additional sections will prompt for the API endpoint paths."])

            auth.start()

            headers.start(["Define any HTTP headers used throughout this spec. They will be referenced later when the API endpoints are defined.",
                           "Headers 'Content-Type' and 'Authentication' headers are referred to elsewhere."])

            paths.prep(auth, servers, headers, parameters, tags)
            paths.start(["Let's define the API endpoints. Each endpoint will be a portion of the URL appended to the server URL.",
                        "Additional information collected will include the API call method and any API input parameters."])
        except (Exception, KeyboardInterrupt) as err:
            if not isinstance(err, KeyboardInterrupt):
                print(traceback.format_exc())
            # can't save anything if haven't started building the document
            if not info:
                sys.exit()

            save_results = common.prompt_input("\nData input has been interrupted. Do you want to save the input so far or exit without saving?",
                                                choices=[constants.CHOICE_YES, constants.CHOICE_EXIT],
                                                default=constants.CHOICE_YES)
            if save_results == constants.CHOICE_EXIT:
                sys.exit()

            # continue
            interrupted = True

        spec = self.build_spec(openapi_version,
                               info,
                               external_docs,
                               auth,
                               servers,
                               headers,
                               parameters,
                               paths,
                               tags)

        common.multiline_output(["Spec generation complete."])

        # confirm that we built a valid spec
        if not interrupted:
            is_valid = validate_spec(spec)

            if is_valid:
                validation_msg = "Document validation complete."
            else:
                validation_msg = "Document validation failed. Continued use may not succeed."

            common.multiline_output([validation_msg])

        file_name = f"{info.name.replace(' ', '_')}_openapi_spec_{info.version}.json"

        while True:
            prompt_result = common.prompt_input(["Save the spec to a file or display on screen."],
                                                choices=[f"file: {file_name}", "specify new file path and name", "screen", "exit"])
            if prompt_result == "exit":
                return

            if prompt_result == "screen":
                print(json.dumps(spec, indent=4))
            else:
                break

        if file_name not in prompt_result:
            file_name = common.prompt_input("Specify new file path and name")

        save_to_file(spec, os.path.expanduser(file_name))
        common.multiline_output([f"'{file_name}' file saved."], prefix=None)

        common.multiline_output([f"{constants.TOOL_NAME} is complete."], prefix=None)

    def init_spec_from_file(self, file: str) -> Union[dict, None]:
        """read contents of a file and validate that it's in openapi spec format

        :param file: path to openapi spec file
        :type file: str
        :return: converted spec file into dictionary format
        :rtype: dict or None if cannot convert to a dictionary
        """

        with open(file, "r", encoding="utf-8") as f:
            spec_file = f.read()

        try:
            spec_file_json = json.loads(spec_file)
        except json.decoder.JSONDecodeError as err:
            # maybe in yaml file format
            try:
                spec_file_json = yaml.safe_load(spec_file)
            except Exception:
                common.print_error(f"Unable to convert file: {spec_file} to json: {str(err)}")
                return None

        # validate the file to make sure we have a validate file to start
        validate_spec(spec_file_json)

        return spec_file_json

    def build_spec(self,
                   openapi_version: str,
                   info: Info,
                   external_docs: ExternalDocs,
                   auth: Authentication,
                   servers: Servers,
                   headers: Headers,
                   parameters: Parameters,
                   paths: Paths,
                   tags: Tags) -> dict:
        """give all the data collected, format into an openAPI spec file

        :param openapi_version: version of openAPI spec file
        :type openapi_version: str
        :param info: object with descriptive fields (title, description, etc.)
        :type info: Info
        :param info: object with external documentation
        :type info: ExternalDocs
        :param auth: object with authentication data
        :type auth: Auth
        :param servers: object with servers data
        :type servers: Servers
        :param headers: object with headers data
        :type headers: Headers
        :param parameters: object with parameters data
        :type parameters: Parameters
        :param paths: object with path data
        :type paths: Paths
        :return: assembled openAPI spec doc
        :rtype: dict
        """

        save_to_spec(self.spec, constants.SPEC_OPENAPI_PATH, openapi_version)
        save_to_spec(self.spec, constants.SPEC_INFO_PATH, info.export_section() if info else {})
        save_to_spec(self.spec, constants.SPEC_EXTERNAL_DOCS_PATH, external_docs.export_section() if external_docs else {})
        save_to_spec(self.spec, constants.SPEC_SERVERS_PATH, servers.export_section() if servers else [], merge=False)
        save_to_spec(self.spec, constants.SPEC_HEADERS_PATH, headers.export_section())
        save_to_spec(self.spec, constants.SPEC_PARAMETERS_PATH, parameters.export_section())
        save_to_spec(self.spec, constants.SPEC_PATHS_PATH, paths.export_section() if paths else {})
        save_to_spec(self.spec, constants.SPEC_TAGS_PATH, tags.export_section() if tags else {}, merge=False)

        path_schemas = paths.export_schemas() if paths else None
        if path_schemas:
            save_to_spec(self.spec, constants.SPEC_SCHEMAS_PATH, path_schemas)
        result = save_to_spec(self.spec, constants.SPEC_SECURITY_SCHEMES_PATH, auth.export_section() if auth else {})

        return result
