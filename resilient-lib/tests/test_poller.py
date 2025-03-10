# -*- coding: utf-8 -*-

##########################
# NOTE that the tests here are only written to work with
# Python 3.6 or higher!
##########################

import datetime
import sys
import time
from collections import namedtuple
from threading import Thread

import mock
import pytest
from resilient_lib.components.poller_common import (DEFAULT_CASES_QUERY_FILTER,
                                                    IntegrationError,
                                                    SOARCommon, b_to_s,
                                                    eval_mapping,
                                                    get_last_poller_date,
                                                    poller, s_to_b)
from resilient_lib.util import constants

from resilient import SimpleHTTPException

NEW_CASE_PAYLOAD = {
  "name": "test case",
  "description": u"a short description  ฑ ฒ ณ ด ต ถ ท ธ น ",
  "discovered_date": str(datetime.datetime.now()),
  "start_date": str(datetime.datetime.now()),
  "plan_status": "A"
}



class SimplePollerTester():

    def __init__(self, interval=1):
        self.PACKAGE_NAME = "TEST_PACKAGE"
        self.polling_interval = interval
        self.last_poller_time = get_last_poller_date(10)

        self.count = 0


    @poller("polling_interval", "last_poller_time")
    def good_run(self, *args, **kwargs):
        self.count += 1
        assert "last_poller_time" in kwargs

    @poller("polling_interval", "last_poller_time")
    def bad_run(self, *args, **kwargs):
        self.count += 1
        raise Exception("some exception")

def _raise_generic_exception(*__args, **__kwargs):
    raise Exception("something went wrong!")

def _raise_http_exception(*__args, **__kwargs):
    Response = namedtuple("Response", ["reason", "text"])
    raise SimpleHTTPException(Response("No reason", "something went wrong"))

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_poller_decorator_success():
    """
    NOTE: this test takes 'sleep_time' seconds to run as it is
    testing the poller
    """
    sleep_time = 1

    test_poller = SimplePollerTester(interval=1)

    poller_thread = Thread(target=test_poller.good_run)
    poller_thread.daemon = True
    poller_thread.start()

    time.sleep(sleep_time)
    # allow for flexibility of ± 1
    assert test_poller.count in range(sleep_time-1, sleep_time+2)

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_poller_decorator_failure(caplog):
    """
    Raises and exception to make sure those are handled properly
    """
    sleep_time = 1

    test_poller = SimplePollerTester()

    poller_thread = Thread(target=test_poller.bad_run)
    poller_thread.daemon = True
    poller_thread.start()

    time.sleep(sleep_time)
    # allow for flexibility of ± 1
    assert test_poller.count in range(sleep_time-1, sleep_time+2)

    # the actual ERROR message has the line number, but that could easily change
    # so we're splitting up the assertions here around the line number
    # ex:
    # "ERROR    resilient_lib.components.poller_common:poller_common.py:83 some exception"
    assert "ERROR    resilient_lib.components.poller_common:poller_common.py" in caplog.text
    assert "some exception" in caplog.text



