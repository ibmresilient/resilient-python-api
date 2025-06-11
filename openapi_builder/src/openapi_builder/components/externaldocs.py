# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from . import common
from . import constants
from .interfaces import SpecificationSection

KEY_URL = "url"
KEY_DESCRIPTION = "description"

class ExternalDocs(SpecificationSection):
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict=None) -> None:
        super().__init__(is_soar,
                         is_terse,
                         constants.SPEC_EXTERNAL_DOCS_PATH,
                         spec_default={},
                         spec=spec)
        self._name = "External documentation"

    def prompt_section(self) -> None:
        """prompt the user for the authentication type(s) used in the API call
            Note: At this point, only one authentication type is coded.
        """
        url = desc = None
        url = common.prompt_input(["URL to API documentation."],
                                   default=self.section.get(KEY_URL),
                                   required=False)
        if url:
            desc = common.prompt_input(["Add any optional description."],
                                       default=self.section.get(KEY_DESCRIPTION),
                                       required=False)

        self.section[KEY_URL] = url
        if desc:
            self.section[KEY_DESCRIPTION] = desc

    # override from SpecificationSection
    def display_existing_section(self):
        return [f"{key}: {value}" for key, value in self.section.items()]
