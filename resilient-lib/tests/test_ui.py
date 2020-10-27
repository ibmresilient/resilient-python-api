import pytest

from resilient_lib.ui import Tab, Datatable, Field
from resilient_lib.ui.common import permission_to_edit

class TestTabMetaclass(object):
	"""
	Confirm that a class can't be defined without all of the required
	class variables being selected.
	"""

	def test_name_is_required(self):
		with pytest.raises(AttributeError, match="NAME"):
			class TestTab(Tab):
				UUID = "test"
				SECTION = "test"
				CONTAINS = []

	def test_uuid_is_required(self):
		with pytest.raises(AttributeError, match="UUID"):
			class TestTab(Tab):
				NAME = "test"
				SECTION = "test"
				CONTAINS = []

	def test_section_is_required(self):
		with pytest.raises(AttributeError, match="SECTION"):
			class TestTab(Tab):
				NAME = "test"
				UUID = "test"
				CONTAINS = []

	def test_contains_is_required(self):
		with pytest.raises(AttributeError, match="CONTAINS"):
			class TestTab(Tab):
				NAME = "test"
				UUID = "test"
				SECTION = "test"

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

	def test_function_permissions_override_global(self):
		opts = {
			"resilient":{
				"ui_lock": "True",
			},
			"fn_test": {
				"ui_lock": "False"
			}
		}
		assert permission_to_edit(TestEditPermissions.TestTab, opts)

