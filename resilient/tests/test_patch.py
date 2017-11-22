# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
from __future__ import print_function
import pytest
import resilient


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
        assert change["old_value"]["object"] == 1
        assert change["new_value"]["object"] == 5

        change = changes[1]
        assert change["field"] == "properties.b"
        assert change["old_value"]["object"] == 2
        assert change["new_value"]["object"] == 6

        change = changes[2]
        assert change["field"] == "c"
        assert not change["old_value"]["object"]
        assert change["new_value"] ["object"]== 7

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
        assert changes[0]["old_value"]["object"]== 3
        assert changes[0]["new_value"]["object"] == 5

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
        assert changes[0]["old_value"]["object"] == 5
        assert changes[0]["new_value"]["object"] == 8

    def test_null_old_value(self):
        patch = resilient.Patch({"blah": "old value"})

        patch.add_value("blah", "new value", old_value=None)

        mydict = patch.to_dict()

        assert mydict

        changes = mydict["changes"]

        assert changes

        assert len(changes) == 1
        assert changes[0]["field"] == "blah"
        assert not changes[0]["old_value"]["object"]
        assert changes[0]["new_value"]["object"]== "new value"

    def test_has_changes(self):
        patch = resilient.Patch(dict(testfield=1))

        assert not patch.has_changes()

        patch.add_value("testfield", 5)

        assert patch.has_changes()

    def test_delete(self):
        patch = resilient.Patch(dict(a=1, b=2))

        assert not patch.has_changes()

        patch.add_value("a", 11)

        assert patch.has_changes()

        assert patch.get_old_value("a") == 1
        assert patch.get_new_value("a") == 11

        patch.delete_value("a")

        assert not patch.has_changes()


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

    def test_exchange_conflicting_value(self):
        # Given a base object with a value of "test1".
        base = dict(mytest1 = "test1")

        # And a patch that is attempting to modify that base object to have a value of "test2".
        patch = resilient.Patch(base)

        patch.add_value("mytest1", "test2")

        # Confirm that it does indeed have an "old value" of "test1" (this is taken from the base object).
        assert patch.get_old_value("mytest1") == "test1"

        # When we create a patch status that simulates a conflict error from the server (where the
        # value of base changed from "test1" to "blah").
        patch_status = resilient.PatchStatus({
            "success": False,
            "field_failures": [
                {
                    "field": "mytest1",
                    "your_original_value": "test2",
                    "actual_current_value": "blah"
                }
            ],
            "message": "Some message"
        })

        # When I exchange the conflicting value...
        patch.exchange_conflicting_value(patch_status, "mytest1", "test2")

        # The patch's "old value" will be the current server's value.
        assert patch.get_old_value("mytest1") == "blah"
        assert patch.get_new_value("mytest1") == "test2"




