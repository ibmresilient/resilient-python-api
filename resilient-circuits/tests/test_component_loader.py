#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
import copy
from resilient_circuits.component_loader import ComponentLoader
from resilient_circuits import constants, helpers
from tests import mock_constants, mock_paths


class TestComponentLoader:

    @pytest.mark.parametrize("ep_str", ["mock_component:MockInboundAppComponent"])
    @pytest.mark.parametrize("path_dist", [mock_paths.SHARED_MOCK_DATA_DIR])
    def test_discover_installed_components_with_inbound_app(self, fx_add_entry_point):
        found = False

        cmp_loader_opts = copy.deepcopy(mock_constants.MOCK_OPTS)
        cmp_loader_opts["componentsdir"] = mock_paths.SHARED_MOCK_DATA_DIR

        cmp_loader = ComponentLoader(cmp_loader_opts)
        installed_cmps = cmp_loader.discover_installed_components()

        assert len(installed_cmps) > 0

        for c in installed_cmps:
            if c.__module__ == "mock_component":
                found = True

        assert found is True

    @pytest.mark.parametrize("ep_str", ["mock_component:MockInboundAppComponent"])
    @pytest.mark.parametrize("path_dist", [mock_paths.SHARED_MOCK_DATA_DIR])
    def test_installed_components_with_custom_inbound_q(self, fx_add_entry_point):
        found = False
        custom_q_name = "mock_inbound_custom_q"

        cmp_loader_opts = copy.deepcopy(mock_constants.MOCK_OPTS)
        cmp_loader_opts["componentsdir"] = mock_paths.SHARED_MOCK_DATA_DIR

        cmp_loader_opts["mock_component"] = {}
        cmp_loader_opts["mock_component"][constants.INBOUND_MSG_APP_CONFIG_Q_NAME] = custom_q_name

        cmp_loader = ComponentLoader(cmp_loader_opts)
        installed_cmps = cmp_loader.discover_installed_components()

        assert len(installed_cmps) > 0

        for c in installed_cmps:
            if c.__module__ == "mock_component":

                inbound_handlers = helpers.get_handlers(c, handler_type="inbound_handler")
                assert len(inbound_handlers) > 0

                for ih in inbound_handlers:
                    if ih[0] == "_inbound_app_mock_one":
                        found = True
                        assert ih[1].channel == "{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, custom_q_name)

        assert found is True
