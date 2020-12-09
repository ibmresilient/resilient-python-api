# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use
import resilient
import copy
from resilient_circuits.app import AppArgumentParser
from resilient_lib.components.resilient_common import str_to_bool
import logging

LOG = logging.getLogger(__name__)

TYPES_URL = "/types"
ORGANIZATION_TYPE = "organization"

LAYOUT_FOR_TYPE_QUERY = "/layouts?type={}"
LAYOUT_FOR = "/layouts/{}"


INCIDENT_TABS_NAME = "incident"
UI_LOCK = "ui_lock"


def get_organization_layout(client, layout_name):
    # first get a type ID for layout UI
    types = client.get(TYPES_URL)
    if ORGANIZATION_TYPE not in types:
        LOG.debug(types)
        raise KeyError("Can't find '{}' in the list of types.".format(ORGANIZATION_TYPE))

    organization = types[ORGANIZATION_TYPE]
    organization_type_id = organization["type_id"]
    # for organization extract UI layouts
    incident_layout = client.get(LAYOUT_FOR_TYPE_QUERY.format(organization_type_id))
    incident_tabs = [layout for layout in incident_layout if layout['name'] == layout_name]

    if not incident_tabs:
        raise ValueError("No UI tabs are received from the platform for {} layout.".format(layout_name))
    elif len(incident_tabs) != 1:
        raise ValueError("Expected 1 tab for {} layout, {} were returned".format(layout_name, len(incident_tabs)))

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

def add_missing_fields(og_layout, tab):
    """
    Adds missing fields to the layout.
    """
    layout = copy.deepcopy(og_layout)
    missing_fields = tab.get_missing_fields(layout.get("content"))
    if not missing_fields:
        return og_layout
    tab_data = tab.get_from_tabs(layout.get("content"))
    tab_data['fields'].extend(missing_fields)
    return layout

def add_missing_conditions(og_layout, tab):
    """
    Adds missing conditions. Removes value = None from all existing condition, because that's what
    the UI does.
    """
    layout = copy.deepcopy(og_layout)
    tab_data = tab.get_from_tabs(layout.get("content"))
    # remove null values from conditions
    if tab_data.get('show_if'):
        for condition in tab_data.get('show_if'):
            if condition.get('value') is None:
                condition.pop('value')

    missing_conditions = tab.get_missing_conditions(layout.get("content"))
    if not missing_conditions:
        return layout  # still return updated one since we deleted nulls
    if not tab_data.get('show_if'):
        tab_data['show_if'] = []
    tab_data.get('show_if').extend(missing_conditions)
    return layout
    
def update_tab(client, layout, tab):
    """
    Needs to get the tab and add missing fields and conditions to it.
    """
    layout = copy.deepcopy(layout)
    layout = add_missing_fields(layout, tab)
    layout = add_missing_conditions(layout, tab)
    return client.put(LAYOUT_FOR.format(layout['id']), payload=layout)


def permission_to_edit(tab, opts):
    """
    Gets the config and determines if the UI had been locked or is allowed to be edited.
    :param tab: class or instance that's a subclass of ui.Tab
    :return: If app.config locks the tab or not
    """
    if opts.get(tab.SECTION):
        section_lock = str_to_bool(opts.get(tab.SECTION).get(UI_LOCK))
        return not section_lock
    if opts.get('integrations'):
        integrations_lock = str_to_bool(opts.get('integrations').get(UI_LOCK))
        return not integrations_lock
    if opts.get('resilient'):
        global_lock = str_to_bool(opts.get('resilient').get(UI_LOCK))
        return not global_lock

    return True


def create_tab(tab, update_existing=False):
    """
    If allowed by app.config - creates or updates a tab in the UI according to the
    specification passed in the class.
    Can be forbidden to make changes by adding `ui_lock=<true/on>` in app.config under integration section,
    resilient, or "integrations".

    :param tab: Subclass of ui.Tab that has required parameters and describes the required layout.
    :param update_existing: Defines the behavior if tab is already present in the system.
    Either simply leave it alone, or go through required elements and add those that are missing.
    """
    try:
        opts = _get_opts()
        if not permission_to_edit(tab, opts):
            LOG.info("No permission to edit UI for {}".format(tab.SECTION))
            return
        client = resilient.get_client(opts)
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
    except Exception as e:
        LOG.error("Failed to create/update tab in the UI for {}".format(tab.SECTION))
        LOG.error(str(e))


def _get_opts():
    """
    Gets options from AppArgumentParser in the same manner as circuits does.
    """
    return AppArgumentParser().parse_args()
