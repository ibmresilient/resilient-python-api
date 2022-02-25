# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2018. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import datetime
import io
import logging
import mimetypes
import os
import sys
import tempfile

import resilient
from bs4 import BeautifulSoup
from cachetools import TTLCache, cached
from six import string_types

INCIDENT_FRAGMENT = '#incidents'
PAYLOAD_VERSION = "1.0"

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())


def build_incident_url(url, incidentId):
    """
    Build the url to link to a SOAR incident

    :param url: the URL of your SOAR instance
    :type url: str
    :param incidentId: the id of the incident
    :type incidentId: str|int
    :return: full URL to the incident
    :rtype: str
    """
    return '/'.join([url, INCIDENT_FRAGMENT, str(incidentId)])


def build_resilient_url(host, port):
    """
    Build basic url to resilient instance

    :param host: host name
    :type host: str
    :param port: port
    :type port: str|int
    :return: base url
    :rtype: str
    """
    if host.lower().startswith("http"):
        return "{0}:{1}".format(host, port)

    return "https://{0}:{1}".format(host, port)


def clean_html(html_fragment):
    """
    Resilient textarea fields return html fragments. This routine will remove the
    html and insert any code within ``<div></div>`` with a linefeed

    .. note::
        The string returned from this method may not format well as no presentation of line feeds are preserved,
        tags such as ``<br>`` or ``<ol>``, ``<ul>``, etc. are removed. See :class:`.MarkdownParser` class for a better way to translate
        html input to markdown.

    :param html_fragment: the html to clean up
    :type html_fragment: str
    :return: cleaned up code
    :rtype: str
    """

    if not html_fragment or not isinstance(html_fragment, string_types):
        return html_fragment

    s = BeautifulSoup(unescape(html_fragment), "html.parser")

    return ' '.join(s.strings)


def unescape(data):
    """
    Return unescaped data such as:
        * ``&gt;`` converts to ``>``
        * ``&quot`` converts to ``'``

    :param data: text to convert
    :type data: str
    :return: the text unescaped
    :rtype: str
    """
    if data is None:
        return None

    if sys.version_info.major < 3:
        # In PY 2, unescape is part of HTMLParser
        from HTMLParser import HTMLParser
        h = HTMLParser()
        return h.unescape(data)

    else:
        # In PY 3, unescape is in html library
        import html

        return html.unescape(data)


def validate_fields(field_list, kwargs):
    """
    Ensure each mandatory field in ``field_list`` is present in ``kwargs``.
    Throw ValueError if not.

    ``field_list`` can be a list/tuple of ``strings`` where each string is
    a field name or it can be a list/tuple of ``dicts`` where each item
    has the attributes ``name`` (**required**) and ``placeholder`` (**optional**).

    ``kwargs`` can be a dict/namedtuple. If it is a namedtuple tries to call it's
    ``kwargs._as_dict()`` method and raises a ``ValueError`` if it cannot.

    * If the value of the item in ``kwargs`` is equal to its ``placeholder``
      defined in ``field_list``, a ``ValueError`` is raised.

    * If an item in ``kwargs`` is a *Resilient Select Function Input*, its
      value will be a ``dict`` that has a ``name`` attribute. This returns
      the value of ``name``.

    * If an item in ``kwargs`` is a *Resilient Multi-Select Function Input*, its
      value will be a list of ``dicts`` that have the ``name`` attribute. This
      returns a list of the ``name`` values for that item.

    :param field_list: the mandatory fields. *Can be an empty list if no mandatory fields.*
    :type field_list: list|tuple
    :param kwargs: dict or a namedtuple of all the fields to search.
    :type kwargs: dict|namedtuple
    :raises ValueError: if a field is missing
    :return: a Dictionary of all fields with Select/Multi-Select fields handled.
    :rtype: dict
    """

    mandatory_fields = field_list
    provided_fields = kwargs
    return_fields = {}
    mandatory_err_msg = "'{0}' is mandatory and is not set. You must set this value to run this function"

    # This is needed to handle something like: validate_fields(('incident_id'), kwargs)
    # In this case field_list will be a string and not a tuple
    if isinstance(mandatory_fields, string_types):
        mandatory_fields = [mandatory_fields]

    if not isinstance(mandatory_fields, list) and not isinstance(mandatory_fields, tuple):
        raise ValueError("'field_list' must be of type list/tuple, not {0}".format(type(mandatory_fields)))

    if not isinstance(provided_fields, dict):
        try:
            provided_fields = provided_fields._asdict()
        except AttributeError:
            raise ValueError("'kwargs' must be of type dict or namedtuple, not {0}".format(type(provided_fields)))

    # Validate that mandatory fields exist + are not equal to their placeholder values
    for field in mandatory_fields:

        placeholder_value = None

        if isinstance(field, dict):
            placeholder_value = field.get("placeholder")
            field = field.get("name")

        # If the field value is a defined empty str, raise an error
        if isinstance(provided_fields.get(field), string_types):
            if not provided_fields.get(field):
                raise ValueError(mandatory_err_msg.format(field))

        if provided_fields.get(field) is None:
            raise ValueError(mandatory_err_msg.format(field))

        if placeholder_value and provided_fields.get(field) == placeholder_value:
            raise ValueError(
                "'{0}' is mandatory and still has its placeholder value of '{1}'. You must set this value correctly to run this function".format(
                    field, placeholder_value))

    # Loop provided fields and get their value
    for field_name, field_value in provided_fields.items():

        # Handle if Select Function Input type
        if isinstance(field_value, dict) and field_value.get("name"):
            field_value = field_value.get("name")

        # Handle if 'Text with value string Input' type
        elif isinstance(field_value, dict) and field_value.get("content"):
            field_value = field_value.get("content")

        # Handle if Multi-Select Function Input type
        # There is a chance the list has already been "normalized", so just append as is
        elif isinstance(field_value, list):
            field_value = [f.get("name") if isinstance(f, dict) else f for f in field_value]

        return_fields[field_name] = field_value

    return return_fields


