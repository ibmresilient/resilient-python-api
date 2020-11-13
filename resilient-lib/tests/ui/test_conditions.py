import pytest
from mock import patch
from resilient_lib.ui import Field, Tab
import uuid

class TestConditions(object):
    def test_can_initialize(self):
        assert Field('test').conditions is not None
        assert Field('test').conditions.has_value() is not None
        assert Field('test').conditions.equals("test") is not None
    
    def test_conditions_added_to_dto(self):
        class TestTab(Tab):
            NAME = "test_tab"
            UUID = uuid.uuid4()
            SECTION = "fn_test"
            
            CONTAINS = [Field("test")]
            SHOW_IF = [Field("test").conditions.contains("value")]
        
        assert TestTab.as_dto()['show_if'] == TestTab.SHOW_IF
