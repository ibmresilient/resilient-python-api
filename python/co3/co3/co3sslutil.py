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

import ssl

# Additional certificate validation function.  Called by the Python SSL library.
#
# cert is the certificate as returned by SSLSocket.getpeercert().
#
# If you're running with Python 3, we will make use of ssl.match_hostname which is consistent
# with RFC 2818.
#
# Pyton 2.7.8 and before does not have that function so we will do a
# relatively lame version of it.  It appears that ssl.match_hostname will
# appear in Python 2.7.9 and if it's available, we will use it.
#
def match_hostname(cert, hostname):
    names = []

    # Python 3 has an ssl.match_hostname method, which does hostname validation.  It will allow
    # more certificates than we do in our else clause (which is a very simplified version).
    if "match_hostname" in dir(ssl):
        ssl.match_hostname(cert, hostname)
        return
    else:
        for sub in cert.get('subject', ()):
            for key, value in sub:
                if key == 'commonName':
                    names.append(value)
                    if value == hostname:
                        return

    raise Exception("{0} does not match the expected value in the certificate {1}".format(hostname, str(names)))
