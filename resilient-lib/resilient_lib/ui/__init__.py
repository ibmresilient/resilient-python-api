"""
How do we want to use this?

Sublass the tab and add the dependencies?
class QRadarTab(UITab):
	UUID = "abcdefg"
	name = "QRadar Tab"

	FIELDS = [
		UIField("api_name"),
		UITable("api_name")
	]

	CONDITIONS = []
"""
from .common import get_incident_tabs, create_tab_if_doesnt_exist
from .tab import Tab
from .elements import Datatable
