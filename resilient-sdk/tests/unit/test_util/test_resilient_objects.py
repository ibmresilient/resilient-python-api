#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from resilient_sdk.util.resilient_objects import ResilientObjMap, ResilientTypeIds, ResilientFieldTypes


def test_resilient_obj_map():

    assert ResilientObjMap.MESSAGE_DESTINATIONS == "programmatic_name"
    assert ResilientObjMap.FUNCTIONS == "export_key"
    assert ResilientObjMap.WORKFLOWS == "programmatic_name"
    assert ResilientObjMap.RULES == "name"
    assert ResilientObjMap.FIELDS == "name"
    assert ResilientObjMap.INCIDENT_ARTIFACT_TYPES == "programmatic_name"
    assert ResilientObjMap.DATATABLES == "type_name"
    assert ResilientObjMap.TASKS == "programmatic_name"
    assert ResilientObjMap.PHASES == "export_key"
    assert ResilientObjMap.SCRIPTS == "export_key"


def test_resilient_type_ids():

    assert ResilientTypeIds.INCIDENT == 0
    assert ResilientTypeIds.TASK == 1
    assert ResilientTypeIds.NOTE == 2
    assert ResilientTypeIds.MILESTONE == 3
    assert ResilientTypeIds.ARTIFACT == 4
    assert ResilientTypeIds.ATTACHMENT == 5
    assert ResilientTypeIds.ACTION_INVOCATION == 6
    assert ResilientTypeIds.ORG == 7
    assert ResilientTypeIds.DATATABLE == 8
    assert ResilientTypeIds.LAYOUT == 9
    assert ResilientTypeIds.MESSAGE_DESTINATION == 10
    assert ResilientTypeIds.FUNCTION == 11


def test_resilient_field_types():

    assert ResilientFieldTypes.ACTIVITY_FIELD == "actioninvocation"
    assert ResilientFieldTypes.FUNCTION_INPUT == "__function"
