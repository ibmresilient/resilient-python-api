#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Implementation of AppFunctionComponent"""

import logging
from resilient_circuits import ResilientComponent, handler
from resilient_lib import RequestsCommon, validate_fields

LOG = logging.getLogger(__name__)


class AppFunctionComponent(ResilientComponent):
    # TODO: write unit test for this
    def __init__(self, opts, package_name):
        super(AppFunctionComponent, self).__init__(opts)
        self.PACKAGE_NAME = package_name
        self.app_configs = validate_fields([], opts.get(package_name, {}))
        self.rc = RequestsCommon(opts=opts, function_opts=self.app_configs)

    @handler("reload")
    def _reload(self, event, opts):
        """TODO"""
        self.app_configs = validate_fields([], opts.get(self.PACKAGE_NAME, {}))
