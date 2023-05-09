![IBM Security](https://raw.githubusercontent.com/ibmresilient/resilient-python-api/master/resilient-sdk/assets/IBM_Security_lockup_pos_RGB.png)

# IBM SOAR App Config Plugins
- [Release Notes](#release-notes)
- [Overview](#overview)
- [Usage](#usage)
- [Creating a Custom Plugin](#creating-a-custom-plugin)
  - [Edge Gateway Deployment](#edge-gateway-deployment)
- [License and Terms](#license-and-terms)

## Release Notes
* **v1.0.0** introduced `resilient-app-config-plugins`. This release included the built-in plugins for HashiCorp Vault, Cyberark, and Keyring.

## Overview
This package (`resilient-app-config-plugins`) is a Python package for the base classes for App Config plugins. This package exposes built-in plugins, as well as the interface class that outlines how to implement custom plugins. App Config plugins allow you to use external credential providers (sometimes referred to here as PAMs) manage secrets. With App Config plugins, your secrets are managed by your provider and loaded only into memory on an as-need basis for your SOAR apps. Credentials are kept out of logs and never saved to disk.

## Usage
See the official IBM documentation for details on how to use each supported App Config plugin: [ibm.biz/soar-docs](https://ibm.biz/soar-docs).

## Creating a Custom Plugin

You can create your own plugin to connect `resilient-circuits` to any external credential provider that may not be built-in to the `resilient-circuits` framework. To create a custom plugin, you'll need to create a custom implementation of this package. If you plan to deploy the app on the Edge Gateway, you will also require a custom docker registry from which your Edge Gateway machine is setup to pull from.

1. Clone this repo to your local machine: `git clone https://github.com/ibmresilient/resilient-python-api.git`
1. Open the repo in your favorite code editor
1. Navigate to the `resilient-app-config-plugins/resilient_app_config_plugins` directory and create a new `.py` file with the name of your PAM solution which you wish to integrate with.
1. This Python file should expose a custom class, which implements the interface defined by `resilient_app_config_plugins.plugin_base.PAMPluginInterface`. That interface requires that you implement a constructor, a `get()` method, and a `selftest()` method. See one of the built-in plugins for details. The most important part is to implement the `get()` method to make a REST request out to the solution to retrieve the data affiliated with the value that you set for that config in your app.config file. The format which you use to reference values in the app.config is up to you.

    This Python file should expose a custom class, which implements the interface defined by `resilient_app_config_plugins.plugin_base.PAMPluginInterface`. That interface requires that you implement a constructor, a `get()` method, and a `selftest()` method. See one of the built-in plugins for details. The most important part is to implement the `get()` method to make a REST request out to the solution to retrieve the data affiliated with the value that you set for that config in your app.config file. The format which you use to reference values in the app.config is up to you.

    Note that there are a few conventions that we use which are exposed from the parent class `PAMPluginInterface`. 
    * `PAM_VERIFY_SERVER_CERT`: true, false or path to a certificate file for self-signed certs. Should be parsed with `resilient_app_config_plugins.plugin_base.get_verify_from_string()` to properly read the value
    * `PAM_ADDRESS`: address where the PAM endpoint is hosted
    * `PAM_APP_ID`: ID needed to authenticate to endpoint with plugin

    **Example:**

    ```python
    import requests
    from resilient_app_config_plugins.plugin_base import PAMPluginInterface

    class MyPlugin(PAMPluginInterface):
        def __init__(self, protected_secrets_manager, key, *args, **kwargs):
            """
            here save the protected_secrets_manager and key variables if needed
            """
            pass
        def get(self, plain_text_value, default=None):
            """
            plain_text_value is the content of a ^-prefixed string from the app.config.
            parse the value as needed to reach out to your endpoint
            """
            return plain_text_value
        def selftest(self):
            """
            return a tuple of a boolean and a string
            where the boolean indicates whether or not the
            plugin is correctly configured and the string 
            is a reason for why it might not be correctly configured.
            """
            return True, ""
    ```

1. Add the class to the `__init__.py` file at the root of the package. Exposing your class here is the key to allowing the `resilient` package to load your plugin:

    ```python
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    # (c) Copyright IBM Corp. 2023. All Rights Reserved.

    # All valid built-in PAM plugins must be defined and imported here
    from .cyberark import Cyberark
    from .hashicorp import HashiCorpVault
    from .keyring import Keyring
    from .my_custom_plug import MyPlugin
    ```

---

### Edge Gateway Deployment

Deploying an app with a custom App Config plugin requires a custom Docker registry to which you can push and host app container images. This guide assumes your Docker registry is configured and your Edge Gateway is configured to pull from that registry.

6. *(Edge Gateway deployment only)*: To add the package to your container image, build the wheel for your custom implementation of the `resilient-app-config-plugins` package:

    ```sh
    cd resilient-app-config-plugins
    pip install build
    python -m build
    ```

1. *(Edge Gateway deployment only)*: For each app which you wish to include this custom plugin, download the source code from App Exchange. You will have to rebuild each app with the plugins included
1.  *(Edge Gateway deployment only)*: Edit the Dockerfile so that the .whl file created by `build` is copied to the Docker image and installed with pip (NOTE: you first have to copy the .whl file to a location knowable by the Dockerfile, usually this is a folder called `dist` within the app's package structure):

    ```Docker
    COPY ./dist /tmp/packages
    RUN pip install /tmp/packages/resilient_app_config_plugins-*.whl
    ```

9. *(Edge Gateway deployment only)*: Repackage the app with `resilient-sdk package`:

    ```sh
    resilient-sdk package -p . --repository-name <repo name>
    ```

1. *(Edge Gateway deployment only)*: Rebuild the Docker image:

    ```sh
    docker build . -t <docker registry address>/<repo name>/<app name>:<version>
    ```

1. *(Edge Gateway deployment only)*: When installing the app through the Edge Gateway, make sure to use the app's `/dist/*.zip` file rather than the `.zip` file found on app exchange as the custom one will contain your repository name.

## License and Terms

Copyright © IBM Corporation 2023

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
