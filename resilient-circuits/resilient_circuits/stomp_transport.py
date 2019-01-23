# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.
""" stompest StompFrameTransport allowing for ssl.wrap_socket """

import logging
import ssl
import socket
import re
from stompest.sync.transport import StompFrameTransport
from stompest.error import StompConnectionError

LOG = logging.getLogger(__name__)

class RedactingFilter(logging.Filter):
    """ Redacting logging filter to prevent Resilient circuits passcode value from being logged.

    """
    def __init__(self):
        super(RedactingFilter, self).__init__()

    def filter(self, record):
        if re.search("passcode", record.msg):
            record.msg = re.sub(r"(.*'passcode':\s+)(.+?)(,\s+.*)", r"\1***\3", record.msg)
        return True

class EnhancedStompFrameTransport(StompFrameTransport):
    """ add support for older ssl module and http proxy """

    proxy_host = None
    proxy_port = None
    proxy_user = None
    proxy_password = None

    @staticmethod
    def match_hostname(cert, hostname):
        """ Check that hostname matches cert """
        names = []
        # Python 3 has an ssl.match_hostname method, which does hostname validation.
        try:
            ssl.match_hostname(cert, hostname)
            return
        except AttributeError as err:
            # We don't have the backported python 3 ssl module, do a simplified check
            for sub in cert.get('subject', ()):
                for key, value in sub:
                    if key == 'commonName':
                        names.append(value)
                        if value == hostname:
                            return
        raise Exception("{0} does not match the expected value in the certificate {1}".format(hostname, str(names)))

    def connect(self, timeout=None):
        """ Allow older versions of ssl module, allow http proxy connections """
        LOG.debug("stomp_transport.connect()")

        # Pre-instantiate logger for "stompest.sync.client" and add Redacting filter
        # to prevent passcode value from being logged.
        logging.getLogger("stompest.sync.client").addFilter(RedactingFilter())

        ssl_params = None
        if isinstance(self.sslContext, dict):
            # This is actually a dictionary of ssl parameters for wrapping the socket
            ssl_params = self.sslContext
            self.sslContext = None

        try:
            if self.proxy_host:
                LOG.info("Connecting through proxy %s", self.proxy_host)
                import socks
                self._socket = socks.socksocket()
                self._socket.set_proxy(socks.HTTP, self.proxy_host, self.proxy_port, True,
                                       username=self.proxy_user, password=self.proxy_password)
            else:
                self._socket = socket.socket()

            self._socket.settimeout(timeout)
            self._socket.connect((self.host, self.port))

            if ssl_params:
                # For cases where we don't have a modern SSLContext (so no SNI)
                cert_required = ssl.CERT_REQUIRED if ssl_params["ca_certs"] else ssl.CERT_NONE
                self._socket = ssl.wrap_socket(
                    self._socket,
                    keyfile=ssl_params['key_file'],
                    certfile=ssl_params['cert_file'],
                    cert_reqs=cert_required,
                    ca_certs=ssl_params['ca_certs'],
                    ssl_version=ssl_params['ssl_version'])
                if cert_required:
                    LOG.info("Performing manual hostname check")
                    cert = self._socket.getpeercert()
                    self.match_hostname(cert, self.host)

            if self.sslContext:
                self._socket = self.sslContext.wrap_socket(self._socket, server_hostname=self.host)

        except IOError as e:
            raise StompConnectionError('Could not establish connection [%s]' % e)
        self._parser.reset()
