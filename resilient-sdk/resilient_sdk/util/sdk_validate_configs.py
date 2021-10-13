#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2021. All Rights Reserved.

import re
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from resilient_sdk.util import sdk_helpers, constants
from resilient_sdk.util import package_file_helpers as package_helpers

# formatted strings follow array of values: [attr, attr_value, <OPTIONAL: fail_msg_lambda_supplement>]
setup_py_attributes = {
    "name": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"[^a-z_]+", str(x)),
        "fail_msg": "setup.py attribute '{0}' is has invalid character(s)",
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Make sure that '{0}' is all lowercase and does not include and special characters besides underscores",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    },
    "display_name": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"^<<|>>$", str(x)),
        "fail_msg": "setup.py attribute '{0}' appears to still be the default value '{1}'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Please set '{0}' to an appropriate value. This value will be displayed when the integration is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    },
    "license": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"^<<|>>$", str(x)), # TODO: what are the GPL's?
        "fail_msg": "setup.py attribute '{0}' appears to still be the default value '{1}'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Please set '{0}' to an appropriate value. More info TODO: HERE", # TODO: documentation link 
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    },
    "author": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"^<<|>>$", str(x)),
        "fail_msg": "setup.py attribute '{0}' appears to still be the default value '{1}'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Please set '{0}' to the name of the author",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    },
    "author_email": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"@example\.com", str(x)),
        "fail_msg": "setup.py attribute '{0}' appears to still be the default value '{1}'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Please set '{0}' to the author's contact email",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    },
    "description": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"^(?!Resilient Circuits Components).+", str(x)),
        "fail_msg": "setup.py attribute '{0}' doesn't start with 'Resilient Circuits Components'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "'{0}' should start with 'Resilient Circuits Components'. This will be displayed when the integration is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    },
    "long_description": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"^(?!Resilient Circuits Components).+", str(x)),
        "fail_msg": "setup.py attribute '{0}' doesn't start with 'Resilient Circuits Components'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "'{0}' should start with 'Resilient Circuits Components'. This will be displayed when the integration is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    },
    "install_requires": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: package_helpers.get_dependency_from_install_requires(x, "install_requires"),
        "fail_msg": "'resilient_circuits' must be included as a dependency in '{0}'",
        "missing_msg": "'resilient_circuits' must be included as a dependency in '{0}'",
        "solution": "Please include 'resilient_circuits' as a requirement in '{0}'",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    },
    "python_requires": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: package_helpers.get_required_python_version(x) < sdk_helpers.MIN_SUPPORTED_PY_VERSION,
        "fail_msg": "Given version '{2[0]}.{2[1]}' in setup.py is too low",
        "fail_msg_lambda_supplement": lambda x: package_helpers.get_required_python_version(x),
        "missing_msg": "'python_requires' is a recommended attribute",
        "solution": "Suggested value is 'python_requires>={0}.{1}'".format(
            sdk_helpers.MIN_SUPPORTED_PY_VERSION[0],
            sdk_helpers.MIN_SUPPORTED_PY_VERSION[1]
        ),
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    },
    "entry_points": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: False if not any([ep not in x for ep in package_helpers.SUPPORTED_EP]) else True,
        "fail_msg": "'{0}' is missing {2} which is one of the required entry points", 
        "fail_msg_lambda_supplement": lambda x: [ep for ep in package_helpers.SUPPORTED_EP if ep not in x],
        "missing_msg": "'{0}' is missing",
        "solution": "Please make sure that all of the following values for '{0}' are implemented: " + str(package_helpers.SUPPORTED_EP),
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }
}
