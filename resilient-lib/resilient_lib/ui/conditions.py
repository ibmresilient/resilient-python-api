# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2024. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

"""
Enables conditions to be used with different UI elements in the Tab definition.
In a way like:

class TestTab(Tab):
    ...
    SHOW_IF = [
        Field('qradar_id').conditions.has_value(),
        Field('desription').conditions.contains('ATP')
    ]
"""

from resilient_lib import IntegrationError

class Conditions(object):
    def __init__(self, api_name):
        self.api_name = api_name


class FieldConditions(Conditions):
    def _get_value_for_select_field(self, value):
        """
        base helper method which allows subclasses to change the
        behavior of condition method which require lookups for
        values (i.e. select fields need to look up value type-ids)

        :param value: display name to condition on
        :type value: str
        :return: API reference to use when constructing the condition
                 (usually just the value, though some cases require references to other values)
        :rtype: str
        """
        return value

    def equals(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "equals",
            "value": self._get_value_for_select_field(value)
        }

    def doesnt_equal(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_equals",
            "value": self._get_value_for_select_field(value)
        }

    def contains(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "contains",
            "value": self._get_value_for_select_field(value)
        }

    def doesnt_contain(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_contains",
            "value": self._get_value_for_select_field(value)
        }

    def has_value(self):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "has_a_value"
        }

    def doesnt_have_value(self):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_has_a_value"
        }

class SelectFieldCondition(FieldConditions):
    def __init__(self, api_name, res_client):
        super(SelectFieldCondition, self).__init__(api_name)
        self.client = res_client

    def _get_value_for_select_field(self, value):
        """
        Override default value selector to select the value
        rather than label for select fields.

        This allows us to construct conditions like:
            SelectField("my_select").conditions.contains("a")
        which translates to
            {
              "field": "incident.my_select",
              "condition": "equals",
              "value": 101
            }

        :param value: value label to find
        :type value: str
        :raises IntegrationError: if value label doesn't exist for select field
        :return: value's value in the backend reference (an id, usually a low number)
        :rtype: str
        """
        inc_types = self.client.cached_get("/types/incident")
        for value_mapping in inc_types.get("fields", {}).get(self.api_name, {}).get("values", {}):
            if value_mapping.get("label") == value:
                return str(value_mapping.get("value"))
        raise IntegrationError("Couldn't find value '{0}' for select field '{1}'".format(value, self.api_name))

    def has_one_of(self, values):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "in",
            "value": [self._get_value_for_select_field(value) for value in values]
        }

    def doesnt_have_one_of(self, values):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_in",
            "value": [self._get_value_for_select_field(value) for value in values]
        }

    def contains(self, value):
        """This doesn't apply to select fields so override FieldCondition to raise error"""
        raise IntegrationError("Cannot use 'contains' condition for select field")

    def doesnt_contain(self, value):
        """This doesn't apply to select fields so override FieldCondition to raise error"""
        raise IntegrationError("Cannot use 'doesnt_contain' condition for select field")
