#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import copy

from resilient_circuits.component_loader import ComponentLoader
from resilient_circuits import constants, helpers
from importlib.metadata import EntryPoint
from mock import patch
from tests import mock_constants, mock_paths


class TestComponentLoader:

    def test_discover_installed_components_with_inbound_app(self):
        found = False

        cmp_loader_opts = copy.deepcopy(mock_constants.MOCK_OPTS)
        cmp_loader_opts["componentsdir"] = mock_paths.SHARED_MOCK_DATA_DIR

        with patch("resilient_circuits.component_loader.iter_entry_points") as mock_entry_points:
            mock_entry_points.return_value = [EntryPoint(group="resilient.circuits.components", name="mock_component", value="mock_component:MockInboundAppComponent")]
            cmp_loader = ComponentLoader(cmp_loader_opts)
            installed_cmps = cmp_loader.discover_installed_components("resilient.circuits.components")

            assert len(installed_cmps) > 0

            for c in installed_cmps:
                if c.__module__ == "mock_component":
                    found = True

            assert found is True

    def test_installed_components_with_custom_inbound_q(self):
        found = False
        custom_q_name = "mock_inbound_custom_q"

        cmp_loader_opts = copy.deepcopy(mock_constants.MOCK_OPTS)
        cmp_loader_opts["componentsdir"] = mock_paths.SHARED_MOCK_DATA_DIR

        cmp_loader_opts["mock_component"] = {}
        cmp_loader_opts["mock_component"][constants.INBOUND_MSG_APP_CONFIG_Q_NAME] = custom_q_name

        with patch("resilient_circuits.component_loader.iter_entry_points") as mock_entry_points:
            mock_entry_points.return_value = [EntryPoint(group="resilient.circuits.components", name="mock_component", value="mock_component:MockInboundAppComponent")]
            cmp_loader = ComponentLoader(cmp_loader_opts)
            installed_cmps = cmp_loader.discover_installed_components("resilient.circuits.components")

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
