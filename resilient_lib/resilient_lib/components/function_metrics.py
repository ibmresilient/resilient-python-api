# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2018. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

from datetime import datetime
import platform
import pkg_resources  # part of setuptools

class FunctionMetrics:
    """
    Use this function to track metrics on the function's operation. It tracks information on the package,
    it's environment and the execution time
    """

    def finish(self):
        self.end_time = datetime.now()

        ttl_time = self.end_time - self.start_time

        # get information about the package we're running
        pkg = pkg_resources.get_distribution(self.func)

        return {
            "package": pkg.project_name,
            "version": pkg.version,
            "host": platform.node(),
            "execution_time_ms": int(ttl_time.total_seconds() * 1000),
            "timestamp": self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __init__(self, func):
        self.start_time = datetime.now()
        self.func = func

