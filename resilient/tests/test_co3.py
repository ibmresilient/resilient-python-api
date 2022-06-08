import resilient
from mock import patch


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
