[![Build Status](https://travis.ibm.com/Resilient/resilient-python-api.svg?token=ga58Yr4soAPHbQj4XsUF&branch=master)](https://travis.ibm.com/Resilient/resilient-python-api)

![IBM Security](./assets/IBM_Security_lockup_pos_RGB.png)


# IBM Resilient Python SDK


## Table of Contents

 * [Overview](#overview)
 * [Installation](#installation)
 * [Usage](#usage)
 * [Supported Python Versions](#supported-python-versions)
 * [Documentation](#documentation)
 * [License and Terms](#license-and-terms)


## Overview

The IBM Resilient Python SDK provides the tools and infrastructure
you need to develop Resilient Apps that are on the [App Exchange](https://exchange.xforce.ibmcloud.com/hub/?br=Resilient).

For more information, visit the
[IBM Resilient Python SDK setup guide](https://<link_to_setup_guide>).


## Installation

To install the IBM Resilient Python SDK, simply execute the following command
in a terminal:

```
$ pip install resilient-sdk
```

## Usage

### codegen
Generate boilerplate code to start developing an App
```
$ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
```

### docgen
Generate documentation for an App
```
$ resilient-sdk docgen -p <path_to_package>
```

### extract
Extract data in order to publish a .res file
```
$ resilient-sdk extract -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
```

### app:package
Package an Integration into a Resilient App
```
$ resilient-sdk app:package -p <path_to_directory> --display_name "My Custom App"
```

### app:convert
Convert an old (built) Integration that can be in .tar.gz or .zip format into
a Resilient App
```
$ resilient-sdk app:convert -p <path_to_old_built_distribution>
```


## Supported Python Versions

We currently support Python 2.7+ and Python 3.6+


## Documentation

* [Setup Guide](https://<link_to_setup_guide>)


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