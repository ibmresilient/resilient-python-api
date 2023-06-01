#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

from resilient_app_config_plugins.plugin_base import PAMPluginInterface

class MyMockPlugin(PAMPluginInterface):
    def __init__(self, *args, **kwargs):
        pass
    def get(self, key, default=None):
        return "MOCK"
    def selftest(self):
        return True, ""

class MyBadMockPlugin(): # does not implement required Interface
    def __init__(self, *args, **kwargs):
        pass
    def get(self, key):
        return "MOCK"
    def selftest(self):
        return True, ""
