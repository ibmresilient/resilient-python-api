# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from . import common
from .interfaces import SpecificationSection

class Tags(SpecificationSection):
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 spec: dict = None):
        super().__init__(is_soar,
                         is_terse,
                         ["tags"],
                         spec_default=[],
                         spec=spec)

    # override of SpecificationSection
    def display_existing_section(self) -> list[str]:
        """ Return any existing tags """
        return [tag.get("name") for tag in self.section]

    def prompt_section(self) -> None:
        """Prompt for the tags used by the paths in this OpenAPI spec document.
            Basic url conventions must be used
        """
        new_tags = []

        while True:
            another = common.make_another(new_tags + self.section, default="a ")
            tags = common.prompt_input(f"* Enter {another}tag. Multiple tags may be entered, separated by commas.",
                                         required=False)

            if not tags:
                break

            new_tags.extend(common.separate_multiple(tags))

        self.update_section([{"name": tag} for tag in new_tags])
