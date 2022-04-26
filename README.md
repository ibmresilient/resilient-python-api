![IBM Security](https://raw.githubusercontent.com/ibmresilient/resilient-python-api/master/resilient-sdk/assets/IBM_Security_lockup_pos_RGB.png)

# IBM SOAR Python APIs

This directory contains

 * [resilient](./resilient), the `resilient` Python Client Module for the IBM SOAR platform APIs.
 * [resilient-circuits](./resilient-circuits), an application framework for SOAR Action Module.
 * [resilient-lib](./resilient-lib), a package with common library calls which facilitate the development of functions for IBM SOAR.
* [resilient-sdk](./resilient-sdk), a CLI tool for app development including code generation, code validation, documentation generation, and exporting SOAR appliance components such as scripts, rules, playbooks, custom fields, etc.

See more details of usage and examples for these packages at our [docs](https://ibm.biz/soar-python-docs).


## Certificates

In order to connect to the SOAR server, if the server
doesn't have a trusted TLS certificate, you must provide the server's
certificate in a file (e.g. "cacerts.pem").  The quickest way to do this
is to use either `openssl` or the Java `keytool` command line utilities.

Using openssl to create the cacerts.pem file (using Linux or Mac OS):
```
openssl s_client -connect SERVER:443 -showcerts -tls1 < /dev/null > cacerts.pem 2> /dev/null
```

Using keytool to create the cacerts.pem file (Linux, Mac OS or Windows):
```
keytool -printcert -rfc -sslserver SERVER:443 > cacerts.pem
```

WARNING:  In a production setting, you should take care to get the certificate
from a trusted source and confirm its fingerprint.

When connecting to a SOAR server with the Python libraries,
the hostname you specify must match exactly the name in the server
certificate.  If there is a mismatch, the permanent solution is to either
change your DNS server or change the server certificate so it matches. It is
also possible to modify your 'hosts' file temporarily, but that is not a permanent
solution.



# Contributing

Please report issues using the [Issues](https://github.com/ibmresilient/resilient-python-api/issues) tab on GitHub.

Contributions are welcome.  Please read the [CONTRIBUTING](CONTRIBUTING.md) guidelines for more about the process.


# Open Source @ IBM

[Find more open source projects on the IBM Github Page](http://ibm.github.io/)

