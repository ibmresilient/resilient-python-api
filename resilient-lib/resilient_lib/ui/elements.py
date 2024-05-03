# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2024. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

from resilient import get_client
from resilient_lib import clean_html

from .conditions import Conditions, FieldConditions, SelectFieldCondition


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


class SelectField(Field):

    def __init__(self, api_name, opts):
        super(SelectField, self).__init__(api_name)
        res_client = get_client(opts)
        self.conditions = SelectFieldCondition(api_name=api_name, res_client=res_client)


class Datatable(UIElementBase):
    ELEMENT_TYPE = "datatable"

    def as_dto(self):
        return {
            "element": self.ELEMENT_TYPE,
            "content": self.api_name
        }

class View(UIElementBase):
    ELEMENT_TYPE = "view"

    def as_dto(self):
        return {
            "element": self.ELEMENT_TYPE,
            "content": self.api_name
        }

class Header(UIElementBase):
    ELEMENT_TYPE = "header"

    def __init__(self, content, show_link_header=False):
        """
        Headers aren't api_name based, they're "content" based.
        So we use the super class to use its validations but we overwrite
        the Conditions and add a ``content`` variable

        :param content: header content to display
        :param show_link_header: boolean to enable "show link header" in UI for header element; defaults to False
        :type content: str
        """
        super(Header, self).__init__(content)
        self.content = content
        self.show_link_header = show_link_header if show_link_header else False
        self.conditions = Conditions(self.content)

    def as_dto(self):
        return {
            "element": self.ELEMENT_TYPE,
            "content": self.content,
            "show_link_header": self.show_link_header
        }

class HTMLBlock(UIElementBase):
    ELEMENT_TYPE = "html"

    def __init__(self, content):
        """
        HTML blocks aren't api_name based, they're "content" based.
        So we use the super class to use its validations but we overwrite
        the Conditions and add a ``content`` variable

        :param content: HTML content to display
        :type content: str
        """
        super(HTMLBlock, self).__init__(content)
        self.content = content
        self.conditions = Conditions(self.content)

    def as_dto(self):
        return {
            "element": self.ELEMENT_TYPE,
            "content": self.content
        }

    def exists_in(self, fields):
        """
        HTML needs to implement custom logic here because HTML tags
        might need to be cleaned to compare developer input vs
        server-cleaned HTML responses
        """
        return next((field for field in fields
                    if field["element"] == self.ELEMENT_TYPE and clean_html(field["content"]) == clean_html(self.api_name)
                    ), None) is not None

class Section(UIElementBase):
    """
    This class behaves like a UIElementBase in that it can
    live in the ``CONTAINS`` section of the Tab class,
    but under the hood it doesn't work much like other UIElementBase's.

    Adding it to a Tab or using it to update a Summary will create a new
    section object in the layout

    Example Tab which contains a Section:

    .. code-block::python

        class MyTestTab(Tab):
            SECTION = "fn_test"
            NAME = "Test Tab"
            UUID = "b27793a5-7a40-407f-a8a6-ab0376875813"

            CONTAINS = [
                HTMLBlock("<h3>HTML header</h3><br><br><p>New Paragraph with <b>bold text</b>"),
                Section(
                    element_list=[
                        Field("creator_id"),
                        Field("city"),
                        Datatable("test_dt"),
                        View("Co3.Views.IncidentsComments")
                    ],
                    show_if=[
                        Field("incident_type_ids").conditions.has_value()
                    ]
                ),
                Field("creator_id")
            ]

            SHOW_IF = [
                SelectField("my_select").conditions.has_one_of(["a", "b"])
            ]

    """
    ELEMENT_TYPE = "section"

    def __init__(self, element_list, show_if=None, show_link_header=False):
        """
        We call super init to validate required fields but otherwise we
        implement all our own methods.

        :param element_list: list of fields, datatables, etc.. to include in the section
        :type element_list: list[UIElementBase]
        :param show_if: list of condition DTOs, defaults to None (i.e. show always)
        :type show_if: list[dict], optional
        :param show_link_header: boolean to enable "show link header" in UI for header element; defaults to False
        :type show_link_header: bool, optional
        """
        super(Section, self).__init__(None)
        self.fields = element_list if element_list else []
        self.show_if = show_if if show_if else []
        self.show_link_header = show_link_header if show_link_header else False

        assert isinstance(self.fields, list), "'element_list' must be a list"
        assert isinstance(self.show_if, list), "'show_if' must be a list"
        assert all([element.ELEMENT_TYPE != self.ELEMENT_TYPE for element in self.fields]), "Cannot create nested Sections"

    def as_dto(self):
        return {
            "element": self.ELEMENT_TYPE,
            "fields": [element.as_dto() for element in self.fields] if self.fields else [],
            "show_if": self.show_if,
            "show_link_header": self.show_link_header
        }

    def exists_in(self, fields):
        """
        Given a list of fields of a tab, find if this section (exactly!) already exists.
        """
        full_matches = []
        # have to do a naive search through the "sections" objects of the server layout
        server_side_sections_list = [field for field in fields
                    if field["element"] == self.ELEMENT_TYPE]
        if not server_side_sections_list:
            return False # short circuit return False if there are no Section objects in the layout on the server

        # for each section from the server
        for section in server_side_sections_list:
            # see if there is a full match of this Section object to the section from the server
            full_match = all([field.exists_in(section.get("fields")) for field in self.fields])
            full_matches.append(full_match)

        # if any of the above were full matches, then this Section exists
        return any(full_matches)
