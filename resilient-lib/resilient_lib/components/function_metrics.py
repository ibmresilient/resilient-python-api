# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

from datetime import datetime
import platform
import pkg_resources  # part of setuptools

METRICS_VERSION = "1.0"

class FunctionMetrics:
    """
    Use this function to track metrics on the function's operation. It tracks information on the package,
    it's environment and the execution time
    """

    def finish(self):
        """ build out the final metrics data structure """
        self.end_time = datetime.now()

        ttl_time = self.end_time - self.start_time

        try:
            # get information about the package we're running
            pkg = pkg_resources.get_distribution(self.func)
        except pkg_resources.DistributionNotFound:
            pkg = MissingPkg()

        return {
            "version": METRICS_VERSION,
            "package": pkg.project_name,
            "package_version": pkg.version,
            "host": platform.node(),
            "execution_time_ms": int(ttl_time.total_seconds() * 1000),
            "timestamp": self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __init__(self, func):
        self.start_time = datetime.now()
        self.func = func


class MissingPkg:
    """ mock package use when the package name provided isn't found """
    project_name = "unknown"
    version = "unknown"

