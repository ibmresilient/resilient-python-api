# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.
# pragma pylint: disable=line-too-long

import logging
import re
from six import string_types, PY3
from resilient_circuits import constants

class RedactingFilter(logging.Filter):
    """ Redacting logging filter to prevent Resilient circuits sensitive password values from being logged.

    """
    def __init__(self):
        super(RedactingFilter, self).__init__()

        pattern = "|".join(constants.PASSWORD_PATTERNS)

        # see https://regex101.com/r/ssoH91 for detailed test
        # this is the more performant version where only one regex is checked
        self.redact_regex = re.compile(r"""
            ((?:{0})       # start capturing group for password pattern from constants.PASSWORD_PATTERNS
            \w*?[\'\"]?    # match any word characters (lazy) and zero or one quotation marks
            \W*?u?[\'\"]   # match any non-word characters (lazy) up until exactly one quotation mark
                            # and potentially a u'' situation for PY27
                            # (this quotation mark indicates the beginning of the secret value)
            )              # end first capturing group
            (.*?)          # capture the problematic content (lazy capture up until end quotation mark)
            ([\'\"])       # capturing group to end the regex match
        """.format(pattern), re.X | re.I)

    def filter(self, record):
        try:
            if record.args:
                record.args = tuple(self.redact_regex.sub(r"\1***\3", str(arg)) for arg in record.args)
            else:
                record.msg = self.redact_regex.sub(r"\1***\3", str(record.msg))
            # The stomp.py library we use can leak passwords in the frame logs in certain situations.
            # We can remove those by checking for the "sending frame" log message
            # and then rendering the message to check if the passcode value is included.
            # If so, then return False thus skipping this log record
            if "sending frame:" in record.msg:
                if "passcode" in record.getMessage():
                    return False
        except Exception as err:
            return True

        return True
