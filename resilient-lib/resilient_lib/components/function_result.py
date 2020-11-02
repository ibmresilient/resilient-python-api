# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import json
from .function_metrics import FunctionMetrics

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
    def __init__(self, pkgname, **kwargs):
        """
        build initial payload data structure and the start the timers for metrics collection
        :param pkgname: package name to capture stats on which package is being used
        :param kwargs: input parameters for this function
        """
        self.fm = FunctionMetrics(pkgname)
        self.payload = {
            "version": PAYLOAD_VERSION,
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
        self.payload['success'] = success
        self.payload['reason'] = reason
        self.payload['content'] = content
        self.payload['metrics'] = self.fm.finish()

        try:
            self.payload['raw'] = json.dumps(content)
        except:
            pass

        return self.payload
