import resilient
import copy
from resilient_circuits.app import AppArgumentParser
import logging

LOG = logging.getLogger(__name__)

TYPES_URL = "/types"
ORGANIZATION_TYPE = "organization"

LAYOUT_FOR_TYPE_QUERY = "/layouts?type={}"
LAYOUT_FOR = "/layouts/{}"


INCIDENT_TABS_NAME = "incident"


def get_organization_layout(client, layout_name):
	# first get a type ID for layout UI
	types = client.get(TYPES_URL)
	if ORGANIZATION_TYPE not in types:
		raise KeyError("Can't find 'organization' in the list of types.")

	organization = types[ORGANIZATION_TYPE]
	organization_type_id = organization["type_id"]
	# for organization extract UI layouts
	incident_layout = client.get(LAYOUT_FOR_TYPE_QUERY.format(organization_type_id))
	incident_tabs = [layout for layout in incident_layout if layout['name'] == layout_name]

	if not incident_tabs:
		raise ValueError("No UI tabs are accessible")
	elif len(incident_tabs) != 1:
		raise ValueError("Incorrect number of UI tabs supplied") 

	return incident_tabs[0]


def get_incident_layout(client):
	return get_organization_layout(client, INCIDENT_TABS_NAME)

def get_incident_tabs(client):
	"""
	Get a list of incident tabs exposed to user.
	:param client: Resilient client
	:returns: a tuple of layout id for incident UI and current list of UI tabs
	"""
	
	tab_data = get_incident_layout(client)
	return tab_data.get('content')


def add_tab_to_layout(client, layout, new_tab):
	layout = copy.deepcopy(layout)
	layout['content'].append(
		new_tab
	)
	return client.put(LAYOUT_FOR.format(layout['id']), payload=layout)

def update_tab(client, layout, tab):
	"""
	Needs to get the tab and add missing fields to it.
	"""
	layout = copy.deepcopy(layout)
	missing_fields = tab.get_missing_fields(layout.get("content"))
	print("missing fields")
	if not len(missing_fields):
		return None
	tab_data = tab.get_from_tabs(layout.get("content"))
	tab_data['fields'].extend(missing_fields)

	return client.put(LAYOUT_FOR.format(layout['id']), payload=layout)

def permission_to_edit(tab):
	"""
	Gets the config and determines if the UI had been locked or is allowed to be edited.
	:param tab: class or instance that's a subclass of ui.Tab
	:return: If app.config locks the tab or not
	"""
	config = resilient.get_config_file()
	opts = AppArgumentParser(config_file=config).parse_args()
	if opts.get(tab.SECTION) and opts.get(tab.SECTION).get('ui_lock'):
		return False
	if opts.get('integrations') and opts.get('integrations').get('ui_lock'):
		return False
	if opts.get('resilient', {}).get('ui_lock'):
		return False

	return True

def create_tab(tab, update_existing=False):
	if not permission_to_edit(tab):
		LOG.info("No permission to edit UI for {}".format(tab.SECTION))
		return
	client = get_resilient_client()
	layout = get_incident_layout(client)

	# check if tab already exists in the layout
	if tab.exists_in(layout.get("content")):
		if update_existing:
			LOG.info("UI tab for {} already exists. Checking for updates.".format(tab.SECTION))
			return update_tab(client, layout, tab)
		else:
			LOG.info("UI tab for {} already exists. Not updating.".format(tab.SECTION))
			return
	LOG.info("Creating a UI tab for {}".format(tab.SECTION))
	return add_tab_to_layout(client, layout, tab.as_dto())


def get_resilient_client():	
	config = resilient.get_config_file()
	args = AppArgumentParser(config_file=config)
	opts = args.parse_args()

	return resilient.get_client(opts)

