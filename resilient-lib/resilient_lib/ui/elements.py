UI_DATATABLE_ELEMENT = "datatable"


class Datatable(object):
	def __init__(self, api_name):
		self.api_name = api_name

	def as_dto(self):
		return {
			"step_label": None,
			"show_if": None,
			"element": UI_DATATABLE_ELEMENT,
			"field_type": None,
			"content": self.api_name,
			"show_link_header": False
		}


