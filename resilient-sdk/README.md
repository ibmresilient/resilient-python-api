![IBM Security](https://raw.githubusercontent.com/ibmresilient/resilient-python-api/master/resilient-sdk/assets/IBM_Security_lockup_pos_RGB.png)

# IBM SOAR SDK


## Overview

The IBM SOAR SDK, formerly the IBM Resilient SDK, provides the tools and infrastructure you need to develop IBM SOAR Apps, which you can then post on our [App Exchange](https://exchange.xforce.ibmcloud.com/hub/?br=Resilient).

## Installation

To install the IBM SOAR SDK, execute the following command:

```
$ pip install resilient-sdk
```

## Usage

### Configuration
Similar to our `resilient-circuits` library, the SDK it requires an `app.config` created in the default location: `~/.resilient` with the following minimum configurations:
```
[resilient]
host=my_soar_instance.ibm.com
org=Test Organization
api_key_id=<id>
api_key_secret=<secret>
cafile=false
```

> **NOTE:** Commands that interact with the SOAR platform support the `--config|-c` argument, which precedes the default location. For example:
> ```
> $ resilient-sdk clone -r "Display name of Rule" "Cloned Rule display name" -c path/to/my/custom_file.config
> ```

### `codegen:`
Generates boilerplate code used to begin developing an app.
```
$ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
```

Note: When using --incidenttype for a child custom incident type, refer instead to the parent incident type.

### `docgen:`
Generates boilerplate documentation for an app.
```
$ resilient-sdk docgen -p <path_to_package>
```

### `extract:`
Extracts data needed to publish a .res file.
```
$ resilient-sdk extract -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
```

### `package:`
Package your Python Package into a SOAR app format.
```
$ resilient-sdk package -p <path_to_directory> --display-name "My Custom app"
```

### `clone:`
Duplicates an existing Action-related object (Function, Rule, Script, Message Destination, Workflow) with a new API or display name.
```
$ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name>
```
```
$ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name> --changetype artifact
```

## Supported Python Versions

Python 2.7+ and Python 3.6+


## Documentation
For details on the Resilient SDK commands, use the `-h` option on the command line. For example, `resilient-sdk -h` and `resilient-sdk codegen -h`.

For more examples on its usage see [ibm.biz/soar-python-docs](https://ibm.biz/soar-python-docs)

The IBM SOAR App Developer's Guide provides information on using the Resilient SDK to develop and package apps. The guide is available on the IBM Knowledge Center at [ibm.biz/soar-docs](https://ibm.biz/soar-docs). On this web page, select your IBM SOAR platform version. On the follow-on page, you can find the App Developer's Guide by expanding **Apps** in the Table of Contents pane.


## Change Log
Our change log can be found at [ibm.biz/resilient-sdk-changes](https://ibm.biz/resilient-sdk-changes)


## License and Terms

Copyright © IBM Corporation 2021

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.