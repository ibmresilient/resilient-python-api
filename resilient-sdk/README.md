![IBM Security](./assets/IBM_Security_lockup_pos_RGB.png)

### Changelog
<!-- Changelog will go here -->

# IBM Resilient Python SDK


## Table of Contents

 * [Overview](#overview)
 * [Installation](#installation)
 * [Usage](#usage)
 * [Supported Python Versions](#supported-python-versions)
 * [Documentation](#documentation)
 * [License and Terms](#license-and-terms)


## Overview

The IBM Resilient Python SDK provides the tools and infrastructure you need to develop Resilient Apps, which you can then post on [App Exchange](https://exchange.xforce.ibmcloud.com/hub/?br=Resilient).

For more information, refer to the [Resilient SOAR Platform App Developer's Guide](https://www.ibm.com/support/knowledgecenter/SSBRUQ_37.0.0/doc/app_dev/app_intro.html).


## Installation

To install the IBM Resilient Python SDK, simply execute the following command
in a terminal:

```
$ pip install resilient-sdk
```

## Usage

### `codegen:`
Generate boilerplate code to start developing an app
```
$ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
```

### `docgen:`
Generate documentation for an app
```
$ resilient-sdk docgen -p <path_to_package>
```

### `extract:`
Extract data in order to publish a .res file
```
$ resilient-sdk extract -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
```

### `package:`
Package an integration into a Resilient app
```
$ resilient-sdk package -p <path_to_directory> --display-name "My Custom app"
```

## Supported Python Versions

Python 2.7+ and Python 3.6+


## Documentation

* [Setup Guide](https://developer.ibm.com/security/resilient/sdk/)


## License and Terms

Copyright © IBM Corporation 2020

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