def get_file_attachment(res_client, incident_id, artifact_id=None, task_id=None, attachment_id=None):
    """
    Call the Resilient REST API to get the attachment or artifact data for
    an Incident or a Task

    * If ``incident_id`` and ``artifact_id`` are defined it will get that Artifact
    * If ``incident_id`` and ``attachment_id`` are defined it will get that Incident Attachment
    * If ``incident_id``, ``task_id`` and ``attachment_id`` are defined it will get that Task Attachment

    .. note::
        The ``artifact_id`` must reference an Artifact that is a downloadable type or it will
        raise a ``resilient.SimpleHTTPException``

    **Example:**

    .. code-block:: python

        artifact_data = get_file_attachment(self.rest_client(), incident_id=2001, artifact_id=1)

        with open("malware.eml", "wb") as f:
            f.write(artifact_data)

    :param res_client: required for communication back to resilient
    :type res_client: resilient_circuits.ResilientComponent.rest_client()
    :param incident_id: id of the Incident
    :type incident_id: int|str
    :param artifact_id: id of the Incident's Artifact to download
    :type artifact_id: int|str
    :param task_id: id of the Task to download it's Attachment from
    :type task_id: int|str
    :param attachment_id: id of the Incident's Attachment to download
    :type attachment_id: int|str
    :return: byte string of attachment
    :rtype: str
    """

    if incident_id and artifact_id:
        data_uri = "/incidents/{}/artifacts/{}/contents".format(incident_id, artifact_id)
    elif attachment_id:
        if task_id:
            data_uri = "/tasks/{}/attachments/{}/contents".format(task_id, attachment_id)
        elif incident_id:
            data_uri = "/incidents/{}/attachments/{}/contents".format(incident_id, attachment_id)
        else:
            raise ValueError("task_id or incident_id must be specified with attachment")
    else:
        raise ValueError("artifact or attachment or incident id must be specified")

    # Get the data
    return res_client.get_content(data_uri)


def get_file_attachment_metadata(res_client, incident_id, artifact_id=None, task_id=None, attachment_id=None):
    """
    Call the Resilient REST API to get the attachment or artifact attachment metadata

    :param res_client: required for communication back to resilient
    :type res_client: resilient_circuits.ResilientComponent.rest_client()
    :param incident_id: id of the Incident
    :type incident_id: int|str
    :param artifact_id: id of the Incident's Artifact
    :type artifact_id: int|str
    :param task_id: id of the Task to get it's Attachment metadata
    :type task_id: int|str
    :param attachment_id: id of the Incident's Attachment
    :type attachment_id: int|str
    :return: File metadata returned from endpoint
    :rtype: dict
    """

    if incident_id and artifact_id:
        metadata_url = "/incidents/{}/artifacts/{}".format(incident_id, artifact_id)
        return res_client.get(metadata_url)["attachment"]

    if attachment_id:
        if task_id:
            metadata_url = "/tasks/{}/attachments/{}".format(task_id, attachment_id)
        elif incident_id:
            metadata_url = "/incidents/{}/attachments/{}".format(incident_id, attachment_id)
        else:
            raise ValueError("If attachment_id is defined, you must specify task_id OR incident_id")

        return res_client.get(metadata_url)

    raise ValueError("artifact_id AND incident_id, OR attachment_id AND (task_id OR incident_id) must be specified")


