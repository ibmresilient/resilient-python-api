# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2018. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import datetime
import tempfile
import os
import io
import shutil
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
            raise ValueError('Required field is missing or empty: ' + field)


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

    elif attachment_id:
        if task_id:
            metadata_url = "/tasks/{}/attachments/{}".format(task_id, attachment_id)
        elif incident_id:
            metadata_url = "/incidents/{}/attachments/{}".format(incident_id, attachment_id)
        else:
            raise ValueError("task_id or incident_id must be specified with attachment")

        return res_client.get(metadata_url)

    else:
        raise ValueError("artifact or attachment or incident id must be specified")


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


def get_app_config_option(app_configs, option_name, optional=False, placeholder=None):
    """Given option_name, checks if it is in app_configs. Raises ValueError if
    optional=False and its value is None or equals the given placeholder

    - app_configs: [Dict] of all appconfigs. (Generally self.options)
    - option_name: [String] name of the option to get
    - optional:    [Bool] if the option is mandatory or not. Default: False
    - placeholder: [String] the default placeholder that is specified in the config.py file. If the
    value of the option_name matches this placeholder, a ValueError is raised. Default: None.
    - Return: the value of option_name"""

    option = app_configs.get(option_name)
    err = "'{0}' is mandatory and is not set in app.config file. You must set this value to run this function".format(option_name)

    if not option and optional is False:
        raise ValueError(err)
    elif optional is False and placeholder is not None and option == placeholder:
        raise ValueError(err)
    else:
        return option


def get_function_input(inputs, input_name, optional=False):
    """Given input_name, checks if it defined in inputs. Raises ValueError if
    optional=False and input_name is not found or undefined

    - inputs:     [Dict] of all function inputs. Generally 'kwargs'.
    - input_name: [String] name of the input to get
    - optional:   [Bool] if the input is mandatory or not. Default: False
    - Return:     the value of input_name"""

    the_input = inputs.get(input_name)

    if not the_input and optional is False:
        err = "'{0}' is a mandatory function input".format(input_name)
        raise ValueError(err)
    else:
        # Handle if select input type
        if isinstance(the_input, dict):
            the_input = the_input.get("name")

        # Handle if multi-select input type
        elif isinstance(the_input, list):
            the_input = [i.get("name") for i in the_input]

        return the_input


def get_all_function_inputs(inputs, mandatory_inputs=[]):
    """If mandatory input is not defined in inputs, a ValueError is raised.

    - inputs:           [Dict] of all function inputs. Generally 'kwargs'.
    - mandatory_inputs: [List] of the names of inputs that are required for the function to run. Default is an empty List.
    - Return: a Dict of each input input_name/input_value"""

    fn_inputs = {}

    try:
        validate_fields(mandatory_inputs, inputs)

    except ValueError as err:
        raise ValueError("Mandatory function input not defined\n{0}".format(err))

    for i in inputs:
        optional = i not in mandatory_inputs
        fn_inputs[i] = get_function_input(inputs=inputs, input_name=i, optional=optional)

    return fn_inputs


def write_to_tmp_file(data, tmp_file_name=None, path_tmp_dir=None):
    """Writes data to a safely created temp file. If no tmp_file_name is
    provided, a temp name will be given If no path_tmp_dir is provided a
    temp directory is created with the prefix 'resilient-lib-tmp-'.

    - data: [Bytes] to be written to the file
    - tmp_file_name: [String] name to be given to the file.
    - path_tmp_dir: [String] path to an existing directory to use as the temp dir
    - Return: a Tuple (path_tmp_file, path_tmp_dir)
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
