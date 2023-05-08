#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2021. All Rights Reserved.

import re

from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers, sdk_validate_helpers
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue

DEFAULT_SETUP_ATTR_REGEX = r"^<<|>>$"

# formatted strings follow array of values: [attr, attr_value, <OPTIONAL: fail_msg_lambda_supplement>]
setup_py_attributes = [
    ("name", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"[^a-z_0-9]+", x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' has invalid character(s) in '{1}'",
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Make sure that '{0}' is all lowercase and contains only letters, numbers or underscores",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }),
    ("display_name", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(DEFAULT_SETUP_ATTR_REGEX, x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' remains unchanged from the default value '{1}'", 
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Set '{0}' to an appropriate value. This value is displayed when the app is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    }),
    ("display_name", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": sdk_validate_helpers.check_display_name_not_equal_to_name,
        "include_setup_py_path_in_fail_func": True,
        "fail_msg": u"'{0}' should not be the same as 'name'", 
        "solution": u"Set '{0}' to a value that will be displayed when installed on App Host",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }),
    ("license", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(DEFAULT_SETUP_ATTR_REGEX, x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' remains unchanged from the default value '{1}'", 
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Set '{0}' to a valid license.",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }),
    ("url", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: not sdk_helpers.is_valid_url(x),
        "fail_msg": u"'{1}' is not a valid '{0}'",
        "missing_msg": "'url' is a recommended attribute",
        "solution": "Include a valid URL for your organization",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    }),
    ("author", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(DEFAULT_SETUP_ATTR_REGEX, x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' remains unchanged from the default value '{1}'", 
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Set '{0}' to the name of the author",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }),
    ("author_email", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"@example\.com", x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' remains unchanged from the default value '{1}'", 
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Set '{0}' to the contact email for the author",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }),
    ("description", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"{0}.*".format(constants.DOCGEN_PLACEHOLDER_STRING), x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' remains unchanged from the default value '{1:29.29}...'", 
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Enter a quick description for the app in '{0}'. This will be displayed when the app is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    }),
    ("long_description", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"{0}.*".format(constants.DOCGEN_PLACEHOLDER_STRING), x, re.IGNORECASE),
        "fail_msg": u"setup.py attribute '{0}' remains unchanged from the default value '{1:29.29}...'",
        "missing_msg": u"setup.py file is missing attribute '{0}' or missing the value for the attribute",
        "solution": u"Enter a detailed description for the app in '{0}'. This will be displayed when the app is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    }),
    ("install_requires", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: package_helpers.get_dependency_from_install_requires(x, constants.CIRCUITS_PACKAGE_NAME) is None,
        "fail_msg": u"'resilient_circuits' must be included as a dependency in '{0}'. Found '{1}'",
        "missing_msg": u"'install_requires' is required in setup.py",
        "solution": u"Include 'resilient_circuits>={0}' as a requirement in '{1}'".format(
            constants.RESILIENT_LIBRARIES_VERSION, "{0}"
        ),
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    }),
    ("install_requires", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: bool(sdk_validate_helpers.check_dependencies_version_specifiers(x)),
        "fail_msg": u"'{0}' has the following improperly formatted dependencies: {2}",
        "fail_msg_lambda_supplement": lambda x: sdk_validate_helpers.check_dependencies_version_specifiers(x),
        "solution": u"All dependencies (other than resilient-circuits) must include a version in the format '~=' or '=='",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    }),
    ("python_requires", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: package_helpers.get_required_python_version(x) < constants.MIN_SUPPORTED_PY_VERSION,
        "fail_msg": u"'{0}' version '{2[0]}.{2[1]}' is not supported",
        "fail_msg_lambda_supplement": lambda x: package_helpers.get_required_python_version(x),
        "missing_msg": "'python_requires' is a recommended attribute",
        "solution": u"Suggested value is 'python_requires>={0}.{1}'".format(
            constants.MIN_SUPPORTED_PY_VERSION[0],
            constants.MIN_SUPPORTED_PY_VERSION[1]
        ),
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    }),
    ("entry_points", {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: False if not any([ep not in x for ep in package_helpers.SUPPORTED_EP]) else True,
        "fail_msg": u"'{0}' is missing {2} which is one of the required entry points", 
        "fail_msg_lambda_supplement": lambda x: [ep for ep in package_helpers.SUPPORTED_EP if ep not in x],
        "missing_msg": u"'{0}' is missing",
        "solution": "Make sure that all of the following values for '{0}' are implemented: " + str(package_helpers.SUPPORTED_EP),
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    })
]


