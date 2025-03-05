# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from . import constants
from . import common
from .interfaces import SpecificationSection

class Headers(SpecificationSection):
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict = None):
        super().__init__(
                         is_soar,
                         is_terse,
                         constants.SPEC_HEADERS_PATH,
                         spec_default={},
                         spec=spec)

    def prompt_section(self) -> None:
        """Collect the headers used by this OpenAPI doc.
            Headers have a name, and a type value (str, int, etc.)
        """

        while True:
            another = common.make_another(self.section)
            header_name = common.prompt_input(f"* Enter {another}header.",
                                        example="X-Requests-Id",
                                        required=False)
            if not header_name:
                break

            header_description = common.prompt_input(f"({header_name}) Enter a description which would help understand the use of this header.",
                                                     required=False)

            header_type = common.prompt_input(f"({header_name}) Enter header type.",
                                                choices=constants.VALUE_TYPES)

            while True:
                try:
                    header_default = common.prompt_input(f"({header_name}) Enter header default value.",
                                                         required=False)

                    header_default = common.convert_value(header_type, header_default)
                    break
                except Exception:
                    common.print_error(f"Default value is invalid for type: '{header_type}'. Reenter.")

            self.update_section(header_name,
                                {
                                    "in": "header",
                                    "name": header_name,
                                    "description": header_description,
                                    "schema": {
                                        "type": header_type,
                                        "default": header_default
                                    }
                                })

    def prompt_existing_headers(self, operation_id: str) -> list:
        """present a list of existing headers and prompt for a selection to be used

        :return: dictionary of references to include with the path information
        :rtype: dict
        """
        all_headers = list(self.section)

        if all_headers:
            selected_headers = common.prompt_input(f"({operation_id}) Identify any headers to include as a comma separated list.",
                                                    choices=all_headers,
                                                    multi_select=True,
                                                    required=False)
            if selected_headers:
                # two different ways to handle parameters: by $ref or in-line
                if constants.IN_LINE_REFERENCES:
                    selected_headers_refs = [self.section[ref] for ref in selected_headers]
                else:
                    selected_headers_refs = [{ constants.INTERNAL_REF: common.make_ref(constants.SPEC_HEADERS_PATH, selected_header) } for selected_header in selected_headers]

                return selected_headers_refs

        return []
