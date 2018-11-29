import json
from .function_metrics import FunctionMetrics

PAYLOAD_VERSION = "1.0"

class FunctionResult:
    def __init__(self, pkgname, **kwargs):
        self.fm = FunctionMetrics(pkgname)
        self.payload = {
            "version": PAYLOAD_VERSION,
            "success": None,
            "reason":  None,
            "content": None,
            "inputs":  kwargs,
            "metrics": None
        }

    def done(self, success, reason, content):
        self.payload['success'] = success
        self.payload['reason'] = reason
        self.payload['content'] = content
        self.payload['metrics'] = self.fm.finish()

        return self.payload
