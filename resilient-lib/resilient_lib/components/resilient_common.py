# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2018. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import datetime
import tempfile
import os
import io
import mimetypes
import base64
import logging
from bs4 import BeautifulSoup
from six import string_types
from cachetools import cached, TTLCache

try:
    from HTMLParser import HTMLParser as htmlparser
except:
    from html.parser import HTMLParser as htmlparser

INCIDENT_FRAGMENT = '#incidents'
PAYLOAD_VERSION = "1.0"

LOG = logging.getLogger(__name__)


def build_incident_url(url, incidentId):
    """
    build the url to link to an resilient incident
    :param url: base url
    :param incidentId:
    :return: full url
    """
    return '/'.join([url, INCIDENT_FRAGMENT, str(incidentId)])


def build_resilient_url(host, port):
    """
    build basic url to resilient instance
    :param host: host name
    :param port: port
    :return: base url
    """
    if host.lower().startswith("http"):
        return "{0}:{1}".format(host, port)

    return "https://{0}:{1}".format(host, port)


def clean_html(html_fragment):
    """
    Resilient textarea fields return html fragments. This routine will remove the html and insert any code within <div></div>
    with a linefeed
    :param html_fragment: str presenting the html to clean up
    :return: cleaned up code. This may not format well as no presentation of line feeds are preserved in the way supported by
       tags such as <br> or <ol>, <ul>, etc. See html2markdown for a better way to translate html input to markdown.
    """

    if not html_fragment or not isinstance(html_fragment, string_types):
        return html_fragment

    s = BeautifulSoup(unescape(html_fragment), "html.parser")

    return ' '.join(s.strings)


def unescape(data):
    """ Return unescaped data such as &gt; -> >, &quot -> ', etc.
    :param data: text to convert
    """
    if data is None:
        return None

    h = htmlparser()
    return h.unescape(data)


def validate_fields(field_list, kwargs):
    """
    Ensure each mandatory field in field_list is present in kwargs.
    Throw ValueError if not.

    field_list can be a list/tuple of strings where each string is
    a field name or it can be a list/tuple of dicts where each item
    has the attributes 'name' (required) and 'placeholder' (optional).

    If the value of the item in kwargs is equal to its placeholder
    defined in field_list, a ValueError is raised.

    If an item in kwargs is a Resilient Select Function Input, its
    value will be a dict that has a 'name' attribute. This returns
    the value of 'name'.

    If an item in kwargs is a Resilient Multi-Select Function Input, its
    value will be a list of dicts that have the 'name' attribute. This
    returns a list of the 'name' values for that item.

    :param field_list: list/tuple of the mandatory fields. Can be an empty list if no mandatory fields.
    :param kwargs: dict of all the fields to search.
    :return: a Dictionary of all fields with Select/Multi-Select fields handled.
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
        raise ValueError("'kwargs' must be of type dict, not {0}".format(type(provided_fields)))

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
        elif isinstance(field_value, list):
            field_value = [f.get("name") for f in field_value]

        return_fields[field_name] = field_value

    return return_fields


def get_file_attachment(res_client, incident_id, artifact_id=None, task_id=None, attachment_id=None):
    """
    call the Resilient REST API to get the attachment or artifact data
    :param res_client: required for communication back to resilient
    :param incident_id: required
    :param artifact_id: optional
    :param task_id: optional
    :param attachment_id: optional
    :return: byte string of attachment
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
    call the Resilient REST API to get the attachment or artifact attachment metadata
    :param res_client: required for communication back to resilient
    :param incident_id: required
    :param artifact_id: optional
    :param task_id: optional
    :param attachment_id: optional
    :return: file attachment metadata
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
    call the Resilient REST API to get the attachment or artifact attachment name
    :param res_client: required for communication back to resilient
    :param incident_id: required
    :param artifact_id: optional
    :param task_id: optional
    :param attachment_id: optional
    :return: file attachment name
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
    call the Resilient REST API to create the attachment on incident or task

    :param res_client: required for communication back to resilient
    :param file_name: required, name of the attachment
    :param dataStream: required, stream of bytes
    :param incident_id: required
    :param task_id: optional
    :param content_type: optional, MIME type of attachment
    :return: new attachment -dictionary of attachment metadata
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
    convert an epoch timestamp to a string using a format
    :param timestamp:
    :param milliseconds: True = epoch in
    :param rtn_format: format of resulant string
    :return: string representation of timestamp
    """
    if milliseconds:
        ts = int(timestamp / 1000)
    else:
        ts = timestamp

    return datetime.datetime.utcfromtimestamp(ts).strftime(rtn_format)


def str_to_bool(value):
    """Represents value as boolean.
    :param value:
    :rtype: bool
    """
    value = str(value).lower()
    return value in ('1', 'true', 'yes')


def write_to_tmp_file(data, tmp_file_name=None, path_tmp_dir=None):
    """Writes data to a file in a safely created temp directory. If no
    `tmp_file_name` is provided, a temp name will be given. If no `path_tmp_dir`
    is provided a temp directory is created with the prefix `resilient-lib-tmp-`.

    When used within a Resilient Function, ensure you safely remove the created temp
    directory in the `finally` block of the FunctionComponent code.

    Example:
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
    :type data: `bytes`
    :param tmp_file_name: name to be given to the file.
    :type tmp_file_name: `str`
    :param path_tmp_dir: path to an existing directory to use as the temp dir
    :type path_tmp_dir: `str`
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