# NOTE: selftest_attributes needs to be a list as the order of these checks MATTERS
selftest_attributes = [
    { # check 1: verify that resilient-circuits is installed in python env
        "func": sdk_validate_helpers.selftest_validate_resilient_circuits_installed,
        "name": "resilient-circuits selftest",

        "fail_msg": "'{0}=={1}' is not supported".format(constants.CIRCUITS_PACKAGE_NAME, "{0}"),
        "fail_solution": "Upgrade '{0}' by running '''pip install -U '{0}>={1}''''".format(constants.CIRCUITS_PACKAGE_NAME, constants.RESILIENT_LIBRARIES_VERSION),

        "missing_msg": "'{0}' is not installed in your Python environment".format(constants.CIRCUITS_PACKAGE_NAME),
        "missing_solution": "Install '{0}' by running '''pip install -U '{0}''''".format(constants.CIRCUITS_PACKAGE_NAME),

        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        "pass_msg": "'{0}' was found in the Python environment with the minimum version installed".format(constants.CIRCUITS_PACKAGE_NAME)
    },
    { # check 2: check that the given package is acutally installed in the env
        "func": sdk_validate_helpers.selftest_validate_package_installed,
        "name": "resilient-circuits selftest",

        "fail_msg": "'{0}' is not installed in your Python environment",
        "solution": "Install '{0}' by running '''pip install {1}'''",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        
        "pass_msg": "'{0}' is correctly installed in your Python environment",
    },
    { # check 3: validate that the selftest file exists
        "func": sdk_validate_helpers.selftest_validate_selftestpy_file_exists,
        "name": "resilient-circuits selftest",

        "fail_msg": "selftest.py is a required file",
        "solution": "Run '''resilient-sdk codegen -p <path_to_package> --reload''' and implement the template selftest function",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        "pass_msg": "selftest.py file found at path '{0}'",
    },
    { # check 4: execute selftest and check how it went
        "func": sdk_validate_helpers.selftest_run_selftestpy,
        "name": "resilient-circuits selftest",

        # if selftest returncode == 1
        "fail_msg": u"selftest.py failed  for {0}. Details:\n\n\t\t{1}\n",
        "fail_solution": "Check your configuration values and make sure selftest.py is properly implemented",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        # if 'unimplemented' is the return value from selftest
        "missing_msg": u"selftest.py not implemented for {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "selftest.py is a recommended check that should be implemented.",

        # if a returncode > 1 comes from running selftest.py
        "error_msg": u"While running selftest.py, 'resilient-circuits' failed to connect to server. Details:\n{0}",
        "error_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        # if selftest.py succeeds (i.e. returncode == 0)
        "pass_msg": u"selftest.py successfully ran for '{0}'",
    }
]


