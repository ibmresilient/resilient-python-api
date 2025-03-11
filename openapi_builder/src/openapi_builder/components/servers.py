# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from urllib.parse import urlparse

from . import common
from .interfaces import SpecificationSection

class Servers(SpecificationSection):
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict = None):
        super().__init__(is_soar,
                         is_terse,
                         ["servers"],
                         spec_default=[],
                         spec=spec)

    # override of SpecificationSection
    def display_existing_section(self) -> list[str]:
        return [server.get("url") for server in self.section]

    def prompt_section(self) -> None:
        """Prompt for the server URL(s) used by the paths in this OpenAPI spec document.
            Basic url conventions must be used
        """
        new_servers = []

        while True:
            another = common.make_another(new_servers + self.section, default="a ")
            servers = common.prompt_input(f"* Enter {another}server URL. Multiple servers may be entered, separated by commas.",
                                         example="https://myserver.com/api/v1",
                                         required=False)
            if not servers:
                if not new_servers and not self.section:
                    common.print_error("Define at least one server URL.")
                else:
                    break
            else:
                server_list = common.separate_multiple(servers)
                for server in server_list:
                    parsed_server = urlparse(server)
                    if not parsed_server.scheme or not parsed_server.hostname:
                        common.print_error(f"Rejecting {server}. Format the URL such as https://myserver.com")
                    else:
                        new_servers.append(server)

        self.update_section([{"url": serv} for serv in new_servers])
