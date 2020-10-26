from .common import get_incident_tabs

TABS_LABEL = "step_label"

UI_TAB_ELEMENT = "tab"
UI_TAB_FIELD_TYPE = "incident"

class Tab(object):
	UUID = None
	NAME = None

	CONTAINS = None

	def __init__(self):
		assert self.UUID, "UUID isn't defined for the tab"
		assert self.NAME, "Name needs to be defined for the tab"

	@classmethod
	def exists(cls, client):
		"""
		Check if the tab exists in Resilient
		"""
		return cls.tab_exists_in(get_incident_tabs(client))

	@classmethod
	def exists_in(cls, tabs):
		"""
		Checks if the tab exists in the list of tabs.
		"""
		return len([x for x in tabs if x.get("predefined_uuid") == cls.UUID or x.get(TABS_LABEL) == cls.NAME]) == 1

	@classmethod
	def as_dto(cls):
		return {
			"step_label": cls.NAME,
			"fields": [field.as_dto() for field in cls.CONTAINS] if cls.CONTAINS else [],
			"show_if": [],
			"element": UI_TAB_ELEMENT,
			"field_type": UI_TAB_FIELD_TYPE,
			"predefined_uuid": cls.UUID,
			"show_link_header": False
		}