# check package files are present
package_files = [ 
    ("MANIFEST.in", {
        "func": sdk_validate_helpers.package_files_manifest,
        "name": "'MANIFEST.in'",

        "fail_msg": "'MANIFEST.in' is missing the following lines: {0}",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,
        "fail_solution": "'MANIFEST.in' file is the list of files to be included during packaging. Be sure it is up to date",

        "missing_msg": "'MANIFEST.in' not found in package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "'MANIFEST.in' has the minimum files included"
    }),

    ("apikey_permissions.txt", {
        "func": sdk_validate_helpers.package_files_apikey_pem,
        "name": "'apikey_permissions.txt'",

        "fail_msg": "'apikey_permnissions.txt' is missing the following required permissions: {0}",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_solution": "Add the required permissions to your 'apikey_permnissions.txt' file",

        "missing_msg": "'apikey_permissions.txt' not found in package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "'apikey_permissions.txt' is valid; it contains the base permissions",
        "pass_solution": "Permissions found: {0}"
    }),

    ("Dockerfile", {
        "func": sdk_validate_helpers.package_files_template_match,
        "name": "'Dockerfile, template match'",

        "fail_msg": "'Dockerfile' does not match the template file ({0:.0f}% match). Difference from template:\n\n\t\t{1}",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,
        "fail_solution": "Ensure that the 'Dockerfile' was generated with the latest version of the resilient-sdk...",

        "missing_msg": "'Dockerfile' not found in package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "'Dockerfile' matches the template"
    }),
    ("Dockerfile", {
        "func": sdk_validate_helpers.package_files_validate_base_image,
        "name": "'Dockerfile, base image'",

        "fail_msg": "Dockerfile is not using the correct base image: {0}", 
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_solution": "This can be fixed by {0}", 

        "pass_msg": "Dockerfile is using the correct base image"
        }),

    ("entrypoint.sh", {
        "func": sdk_validate_helpers.package_files_template_match,
        "name": "'entrypoint.sh'",

        "fail_msg": "'entrypoint.sh' does not match the template file ({0:.0f}% match). Difference from template: \n\n\t\t{1}",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,
        "fail_solution": "Ensure that the 'entrypoint.sh' was generated with the latest version of the resilient-sdk...",

        "missing_msg": "'entrypoint.sh' not found in package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "'entrypoint.sh' matches the template file"
    }),

    ("config.py", {
        "func": sdk_validate_helpers.package_files_validate_config_py,
        "path": "{0}/util/config.py",
        "name": "'config.py'",

        "warn_msg": "'config.py' does not return a string value",
        "warn_severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,
        "warn_solution": "The 'config.py' file defines the contents of the app.config settings for your app",

        "fail_msg": u"{0}",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "missing_msg": "'config.py' not found in package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "'config.py' returned a valid app.config value",
        "pass_solution": u"config data: \n\t\t{0}"
    }),

    ("customize.py", {
        "func": sdk_validate_helpers.package_files_validate_customize_py,
        "path": "{0}/util/customize.py",
        "name": "'customize.py'",

        "fail_msg": "'customize.py' ImportDefinition invalid. {0}",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "missing_msg": "'customize.py' not found in package at path '{0}'",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "'customize.py' returned a valid import definition",
        "pass_solution": u"ImportDefinition found: {0}...; View the entire contents at '{1}'"
    }),

    ("export.res", {
        "func": sdk_validate_helpers.package_files_validate_script_python_versions,
        "path": "{0}/util/customize.py",
        "name": "'SOAR Scripts'",

        "fail_msg": u"Global script '{0}' packaged with this app is written in Python 2",
        "fail_msg_playbooks": u"Local script '{0}' in playbook '{1}' packaged with this app is written in Python 2",
        "fail_msg_sub_playbooks_input": u"Input script for a subplaybook in playbook '{0}' packaged with this app is written in Python 2",
        "fail_msg_sub_playbooks_output": u"Output script for subplaybook '{0}' packaged with this app is written in Python 2",
        "fail_msg_pre_processing": u"Pre-processing script for workflow '{0}' packaged with this app is written in Python 2",
        "fail_msg_post_processing": u"Post-processing script for workflow '{0}' packaged with this app is written in Python 2",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_solution": "Python 2 will soon no longer be supported in SOAR. Update the language of the script to Python 3, being careful to make sure that it is still fully functional",

        "missing_msg": "'customize.py' not found in package at path '{0}'",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

        "pass_msg": "Scripts in app use valid versions of Python",
        "pass_solution": "All scripts are written in Python 3. Be careful to make any new scripts in Python 3 only"
    }),

    ("README.md", {
        "func": sdk_validate_helpers.package_files_validate_readme,
        "name": "'README.md'",

        "fail_codegen_msg": "'README.md' is still the 'codegen' template",
        "fail_codegen_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_codegen_solution": "Be sure that you run '''resilient-sdk docgen -p {0}''' when you are done developing",

        "fail_todo_msg": "'README.md' still has at least one 'TODO'",
        "fail_todo_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_todo_solution": "Make sure to complete the README for your app",

        "fail_placeholder_msg": "'README.md' still has at least one instance of '<!-- {0} -->'",
        "fail_placeholder_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_placeholder_solution": "Edit the README and make sure to remove all '<!-- {0} -->' comments",

        "fail_screenshots_msg": "Cannot find one or more screenshots referenced in the README: {0}",
        "fail_screenshots_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_screenshots_solution": "Make sure all screenshots referenced in the README are placed in the /doc/screenshots folder",

        "missing_msg": "Cannot find README in the package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Generate the documentation using '''resilient-sdk docgen -p {0}'''",

        "pass_msg": "'README.md' has been implemented",
        "pass_solution": "Make sure that all documentation is up to date before packaging"
    }),

    ("app_logo.png", {
        "func": sdk_validate_helpers.package_files_validate_icon,
        "path": package_helpers.PATH_ICON_EXTENSION_LOGO,
        "default_path": package_helpers.PATH_DEFAULT_ICON_EXTENSION_LOGO,
        "name": "'app_logo.png'",
        "width": constants.ICON_APP_LOGO_REQUIRED_WIDTH,
        "height": constants.ICON_APP_LOGO_REQUIRED_HEIGHT,

        "missing_msg": "Cannot find 'app_logo.png' in the package at path '{0}'",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Include a logo for your app at path '{0}' with size {1}x{2}".format(package_helpers.PATH_ICON_EXTENSION_LOGO, "{1}", "{2}"),

        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        "default_icon_msg": "'{0}' is the default icon. Consider using your own logo",
        "default_icon_severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,

        "pass_msg": "'{0}' icon found at {1}",
        "solution": "Icons appear in SOAR when your app is installed with App Host"
    }),

    ("company_logo.png", {
        "func": sdk_validate_helpers.package_files_validate_icon,
        "path": package_helpers.PATH_ICON_COMPANY_LOGO,
        "default_path": package_helpers.PATH_DEFAULT_ICON_COMPANY_LOGO,
        "name": "'company_logo.png'",
        "width": constants.ICON_COMPANY_LOGO_REQUIRED_WIDTH,
        "height": constants.ICON_COMPANY_LOGO_REQUIRED_HEIGHT,

        "missing_msg": "Cannot find 'company_logo.png' in the package at path '{0}'",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Include a logo for your company at path '{0}' with size {1}x{2}".format(package_helpers.PATH_ICON_COMPANY_LOGO, "{1}", "{2}"),

        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        "default_icon_msg": "'{0}' is the default icon. Consider using your own logo",
        "default_icon_severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,

        "pass_msg": "'{0}' icon found at {1}",
        "solution": "Icons appear in SOAR when your app is installed with App Host"
    }),

    ("LICENSE", {
        "func": sdk_validate_helpers.package_files_validate_license,
        "path": "{0}/LICENSE",
        "name": "LICENSE",

        "missing_msg": "Cannot find 'LICENSE' in the package at path {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "Generate the LICENSE using '''resilient-sdk codegen -p {0} --reload'''",

        "fail_msg": "'LICENSE' is the default license file",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "fail_solution": "Provide a 'LICENSE' file in your package directory. Suggested formats: MIT, Apache, and BSD",

        "pass_msg": "'LICENSE' file is valid",
        "pass_solution": "It is recommended to manually validate the license. Suggested formats: MIT, Apache, and BSD"
    })
 ]

