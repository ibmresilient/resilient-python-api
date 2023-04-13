![IBM Security](https://raw.githubusercontent.com/ibmresilient/resilient-python-api/master/resilient-sdk/assets/IBM_Security_lockup_pos_RGB.png)

# IBM SOAR App Config Plugins
- [Release Notes](#release-notes)
- [Overview](#overview)
- [Usage](#usage)
  - [IBM Security Verify Privilege Vault: `IBMVerifyVault`](#ibm-security-verify-privilege-vault-ibmverifyvault)
  - [HashiCorp Vault: `HashiCorpVault`](#hashicorp-vault-hashicorpvault)
  - [Cyberark: `Cyberark`](#cyberark-cyberark)
  - [Keyring: `Keyring`](#keyring-keyring)
- [Creating a Custom Plugin](#creating-a-custom-plugin)
- [License and Terms](#license-and-terms)

## Release Notes
* **v1.0.0** introduced `resilient-app-config-plugins`. This release included the built-in plugins for IBM Security Verify Privilege Vault, HashiCorp Vault, Cyberark, and Keyring.

## Overview
This package (`resilient-app-config-plugins`) is a Python package for the base classes for App Config plugins. This package exposes built-in plugins, as well as the interface class that outlines how to implement custom plugins. App Config plugins allow you to use external credential providers (sometimes referred to here as PAMs) manage secrets. With App Config plugins, your secrets are managed by your provider and loaded only into memory on an as-need basis for your SOAR apps. Credentials are kept out of logs and never saved to disk.

## Usage
Generally, all plugins are configured by setting `PAM_TYPE` in your environment. On Edge Gateway, this is done by setting a protected secret. The values for `PAM_TYPE` can be set to any of the plugins below, or to the name of your custom plugin (see [Creating a Custom Plugin](#creating-a-custom-plugin) for more info).

Each plugin then has its own set of required configurations that must also be set with protected secrets. Refer to the section of the plugin you wish to use for more information.

To reference a secret to be pulled from the plugin in the app.config, use the plugin prefix: **`^`**. Each plugin then will define its own set of rules for proper formatting of a secret's app.config value which will then be parsed and used to collect the secret from the plugin specified. 

### IBM Security Verify Privilege Vault: `IBMVerifyVault`
**TODO**

### HashiCorp Vault: `HashiCorpVault`
**TODO**

### Cyberark: `Cyberark`
**TODO**

### Keyring: `Keyring`
**TODO**

## Creating a Custom Plugin
You can create your own plugin to connect `resilient-circuits` to any external credential provider that may not be built-in to the `resilient-circuits` framework. To create a custom plugin, simply create one Python file. This Python file should expose a custom class, which implements the interface defined by `resilient_app_config_plugins.plugin_base.PAMPluginInterface`. That interface requires that you implement a constructor, a `get()` method, and a `selftest()` method. See one of the built-in plugins for details. **TODO** expand on this

Then set the value for `pam_plugin_path` in the `[resilient]` section of your app.config to the path to the Python file *and* set the value for `PAM_TYPE` in protected secrets to the name of the class (or set `pam_type` to the same value in the `[resilient]` section of the app.config).

**Example:**

```python
# /etc/rescircuits/my_plugin.py

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

```
[fn_my_app]
password=^password_from_my_pam

[resilient]
...
pam_type=MyPlugin
pam_plugin_path=/etc/rescircuits/my_plugin.py
...
```

Note that the only available external libraries for custom plugins is `requests`.

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
