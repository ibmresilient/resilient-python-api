# Sample Custom Threat Service

This sample serves to illustrate how to go about writing a service that meets the criteria for a Custom Threat Service which can be integrated into a Resilient Systems installation.

## Technologies Used

The sample is written in Python using Django and the Django REST Framework (DRF).

The core code lies in the `threats` app which searches sources of threat information and adds them into its database. The initial response will contain any responses from the local database immediately, and will spawn any other sources registered to search their information store asynchronously and insert any newly found information into the local database.

Subsequent searches with matched id (as returned by initial search) will exclusively gather their information from the local database - as more data is populated by the threaded operations from the other sources.

In this example, we currently have one source built (in `sources` app) which searches known phishing-sites information within the `verified_online.csv` file. Currently this is a sample file in the same format as is freely downloadable from phishtank.com.

_The local database is configured as a sqlite database, but one can change the database engine to use by editing/overriding the `DATABASES` setting._

## Installation

It is recommended that one sets up a virtual environment (see https://virtualenvwrapper.readthedocs.org/en/latest/) in which to host the application so that any other python environment is kept clean of requirements that are installed herein. Follow the instructions and create a virtual environment:
e.g.
`$ mkvirtualenv custom_threat_feed`

### Install steps

1. Fetch the sources and change your working directory to the `custom_threat_service` top-level directory.
2. Install the dependencies using `$ pip install -r requirements.txt`
3. Create your database by running `$ ./manage.py syncdb`
    _Notice that standard django admin/authentication apps are in place to allow records to be inserted manually locally for testing purposes_
4. Run the tests to ensure that your environment is good to go `$ ./manage.py test`
5. Run the server using the command `$ ./manage.py runserver` _(assuming the tests pass in step 4)_

The server will now be running over http on port 8000 - to run on a different port pass the port number in the command line - e.g. to run the server on port 4000 execute `./manage.py runserver 4000`

With the help of DRF, you can also make test requests to the service via a browser - navigate to http://localhost:8000, DRF wraps the calls around a user interface in order to aid debugging at the endpoint level.

`curl` is also a good way to test the service from the command line - e.g. try the following set of commands:
```
$ curl --request OPTIONS 'http://localhost:8000/'
$ curl --request POST --header "Content-Type: application/json" --data-binary '{"type": "net.uri", "value": "www.megastore.lu" }' 'http://localhost:8000/'
$ curl 'http://localhost:8000/artifact_id'
```

(Replace `artifact_id` in the 3rd call with the id returned from the 2nd call)

### Sample Configuration with nginx

Once one has confirmed that the service works, it will need to be deployed into an environment that supports adding ssl and basic authentication if desired. More importantly, the test django server does not support `Transfer-Encoding: chunked` - to support these we host python inside a web server that supports these things.

There are many ways to host Python in process pooled environments, one example is `uwsgi` - The following is an example of how to run the service using uwsgi:

```
/home/users/username/.virtualenvs/CustomThreadService/bin/uwsgi --http :8000 \
--home /home/users/username/.virtualenvs/CustomThreadService \
--module custom_threat_service.wsgi
```

_Notice that we are able to use the specific version of `uwsgi` within the virtual environment; there are some other ways to deploy that will allow more choices for deployment - example tutorials can be found within the [uwsgi documentation ](http://uwsgi-docs.readthedocs.org/en/latest/tutorials/Django_and_nginx.html) and at [digitalocean.com](https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-uwsgi-and-nginx-on-ubuntu-14-04) for reference purposes_

#### nginx.conf for custom_threat_service

Here's a sample conf file that can be used as a basis for an nginx server allowing for chunked_transfer_encoding, basic auth, and SSL

```
server {
    # the port your site will be served on
    listen      8001;

    # the domain name it will serve for
    server_name _; # substitute your machine's IP address or FQDN
    charset     utf-8;

    # Enable these settings for SSL
    # ssl on;
    # ssl_certificate /etc/ssl/certs/sample_certificate.crt;
    # ssl_certificate_key /etc/ssl/private/sample_certificate.key;
    # ssl_protocols TLSv1 TLSv1.1 TLSv1.2;

    # Enable these settings for basic auth protection
    # auth_basic                "Custom Threat Service";
    # auth_basic_user_file      /etc/nginx/auth_passwords;

    # max upload size
    client_max_body_size 2048M;   # adjust to taste

    location = /favicon.ico { access_log off; log_not_found off; }

    # This setting may be used if installing uwsgi globally on the server, in which case one can use a socket file instead of a port
    #location / {
    #    uwsgi_pass  unix:/home/users/mjames/src/sample-custom-threat-service/custom_threat_service.sock;
    #    include     /home/users/mjames/src/sample-custom-threat-service/uwsgi_params;
    #}

    # Simple proxy to running uwsgi processes - Notice that auth_basic is being set to `off` even if set ON above - otherwise this would require basic-auth knowledge within the sample
    location / {
        proxy_pass      http://127.0.0.1:8000;
        chunked_transfer_encoding on;
        auth_basic      off;
        proxy_buffering off;
    }
}
```

#### More test curl commands to use to confirm nginx / uwsgi operation

##### Multipart request
```
$ curl -X POST -k -H "Content-Type: multipart/form-data; boundary=hNkAJef6-C3sLds5cHApeUTcq-9GtzFHS1" --data-binary "@request_file.txt" 'http://custom.threat.service.com:8001/'
```

##### Multipart request with Transfer-Encoding
```
curl -X POST -k -H "Content-Type: multipart/form-data; boundary=tM5vs5va8xHEi_WIf-0fvBHQU8wfBK" -H "Transfer-Encoding: chunked" --data-binary "@request_file.txt" 'http://custom.threat.service.com:8001/'
```

*In both the above cases `request_file.txt` contains the request body (like the sample below). BEWARE - multipart requests __must__ use CR/LF (a la DOS/Windows) line-endings, which means that the content cannot simply be copied from here:*
```
--hNkAJef6-C3sLds5cHApeUTcq-9GtzFHS1
Content-Disposition: form-data; name="artifact"
Content-Type: application/json; charset=UTF-8
Content-Transfer-Encoding: 8bit

{"type":"file.content","value":"malware3.bat"}
--hNkAJef6-C3sLds5cHApeUTcq-9GtzFHS1
Content-Disposition: form-data; name="file"; filename="malware3.bat"
Content-Type: application/octet-stream
Content-Transfer-Encoding: binary

X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*

--hNkAJef6-C3sLds5cHApeUTcq-9GtzFHS1--
```



## Configuration

The sample configuration has one source of threat feed other than the local database for already-collected information. To override configuration values one can add a new file named `custom_threat_service/local_settings.py`, or directly edit the values in `custom_threat_service/settings.py`.

Because this is sample code, items within the settings.py file have DEBUG on and the secret key in place to allow a fast running of the sample (these are marked with `SECURITY WARNING` in the file, because you'll want these settings to not be present in a production-like environment).

## Searchers

The classes that search sources of information are called `searchers` within this application, and they should all inherit from the class `BaseArtifactSearch` (defined in `threats/controller.py`).

Two settings control which searchers are started within a scan request (shown below with their default settings)

1. `SYNC_SEARCHERS = [InternalArtifactSearch]`
2. `ASYNC_SEARCHERS = [PhishTankArtifactSearch]`

Searchers may be synchronous or asynchronous - synchronous searchers should return the list of threat hits directly (as a list of `threats/models.py:Threat` objects); asynchronous searchers should add threat information for each result using a call to `store_threat_info` defined in `BaseArtifactSearch`.

To implement another source, follow the example in `sources/phish_tank.py`, which illustrates the minimum that must be implemented:
```
    @classmethod
    def supports(cls, artifact_type):
        # implement this
```
and
```
    @classmethod
    def search(cls, artifact_type, search_term, **kwargs):
        # implement this
```

Asynchronous / Synchronous execution is handled within the base class.

### Phish Tank Searcher
The sample Phish Tank searcher implements a very simple searcher that looks at a file that contains a list of known phishing urls (downloaded from phishtank.com) and creates a threat record based upon that information.

Due to licensing issues, we ship only a sample file in the same format as provided by phishtank.com. To try out with the real list of known phishing websites, please download the latest copy from phishtank.com (At time of writing, they host this file at this location - http://data.phishtank.com/data/online-valid.csv)
