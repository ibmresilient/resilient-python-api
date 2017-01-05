"""Pytest Fixture for Testing Resilient Circuits Components"""

import os
import sys
import pytest
from circuits import Event
from conftest import manager, watcher
#from circuits import Manager

class ResilientCircuits:
    def __init__(self, tmpdir, manager, watcher, request):
        resilient_config_data = """
[resilient]
logfile = circuits.log
loglevel = DEBUG
cafile = false
email = kchurch@us.ibm.com
stomp_port = 65001
host = 192.168.56.102
org = Test
componentsdir = components
password = Pass4Admin
no_prompt_password = True
port = 443
test_actions = True
"""
        self.config_file = tmpdir.join("apptest.config")
        self.logs = tmpdir.mkdir("logs")
        config_data = getattr(request.module, "config_data", "")
        self.config_file.write(resilient_config_data)
        self.config_file.write("log_http_responses = %s\n" % self.logs, mode='a')
        self.config_file.write("logdir = %s\n" % self.logs, mode='a')
        self.config_file.write(config_data, mode='a')
        os.environ["APP_CONFIG_FILE"] = self.config_file.strpath
        from resilient_circuits.app import App

        self.manager = manager
        self.watcher = watcher

        # Remove the pytest commandline arguments so they don't break ArgParse in co3
        sys.argv=sys.argv[0:1]

        app = App().register(manager)
        manager.start()
        assert watcher.wait("registered")
        pytest.wait_for(manager, "_running", True)
        assert watcher.wait("load_all_success", timeout=10)
        def finalizer():
            app.unregister()

        request.addfinalizer(finalizer)

        self.app = app
        #self.circuits_proc = Process(target=app.run, name="reslient-circuits-pytest")
        #self.circuits_proc.daemon = True
        #self.circuits_proc.start()

@pytest.fixture#(scope="module")
def circuits_app(tmpdir, manager, watcher, request):
    return ResilientCircuits(tmpdir, manager, watcher, request)
