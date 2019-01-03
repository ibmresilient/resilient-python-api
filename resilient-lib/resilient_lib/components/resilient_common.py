# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2018. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import datetime
from bs4 import BeautifulSoup
from six import string_types
try:
    from HTMLParser import HTMLParser as htmlparser
except:
    from html.parser import HTMLParser as htmlparser


INCIDENT_FRAGMENT = '#incidents'
PAYLOAD_VERSION = "1.0"

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
    ensure required fields are present. Throw ValueError if not
    :param field_list:
    :param kwargs:
    :return: no return
    """
    for field in field_list:
        if field not in kwargs or kwargs.get(field) == '':
            raise ValueError('Required field is missing or empty: '+field)


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


def get_file_attachment_name(res_client, incident_id, artifact_id=None, task_id=None, attachment_id=None):
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
        name = str(res_client.get(name_url)["attachment"]["name"])
    elif attachment_id:
        if task_id:
            name_url = "/tasks/{}/attachments/{}".format(task_id, attachment_id)
            name = str(res_client.get(name_url)["name"])
        elif incident_id:
            name_url = "/incidents/{}/attachments/{}".format(incident_id, attachment_id)
            name = str(res_client.get(name_url)["name"])
        else:
            raise ValueError("task_id or incident_id must be specified with attachment")
    else:
        raise ValueError("artifact or attachment or incident id must be specified")

    # Return name string
    return name


def readable_datetime(timestamp, milliseconds=True, rtn_format='%Y-%m-%dT%H:%M:%SZ'):
    """
    convert an epoch timestamp to a string using a format
    :param timestamp:
    :param milliseconds: True = epoch in
    :param rtn_format: format of resulant string
    :return: string representation of timestamp
    """
    if milliseconds:
        ts = int(timestamp/1000)
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