def get_file_attachment_name(res_client, incident_id=None, artifact_id=None, task_id=None, attachment_id=None):
    """
    Call the Resilient REST API to get the attachment or artifact attachment name

    :param res_client: required for communication back to resilient
    :type res_client: resilient_circuits.ResilientComponent.rest_client()
    :param incident_id: id of the Incident
    :type incident_id: int|str
    :param task_id: id of the Task
    :type task_id: int|str
    :param attachment_id: id of the Incident's Attachment to get the name for
    :type attachment_id: int|str
    :return: name of the Attachment or Artifact
    :rtype: str
    """

    name = ""
    if incident_id and artifact_id:
        name_url = "/incidents/{}/artifacts/{}".format(incident_id, artifact_id)
        name = res_client.get(name_url)["attachment"]["name"]
    elif attachment_id:
        if task_id:
            name_url = "/tasks/{}/attachments/{}".format(task_id, attachment_id)
            name = res_client.get(name_url)["name"]
        elif incident_id:
            name_url = "/incidents/{}/attachments/{}".format(incident_id, attachment_id)
            name = res_client.get(name_url)["name"]
        else:
            raise ValueError("task_id or incident_id must be specified with attachment")
    else:
        raise ValueError("artifact or attachment or incident id must be specified")

    # Return name string
    return name


def write_file_attachment(res_client, file_name, datastream, incident_id, task_id=None, content_type=None):
    """
    Add a file attachment to Resilient using the REST API
    to an Incident or a Task

    **Example:**

    .. code-block:: python

        with open("malware.eml", "rb") as data_stream:
            res = write_file_attachment(self.rest_client(), "malware.eml", data_stream, 2001)

    :param res_client: required for communication back to resilient
    :type res_client: :class:`ResilientComponent.rest_client() <resilient_circuits.actions_component.ResilientComponent.rest_client()>`
    :param file_name: name of the attachment to create
    :type file_name: str
    :param dataStream: stream of bytes used to create the attachment
    :type dataStream: stream of bytes
    :param incident_id: id of the Incident
    :type incident_id: int|str
    :param task_id: (optional) id of the Task
    :type task_id: int|str
    :param content_type: (optional) MIME type of attachment. Default is ``"application/octet-stream"``
    :param content_type: str
    :return: metadata of new attachment created
    :rtype: dict
    """

    content_type = content_type \
                   or mimetypes.guess_type(file_name or "")[0] \
                   or "application/octet-stream"

    attachment = datastream.read()

    """
    Writing to temp path so that the REST API client can use this file path 
    to read and POST the attachment
    """

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            temp_file.write(attachment)
            temp_file.close()

            # Create a new attachment by calling resilient REST API

            if task_id:
                attachment_uri = "/tasks/{}/attachments".format(task_id)
            else:
                attachment_uri = "/incidents/{}/attachments".format(incident_id)

            new_attachment = res_client.post_attachment(attachment_uri,
                                                        temp_file.name,
                                                        filename=file_name,
                                                        mimetype=content_type)
        finally:
            os.unlink(temp_file.name)

    if isinstance(new_attachment, list):
        new_attachment = new_attachment[0]

    return new_attachment


def readable_datetime(timestamp, milliseconds=True, rtn_format='%Y-%m-%dT%H:%M:%SZ'):
    """
    Convert an epoch timestamp to a string using a format

    :param timestamp: ts of object sent from Resilient Server i.e. ``incident.create_date``
    :type timestamp: int
    :param milliseconds: Set to ``True`` if ts in milliseconds
    :type milliseconds: bool
    :param rtn_format: Format of resultant string. See https://docs.python.org/3.6/library/datetime.html#strftime-and-strptime-behavior for options
    :type rtn_format: str
    :return: string representation of timestamp
    :rtype: str
    """
    if milliseconds:
        ts = int(timestamp / 1000)
    else:
        ts = timestamp

    return datetime.datetime.utcfromtimestamp(ts).strftime(rtn_format)


def str_to_bool(value):
    """
    Convert value to either a ``True`` or ``False`` boolean

    Returns ``False`` if ``value`` is anything
    other than: ``'1', 'true', 'yes' or 'on'``

    :param value: the value to convert
    :type value: str
    :return: ``True`` or ``False``
    :rtype: bool
    """
    value = str(value).lower()
    return value in ('1', 'true', 'yes', 'on')


