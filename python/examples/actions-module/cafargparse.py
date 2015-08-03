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

"""Parser for commandline arguments to the Actions Module samples"""

import co3


class CafArgumentParser(co3.ArgumentParser):
    """Arguments for STOMP connection"""

    DEFAULT_PORT = 65001

    def __init__(self):
        super(CafArgumentParser, self).__init__(config_file="samples.config")

        default_stomp_host = self.getopt("resilient", "shost")
        default_stomp_port = self.getopt("resilient", "sport") or self.DEFAULT_PORT

        self.add_argument('--shost',
                          default=default_stomp_host,
                          help="STOMP host name (default is to use the value specified in --host)")

        self.add_argument('--sport',
                          type=int,
                          default=default_stomp_port,
                          help="STOMP port number")

        self.add_argument('destination',
                          nargs=1,
                          help="The destination to connect to (e.g. actions.201.test)")


    def parse_args(self, args=None, namespace=None):
        args = super(CafArgumentParser, self).parse_args(args, namespace)

        if not args.shost:
            args.shost = args.host

        return args
