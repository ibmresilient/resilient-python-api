#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

"""Methods and classes for manipulating patch-related elements for the Resilient REST API"""

class Change(object):
    """Represents a change in a Patch object."""
    def __init__(self, field_name, new_value, old_value):
        self.field_name = field_name
        self.new_value = new_value
        self.old_value = old_value

    def to_dict(self):
        """Creates a DTO/dict object from this change."""
        return dict(field = self.field_name, new_value = self.new_value, old_value = self.old_value)

class Patch(object):
    """Represents a patch to be applied to an object on the server."""
    def __init__(self, previous_object, version = None):
        """ previous_object: The last known state of the object being patched.  You can supply None here, but
                             if you do that then you'll need to provide old_value in your calls to add_value.
            version: The last known version of the object being patched.  If omitted then the 'vers' item in
                     the passed in previous_object will be used.  If one doesn't exist there then the version
                     won't be passed to the server."""
        self.previous_object = previous_object

        if version:
            self.version = version
        elif "vers" in previous_object:
            # if the object contains a "vers" field, then use it.
            self.version = previous_object["vers"]
        else:
            self.version = None

        # Keep the changes ordered.  Really this just simplifies testing a little bit with no perceivable
        # downside.
        self.changes = collections.OrderedDict()

    def _get_old_value(self, field_name):
        """Helper to get the 'old value' for a field from the previous_object passed into our constructor."""
        if not self.previous_object:
            raise ValueError("Constructor previous_object or method old_value argument is required")

        val = self.previous_object

        parts = field_name.split(".")

        for part in parts:
            if part not in val:
                val = None
                break

            val = val[part]

        if isinstance(val, dict):
            raise ValueError("Invalid field_name parameter")

        return val

    def add_value(self, field_name, new_value, old_value=None):
        """Adds a value to the patch.

           field_name: The name of the field.
           new_value: The value to add to the patch.
           old_value: The last known value of the field being patched.  If omitted then we'll pull the old
                      value from the previous_object that you passed into the constructor."""

        if not old_value:
            old_value = self._get_old_value(field_name)

        self.changes[field_name] = Change(field_name, new_value, old_value)

    def _get_change_with_field_named(self, field_name):
        """Helper to find an existing change in the list of changes."""
        if field_name in self.changes:
            return self.changes[field_name]

        return None

    def update_for_overwrite(self, patch_status_dict):
        """Changes to patch to reflect the current values in patch_status_dict.  Use this method if you want to
        re-apply a patch operation that failed because of field conflicts...without concern with the previous
        values.
           patch_status_dict: The return from the patch operation.  It is assumed that this has a "field_failures"
                              property."""
        if not "field_failures" in patch_status_dict:
            raise ValueError("Expected field_failures in patch status return")

        failures = patch_status_dict["field_failures"]

        for failure in failures:
            field_name = failure["field"]

            change = self._get_change_with_field_named(field_name)

            if not change:
                raise ValueError("No change exists for field failure found in patch status")

            change.old_value = failure["actual_current_value"]

    def to_dict(self):
        """Converts this patch object to a dict that can be posted to the server."""
        changes = []

        for field_name, change in self.changes.iteritems():
            changes.append(change.to_dict())

        patch = dict(changes = changes)

        if self.version:
            patch["version"] = self.version

        return patch

