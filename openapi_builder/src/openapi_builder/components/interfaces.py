# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from typing import Union, Tuple
from . import common

class SpecificationSection():
    def __init__(self,
                 is_soar: bool,
                 is_terse: bool,
                 path: list,
                 spec_default=None,
                 spec: dict=None
                 ) -> None:
        self._name = self.__class__.__name__
        self._path = path
        self.is_soar = is_soar
        self.is_terse = is_terse
        self._section = self.import_spec(spec, spec_default)

    @property
    def section(self):
        return self._section

    def update_section(self, *args) -> None:
        """ Add the items to the class data structure until it needs to be included in the
            completed json OpenAPI document.
        """
        if isinstance(self._section, list):
            if isinstance(args[0], list):
                self._section.extend(args[0])
            else:
                self._section.append(args[0])
        else:
            self._section[args[0]] = args[1]

    def import_spec(self, spec: dict, spec_default=Union[dict, list]) -> dict:
        """Navigate an openapi specification document, collecting only the section of data
           for this class

        :param spec: full specification document when editing an existing document
        :type spec: dict
        :return: section of data for this class
        :rtype: dict
        """
        spec_default = spec_default if spec_default is not None else {}

        if not spec:
            return spec_default

        nav_spec = spec if spec else {}
        for path in self._path:
            if path not in nav_spec:
                if path == self._path[-1]:
                    return spec_default
                nav_spec[path] = {}

            nav_spec = nav_spec.get(path)

        return nav_spec

    def start(self, intro: list=None, example: str=None) -> None:
        """ Add sections start with an introduction statement, any existing section items
            (for example, any existing headers) and then call the inheriting class's 
            prompt_section() method to collect all necessary data.

        :param intro: Any text to introduce this section, defaults to None
        :type intro: list, optional
        :param example: Any example text to help with data entry, defaults to None
        :type example: str, optional
        """
        prompt = [self._name]
        if not self.is_terse:
            prompt += intro if intro else []

        common.multiline_output(prompt, example=example)

        if self._section:
            self.display_section()

        self.prompt_section()

    def export_section(self) -> dict:
        """export the external docs to be used in the openapi spec file

        :return: external docs
        :rtype: dict
        """
        return self._section

    def prompt_section(self) -> None:
        """Implementation specific. This method is intended to prompt for new
            data to include
        """
        raise NotImplementedError()

    def display_section(self) -> None:
        """ General module to display the existing modules based on the section dictionary keys
            This module should be overridden by the inheriting class for specific data presentation.
        """
        common.multiline_output([f"Existing {self._name.lower()}"] +
                                 common.pad_existing(self.display_existing_section()),
                                 prefix=None)

    def display_existing_section(self) -> Tuple[dict, list]:
        """ return the section for additional processing, such as display. """
        return  self._section
