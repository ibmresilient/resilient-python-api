# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import base64
import datetime
import functools
import logging
import traceback
from ast import literal_eval
from threading import Event

from cachetools import LRUCache, cached
from resilient import Patch, SimpleHTTPException
from resilient_lib import (IntegrationError, clean_html, get_file_attachment,
                           get_file_attachment_name)
from six import raise_from

LOG = logging.getLogger(__name__)

TYPES_URI = "/types"
INCIDENTS_URI = "/incidents"
ARTIFACTS_URI = "/artifacts"
ARTIFACT_FILE_URI = "/".join([ARTIFACTS_URI, "files"])

DEFAULT_CASES_QUERY_FILTER = "return_level=normal"

# P O L L E R   L O G I C
def poller(named_poller_interval, named_last_poller_time):
    """
    Decorator to wrap a function as the logic for a poller.

    **Example:**

    .. code-block:: python

        import logging
        from threading import Thread

        from resilient_circuits import AppFunctionComponent, is_this_a_selftest
        from resilient_lib import poller, get_last_poller_date

        PACKAGE_NAME = "fn_my_app"

        LOG = logging.getLogger(__name__)

        class MyPoller(AppFunctionComponent):

            def __init__(self, opts):
                super(PollerComponent, self).__init__(opts, PACKAGE_NAME)

                polling_interval = 5 # set to 5 seconds or could get from ``self.options``
                last_poller_time = get_last_poller_date(120) # look back 2 hours

                if is_this_a_selftest(self):
                    LOG.warn("Running selftest -- disabling poller")
                else:
                    poller_thread = Thread(target=self.run)
                    poller_thread.daemon = True
                    poller_thread.start()

            @poller('polling_interval', 'last_poller_time')
            def run(self, *args, **kwargs):

                # poll endpoint
                query_results = query_entities_since_last_poll(kwargs['last_poller_time'])

                # process any results to create, update, or close case in SOAR
                if query_results:
                    self.process_entity_list(query_results)


    :param named_poller_interval: name of instance variable containing the poller interval in seconds
    :type named_poller_interval: str
    :param named_last_poller_time: name of instance variable containing the lookback value in mseconds
    :type named_last_poller_time: datetime
    """
    def poller_wrapper(func):
        # decorator for running a function forever, passing the ms timestamp of
        #  when the last poller run to the function it's calling
        @functools.wraps(func)
        def wrapped(self, *args):

            last_poller_time = getattr(self, named_last_poller_time)
            exit_event = Event()

            while not exit_event.is_set():
                try:
                    LOG.info("%s polling start.", self.PACKAGE_NAME)
                    poller_start = datetime.datetime.now()
                    # function execution with the last poller time in ms
                    func(self, *args, last_poller_time=int(last_poller_time.timestamp()*1000))

                except Exception as err:
                    LOG.error(str(err))
                    LOG.error(traceback.format_exc())
                finally:
                    LOG.info("%s polling complete.", self.PACKAGE_NAME)
                    # set the last poller time for next cycle
                    last_poller_time = poller_start

                    # sleep before the next poller execution
                    exit_event.wait(getattr(self, named_poller_interval))
            exit_event.set() # loop complete

        return wrapped
    return poller_wrapper

