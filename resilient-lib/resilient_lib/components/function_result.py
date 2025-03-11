# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import json
from .function_metrics import FunctionMetrics, LowCodeMetrics

PAYLOAD_VERSION = "1.0"

class ResultPayload:
    """ Class to create a standard payload for functions. The resulting payload follows the following format:
        1.0
        { "version": "1.0"       -- used to track different versions of the payload
          "success": True|False
          "reason": str          -- a string to explain if success=False
          "content": json        -- the result of the function call
          "raw": str             -- a string representation of content. This is sometimes needed when the result of one function is
                                    piped into the next
          "inputs": json         -- a copy of the input parameters, useful for post-processor script use
          "metrics": json        -- a set of information to capture specifics metrics about the function's runtime environment
        }
    """
    def __init__(self, pkgname, version=PAYLOAD_VERSION, **kwargs):
        """
        build initial payload data structure and the start the timers for metrics collection
        :param pkgname: package name to capture stats on which package is being used
        :param kwargs: input parameters for this function
        """
        self.metrics = FunctionMetrics(pkgname)
        self.fm = self.metrics # for backward compatibility, but using `.metrics` going forward
        self.payload = {
            "version": version,
            "success": None,
            "reason":  None,
            "content": None,
            "raw": None,
            "inputs":  kwargs,
            "metrics": None
        }

    def done(self, success, content, reason=None):
        """
         complete the function payload
        :param success: True|False
        :param content: json result to pass back
        :param reason: comment fields when success=False
        :return: completed payload in json
        """
        self.payload["success"] = success
        self.payload["reason"] = reason
        self.payload["content"] = content
        self.payload["metrics"] = self.metrics.finish()

        if float(self.payload.get("version", 2.0)) < 2.0:
            try:
                self.payload["raw"] = ""
            except:
                pass

        return self.payload

class LowCodePayload(ResultPayload):
    """
    Low code payload. Very similar to function ResultPayload

    Payload schema :

    .. code-block::

        request_originator:
          "$ref": "#/components/schemas/RequestOriginatorDTO"
        version:
          type: string
        status_code:
          type: integer
          format: int32
          description: "Rest API invocation http status code."
        success:
          type: boolean
          description: "Rest API invocation is successful or not."
        content:
          type: string
          description: "The rest api response content value."
        content_type:
          type: string
          description: "The rest api response content type. e.g., application/json"
        reason:
          type: string
          description: "The reason if the rest api invocation is failed."
        metrics:
          "$ref": "#/components/schemas/ResponseMetricsDTO"

    """

    def __init__(self, pkgname, version, **kwargs):
        self.metrics = LowCodeMetrics(pkgname)
        self.payload = {
            "request_originator": kwargs.get("request_originator"),
            "version": version
        }

    def done(self, success, content, status_code=None, reason=None, content_type=None):
        """
        The low code function is complete. If unsuccessful, give a reason.
        Set the success value, content, and reason (if success=False).
        Also build the payload object and finish measuring the metrics.

        :param success: True|False
        :param content: string of json result to pass back
        :param reason: comment fields when success=False
        :param content_type: request_payload.response_content_type result
        :return: completed payload in json
        """
        self.payload["success"] = success
        self.payload["reason"] = reason
        self.payload["status_code"] = status_code
        self.payload["content"] = content
        self.payload["content_type"] = content_type
        self.payload["metrics"] = self.metrics.finish()

        return self.payload
