# -*- coding: utf-8 -*-

from datetime import datetime

from resilient_lib.components import poller_common

NEW_CASE_PAYLOAD = {
  "name": "test case",
  "description": "a short description",
  "discovered_date": str(datetime.now()),
  "start_date": str(datetime.now()),
  "plan_status": "A"
}

def test_get_soar_case(fx_mock_resilient_client):
    soar_common = poller_common.SOARCommon(fx_mock_resilient_client)

    case, _err_msg = soar_common.get_soar_case({ "id": 2314 }, open_cases=False)

    assert case["plan_status"] == "A"
    assert case["id"] == 2314

def test_get_soar_cases(fx_mock_resilient_client):
    soar_common = poller_common.SOARCommon(fx_mock_resilient_client)

    cases, _err_msg = soar_common.get_soar_cases({ "id": 2314 }, open_cases=False)

    assert cases
    assert len(cases) == 1
    assert cases[0]["id"] == 2314

def test_create_soar_case(fx_mock_resilient_client):
    soar_common = poller_common.SOARCommon(fx_mock_resilient_client)

    created_case = soar_common.create_soar_case(NEW_CASE_PAYLOAD)
    
    assert created_case["name"] == "test case"

def test_update_soar_case(fx_mock_resilient_client):
    soar_common = poller_common.SOARCommon(fx_mock_resilient_client)

    updated_case = soar_common.update_soar_case(2314, {"description": "now has a description"})

    assert updated_case["id"] == 2314
    assert updated_case["success"]

def test_create_case_comment(fx_mock_resilient_client):
    soar_common = poller_common.SOARCommon(fx_mock_resilient_client)

    comment = "A test comment"

    resp = soar_common.create_case_comment(2314, None, None, comment)

    assert resp["text"]["content"] == comment

def test_get_case(fx_mock_resilient_client):
    soar_common = poller_common.SOARCommon(fx_mock_resilient_client)

    case = soar_common.get_case(2314)

    assert "case_types" in case
    assert case["id"] == 2314

def test_