class SOARCommon():
    """
    Common methods for accessing IBM SOAR cases and their entities: comments, attachments, etc.
    This class and its methods should be used in conjunction with wrapped
    polling logic to communicated with the SOAR platform.
    """
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def _build_search_query(self, search_fields, open_cases=True):
        """[Build the json structure needed to search for cases]

        Args:
            search_fields ([dict/list]): [key/value pairs to search custom fields with specific values. If
                                         a value contains "*" then a search is used with 'has_a_value']
            NOTE: search_fields works on custom fields

        Returns:
            query_string ([dict]): [json stucture used for cases searching]
        """
        query = {
            "filters": [{
                "conditions": [
                 ]
            }],
            "sorts": [{
                "field_name": "create_date",
                "type": "desc"
            }]
        }

        if open_cases:
            field_search = {
                            "field_name": "plan_status",
                            "method": "equals",
                            "value": "A"
                          }
            query['filters'][0]['conditions'].append(field_search)

        if isinstance(search_fields, dict):
            for search_field, search_value in search_fields.items():
                field_search = {
                            "field_name": "properties.{0}".format(search_field)
                        }
                if isinstance(search_value, bool):
                    field_search['method'] = "has_a_value" if search_value else "does_not_have_a_value"
                else:
                    field_search['method'] = "equals"
                    field_search['value'] = search_value

                query['filters'][0]['conditions'].append(field_search)

        return query

    def _query_cases(self, query, filters=DEFAULT_CASES_QUERY_FILTER):
        """ run a query to find case(s) which match the query string
        Args:
            query [str]: query string to find cases
            filters [str]: Filters for the end of the uri
        Returns:
            query_results [list]: List of query results
        """
        query_uri = "/".join([INCIDENTS_URI, "query?{}".format(filters)])
        try:
            return self.rest_client.post(query_uri, query), None
        except SimpleHTTPException as err:
            LOG.error(str(err))
            LOG.error(query)
            return None, str(err)

    def _patch_case(self, case_id, case_payload):
        """
        _patch_case will update an case with the specified json payload.

        :param case_id: case ID of case to be updated.
        :param case_payload: case fields to be updated.
        :return:
        """
        try:
            # Update case
            case_url = "/".join([INCIDENTS_URI, str(case_id)])
            case = self.rest_client.get(case_url)
            patch = Patch(case)

            # Iterate over payload dict.
            for name, _ in case_payload.items():
                if name == 'properties':
                    for field_name, field_value in case_payload['properties'].items():
                        patch.add_value(field_name, field_value)
                else:
                    payload_value = case_payload.get(name)
                    patch.add_value(name, payload_value)

            patch_result = self.rest_client.patch(case_url, patch)
            result = self._chk_status(patch_result)
            # add back the case id
            result['id'] = case_id
            return result

        except Exception as err:
            LOG.error(str(err))
            raise_from(IntegrationError("_patch_case failed to update case in SOAR"), err)

    def _get_artifact_types(self):
        """ get all artifact types labels """
        return self._get_type("artifact", "type")

    def _get_incident_types(self):
        """ get all case_type_id labels """
        return self._get_type("incident", "incident_type_ids")

    def _get_resolution_types(self):
        """ get case resolution_types labels """
        return self._get_type("incident", "resolution_id")

    def _get_type(self, obj_type, lookup_field):
        """ get a specified SOAR field set of values, based on their ID (ex. status, incident_type_ids) """
        type_info = self._get_types(obj_type)

        # create a lookup table based on field name
        return { type['value']: type['label'] for type in type_info['fields'][lookup_field]['values'] }

    @cached(cache=LRUCache(maxsize=100))
    def _get_types(self, res_type):
        """ cached API call to get types information for a given type: case, artifact, etc. """
        uri = "/".join([TYPES_URI, res_type])
        return self.rest_client.get(uri)

    def _get_case_info(self, case_id, child_uri):
        """ API call for a given case and it's child objects: tasks, notes, attachments, etc. """
        try:
            uri = "/".join([INCIDENTS_URI, str(case_id)])
            if child_uri:
                uri = "/".join([uri, child_uri])

            response = self.rest_client.get(uri=uri)
            return response

        except Exception as err:
            raise_from(IntegrationError("failed to get case info from SOAR"), err)

    def _filter_comments(self, soar_comment_list, entity_comments, filter_soar_header=None):
        """
        Need to avoid creating same IBM SOAR case comments over and over
            this logic will read all SOAR comments from a case
            and remove those comments which have already sync using soar_header as a filter

        Args:
            soar_comment_list ([list]): [list of text portion of a case's comments]
            entity_comments ([list]): [list comments which the endpoint's entity contains.
                                       This will be a mix of comments sync'd from SOAR and new comments]
            filter_soar_header ([str]): [title added to SOAR comments to be filtered]
        Returns:
            new_comments ([list])
        """

        if filter_soar_header:
            # Filter entity comments with our SOAR header
            staged_entity_comments = [comment for comment in entity_comments \
                                        if clean_html(filter_soar_header) not in clean_html(comment)]
        else:
            staged_entity_comments = entity_comments.copy()

        # filter out the comments already sync'd to SOAR
        if soar_comment_list:
            already_synced = [clean_html(soar_comment) for soar_comment in soar_comment_list]
            new_entity_comments = [comment for comment in staged_entity_comments\
                if clean_html(comment) not in already_synced]
        else:
            new_entity_comments = staged_entity_comments

        return new_entity_comments

    def _chk_status(self, resp, rc=200):
        """
        Check the return status. If return code is not met, raise IntegrationError,
        if success, return the json payload

        :param resp: requests response object
        :param rc: acceptable status code or a list of two numbers indicating an acceptable range
        :type rc: int|[int, int]
        :return: json value of the resp object if call was successful
        """
        if hasattr(resp, "status_code"):
            if isinstance(rc, list):
                rc.sort()
                if resp.status_code < rc[0] or resp.status_code > rc[-1]:
                    raise IntegrationError("status code failure: {0}".format(resp.status_code))
            elif resp.status_code != rc:
                raise IntegrationError("status code failure: {0}".format(resp.status_code))

            return resp.json()

        return {}

    def get_soar_case(self, search_fields, open_cases=True, uri_filters=DEFAULT_CASES_QUERY_FILTER):
        """
        Find a SOAR case which contains custom field(s) associated with the associated endpoint.
        Returns only one case. See :class:`SOARCommon.get_soar_cases()` for examples.

        .. note::

            ``search_fields`` only supports custom fields.

        :param search_fields: Dictionary containing key/value pairs to search for a case match.
            Field values can be True/False for ``has_a_value`` or ``does_not_have_a_value``,
            otherwise a field will use ``equals`` for the value.
        :type search_fields: dict
        :param uri_filters: Filters for the end of the uri. Default is "return_level=normal"
        :type uri_filters: str
        :param open_cases: True if only querying open cases.
        :type open_cases: bool
        :return: A tuple with the matching case, if any, and any associated error message if something went wrong.
            Returns ``None`` if no associated case was found.
        :rtype: tuple(dict, str)
        """
        r_cases, error_msg = self.get_soar_cases(search_fields, open_cases=open_cases, uri_filters=uri_filters)
        if error_msg:
            return None, error_msg
        # return first case
        return (r_cases[0] if r_cases else None, None)

    def get_soar_cases(self, search_fields, open_cases=True, uri_filters=DEFAULT_CASES_QUERY_FILTER):
        """
        Get all IBM SOAR cases that match the given search fields.
        To find all cases that are synced from the endpoint platform,
        provide the unique search field that matches the unique id of your
        endpoint solution.

        **Example:**

        .. code-block:: python

            from resilient_lib import SOARCommon

            soar_common = SOARCommon(res_client)
            found_id = get_id_from_endpoint_query_result()
            cases = soar_common.get_soar_cases({ "endpoint_id": found_id }, open_cases=False)

        .. note::

            ``search_fields`` only supports custom fields.

        :param search_fields: Dictionary containing key/value pairs to search for a case match.
            Field values can be True/False for ``has_a_value`` or ``does_not_have_a_value``,
            otherwise a field will use ``equals`` for the value.
        :type search_fields: dict
        :param uri_filters: Filters for the end of the uri. Default is "return_level=normal"
        :type uri_filters: str
        :param open_cases: True if only querying open cases.
        :type open_cases: bool
        :return: A tuple with a list of cases whose values match the ``search_fields`` and any associated error message.
        :rtype: tuple(dict, str)
        """
        query = self._build_search_query(search_fields, open_cases=open_cases)
        return self._query_cases(query, filters=uri_filters)

    def create_soar_case(self, case_payload):
        """
        Create a new IBM SOAR case based on a payload formatted for the API call.

        :param case_payload: Fields to use for creating a SOAR case
        :type case_payload: dict

        :return: API result with the created case
        :rtype: dict
        """
        try:
            # Post case to IBM SOAR
            case = self.rest_client.post(INCIDENTS_URI, case_payload)
            return case
        except Exception as err:
            LOG.error(str(err))
            raise_from(IntegrationError("create_soar_case failed to create case in SOAR"), err)

    def update_soar_case(self, case_id, case_payload):
        """
        Update an IBM SOAR case (usually from a rendered Jinja template).

        :param case_payload: Fields to be updated and their values
        :type case_payload: dict
        :return: The updated SOAR case case
        :rtype: dict
        """
        try:
            result = self._patch_case(case_id, case_payload)
            return result

        except Exception as err:
            LOG.error(str(err))
            raise_from(IntegrationError("update_soar_case failed to update case in SOAR"), err)

    def update_soar_cases(self, payload):
        """
        Update mulitple IBM SOAR cases (usually from a rendered Jinja template).

        **Example:**

        .. code-block:: python

            payload = {
                "patches": {
                    "incidentID1": {
                        "changes": [
                            {
                                "field": {"name": "incident_field_name"},
                                "old_value": {"field_type": "current_value"},
                                "new_value": {"field_type": "new_value"}
                            },
                            {
                                "field": {"name": "incident_field_name"},
                                "old_value": {"id": 1},
                                "new_value": {"id": 2}
                            }
                        ],
                        "version": 12345 #Current version + 1
                    },
                    "2315": {
                        "changes": [
                            {
                                "field": {"name": "start_date"},
                                "old_value": {"date": None},
                                "new_value": {"date": 1681753245000}
                            },
                            {
                                "field": {"name": "zip"},
                                "old_value": {"text": None},
                                "new_value": {"text": "14294"}
                            }
                        ],
                        "version": 14
                    }
                }
            }

        :param payload: Dictionary that contains changes to make to SOAR cases
        :type payload: dict
        :return: Dictionary of failures if any occur
        :rtype: dict
        """
        try:
            result = self.rest_client.put("/incidents/patch", payload)
        except Exception as err:
            LOG.error(str(err))
            raise_from(IntegrationError("update_soar_cases failed to update cases in SOAR"), err)

        return result

    def create_case_comment(self, case_id, note, entity_comment_id=None, entity_comment_header=None):
        """
        Add a comment to the specified SOAR case by ID.

        :param case_id: SOAR case ID
        :type case_id: str|int
        :param note: Content to be added as a note to the case
        :type note: str
        :param entity_comment_id: (Optional) entity comment id if updating an existing comment
        :type entity_comment_id: str|int
        :param entity_comment_header: (Optional) header to place in bold at the top of the note
        :type entity_comment_header: str
        :return: Response from posting the comment to SOAR
        :rtype: dict
        """
        try:
            uri = "/".join([INCIDENTS_URI, str(case_id), "comments"])
            if entity_comment_header:
                comment = u"<b>{} ({}):</b><br>{}".format(entity_comment_header, entity_comment_id, note)
            else:
                comment = note

            note_json = {
                'format': 'html',
                'content': comment
            }
            payload = {'text': note_json}

            return self.rest_client.post(uri=uri, payload=payload)

        except Exception as err:
            LOG.error(str(err))
            raise_from(IntegrationError("failed to create comment in SOAR"), err)

    def create_datatable_row(self, case_id, datatable, rowdata):
        """
        Create a row in a SOAR datatable.
        ``rowdata`` should be formatted as a dictionary of
        column name and value pairs

        **Example:**

        .. code-block:: python

            from resilient_lib import SOARCommon

            soar_common = SOARCommon(res_client)

            case_id = get_case_id()
            rowdata = {"column_1_api_name": 1, "column_2_api_name": 2}

            soar_common.create_datatable_row(case_id, "my_dt", rowdata)

        :param case_id: case containing the datatable
        :type case_id: str|int
        :param datatable: API name of datatable
        :type datatable: str
        :param rowdata: columns and values to add
        :type rowdata: dict
        """
        uri = "/".join([INCIDENTS_URI, str(case_id), "table_data", datatable, "row_data"])


        formatted_cells = {}

        for column in rowdata:
            formatted_cells[column] = {"value": rowdata.get(column)}

        formatted_cells = {"cells": formatted_cells}

        return self.rest_client.post(uri=uri, payload=formatted_cells)

    def get_case(self, case_id):
        """
        Get a SOAR case based on the case id
        
        :param case_id: ID of the case to get the details of
        :type case_id: str|int
        :return: Details of the case for a given ID
        :rtype: dict
        """
        case = self._get_case_info(case_id, None)
        # create a new field of the incident_type_ids in label form
        case['case_types'] = self.lookup_incident_types(case['incident_type_ids'])
        return case

    def get_case_attachment(self, case_id, artifact_id=None, task_id=None, attachment_id=None, return_base64=True):
        """
        Get contents of a file attachment or artifact.

        * If ``incident_id`` and ``artifact_id`` are defined it will get that Artifact
        * If ``incident_id`` and ``attachment_id`` are defined it will get that Incident Attachment
        * If ``incident_id``, ``task_id`` and ``attachment_id`` are defined it will get that Task Attachment
        
        :param case_id: ID of the case to get the details of
        :type case_id: str|int
        :param artifact_id: ID of the Incident's Artifact to download
        :type artifact_id: str|int
        :param task_id: ID of the Task to download it's Attachment from
        :type task_id: str|int
        :param attachment_id: id of the Incident's Attachment to download
        :type attachment_id: int|str
        :param return_base64: if False, return value of the content will be given as bytes, default True returns a base64 encoded string
        :type return_base64: bool
        :return: name of the artifact or file and base64 encoded string or byte string of attachment
        :rtype: tuple(str, bytes|base64(str))
        """
        file_content = get_file_attachment(self.rest_client, case_id, artifact_id=artifact_id, task_id=task_id, attachment_id=attachment_id)
        if return_base64:
            file_content = b_to_s(base64.b64encode(file_content))

        file_name = get_file_attachment_name(self.rest_client, case_id, artifact_id=artifact_id, task_id=task_id, attachment_id=attachment_id)
        return file_name, file_content

    def get_case_artifacts(self, case_id):
        """
        Get all case artifacts

        :param case_id: ID of the case to get the details of
        :type case_id: str|int
        """
        return self._get_case_info(case_id, "artifacts")

    def get_case_comments(self, case_id):
        """
        Get all case comments 

        :param case_id: ID of the case to get the details of
        :type case_id: str|int
        """
        return self._get_case_info(case_id, "comments")

    def get_case_attachments(self, case_id, return_base64=True):
        """
        Get all case attachments
        
        :param case_id: ID of the case to get the details of
        :type case_id: str|int
        :param return_base64: if False, return value of the content will be given as bytes
        :type return_base64: bool
        :return: list of attachments associated with the given case
        :rtype: list[tuple(str, bytes|base64(str))]
        """
        attachments =  self._get_case_info(case_id, "attachments")
        for attachment in attachments:
            _, attachment['content'] = self.get_case_attachment(case_id, attachment_id=attachment['id'], return_base64=return_base64)

        return attachments

    def lookup_artifact_type(self, artifact_type):
        """
        Return an artifact type based on it's ID on SOAR. If not found, return None

        :param artifact_type: artifact type to search for in SOAR
        :type artifact_type: str
        :return: found artifact type if found in SOAR
        :rtype: str
        """
        try:
            types = self._get_artifact_types()
            if artifact_type in types:
                return types[artifact_type]
        except SimpleHTTPException:
            pass
        return None

    def lookup_incident_types(self, incident_type_ids):
        """
        Return an incident type based on it's ID. If not found, return None

        :param incident_type_ids: list of incident type IDs to check for in SOAR
        :type incident_type_ids: list(str)
        :return: list of incident types that match in SOAR what was given
        :rtype: list(str)
        """
        if not incident_type_ids:
            return incident_type_ids

        types = self._get_incident_types()

        return [types[incident_type] for incident_type in incident_type_ids if incident_type in types]

    def filter_soar_comments(self, case_id, entity_comments, soar_header=None):
        """
        Read all SOAR comments from a case and remove those comments which have
        already been synced using ``soar_header`` as a filter

        :param case_id: ([str]): [IBM SOAR case id]
        :type case_id: str|int
        :param entity_comments: list comments which the endpoint's entity contains.
            This will be a mix of comments sync'd from SOAR and new comments
        :type entity_comments: list(str)
        :param soar_header: title added to SOAR comments to be filtered
        :type soar_header: str
        :return: list of remaining comments
        :rtype: list
        """
        # get the SOAR case comments and capture only the text
        soar_comments = self.get_case_comments(str(case_id))
        soar_comment_list = [comment['text'] for comment in soar_comments]

        # filter entity comments with our SOAR header
        return self._filter_comments(soar_comment_list, entity_comments, filter_soar_header=soar_header)

    def get_case_tasks(self, case_id, want_layouts=False, want_notes=False, handle_format="names"):
        """
        Get all the tasks from a SOAR case

        :param case_id: IBM SOAR case id
        :type case_id: str|int
        :param want_layouts: If the task layout should be returned. Default is False.
        :type want_layouts: bool
        :param want_notes: If the task notes should be returned. Default is False.
        :type want_notes: bool
        :param handle_format: The format to return can be names, ids, or objects. Default is names.
        :type handle_format: str
        :return: A list of all the tasks for the given SOAR case
        :rtype: list
        """
        uri = "/incidents/{}/tasks?want_layouts={}&want_notes={}&handle_format={}".format(case_id, want_layouts, want_notes, handle_format)
        try:
            tasks = self.rest_client.get(uri=uri)
        except Exception as err:
            LOG.error(str(err))
            raise_from(IntegrationError("get_case_tasks failed to get SOAR case tasks"), err)

        return tasks

