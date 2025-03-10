# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from .interfaces import SpecificationSection
from . import constants
from . import common

class Authentication(SpecificationSection):
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict=None) -> None:
        super().__init__(is_soar,
                         is_terse,
                         ["components", "securitySchemes"],
                         spec_default={},
                         spec=spec)

    def get_auth_info(self, auth_type: str) -> dict:
        """ return information about a given authentication type, or if not found,
            return any empty dictionary """
        return self.section.get(auth_type, {})

    def prompt_section(self) -> None:
        """prompt the user for the authentication type(s) used in the API call
            Note: At this point, only one authentication type is coded.
        """
        # common.multiline_output(["Authentication"])
        # if self._auth_dict:
        #     self.display_auth_types()

        while True:
            another = common.make_another(self.section, default="the ")

            auth_choice = common.prompt_input([f"* Define {another}authentication method used."],
                                               choices=[constants.CHOICE_BASICAUTH,
                                                        constants.CHOICE_BEARER,
                                                        constants.CHOICE_API_TOKEN],
                                               required=False)

            if not auth_choice:
                return

            auth, security_info = constants.SECURITY_TYPES[auth_choice]
            if auth_choice == constants.CHOICE_API_TOKEN:
                location = common.prompt_input(["Define the location of the API key."],
                                    choices=[constants.API_KEY_HEADER, constants.API_KEY_QUERY],
                                    default=constants.API_KEY_HEADER)

                security_header = common.prompt_input([f"Define the {location} setting that will contain the API key."], example="X-API-Key")
                security_info["name"] = security_header
                security_info["in"] = location

            # make sure if an existing authentication exists, version it
            version = 2
            while auth in self.section:
                auth = f"{auth}{version}"
                version += 1

            self.update_section(auth, security_info)

    def display_existing_section(self) -> list:
        """ Return information about the authentication types. Since different
            schemes present different information, each needs to be handled differently.
            Note: OAuth is not yet supported.
        """
        existing_auths = []
        for auth_type, auth_info in self.section.items():
            auth = auth_type
            if auth_info["type"].lower() == "http":
                if "bearerFormat" in auth_info:
                    auth = f"{auth} ({auth_info['scheme']}:{auth_info['bearerFormat']})"
                else:
                    auth = f"{auth} ({auth_info['scheme']})"
            else:
                auth = f"{auth} ({auth_info['type']})"
            existing_auths.append(auth)

        return  existing_auths
