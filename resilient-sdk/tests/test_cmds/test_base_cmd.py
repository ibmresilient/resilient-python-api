#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.


import pytest
from argparse import ArgumentParser
from resilient_sdk.cmds.base_cmd import BaseCmd


def test_no_CMD_NAME(fx_get_sub_parser):

    class MockClass(BaseCmd):
        pass

    with pytest.raises(AssertionError):
        MockClass(fx_get_sub_parser)


def test_no_CMD_HELP(fx_get_sub_parser):

    class MockClass(BaseCmd):
        CMD_NAME = "mock"

    with pytest.raises(AssertionError):
        MockClass(fx_get_sub_parser)


def test_no_setup_method(fx_get_sub_parser):
    class MockClass(BaseCmd):
        CMD_NAME = "mock"
        CMD_HELP = "mock"

    with pytest.raises(NotImplementedError):
        MockClass(fx_get_sub_parser)


def test_get_res_obj_parser(fx_cmd_line_args_codegen_package):
    class MockClass(BaseCmd):
        CMD_NAME = "mock"
        CMD_HELP = "mock"

        def setup(self):
            pass

        def execute_command(self):
            pass

    res_obj_parser = MockClass._get_res_obj_parser()

    assert isinstance(res_obj_parser, ArgumentParser)

    args = res_obj_parser.parse_known_args()[0]

    assert args.function == ["mock_function_one"]
    assert args.messagedestination == ["fn_main_mock_integration"]
    assert args.rule == ["Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination"]
    assert args.workflow == ["mock_workflow_one", "mock_workflow_two"]
    assert args.field == ["mock_field_number", "mock_field_number", "mock_field_text_area"]
    assert args.artifacttype == ["mock_artifact_2", "mock_artifact_type_one"]
    assert args.datatable == ["mock_data_table"]
    assert args.task == ["mock_custom_task_one", "mock_cusom_task__________two"]
    assert args.script == ["Mock Script One"]


def test_parser_parents():
    # TODO
    pass


def test_get_io_parser():
    # TODO
    pass


def test_get_zip_parser():
    # TODO
    pass