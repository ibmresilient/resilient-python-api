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
class Conditions(object):
    def __init__(self, api_name):
        self.api_name = api_name


class FieldConditions(Conditions):
    def has_value(self):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "has_a_value"
        }

    def equals(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "equals",
            "value": value
        }

    def contains(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "contains",
            "value": value
        }

    def doesnt_contain(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_contains",
            "value": value
        }

    def doesnt_equal(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_equals",
            "value": value
        }

    def doesnt_have_value(self, value):
        return {
            "field": "incident.{}".format(self.api_name),
            "condition": "not_has_a_value"
        }
