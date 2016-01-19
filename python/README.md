# Python Examples (python directory)

This directory contains the Resilient Python client library
([co3](co3) subdirectory), and examples for the Resilient Actions Module
and REST APIs ([examples](examples) subdirectory).


## Co3 Python Client (python/co3 directory)

The Resilient Python Client (`co3` module) is a simple wrapper around the Python
requests module that contains tools helpful in calling the Resilient REST API
and Actions Module.

It provides a SimpleClient class that you use to call the Resilient REST API.

It provides an ArgumentParser class (which extends `argparse.ArgumentParser`) to
simplify the writing of command line utilities.  This provides support for
standard arguments such as `--host` and `--email` that Resilient-oriented
command line tools will generally need.  The ArgumentParser can read defaults
from a configuration file, and override them from the command line.


### Installing the 'co3' module

To package the 'co3' Python module for installation, use:

    python setup.py sdist --formats=gztar

This creates a single file `dist/co3-x.x.x.tar.gz` (the filename will
vary according to the current version of this repository).

Install the package file using `pip`:

    pip install co3-x.x.x.tar.gz


## Certificates

Note that in order to connect to the server, you must provide the server's
CA certificate in a file (e.g. "cacerts.pem").  The quickest way to do this
is to use either openssl or the Java keytool command line utilities.

Using openssl to create the cacerts.pem file (using Linux or Mac OS):
```
openssl s_client -connect SERVER:65001 -showcerts -tls1 < /dev/null > cacerts.pem 2> /dev/null
```
Using keytool to create the cacerts.pem file (Linux, Mac OS or Windows):
```
keytool -printcert -rfc -sslserver SERVER:65001 > cacerts.pem
```
WARNING:  In a production setting, you should take care to get the certificate
from a trusted source and confirm its fingerprint.

The host you specify with `--host` must match exactly the name in the server
certificate.  If there is a mismatch, the permanent solution is to either
change your DNS server or change the server certificate so it matches. It is
also possible to modify your hosts file temporarily, but that is not a permanent
solution.


## Resilient API Examples (python/examples directory)

The [examples](examples) directory contains several utilities and examples
that make use of the Resilient REST API and the Resilient Actions Module.

For further details, see the `README.md` supplied with each example.
