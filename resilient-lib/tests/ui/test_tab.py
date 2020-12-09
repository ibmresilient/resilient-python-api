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

class TestTab(object):
    class FakeTab(Tab):
        NAME = "Fake"
        UUID = "42"
        SECTION = "fake"

        CONTAINS = [
            Datatable("test_table1"),
            Datatable("test_table2"),
            Field("test_field1"),
            Field("test_field2")
        ]

    def test_exists_in(self):
        """
        This is a simplified version of "content" of a layout
        """
        assert TestTab.FakeTab.exists_in([
            {"predefined_uuid": "1"},
            {"predefined_uuid": "2"},
            {"predefined_uuid": "42"}
        ])

    def test_all_missing_fields(self):
        tabs = [
            {"predefined_uuid": "1"},
            {"predefined_uuid": "2"},
            {"predefined_uuid": "42",
             "fields": []
            }
        ]
        missing_fields = TestTab.FakeTab.get_missing_fields(tabs)
        assert len(missing_fields) == len(TestTab.FakeTab.CONTAINS)

    def test_all_missing_fields_with_other_existing(self):
        tabs = [
            {"predefined_uuid": "1"},
            {"predefined_uuid": "2"},
            {"predefined_uuid": "42",
             "fields": [
                 Datatable("unrelated").as_dto()
             ]
            }
        ]
        missing_fields = TestTab.FakeTab.get_missing_fields(tabs)
        assert len(missing_fields) == len(TestTab.FakeTab.CONTAINS)

    def test_one_missing_field(self):
        tabs = [
            {"predefined_uuid": "1"},
            {"predefined_uuid": "2"},
            {"predefined_uuid": "42",
             "fields": [
                 Datatable("test_table1").as_dto()
             ]
            }
        ]
        tab = TestTab.FakeTab.get_from_tabs(tabs)
        missing_fields = TestTab.FakeTab.get_missing_fields(tabs)
        assert len(missing_fields) == len(TestTab.FakeTab.CONTAINS)-1
        assert not Datatable("test_table1").exists_in(missing_fields)

    def test_one_missing_field_with_extra_fields(self):
        tabs = [
            {"predefined_uuid": "1"},
            {"predefined_uuid": "2"},
            {"predefined_uuid": "42",
             "fields": [
                 Datatable("test_table1").as_dto(),
                 Datatable("unrelated").as_dto()
             ]
            }
        ]
        tab = TestTab.FakeTab.get_from_tabs(tabs)
        missing_fields = TestTab.FakeTab.get_missing_fields(tabs)
        assert len(missing_fields) == len(TestTab.FakeTab.CONTAINS)-1
        assert not Datatable("test_table1").exists_in(missing_fields)
