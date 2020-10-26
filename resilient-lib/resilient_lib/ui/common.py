import resilient
import copy


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
	print(layout)
	return client.put(LAYOUT_FOR.format(layout['id']), payload=layout)


def create_tab_if_doesnt_exist(tab):
	config = resilient.get_config_file()
	args = resilient.ArgumentParser(config)
	opts = args.parse_args()

	client = resilient.get_client(opts)

	layout = get_incident_layout(client)

	if tab.exists_in(layout.get("content")):
		return

	print(tab.as_dto())

	return add_tab_to_layout(client, layout, tab.as_dto())


