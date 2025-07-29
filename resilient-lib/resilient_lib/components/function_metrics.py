# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

from datetime import datetime
import platform
import importlib

METRICS_VERSION = "1.0"
LOW_CODE_METRICS_VERSION = "2.0"

class FunctionMetrics:
    """
    Use this function to track metrics on the function's operation. It tracks information on the package,
    it's environment and the execution time
    """

    def finish(self):
        """ build out the final metrics data structure """
        self.end_time = datetime.now()

        total_time = self.end_time - self.start_time

        try:
            # get information about the package we're running
            pkg_version = importlib.metadata.version(self.func)
            pkg_project_name = importlib.metadata.Distribution.from_name(self.func).name
        except importlib.metadata.PackageNotFoundError:
            pkg = MissingPkg()
            pkg_version = pkg.version
            pkg_project_name = pkg.project_name

        return {
            "version": self.version,
            "package": pkg_project_name,
            "package_version": pkg_version,
            "host": platform.node(),
            "execution_time_ms": int(total_time.total_seconds() * 1000),
            "timestamp": self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __init__(self, func):
        self.func = func
        self.start_time = datetime.now()
        self.end_time = None
        self.version = METRICS_VERSION


class LowCodeMetrics(FunctionMetrics):

    def __init__(self, func):
        super(LowCodeMetrics, self).__init__(func)
        self.version = LOW_CODE_METRICS_VERSION

    def finish(self):
        metrics = super(LowCodeMetrics, self).finish()
        del metrics["timestamp"] # LowCodeMetrics does not support timestamp in DTO
        return metrics

class MissingPkg:
    """ mock package use when the package name provided isn't found """
    project_name = "unknown"
    version = "unknown"

    def __str__(self):
        return "{0} {1}".format(self.project_name, self.version)