def write_to_tmp_file(data, tmp_file_name=None, path_tmp_dir=None):
    """
    Writes data to a file in a safely created temp directory.

    * If no ``tmp_file_name`` is provided, a temp name will be given
    * If no ``path_tmp_dir`` is provided a temp directory is created with the prefix **resilient-lib-tmp-**

    .. note::

        When used, ensure you safely remove the created temp directory
        in the ``finally`` block of the ``FunctionComponent`` code.

    **Example:**

    .. code-block:: python

        import os
        import shutil

        try:
            path_tmp_file, path_tmp_dir = write_to_tmp_file(attachment_contents, tmp_file_name=attachment_metadata.get("name"))

        except Exception:
            yield FunctionError()

        finally:
            if path_tmp_dir and os.path.isdir(path_tmp_dir):
                shutil.rmtree(path_tmp_dir)

    :param data: bytes to be written to the file
    :type data: bytes
    :param tmp_file_name: name to be given to the file
    :type tmp_file_name: str
    :param path_tmp_dir: path to an existing directory to use as the temp dir
    :type path_tmp_dir: str
    :return: a tuple (path_tmp_file, path_tmp_dir)
    :rtype: tuple
    """

    # If no tmp_file_name provided use next tempfile candidate name
    if not tmp_file_name:
        tmp_file_name = next(tempfile._get_candidate_names())

    # If no path_tmp_dir provided, create one
    if not path_tmp_dir:
        path_tmp_dir = tempfile.mkdtemp(prefix="resilient-lib-tmp-")

    elif not os.path.isdir(path_tmp_dir):
        raise IOError("Path does not exist: {0}".format(path_tmp_dir))

    # Generate path to tmp file
    path_tmp_file = os.path.join(path_tmp_dir, tmp_file_name)

    # Write the file
    with io.open(path_tmp_file, mode="wb") as temp_file:
        temp_file.write(data)

    return (path_tmp_file, path_tmp_dir)


def close_incident(res_client, incident_id, kwargs, handle_names=False):
    """
    Close an incident in SOAR.

    * Any **required on close (roc)** fields that
      are needed, pass them as a ``field_name:field_value`` dict in ``kwargs``

    * If any **roc** select field needs to be identified as its name,
      set ``handle_names`` to ``True``

    **Example:**

    .. code-block:: python

        res = close_incident(
            res_client=self.rest_client(),
            incident_id=fn_inputs.incident_id,
            kwargs={"resolution_id": "Duplicate", "resolution_summary": "This ticket is a duplicate"},
            handle_names=True
        )

    :param res_client: required for communication back to resilient
    :type res_client: resilient_circuits.ResilientComponent.rest_client()
    :param incident_id: id of the incident
    :type incident_id: int|str
    :param kwargs: required fields needed to close an incident in a ``field_name:field_value`` format
    :type kwargs: dict
    :param handle_names: if ``True``, any select field types in ``kwargs`` will take ``str`` instead of ``int`` as their value
    :type handle_names: bool
    :return: Response from the server indicating if the incident was closed or not
    :rtype: requests.Response
    """

    if not incident_id:
        raise ValueError("'incident_id' must be specified")

    # API call to the TypeRest for fields "required": "close" if not in kwargs throw an error
    required_fields = _get_required_fields(res_client)

    missing_fields = [field for field in required_fields if field not in kwargs]
    if missing_fields:
        raise ValueError("Missing mandatory field(s) to close an incident: {0}".format(missing_fields))

    # check for known mandatory field "plan_status" if not in kwargs add it
    mandatory_fields = kwargs.copy()
    if "plan_status" not in mandatory_fields:
        mandatory_fields["plan_status"] = "C"

    # API call to the Resilient REST API to patch the incident data (close incident)
    response = _patch_to_close_incident(res_client, incident_id, mandatory_fields, handle_names)

    return response


def _get_required_fields(res_client):
    """
    :param res_client: required for communication back to resilient
    :return: list
    """
    fields = _get_incident_fields(res_client)
    fields_required = [field for field in fields if fields[field].get("required") == "close"]

    return fields_required


@cached(cache=TTLCache(maxsize=10, ttl=600))
def _get_incident_fields(res_client):
    """
    call the Resilient REST API to get list of fields required to close an incident
    this call is cached for multiple calls
    :param res_client: required for communication back to resilient
    :return: json
    """
    uri = "/types/incident"
    response = res_client.get(uri)
    incident_fields = response.get("fields")

    return incident_fields


def _patch_to_close_incident(res_client, incident_id, close_fields, handle_names=False):
    """
    call the Resilient REST API to patch incident
    :param res_client: required for communication back to resilient
    :param incident_id: required
    :param close_fields: required
    :return: response object
    """
    uri = "/incidents/{}".format(incident_id)

    if handle_names:
        uri = "{0}?handle_format=names".format(uri)

    previous_object = res_client.get(uri)
    patch = resilient.Patch(previous_object)

    for field in close_fields:
        patch.add_value(field, close_fields[field])

    response = res_client.patch(uri, patch)

    return response
