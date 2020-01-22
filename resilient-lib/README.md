### Changelog
<!-- Changelog will go here -->
# Resilient Library for Integrations

This package contains common library calls which facilitate the development of functions for IBM Resilient.

## Revision History

|Revision | Notes    |
|---------|----------|
| v34     | Added timeout to [integrations]. For previous versions, this value should be added manually |

## Modules in this package include:

* function_results - A class to standardize on the payload returned from functions. In addition to integration results returned, meta-data about the integration execution environment is returned (see `function_results.ResultPayload`).

json structure created:

```
{ 
  "version": "1.0",       -- used to track different versions of the payload
  "success": True|False,
  "reason": str,          -- a string to explain if success=False
  "content": json,        -- the result of the function call
  "raw": str,             -- a string representation of content. This is sometimes
                             needed when the result of one function is piped into 
                             the next
  "inputs": json,         -- a copy of the input parameters, useful for post-processor 
                             script use
  "metrics": json         -- a set of information to capture specifics metrics 
                             about the function's runtime environment
}
```
* function\_metrics - A class to collect metrics information to be added to the resulting json payload. This is embedded in `function_results.ResultPayload`

json structure created:

```
{
    "version": "1.0",
    "package": str,            -- function name
    "package_version": str,    -- function version
    "host": str,               -- hostname of execution node
    "execution_time_ms": int   -- execution time of function in milliseconds
    "timestamp": str           -- execution date/time formatted as: 
                                  yyyy-MM-dd hh:mm:ss
}
```
* html2markdown - A class to convert html code to markdown. Parameters exist to customize the conversion to the type of markdown output required.
* integration_errors - Contains a simple exception for function failures: `IntegrationError`
* requests_common - A class of common code for making REST API calls with logic for proxies and standard return code handling.
* resilient_common - Common code for interacting with Resilient. Functions include:
      
      * build\_incident_url - Build a URL back to the issuing incident for 3rd party software reference.
      * build\_resilient_url - Build a URL to access resilient. Useful for API calls.
      * clean_html - Remove html code from rich text fields. Data is concatenated together. Use html2markdown for better results.
      * unescape - Restore data which has been encoded for URL transmission (ex. \&gt; = >).
      * validate_fields - Ensure require fields from Resilient or the app.config file are present.
      * get\_file_attachment - Return a byte string of a Resilient attachment related to an incident, task or artifact.
      * get\_file\_attachment\_name - Return the name of an attachment
      * readable_datetime - Convert epoch formatted data and time value into a string.
      * str\_to_bool - Convert string values into boolean.

## Prerequisites:

```
resilient version 30 or later
resilient-circuits version 30 or later
```

## Usage examples:

```
from resilient_lib import build_incident_url, build_resilient_url

url_to_incident = build_incident_url(build_resilient_url("https://my.resilient.com", 
                                     8443), 12345)
self.assertEqual("https://my.resilient.com:8443/#incidents/12345", url_to_incident)
```

```
from resilient_lib import RequestsCommon
from resilient_lib import ResultPayload

fr = ResultPayload(pgkname, **function_params)

req_common = RequestsCommon(app_config_params, function_params)
result = req_common.execute_call('post', issue_url, payload, log=log,
                                 basicauth=(function_params['user'], 
                                 function_params['password']), verify_flag= 
                                 function_params['verifyFlag'], headers=HTTP_HEADERS)

results_payload = fr.done(True, None, result)

```

```
from resilient_lib import MarkdownParser

data = "<div class='rte'><div><strong><u>underline and strong</u></strong></div></div>"
markdown = "*_underline and strong_*"

parser = MarkdownParser(bold="*", underline="_") # override defaults
converted = parser.convert(data)
self.assertEqual(converted, markdown)
```
* oauth2_client_credentials_session - has OAuth2ClientCredentialsSession class that 
standardizes OAuth2 Client Credential flow's implementation. It subclasses `requests.Session` to
provide a convenient interaction.
```
Usage example:
>>> api1 = OAuth2ClientCredentialsSession('https://example1.com/<tenant_id>/oauth/v2/',\
                    client_id='xxx', client_secret='xxx')
>>> api2 = OAuth2ClientCredentialsSession('https://example2.com/<tenant_id>/oauth/v2/',\
                    client_id='xxx', client_secret='xxx')
>>>
>>> api1.post('https://example1.com/v4/me/messages', data={}) # use as a regular requests session object
>>> api2.get('https://example2.com/v2/me/updates')
>>> # When writing an integration, use RequestsCommon to get the proxies defined in in your app.config file.
>>> rc = RequestsCommon(xxx)
>>> api3 = OAuth2ClientCredentialsSession('https://example3.com/{}/test', proxies=rc.get_proxies())
```
## Installation

Install this package as:
   
```
$ pip install resilient_lib-<version>.tar.gz
```

## Setup

To configure the library properties, run: `resilient-circuits config [-u | -c]`. 
Then edit the [integrations] section to define proxy settings which will be used for all integrations which use this library:

```
[integrations]
# These proxy settings will be used by all integrations. 
# To override, add any parameter to your specific integration section
http_proxy=
https_proxy=
timeout=30
```
