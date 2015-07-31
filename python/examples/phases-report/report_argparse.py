#!/usr/bin/env python

# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Parser for commandline arguments and config properties"""

import sys
import co3
import getpass
if sys.version_info.major < 3:
    import ConfigParser as configparser
else:
    import configparser
from datetime import datetime


class ReportOpts(dict):
    """A dictionary of the commandline options"""
    def __init__(self, config, dictionary):
        super(ReportOpts, self).__init__()
        self.config = config
        if dictionary is not None:
            self.update(dictionary)

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Date must be YYYY-MM-DD: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

class ReportArgumentParser(co3.ArgumentParser):
    """Helper to parse command line arguments."""

    def __init__(self, config_file="report.config"):
        super(ReportArgumentParser, self).__init__(config_file)

        self.add_argument("--since",
                          type=valid_date,
                          help="Only report incidents created since this date (YYYY-MM-DD)")


    def parse_args(self, args=None, namespace=None):
        args = super(ReportArgumentParser, self).parse_args(args, namespace)

        return ReportOpts(self.config, vars(args))
