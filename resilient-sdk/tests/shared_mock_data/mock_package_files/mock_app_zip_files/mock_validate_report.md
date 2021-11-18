

# Validation Report for Main Mock Integration

| SDK Version       | Generation Time          |
| :---------------- | ------------------------ |
| 0.0.0 | 0000/00/00 00:00:00 |

## App Details
| Attribute | Value |
| --------- | ----- |
| `display_name` | Main Mock Integration |
| `name` | fn_main_mock_integration |
| `version` | 1.0.0 |
| `author` | `<<your name here>>` |
| `author_email` | you@example.com |
| `install_requires` | ['resilient_circuits>=30.0.0'] |
| `description` | Resilient Circuits Components for 'fn_main_mock_integration' |
| `long_description` | Resilient Circuits Components for 'fn_main_mock_integration'    A mock description of mock_function_one with unicode:  ล ฦ ว ศ ษ ส ห ฬ อ |
| `url` | https://ibm.com/mysupport |
| `entry_points` | {'resilient.circuits.configsection': '/Users/bobleckel/soar/resilient-python-api-worktrees/resilient-python-api/resilient-sdk/tests/test_temp/fn_main_mock_integration/fn_main_mock_integration/util/config.py',<br> 'resilient.circuits.customize': '/Users/bobleckel/soar/resilient-python-api-worktrees/resilient-python-api/resilient-sdk/tests/test_temp/fn_main_mock_integration/fn_main_mock_integration/util/customize.py',<br> 'resilient.circuits.selftest': '/Users/bobleckel/soar/resilient-python-api-worktrees/resilient-python-api/resilient-sdk/tests/test_temp/fn_main_mock_integration/fn_main_mock_integration/util/selftest.py'} |
| `SOAR version` | 41.0.6783 |
| `Proxy support` | Proxies not fully supported unless running on AppHost>=1.6 and resilient-circuits>=42.0.0 |

---


## `setup.py` file validation
| Severity | Name | Description | Solution |
| --- | --- | --- | --- |
| <span style="color:red">CRITICAL</span> | invalid value in `setup.py` | `setup.py` attribute `license` remains unchanged from the default value `<<insert here>>` | Set `license` to an valid license. |
| <span style="color:red">CRITICAL</span> | invalid value in `setup.py` | `setup.py` attribute `author` remains unchanged from the default value `<<your name here>>` | Set `author` to the name of the author |
| <span style="color:red">CRITICAL</span> | invalid value in `setup.py` | `setup.py` attribute `author_email` remains unchanged from the default value `you@example.com` | Set `author_email` to the author`s contact email |
| <span style="color:orange">WARNING</span> | invalid value in `setup.py` | `setup.py` attribute `description` remains unchanged from the default value `Resilient Circuits Components...` | Enter text that describes the app in `description`. This will be displayed when the app is installed |
| <span style="color:orange">WARNING</span> | invalid value in `setup.py` | `setup.py` attribute `long_description` remains unchanged from the default value `Resilient Circuits Components...` | Enter text that describes the app in `long_description`. This will be displayed when the app is installed |


---


## Package files validation

### `README.md`
<span style="color:red">CRITICAL</span>: Cannot find the following screenshot(s) referenced in the README: [`./doc/screenshots/custom_layouts.png`]

Make sure all screenshots referenced in the README are placed in the /doc/screenshots folder


### `MANIFEST.in`
<span style="color:orange">WARNING</span>: `MANIFEST.in` is missing the following lines: [`include apikey_permissions.txt`, `recursive-include fn_main_mock_integration/util *`, `include icons/*.png`, `recursive-include payload_samples/*/ *.json`, `include tox.ini`, `recursive-include tests/ *`]

The `MANIFEST.in` file is the list of files to be included during packaging. Be sure it is up to date


### `Dockerfile`
<span style="color:orange">WARNING</span>: `Dockerfile` does not match the template file (95% match). Difference from template:

```diff
--- Dockerfile template
+++ Dockerfile
@@ -7 +7 @@
-ARG RESILIENT_CIRCUITS_VERSION=43.0.0
+ARG RESILIENT_CIRCUITS_VERSION=37
@@ -47,3 +46,0 @@
-# create arbitrary group for user 1001
-RUN groupadd -g 1001 default && usermod -g 1001 default
-
@@ -53 +50 @@
-    chgrp -R 1001 /var/log/${PATH_RESILIENT_CIRCUITS} && \
+    chgrp -R 0 /var/log/${PATH_RESILIENT_CIRCUITS} && \
```

Ensure that the `Dockerfile` was generated with the latest version of the resilient-sdk...


### `entrypoint.sh`
<span style="color:orange">WARNING</span>: `entrypoint.sh` file does not match the template file (88% match). Difference from template: 

```diff
--- entrypoint.sh template
+++ entrypoint.sh
@@ -10,2 +10 @@
-  echo -n "`date +`%F %T,%N INFO ``"
-  if ! echo $APP_CONFIG_SHA | sha256sum --check --quiet
+  if ! echo $APP_CONFIG_SHA | sha256sum --check
@@ -16 +14,0 @@
-  if [ "$CIRCUITS_PID" != "`ps -o pid= -p $CIRCUITS_PID|xargs`" ]; then break; fi
```

Ensure that the `entrypoint.sh` was generated with the latest version of the resilient-sdk...


### `apikey_permissions.txt`
<span style="color:green">Pass</span>


### ``config.py``
<span style="color:green">Pass</span>


### ``customize.py``
<span style="color:green">Pass</span>

 
---
 

## `resilient-circuits` selftest
<span style="color:red">CRITICAL</span>: `selftest.py` not implemented for fn_main_mock_integration

`selftest.py` is a recommended check that should be implemented.

---