payload_samples_attributes = {
    "func": sdk_validate_helpers.payload_samples_validate_payload_samples,

    # if import definition isn't readable or is corrupt
    "no_import_def_msg": "'ImportDefinition' is corrupt: '{0}'",
    "no_import_def_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

    # if import def doesn't have the correct "function" section
    "no_func_msg": "'ImportDefinition' is missing a 'function' section:'{0}'",
    "no_func_severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,

    # if "function" list element section doesn't have a "name"
    "no_func_name_msg": "'ImportDefinition.function' list is missing a 'name' for function: '{0}'",
    "no_func_name_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

    # if payload_samples file doesn't exist
    "payload_file_missing_msg": "{0} for '{1}' not found",
    "payload_file_missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

    # if payload file is not readable json
    "payload_file_invalid_msg": "{0} for '{1}' not valid JSON",
    "payload_file_invalid_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

    # if payload file is readable json but empty
    "payload_file_empty_msg": "{0} for '{1}' empty",
    "payload_file_empty_solution": "Fill in values manually or by using '''resilient-sdk codegen -p {0} --gather-results'''",
    "payload_file_empty_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

    # generic solution that instructs user to reload using codegen
    "reload_solution": "Reload code using '''resilient-sdk codegen -p {0} --reload'''",

    # if payload file is readable json
    "pass_msg": "Payload samples for '{0}' are valid",
    "pass_solution": ""
}


