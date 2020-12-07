import pytest

from resilient_lib.ui import Tab
from resilient_lib.ui.common import permission_to_edit

class TestEditPermissions(object):
    class TestTab(Tab):
        NAME = "TestTab"
        UUID = "42"
        SECTION = "fn_test"
        CONTAINS = []

    def test_function_permissions_lock_ui(self):
        opts = {
            "fn_test": {
                "ui_lock": "True"
            }
        }
        assert not permission_to_edit(TestEditPermissions.TestTab, opts)

    def test_integration_permissions_lock_ui(self):
        opts = {
            "integrations":{
                "ui_lock": "True"
            },
            "fn_test": {
            }
        }
        assert not permission_to_edit(TestEditPermissions.TestTab, opts)

    def test_global_permissions_lock_ui(self):
        opts = {
            "resilient": {
                "ui_lock": "True"
            }
        }
        assert not permission_to_edit(TestEditPermissions.TestTab, opts)

    def test_function_permissions_override_global_lock(self):
        opts = {
            "resilient":{
                "ui_lock": "True",
            },
            "fn_test": {
                "ui_lock": "False"
            }
        }
        assert permission_to_edit(TestEditPermissions.TestTab, opts)

    def test_function_permissions_override_global_unlock(self):
        opts = {
            "resilient":{
                "ui_lock": "False",
            },
            "fn_test": {
                "ui_lock": "True"
            }
        }
        assert not permission_to_edit(TestEditPermissions.TestTab, opts)

    def test_function_permissions_override_integrations_unlock(self):
        opts = {
            "resilient": {
                "ui_lock": "False"
            },
            "integrations":{
                "ui_lock": "False",
            },
            "fn_test": {
                "ui_lock": "True"
            }
        }
        assert not permission_to_edit(TestEditPermissions.TestTab, opts)

    def test_integrations_permissions_override_global_unlock(self):
        opts = {
            "resilient":{
                "ui_lock": "False",
            },
            "integrations": {
                "ui_lock": "True"
            }
        }
        assert not permission_to_edit(TestEditPermissions.TestTab, opts)
