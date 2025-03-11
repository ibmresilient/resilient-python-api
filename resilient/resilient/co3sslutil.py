# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
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