@cached(cache=LRUCache(maxsize=100))
def eval_mapping(eval_value, wrapper=None):
    """
    Map a JSON string to a python object. Safely evaluates the values with the use
    of ``ast.literal_eval`` and can ONLY convert to a list or a dictionary.

    .. note::

        ``wrapper`` is optional (but recommended) to ensure that the ``eval_value``
        is properly formatted as JSON. If ``None``, then assumes
        that the ``eval_value`` comes pre-formatted in acceptable JSON format

    This method is intended to be used to safely take input strings from the user's
    config file that will eventually need to evaluated as JSON elsewhere in the code.

    **Example:**

    .. code-block:: python

        from resilient_lib import eval_mapping

        config_value = app_configs.get("some_config")
        # Assume that 'config_value' has a value of
        # '"source":"A","tags":["tagA"],"priorities":[40,50]'

        # parse the values to a dict, using a dictionary wrapper:
        parsed_config = eval_mapping(config_value, "{{ {} }}")

        # the returned value is a dict like:
        # {
        #   "source": "A",
        #   "tags": ["tagA"],
        #   "priorities": [40, 50]
        # }

    :param eval_value: json fragment to evaluate
    :type eval_value: str
    :param wrapper: wrapper to put the source value into ``[{}]`` or ``{{ {} }}``
    :type wrapper: str
    :return: converted data
    :rtype: list|dict
    """
    if not eval_value:
        return None

    try:
        if wrapper:
            eval_value = wrapper.format(eval_value)

        # Try converting input to a dict or array
        result = literal_eval(eval_value)
        # expecting the result to be a list or dictionary
        if not isinstance(result, (list, dict)):
            raise IntegrationError("Unexpected result: %s", result)

        return result

    except Exception as err:
        LOG.error(str(err))
        LOG.error(traceback.format_exc())
        LOG.error("""mapping eval_value must be a string representation of a (partial) array or dictionary e.g. "'value1', 'value2'" or "'key':'value'" """)

    return None

def s_to_b(value):
    """ string to bytes """
    try:
        return bytes(value, 'utf-8')
    except Exception:
        return value

def b_to_s(value):
    """ bytes to string """
    try:
        return value.decode()
    except Exception:
        return value

def get_last_poller_date(polling_lookback):
    """
    Get the last poller datetime based on a lookback value
    Args:
        polling_lookback ([number]): # of minutes to lookback
    Returns:
        [datetime]: [datetime to use for last poller run time]
    """
    return _get_timestamp() - datetime.timedelta(minutes=polling_lookback)

def _get_timestamp():
    """
    Get the current timestamp

    Returns:
        datetime: current datetime
    """
    return datetime.datetime.now()