tests_attributes = [
    # first check tox is installed and meets min version defined in constants.TOX_MIN_PACKAGE_VERSION
    {
        "func": sdk_validate_helpers.tox_tests_validate_tox_installed,
        "name": "tox tests",

        "fail_msg": "'{0}' is not installed in your Python environment",
        "fail_solution": "(OPTIONAL) If you want to verify any tests you have written, install '{0}' by running '''pip install -U {0}'''",

        "upgrade_msg": "The version of '{0}=={1}' installed in your environment does not meet the minimum version required: '{2}'",
        "upgrade_solution": "Install the latest version using '''pip install -U tox'''",
        "upgrade_severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,

        "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,

        "pass_msg": "'{0}' was found in the Python environment"
    },

    # second check tox.ini file is present
    {
        "func": sdk_validate_helpers.tox_tests_validate_tox_file_exists,
        "name": "tox tests",

        "fail_msg": "'{0}' file not found in package path",
        "fail_solution": "(OPTIONAL) If you want to validate tests, include a {0} file",

        "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,

        "pass_msg": "'{0}' file was found in the package"
    },

    # third check envlist = TOX_MIN_ENV_VERSION exists in the file
    {
        "func": sdk_validate_helpers.tox_tests_validate_min_env_version,
        "name": "tox tests",

        "missing_msg": "'envlist={0}' not found in '{1}' file",
        "missing_solution": "Tests must be configured to run 'envlist={0}' or greater",

        "fail_msg": "Unsupported tox environment found in envlist in '{0}' file",
        "fail_solution": "Tests must be configured to run only with tox environments '{0}' or greater",

        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,

        "pass_msg": "Valid '{0}' was found in the '{1}' file"
    },

    # finally run the tests with tox
    {
        "func": sdk_validate_helpers.tox_tests_run_tox_tests,
        "name": "tox tests",

        "fail_msg": u"{0} tests failed. Details:\n\n\t\t{1}\n",

        "error_msg": u"{0} error(s) occurred while running tests. Details:\n\n\t\t{1}\n",

        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "solution": "Run with the '-v' flag to see more information",

        "pass_msg": "{0} tests passed!",
    },
]


pylint_attributes = [
    # first check that pylint is installed and meets minimum version
    {
        "func": sdk_validate_helpers.pylint_validate_pylint_installed,
        "name": "Pylint Scan",

        "fail_msg": "'{0}' is not installed in your Python environment",
        "fail_solution": "(OPTIONAL) If you want to run a Pylint scan, install '{0}' by running '''pip install -U {0}'''",

        "upgrade_msg": "The version of '{0}=={1}' installed in your environment does not meet the minimum version required: '{2}'",
        "upgrade_solution": "Install the latest version using '''pip install -U pylint'''",
        "upgrade_severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,

        "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,

        "pass_msg": "'{0}' was found in the Python environment"
    },

    # second, run pylint and output the output
    {
        "func": sdk_validate_helpers.pylint_run_pylint_scan,
        "name": "Pylint Scan",

        "fail_msg": "The Pylint score was {0:.2f}/10. Details:\n\n\t\t{1}",
        "fail_solution": "Run with '-v' to see the full pylint output",

        "pass_msg": "Pylint scan passed with no errors",
        "pass_solution": "Run with '-v' to see the full pylint output"
    }
]



bandit_attributes = [
    {
        "func": sdk_validate_helpers.bandit_validate_bandit_installed,
        "name": "Bandit Scan",

        "fail_msg": "'{0}' is not installed in your Python environment",
        "fail_solution": "(OPTIONAL) If you want to run a Bandit scan, install '{0}' by running '''pip install -U {0}'''",

        "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,

        "pass_msg": "'{0}' was found in the Python environment"
    },
    {
        "func": sdk_validate_helpers.bandit_run_bandit_scan,
        "name": "Bandit Scan",

        "fail_msg": "Bandit scan failed. Details:\n\n\t\t{0}",
        "fail_solution": "Run again with '-v' to see the full bandit output",

        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        "pass_msg": "Bandit scan passed with no issues",
        "pass_solution": "Run again with '-v' to see the full bandit output"
    }
]
