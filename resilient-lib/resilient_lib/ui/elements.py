# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use
from .conditions import Conditions, FieldConditions


class UIElementBase(object):
    ELEMENT_TYPE = None

    def __init__(self, api_name):
        assert self.ELEMENT_TYPE, "Element type for subclass needs to be defined"
        self.api_name = api_name
        self.conditions = Conditions(self.api_name)

    def as_dto(self):
        """
        Returns a JSON serializable dictionary with DTO representing the field in the tab.
        """
        raise NotImplementedError("DTO represenation for {} is not implemented".format(self.__class__))

    def exists_in(self, fields):
        """
        Given a list of fields of a tab, find if current one is one of them.
        """
        return next((field for field in fields
                    if field["element"] == self.ELEMENT_TYPE and field["content"] == self.api_name), None) is not None


class Field(UIElementBase):
    ELEMENT_TYPE = "field"

    def __init__(self, api_name):
        super(Field, self).__init__(api_name)
        self.conditions = FieldConditions(api_name)

    def as_dto(self):
        return {
            "content": self.api_name,
            "element": self.ELEMENT_TYPE,
            "field_type": "incident"
        }


class Datatable(UIElementBase):
    ELEMENT_TYPE = "datatable"

    def as_dto(self):
        return {
            "element": self.ELEMENT_TYPE,
            "content": self.api_name
        }
