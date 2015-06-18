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

import argparse
import getpass

class ArgumentParser(argparse.ArgumentParser):
  """Helper to parse common Resilient command line arguments.

  It is expected that a command line utility that needs to work with a Resilient
  server will create its own class that inherits this class.  Its __init__
  method will call self.add_argument as necessary.

  See https://docs.python.org/3/library/argparse.html for more details.
  """

  DEFAULT_PORT = 443

  def __init__(self):
    super(ArgumentParser, self).__init__()

    self.add_argument("--email", 
      required = True,
      help = "The email address to use to authenticate to the Resilient server.")

    self.add_argument("--password", 
      help = "WARNING:  This is an insecure option since the password "
             "will be visible to other processes and stored in the "
             "command history.  The password to use to authenticate "
             "to the Resilient server.  If omitted, the you will be prompted.")

    self.add_argument('--host', 
      required = True,
      help = "Resilient server host name")

    self.add_argument('--port', 
      default = self.DEFAULT_PORT,
      help = "Resilient server port number")

    self.add_argument("--proxy",
      nargs = "*",
      help = "An optional HTTP proxy to use when connecting.")

    self.add_argument("--org",
      help = "The name of the organization to use.  If you are a member "
             "of just one organization, then you can omit this argument.")

    self.add_argument("--cafile",
      help = "The name of a file that contains trusted certificates.")

  def parse_args(self):
    args = super(ArgumentParser, self).parse_args()

    password = args.password

    while not password:
      password = getpass.getpass()

    args.password = password

    return args
