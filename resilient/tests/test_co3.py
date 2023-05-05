import json
from mock import patch

import resilient


@patch("resilient.co3base.BaseClient.set_api_key")
@patch("resilient.co3base.BaseClient.get")
def test_get_client(mock_get_call, mock_session):

    mock_cert = ("mock_cert_file_path.pem", "mock_cert_file_key_path.pem")
    mock_opts = {
        "org": "Test Organization",
        "host": "example.com",
        "port": 8080,
        "api_key_id": "1234-efgh",
        "api_key_secret": "abcd-56789",
        "cafile": "FALSE",
        "client_auth_cert": mock_cert[0],
        "client_auth_key": mock_cert[1]
    }
    mock_session_info = {
        "orgs": [{"name": "Test Organization", "id": 201}]
    }
    mock_get_org_data = {
        "actions_framework_enabled": False
    }
    mock_session.return_value = mock_session_info
    mock_get_call.return_value = mock_get_org_data

    res_client = resilient.get_client(mock_opts)

    assert res_client.base_url == "https://example.com:8080"
    assert res_client.cert == mock_cert
    assert res_client.actions_enabled == False

def test_client_put(fx_simple_client):

    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

    test_headers = {"content-type": "application/octet-stream"}

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)    

    requests_adapter.register_uri('PUT',
                                  mock_uri,
                                  status_code=200,
                                  request_headers=test_headers,
                                  text=json.dumps(test_headers))

    uri = "/playbooks/imports"

    r = base_client.put(
        uri,
        "payload",
        headers=test_headers
    )

    assert r['content-type'] == test_headers['content-type']

def test_client_post(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.post("/incidents/1001", {"incident_name": "Mock Incident"})

    assert r.get("incident_id") == 1001

def test_simple_client_get_const(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

    mock_uri = '{0}/rest/const'.format(base_client.base_url)
    mock_response = {"server_version": {"major": 47, "minor": 0, "build_number": 8304, "version": "47.0.8304"}}
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.get_const()

    assert r.get("server_version", {}).get("major") == 47
