import pytest

from resilient_lib.ui import Tab, Datatable, Field

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