# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2024. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import copy
import logging

from resilient_lib.components.resilient_common import str_to_bool

import resilient

LOG = logging.getLogger(__name__)

TYPES_URL = "/types"
ORGANIZATION_TYPE = "organization"

LAYOUT_FOR_TYPE_QUERY = "/layouts?type={}"
LAYOUT_FOR = "/layouts/{}"
SUMMARY_LAYOUT_ID = 8


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

    return get_layout(client, organization_type_id, layout_name)

def get_layout(client, type_id, layout_name):
    # for organization extract UI layouts
    object_layout = client.get(LAYOUT_FOR_TYPE_QUERY.format(type_id))
    layout = [layout for layout in object_layout if layout['name'] == layout_name]

    if not layout:
        raise ValueError("No UI tabs are received from the platform for {} layout.".format(layout_name))
    elif len(layout) != 1:
        raise ValueError("Expected 1 tab for {} layout, {} were returned".format(layout_name, len(layout)))

    return layout[0]


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


def add_components_to_summary(client, components_to_add, summary_layout, header_of_block_to_add_after=None):
    """
    Given a list of components, add them to the Summary Section.

    Only adds components which aren't already in the summary
    (NOTE: if a component exists in the summary but is in being added in
    a Section element, it will be added)

    Optional ``header_of_block_to_add_after`` (ex: "Summary" or "Newsfeed")
    gives you the option to insert your components after the given block's
    name. If that header is not found, adds to the end
    NOTE: ``header_of_block_to_add_after`` only works with "header" elements,
    not "section" elements

    :param client: SOAR rest client
    :type client: co3.SimpleClient
    :param components_to_add: list of UI elements to add
    :type components_to_add: list[UIElementBase]
    :param summary_layout: current summary layout to modify
    :type summary_layout: LayoutDTO
    :param header_of_block_to_add_after: string name of section after which to insert new components, defaults to "Summary"
    :type header_of_block_to_add_after: str, optional
    :return: response from PUT
    :rtype: request.Response
    """
    summary_layout = copy.deepcopy(summary_layout)
    summary_fields = summary_layout.get("content")
    new_components = [component.as_dto() for component in components_to_add if not component.exists_in(summary_fields)]

    if header_of_block_to_add_after:
        try:
            # try to find the index where to insert the new components
            found_i = _find_index_of_end_of_header_block(summary_fields, header_of_block_to_add_after)
            summary_layout["content"] = summary_layout["content"][:found_i] + new_components + summary_layout["content"][found_i:]
        except Exception:
            # generic Exception; if anything goes wrong at all we just want to add to the end of the summary
            summary_layout["content"].extend(new_components)
    else:
        summary_layout["content"].extend(new_components)

    return client.put(LAYOUT_FOR.format(summary_layout["id"]), payload=summary_layout)

def _find_index_of_end_of_header_block(summary_fields, header_block_name):
    """
    Find index where to insert new block, given current ```summary_fields```
    and ```header_block_name``` which defines the block after which to insert.
    If ``header_block_name`` not found, return len(summary_fields) (i.e.
    insert at the end)

    :param summary_fields: list of current summary fields objects
    :type summary_fields: list[dict]
    :param header_block_name: string title of the block to insert after (exact match)
    :type header_block_name: str
    :return: index of block after header given
    :rtype: int
    """
    # find index of
    found = False
    found_i = len(summary_fields)
    for i, field in enumerate(summary_fields):
        # get next header after desired header name is found
        if found and field.get("element") == "header":
            found_i = i
            break
        # if we've found the matching header, we start the actual search
        # since we need to find the index of the *next* header to find where to insert
        if field.get("element") == "header" and field.get("content") == header_block_name:
            found = True

    return found_i


