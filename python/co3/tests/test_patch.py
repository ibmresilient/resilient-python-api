from __future__ import print_function
import pytest
import co3 as resilient

class TestPatch:
    def test_patch(self):
        existing = {"a": 1, "properties": {"b": 2}, "vers": 99}

        patch = resilient.Patch(existing)

        patch.add_value("a", 5)
        patch.add_value("properties.b", 6)
        patch.add_value("c", 7)

        dto = patch.to_dict()

        assert dto["version"] == 99

        changes = dto["changes"]

        assert len(changes) == 3

        change = changes[0]
        assert change["field"] == "a"
        assert change["old_value"] == 1
        assert change["new_value"] == 5

        change = changes[1]
        assert change["field"] == "properties.b"
        assert change["old_value"] == 2
        assert change["new_value"] == 6

        change = changes[2]
        assert change["field"] == "c"
        assert not change["old_value"]
        assert change["new_value"] == 7

    def test_partial_property_name(self):
        existing = {"properties": {"a": 5}}
        patch = resilient.Patch(existing)

        with pytest.raises(ValueError) as exception_info:
            patch.add_value("properties", 99)

        assert "Invalid field_name parameter" in str(exception_info.value)

    def test_no_old_value(self):
        patch = resilient.Patch({})

        # this one is allowed
        patch.add_value("a", new_value=5, old_value=3)

        dto = patch.to_dict()

        changes = dto["changes"]

        assert len(changes) == 1
        assert changes[0]["field"] == "a"
        assert changes[0]["old_value"] == 3
        assert changes[0]["new_value"] == 5

        with pytest.raises(ValueError) as exception_info:
            patch.add_value("b", new_value=10)

        assert "Constructor previous_object or method old_value argument is required" in str(exception_info.value)

    def test_add_twice(self):
        patch = resilient.Patch({"a": 5})

        patch.add_value("a", 7)
        patch.add_value("a", 8)

        mydict = patch.to_dict()

        changes = mydict["changes"]

        assert len(changes) == 1

        assert changes[0]["field"] == "a"
        assert changes[0]["old_value"] == 5
        assert changes[0]["new_value"] == 8

    def test_null_old_value(self):
        patch = resilient.Patch({"blah": "old value"})

        patch.add_value("blah", "new value", old_value=None)

        mydict = patch.to_dict()

        assert mydict

        changes = mydict["changes"]

        assert changes

        assert len(changes) == 1
        assert changes[0]["field"] == "blah"
        assert not changes[0]["old_value"]
        assert changes[0]["new_value"] == "new value"

class TestPatchStatus:
    @pytest.mark.parametrize("success", (True, False))
    def test_success(self, co3_args, success):
        test_data = {
            "success": success
        }

        status = resilient.PatchStatus(test_data)

        assert status.is_success() == success

    @staticmethod
    def _make_test_data():
        return {
            "success": False,
            "field_failures": [
                {
                    "field": "mytest1",
                    "your_original_value": "original1",
                    "actual_current_value": "current1"
                }, {
                    "field": "mytest2",
                    "your_original_value": "original2",
                    "actual_current_value": "current2"
                }
            ],
            "message": "Some message"
        }

    def test_has_failures(self):
        status = resilient.PatchStatus(TestPatchStatus._make_test_data())

        assert not status.is_success()
        assert status.has_field_failures()
        assert status.get_conflict_fields() == ["mytest1", "mytest2"]

        assert status.is_conflict_field("mytest1")
        assert status.is_conflict_field("mytest2")

        assert not status.is_conflict_field("blah")

    def test_values(self):
        status = resilient.PatchStatus(TestPatchStatus._make_test_data())

        assert status.get_your_original_value("mytest1") == "original1"
        assert status.get_actual_current_value("mytest1") == "current1"

        assert status.get_your_original_value("mytest2") == "original2"
        assert status.get_actual_current_value("mytest2") == "current2"

    def test_field_name_found(self):
        status = resilient.PatchStatus(TestPatchStatus._make_test_data())

        with pytest.raises(ValueError) as exception_info:
            status.get_your_original_value("blah")

        assert "No conflict found for field blah" in str(exception_info.value)

        with pytest.raises(ValueError) as exception_info:
            status.get_your_original_value("blah")

        assert "No conflict found for field blah" in str(exception_info.value)

    def test_message(self):
        status = resilient.PatchStatus(TestPatchStatus._make_test_data())

        assert status.get_message() == "Some message"