def get_incident(res_client, incident_id):
    """
    call the Resilient REST API to get the incident data
    :param res_client: required for communication back to resilient
    :param incident_id: required
    :return: dict
    """
    data_uri = "/incidents/{}".format(incident_id)
    return res_client.get(data_uri)


def patch_incident(res_client, incident_id, body):
    """
    call the Resilient REST API to patch incident
    :param res_client: required for communication back to resilient
    :param incident_id: required
    :return: dict
    """
    data_uri = "/incidents/{}".format(incident_id)
    return res_client.patch(data_uri, body)


@cached(cache=TTLCache(maxsize=10, ttl=600))
def get_field_type(res_client, field_name):
    """
    call the Resilient REST API to get input_type
    this call is cached for multiple calls
    :param res_client: required for communication back to resilient
    :param field_name: required
    :return: dict
    """
    uri = "/types/incident"
    response = res_client.get(uri)
    LOG.debug("FIELD TYPE {}".format(response))
    field_type = response["fields"][field_name]["input_type"]
    LOG.debug("FIELD TYPE {}".format(field_type))
    # field_type = response.get("fields").get(field_name).get("input_type")
    return field_type


@cached(cache=TTLCache(maxsize=10, ttl=600))
def get_fields_required_to_close(res_client):
    """
    call the Resilient REST API to get list of fields required to close an incident
    this call is cached for multiple calls
    :param res_client: required for communication back to resilient
    :param field_name: required
    :return: dict
    """
    uri = "/types/incident"
    response = res_client.get(uri)
    fields_required = []
    # for field in response:
    #     if "required" in field and field["required"] == "close":
    #         fields_required.append(field["name"])
    return fields_required


def close_incident(res_client, incident_id, kwargs):
    if not incident_id:
        raise ValueError("incident id must be specified")

    # API call TypeRest for "required": "close" compare 2 lists
    # get /orgs/{org_id}/types/{type}/fields
    required_fields = get_fields_required_to_close(res_client)
    for field in required_fields:
        if field not in kwargs:
            raise ValueError("'{0}' is mandatory and is not set. You must set this value to run this function.".format(field))


    # build changes_list to be used it in patch API call
    changes_list = []

    # 1. Get fields for patch API

    # dict of field_name:new_value pairs
    provided_fields = kwargs

    """get incident version to be used it in patch API call get version and old_value"""
    incident = get_incident(res_client, incident_id)
    incident_version = incident.get("vers")

    # custom mandatory field/s (resolution_id, resolution_summary & other)
    custom_mandatory_field = {}
    """ 
    loop for each field_name:new_value pair from provided_fields to build an dict (custom_mandatory_field) and append it
    to the changes_list of dicts changes_list.append(custom_mandatory_field), check for empty
    
    custom_mandatory_field is to match the schema:
    {
      "field": {
        "name": field_name
      },
      "old_value": {
        get_field_type(res_client, field_name): incident.get(field_name)
      },   TODO: populate from API get incident call {}
      "new_value": {
        get_field_type(res_client, field_name): new_value    TODO: call the Resilient REST API to get the input_type for provided_field str
      }
    }
    """

    # known mandatory field (plan_status)
    """check if that field exists in changes_list if not append it to the list"""
    known_mandatory_field = {
        "field": "plan_status",
        "old_value": {"text": "A"},
        "new_value": {"text": "C"}
    }

    # 2. Build the body of the patch API cal
    body = {}
    """build the body of the API call
    body = {
        "changes": changes_list,
        "version": incident_version
    }    
    """

    # 3. call the Resilient REST API to patch the incident data (close incident)
    response = patch_incident(res_client, incident_id, body)

    return "OK"
