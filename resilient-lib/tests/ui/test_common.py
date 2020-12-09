import pytest
from mock import patch
from resilient_lib.ui import Tab, Datatable, Field
from resilient_lib.ui import create_tab


class MockTab(Tab):
    NAME = "test"
    UUID = "test"
    SECTION = "test"
    CONTAINS = [
        Datatable('test'),
        Field('test')
    ]

    SHOW_IF = [Field('test').conditions.has_value()]

class TestSubmittedData(object):
    """
    Tests that payload submitted to the server contains proper tab information.
    """
    @patch("resilient.get_client")
    @patch("resilient_lib.ui.common._get_opts")
    def test_create_tab(self, _get_opts, get_client):
        # these are a mock of app.config
        _get_opts.return_value = {
            MockTab.SECTION: {
            }
        }
        # this mocks the requests made to /types and /layout?type_id=xxx
        get_client.return_value.get.side_effect = [
            {
                "organization": {
                    "type_id": 42
                }
            },
            [{
                "id": 42,
                "name": "incident",
                "content": []
            }]
        ]

        create_tab(MockTab)

        # assert that PUT was called and correct payload present
        get_client.return_value.put.assert_called_once()
        call_args = get_client.return_value.put.call_args
        payload = call_args.kwargs.get("payload")
        assert MockTab.exists_in(payload.get('content'))
        for field in MockTab.CONTAINS:
            assert field.exists_in(MockTab.get_from_tabs(payload.get('content')).get("fields"))

    @patch("resilient.get_client")
    @patch("resilient_lib.ui.common._get_opts")
    def test_create_tab_with_locked_ui(self, _get_opts, get_client):
        # these are a mock of app.config
        _get_opts.return_value = {
            "resilient": {
                "ui_lock": "True"
            },
            MockTab.SECTION: {
            }
        }
        # this mocks the requests made to /types and /layout?type_id=xxx
        get_client.return_value.get.side_effect = [
            {
                "organization": {
                    "type_id": 42
                }
            },
            [{
                "id": 42,
                "name": "incident",
                "content": []
            }]
        ]

        create_tab(MockTab)

        # assert that PUT was called and correct payload present
        assert get_client.return_value.put.call_count == 0

    @patch("resilient.get_client")
    @patch("resilient_lib.ui.common._get_opts")
    def test_update_tab_disabled(self, _get_opts, get_client):
        # these are a mock of app.config
        _get_opts.return_value = {
            MockTab.SECTION: {
            }
        }
        # this mocks the requests made to /types and /layout?type_id=xxx
        get_client.return_value.get.side_effect = [
            {
                "organization": {
                    "type_id": 42
                }
            },
            [{
                "id": 42,
                "name": "incident",
                "content": [{
                    "predefined_uuid": MockTab.UUID,
                    "fields": [
                        Field("test").as_dto()
                    ]
                }]
            }]
        ]

        create_tab(MockTab)

        # assert that PUT was called and correct payload present
        get_client.return_value.put.call_count == 0


    @patch("resilient.get_client")
    @patch("resilient_lib.ui.common._get_opts")
    def test_update_tab_enabled(self, _get_opts, get_client):
        # these are a mock of app.config
        _get_opts.return_value = {
            MockTab.SECTION: {
            }
        }
        # this mocks the requests made to /types and /layout?type_id=xxx
        get_client.return_value.get.side_effect = [
            {
                "organization": {
                    "type_id": 42
                }
            },
            [{
                "id": 42,
                "name": "incident",
                "content": [{
                    "predefined_uuid": MockTab.UUID,
                    "fields": [
                        Field("test").as_dto()
                    ]
                }]
            }]
        ]

        create_tab(MockTab, update_existing=True)

        get_client.return_value.put.assert_called_once()
        call_args = get_client.return_value.put.call_args
        payload = call_args.kwargs.get("payload")
        assert MockTab.exists_in(payload.get('content'))
        for field in MockTab.CONTAINS:
            assert field.exists_in(MockTab.get_from_tabs(payload.get('content')).get("fields"))
    
    @patch("resilient.get_client")
    @patch("resilient_lib.ui.common._get_opts")
    def test_conditions_sent(self, _get_opts, get_client):
        # these are a mock of app.config
        _get_opts.return_value = {
            MockTab.SECTION: {
            }
        }
        # this mocks the requests made to /types and /layout?type_id=xxx
        get_client.return_value.get.side_effect = [
            {
                "organization": {
                    "type_id": 42
                }
            },
            [{
                "id": 42,
                "name": "incident",
                "content": [{
                    "predefined_uuid": MockTab.UUID,
                    "fields": [
                        Field("test").as_dto()
                    ]
                }]
            }]
        ]

        create_tab(MockTab, update_existing=True)

        get_client.return_value.put.assert_called_once()
        call_args = get_client.return_value.put.call_args
        payload = call_args.kwargs.get("payload")
        assert MockTab.exists_in(payload.get('content'))
        for field in MockTab.CONTAINS:
            assert field.exists_in(MockTab.get_from_tabs(
                payload.get('content')).get("fields"))
        assert MockTab.get_from_tabs(payload.get('content')).get('show_if') == MockTab.SHOW_IF
