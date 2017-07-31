from __future__ import print_function
import pytest
from co3 import Patch

class TestPatch:
    def test_patch(self):
        existing = {"a": 1, "properties": {"b": 2}, "vers": 99}

        patch = Patch(existing)

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
        patch = Patch(existing)

        with pytest.raises(ValueError) as exception_info:
            patch.add_value("properties", 99)

        assert "Invalid field_name parameter" in str(exception_info.value)

    def test_no_old_value(self):
        patch = Patch({})

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
        patch = Patch({"a": 5})

        patch.add_value("a", 7)
        patch.add_value("a", 8)

        dict = patch.to_dict()

        changes = dict["changes"]

        assert len(changes) == 1

        assert changes[0]["field"] == "a"
        assert changes[0]["old_value"] == 5
        assert changes[0]["new_value"] == 8
