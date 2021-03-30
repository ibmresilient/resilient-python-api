#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""
Common place for helper functions used in tests
"""

import io
import os
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder
from tests.shared_mock_data import mock_paths


def read_mock_json(template_name):
    """
    Read a mock JSON file from .shared_mock_data/resilient_api_data/template_name
    Return it as a Dictionary
    """
    return_json = {}
    template_path = os.path.join(mock_paths.RESILIENT_API_DATA, template_name)
    with io.open(template_path, "r", encoding="utf-8") as template_file:
        return_json = json.load(template_file)
    return return_json


def verify_expected_list(list_expected_strs, list_actual_strs):
    """
    Return True if each str in list_expected_strs is in list_actual_strs
    """
    return all(elem in list_actual_strs for elem in list_expected_strs)


def upload_app_zip(res_client, path_app_zip):
    """
    Uploads the app.zip at path_app_zip to the Appliance that
    res_client is connected to

    :param res_client: required for communication back to resilient
    :type res_client: resilient.co3.SimpleClient obj
    :param path_app_zip: file path to app.zip
    :type path_app_zip: str
    :return: Response after uploading the app.zip
    :rtype: requests.Response obj
    """
    app_zip_name_name = os.path.basename(path_app_zip)

    uri = u"{0}/rest/orgs/{1}{2}".format(res_client.base_url, res_client.org_id, "/apps")

    with open(path_app_zip, "rb") as file_handle:
        multipart_data = {"file": (app_zip_name_name, file_handle, "application/zip")}
        encoder = MultipartEncoder(fields=multipart_data)

        headers = res_client.make_headers(additional_headers={"content-type": encoder.content_type, "accept": "application/json", "text_content_output_format": "objects_convert"})

        return res_client._execute_request(res_client.session.post,
                                           uri,
                                           data=encoder,
                                           params={"handle_format": "objects"},
                                           proxies=res_client.proxies,
                                           cookies=res_client.cookies,
                                           headers=headers,
                                           verify=res_client.verify,
                                           timeout=None)


def install_app_zip(res_client, app_data):
    """
    Installs the app the Appliance that res_client is connected to

    :param res_client: required for communication back to resilient
    :type res_client: resilient.co3.SimpleClient obj
    :param app_data: Dict with info of app to install (Normally the response.json() of the result of upload_app_zip()
    :type app_data: dict
    :return: Response after uploading the app.zip
    :rtype: requests.Response obj
    """
    app_id = app_data.get("id")

    current_installation = app_data.get("current_installation", {})
    current_installation_id = current_installation.get("id")
    current_installation_items = current_installation.get("items")
    current_installation_executables = current_installation.get("executables")
    current_installation_customizations_count = current_installation.get("customizations_count")

    install_payload = {
        "id": current_installation_id,
        "status": "installing",
        "items": current_installation_items,
        "executables": current_installation_executables,
        "customizations_count": current_installation_customizations_count
    }

    uri = "/apps/{0}/installations/{1}".format(app_id, current_installation_id)
    return res_client.put(uri, install_payload)