def permission_to_edit(app_section_name, opts):
    """
    Gets the config and determines if the UI had been locked or is allowed to be edited.
    :param app_section_name: app's section name in the config
    :return: If app.config locks the tab or not
    """
    if opts.get(app_section_name):
        section_lock = str_to_bool(opts.get(app_section_name).get(UI_LOCK))
        return not section_lock
    if opts.get('integrations'):
        integrations_lock = str_to_bool(opts.get('integrations').get(UI_LOCK))
        return not integrations_lock
    if opts.get('resilient'):
        global_lock = str_to_bool(opts.get('resilient').get(UI_LOCK))
        return not global_lock

    return True


def create_tab(tab, opts, update_existing=False):
    """
    If allowed by app.config - creates or updates a tab in the UI according to the
    specification passed in the class.
    Can be forbidden to make changes by adding `ui_lock=<true/on>` in app.config under integration section,
    resilient, or "integrations".

    Example:

    .. code-block::python

        class MyTestTab(Tab):
            SECTION = "fn_test"
            NAME = "Test Tab"
            UUID = "b27793a5-7a40-407f-a8a6-ab0376875813"

            CONTAINS = [
                HTMLBlock("<h3>html block up top</h3><br><br><p>New Paragraph with <b>bold text</b>"),
                View("timer:list"),
                Field("addr"),
                Datatable("test_dt"),
                Section(
                    element_list=[
                        Field("creator_id"),
                        Field("city"),
                        Datatable("test_dt"),
                        View("Co3.Views.IncidentsComments")
                    ],
                    show_if=[
                        Field("incident_type_ids").conditions.equals([21])
                    ]
                ),
                Datatable("test_dt")
            ]

            SHOW_IF = [
                SelectField("my_select").conditions.has_one_of(["a", "b"])
            ]

        try:
            create_tab(MyTestTab, opts, update_existing=True)
            print("Tab created: %s", MyTestTab.NAME)
        except SystemExit as e:
            print("Failed to create tab: %s.\nERROR: %s", MyTestTab.NAME, e)

    :param tab: Subclass of ui.Tab that has required parameters and describes the required layout.
    :param update_existing: Defines the behavior if tab is already present in the system.
    Either simply leave it alone, or go through required elements and add those that are missing.
    """
    try:
        if not permission_to_edit(tab.SECTION, opts):
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

def update_summary_layout(opts, ui_components_to_add, header_of_block_to_add_after=None, app_name=None):
    """
    Add a list of UI components to the Summary Section of the UI customization.

    Optional ``header_of_block_to_add_after`` (ex: "Summary" or "Newsfeed")
    gives you the option to insert your components after the given block's name.
    NOTE: ``header_of_block_to_add_after`` only works with "header" elements,
    not "section" elements

    ``app_name`` is optional as well and is only used to check if permissions
    for UI editing have been disabled in the app's app.config. Best practice
    in a live app is to include this. But if using this for scripting you can
    omit.

    Example:

    .. code-block::python

        update_summary_layout(
            opts=opts,
            ui_components_to_add=[
                Section(
                    element_list=[Header("Summary"), HTMLBlock("<b>Parent Incident</b>"), Field("id")],
                    show_if=[Field("city").conditions.equals("test")]
                )
            ],
            header_of_block_to_add_after="Summary"
        )

    :param opts: app.config dict
    :type opts: dict|AppConfigManager
    :param ui_components_to_add: list of UIElementBase objs
    :type ui_components_to_add: list[UIElementBase]
    :param header_of_block_to_add_after: string name of section after which to insert new components, defaults to None which goes to the end
    :type header_of_block_to_add_after: str, optional
    :param app_name: app's name for its section in the app.config, defaults to None
    :type app_name: str, optional
    :return: REST response from PUT to summary section
    :rtype: requests.Response
    """
    try:
        if not permission_to_edit(app_name, opts):
            LOG.info("No permission to edit UI for {}".format(app_name))
            return

        client = resilient.get_client(opts)
        summary_layout = get_layout(client, SUMMARY_LAYOUT_ID, "incident.summary")

        return add_components_to_summary(client, ui_components_to_add, summary_layout, header_of_block_to_add_after=header_of_block_to_add_after)
    except Exception as e:
        LOG.error("Failed to create/update summary section in the UI")
        LOG.error(str(e))