@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_get_case(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    case = soar_common.get_case(2314)

    assert "case_types" in case
    assert case["id"] == 2314




@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_get_soar_case(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    case, _err_msg = soar_common.get_soar_case({ "id": 2314 }, open_cases=False)

    assert case["plan_status"] == "A"
    assert case["id"] == 2314
    assert fx_mock_resilient_client.session.adapters.get("https://").last_request.query == DEFAULT_CASES_QUERY_FILTER




@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_get_soar_cases_success(fx_mock_resilient_client, caplog):
    soar_common = SOARCommon(fx_mock_resilient_client)

    mock_query = "return_level=notnormal"
    cases, _err_msg = soar_common.get_soar_cases({ "id": 2314, "bad_field": True }, open_cases=True, uri_filters=mock_query)

    assert cases
    assert len(cases) == 1
    assert cases[0]["id"] == 2314
    assert fx_mock_resilient_client.session.adapters.get("https://").last_request.query == mock_query

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_get_soar_cases_failure(fx_mock_resilient_client):
    old_post = fx_mock_resilient_client.post
    fx_mock_resilient_client.post = _raise_http_exception
    soar_common = SOARCommon(fx_mock_resilient_client)

    cases, _err_msg = soar_common.get_soar_cases({ "id": 2314, "bad_field": True }, open_cases=True)

    assert "No reason:  something went wrong" in _err_msg

    # reset
    fx_mock_resilient_client.post = old_post



@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_create_soar_case_success(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    created_case = soar_common.create_soar_case(NEW_CASE_PAYLOAD)

    assert created_case["name"] == "test case"

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_create_soar_case_failure(fx_mock_resilient_client):
    old_post = fx_mock_resilient_client.post
    fx_mock_resilient_client.post = _raise_generic_exception
    soar_common = SOARCommon(fx_mock_resilient_client)

    with pytest.raises(IntegrationError) as err:
        soar_common.create_soar_case(NEW_CASE_PAYLOAD)

    assert "create_soar_case failed to create case in SOAR" in str(err)

    # reset
    fx_mock_resilient_client.post = old_post




@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_update_soar_case_success(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    updated_case = soar_common.update_soar_case(2314, {"description": "now has a description  ฑ ฒ ณ ด ต ถ ท ธ น"})

    assert updated_case["id"] == 2314
    assert updated_case["success"]

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_update_soar_case_failure(fx_mock_resilient_client):
    old_patch = fx_mock_resilient_client.patch
    fx_mock_resilient_client.patch = _raise_generic_exception
    soar_common = SOARCommon(fx_mock_resilient_client)

    with pytest.raises(IntegrationError) as err:
        soar_common.update_soar_case(2314, {"description": "now has a description  ฑ ฒ ณ ด ต ถ ท ธ น"})

    assert "update_soar_case failed to update case in SOAR" in str(err)

    # reset
    fx_mock_resilient_client.patch = old_patch


@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_update_soar_cases(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    payload = {
        "patches": {
            "2314": {
                "changes": [
                    {
                        "field": {"name": "severity_code"},
                        "old_value": {"text": "Low"},
                        "new_value": {"text": "High"}
                    },
                    {
                        "field": {"name": "addr"},
                        "old_value": {"text": None},
                        "new_value": {"text": "123 street"}
                    }
                ],
                "version": 12
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

    updated_cases = soar_common.update_soar_cases(payload)
    assert not updated_cases.get("failures")

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_create_case_comment(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    comment = "A test comment  ฑ ฒ ณ ด ต ถ ท ธ น "

    resp = soar_common.create_case_comment(2314, comment)

    assert resp["text"]["content"] == comment




@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_create_datatable_row(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    rowdata = {"column_1_api_name": 1, "column_2_api_name": 2}
    resp = soar_common.create_datatable_row(2314, "custom_dt", rowdata)

    assert resp["id"] == 27
    assert "cells" in resp
    assert "column_1_api_name" in resp["cells"] and "column_2_api_name" in resp["cells"]




@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_get_case_attachment(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    resp = soar_common.get_case_attachments(2314, return_base64=True)

    assert len(resp) == 2
    assert resp[0]["id"] == 27
    assert resp[1]["id"] == 123
    assert "content" in resp[0] and "content" in resp[1]
    assert resp[0]["content"] == "IlwiYWJjZGVmXCIi"

    resp = soar_common.get_case_attachments(2314, return_base64=False)
    assert resp[0]["content"] == b'"\\"abcdef\\""'




@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_lookup_artifact_type_failure(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    resp = soar_common.lookup_artifact_type("incident")

    assert not resp

@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_lookup_artifact_type_success(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    resp = soar_common.lookup_artifact_type("artifact")

    assert resp == "my artifact"


@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_filter_soar_comments(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    mock_entity_comments = ["new comment to add here", "comment to add"]
    mock_soar_comments = ["new comment to add here"]
    resp = soar_common._filter_comments(mock_soar_comments, mock_entity_comments)

    assert resp == ["comment to add"]


@pytest.mark.livetest
@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="poller common requires python3.6 or higher")
def test_get_case_tasks(fx_mock_resilient_client):
    soar_common = SOARCommon(fx_mock_resilient_client)

    resp = soar_common.get_case_tasks(2314)

    assert isinstance(resp, list)
    # If list returned is greater than 0 then a list of tasks was returned
    assert len(resp) > 0



def test_eval_mapping(caplog):
    # test convert str to dict
    mock_config = '"source":"A","tags":["tagA"],"priorities":[40,50]'
    parsed_config = eval_mapping(mock_config, "{{ {} }}")
    assert parsed_config == { "source": "A", "tags": ["tagA"], "priorities": [40, 50] }

    # test no value given
    assert not eval_mapping(None)

    # test bad result (not list or dict)
    result = eval_mapping("4, 5", "({})")
    assert not result
    assert """mapping eval_value must be a string representation of a (partial) array or dictionary e.g. "'value1', 'value2'" or "'key':'value'""" in caplog.text




def test_s_to_b_and_b_to_s():
    mocks = ["ç∆˚¬å", "test", ]
    for mock_s_val in mocks:
        b = s_to_b(mock_s_val)
        assert b

        s = b_to_s(b)
        assert s
        assert s == mock_s_val

    # check for non-decodeable/encodeable value
    assert b_to_s("1234") == "1234"
    assert s_to_b(1234) == 1234



def test_get_last_poller_date():

    with mock.patch("resilient_lib.components.poller_common._get_timestamp") as mock_time:
        mock_time.return_value = datetime.datetime.fromtimestamp(1234)

        # NOTE: these hard coded timestamps are set to work with
        # Travis's timezone so might not work locally
        x = get_last_poller_date(20)
        assert str(x) == "1970-01-01 00:00:34"


        x = get_last_poller_date(10)
        assert str(x) == "1970-01-01 00:10:34"
