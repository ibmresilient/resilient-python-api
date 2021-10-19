#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2021. All Rights Reserved.

import re, os, pkg_resources, subprocess, logging
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers, constants
from resilient_sdk.util import package_file_helpers as package_helpers

LOG = logging.getLogger(constants.LOGGER_NAME)

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
        "fail_func": lambda x: re.findall(r"^(Resilient Circuits Components).+", str(x)),
        "fail_msg": "setup.py attribute '{0}' appears to still be the default value '{1:29.29}...'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Please make sure that you write your own '{0}'. This will be displayed when the integration is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    },
    "long_description": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: re.findall(r"^(Resilient Circuits Components).+", str(x)),
        "fail_msg": "setup.py attribute '{0}' appears to still be the default value '{1:29.29}...'", 
        "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
        "solution": "Please make sure that you write your own '{0}'. This will be displayed when the integration is installed",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN
    },
    "install_requires": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: False 
            if package_helpers.get_dependency_from_install_requires(x, "resilient_circuits") is not None 
            else False if package_helpers.get_dependency_from_install_requires(x, "resilient-circuits") is not None
            else True,
        "fail_msg": "'resilient_circuits' must be included as a dependency in '{0}'",
        "missing_msg": "'resilient_circuits' must be included as a dependency in '{0}'",
        "solution": "Please include 'resilient_circuits>={0}' as a requirement in '{1}'".format(
            constants.RESILIENT_LIBRARIES_VERSION, "{0}"
        ),
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    },
    "python_requires": {
        "parse_func": package_helpers.parse_setup_py,
        "fail_func": lambda x: package_helpers.get_required_python_version(x) < sdk_helpers.MIN_SUPPORTED_PY_VERSION,
        "fail_msg": "'{0}' version '{2[0]}.{2[1]}' is not officially supported",
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

def selftest_validate_resilient_circuits_installed(attr_dict, **kwargs):
    """
    TODO: unit tests
    selftest.py validation helper method.
    Validates that 'resilient-circuits' is installed in the env
    and confirms that the version is >= constants.RESILIENT_LIBRARIES_VERSION

    :param attr_dict: (required) dictionary of attributes defined in ``selftest_attributes``
    :type attr_dict: dict
    :param path_selftest_py_file: (optional) path to selftest.py
    :type path_selftest_py_file: str
    :param package_name: (optional) name of package being validated
    :type package_name: str
    :param path_package: (optional) path to package
    :type path_package: str
    :return: returns a tuple with the status of the validation and an associated SDKValidateIssue
    :rtype: (bool, SDKValidateIssue)
    """
    LOG.debug("validating that 'resilient-circuits' is installed in the env...\n")

    try:
        # try to parse 'resilient-circuits' version installed in env
        res_circuits_version = sdk_helpers.get_package_version(constants.CIRCUITS_PACKAGE_NAME)
    except pkg_resources.DistributionNotFound as e:
        # if 'resilient-circuits' not installed
        return False, SDKValidateIssue( 
            name=attr_dict.get("missing_name"),
            description=attr_dict.get("missing_msg"),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("missing_solution")
        )
    else:
        # if resilient-circuits was found, then check if version is high enough
        if res_circuits_version < pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION):
            return False, SDKValidateIssue(
                name=attr_dict.get("fail_name"),
                description = attr_dict.get("fail_msg").format(res_circuits_version),
                severity = attr_dict.get("severity"),
                solution = attr_dict.get("fail_solution").format(res_circuits_version)
            )
        else:
            return True, SDKValidateIssue(
                name=attr_dict.get("pass_name"),
                description = attr_dict.get("pass_msg"),
                severity = SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
                solution = ""
            )

def selftest_validate_package_installed(attr_dict, package_name, path_package, **kwargs):
    """
    TODO: unit tests
    selftest.py validation helper method.
    Validates that the package being validated is installed in the python env

    :param attr_dict: (required) dictionary of attributes defined in ``selftest_attributes``
    :type attr_dict: dict
    :param package_name: (required) name of package being validated
    :type package_name: str
    :param path_package: (required) path to package
    :type path_package: str
    :param path_selftest_py_file: (optional) path to selftest.py
    :type path_selftest_py_file: str
    :return: returns a tuple with the status of the validation and an associated SDKValidateIssue
    :rtype: (bool, SDKValidateIssue)
    """
    LOG.debug("validating that the package is installed...\n")

    # check that the package being validated is installed in the environment
    if package_helpers.check_package_installed(package_name):
        return True, SDKValidateIssue(
            name = attr_dict.get("pass_name").format(package_name),
            description = attr_dict.get("pass_msg").format(package_name),
            severity = SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution = ""
        )
    else:
        return False, SDKValidateIssue(
            name = attr_dict.get("fail_name").format(package_name),
            description = attr_dict.get("fail_msg").format(package_name),
            severity = attr_dict.get("severity"),
            solution = attr_dict.get("solution").format(package_name, path_package)
        )

def selftest_validate_selftestpy_file_exists(attr_dict, path_selftest_py_file, **kwargs):
    """
    TODO: unit tests
    selftest.py validation helper method.
    Validates that 'selftest.py' exists in the path given (which should be <path_package>/util/selftest.py)

    :param attr_dict: (required) dictionary of attributes defined in ``selftest_attributes``
    :type attr_dict: dict
    :param path_selftest_py_file: (required) path to selftest.py
    :type path_selftest_py_file: str
    :param package_name: (optional) name of package being validated
    :type package_name: str
    :param path_package: (optional) path to package
    :type path_package: str
    :return: returns a tuple with the status of the validation and an associated SDKValidateIssue
    :rtype: (bool, SDKValidateIssue)
    """
    LOG.debug("validating selftest.py file exists...\n")

    # try to read the selftest.py file in the given path
    try:
        sdk_helpers.validate_file_paths(os.R_OK, path_selftest_py_file)
        issue = SDKValidateIssue(
            attr_dict.get("pass_name"),
            attr_dict.get("pass_msg").format(path_selftest_py_file),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )
        return True, issue
    except SDKException as e:
        # if it can't be read then create the appropriate SDKValidateIssue and return False immediately
        issue = SDKValidateIssue(
            attr_dict.get("fail_name"),
            attr_dict.get("fail_msg"),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("solution")
        )
        return False, issue


def selftest_run_selftestpy(attr_dict, package_name, **kwargs):
    """
    TODO: unit tests
    selftest.py validation helper method.
    Runs selftest.py and validates the output. There are a few paths this method can take...
    If resilient-circuits starts up successfully, then selftest is ran. The error code is then checked.
    If the error code is 1, selftest failed. If 0, selftest either succeeded or was unimplemented.
    These two scenarios are both checked for.
    It is possible for there to be a connection error while starting up resilient-circuits.
    If this is the case, the error string is parsed and output in the appropriate SDKValidateIssue object

    :param attr_dict: (required) dictionary of attributes defined in ``selftest_attributes``
    :type attr_dict: dict
    :param package_name: (required) name of package being validated
    :type package_name: str
    :param path_selftest_py_file: (optional) path to selftest.py
    :type path_selftest_py_file: str
    :param path_package: (optional) path to package
    :type path_package: str
    :return: returns a tuple with the status of the validation and an associated SDKValidateIssue
    :rtype: (bool, SDKValidateIssue)
    """
    # because selftest takes a while to complete we've decided to log this AWLAYS to INFO level
    # thus the logging doesn't go through the normal check for if output should be suppressed
    # this could be implemented as a progress bar if we choose to run selftest as a separate thread
    LOG.info("INFO: Running selftest.py... (this may take a bit to complete)\n")


    # run selftest in package as a subprocess
    selftest_cmd = ['resilient-circuits', 'selftest', '-l', package_name.replace("_", "-")]
    proc = subprocess.run(selftest_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    details = proc.stderr.decode("utf-8")

    # if selftest failed (see details of the return codes @ resilient-circuits.cmds.selftest)
    if proc.returncode == 1:
        details = details[details.rfind("{")+1:details.rfind("}")].strip().replace("\n", ". ").replace("\t", " ")
        return False, SDKValidateIssue(
            name=attr_dict.get("fail_name"),
            description=attr_dict.get("fail_msg").format(package_name, details),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )
    elif proc.returncode > 1:
        # return code is a failure of REST or STOMP connection
        details = details[details.rfind("ERROR"):].strip().replace("\n", ". ").replace("\t", " ")
        return False, SDKValidateIssue(
            name=attr_dict.get("error_name"),
            description=attr_dict.get("error_msg").format(details),
            severity=attr_dict.get("error_severity")
        )
    else:
        # look to see if output has "unimplemented" in it -- that means that user hasn't
        # implemented selftest yet. warn that they should implement selftest
        if details.find("unimplemented") != -1:
            return False, SDKValidateIssue(
                name=attr_dict.get("missing_name"),
                description=attr_dict.get("missing_msg").format(package_name),
                severity=attr_dict.get("missing_severity"),
                solution=attr_dict.get("missing_solution")
            )
        else:
            # finally, if exit code was 0 and unimplemented was not found, the selftest passed
            return True, SDKValidateIssue(
                name=attr_dict.get("pass_name"),
                description=attr_dict.get("pass_msg").format(package_name),
                severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
                solution=""
            )


# NOTE: selftest_attributes needs to be a list as the order of these checks MATTERS
selftest_attributes = [
    { # check 1: verify that resilient-circuits is installed in python env
        "func": selftest_validate_resilient_circuits_installed,

        "fail_name": "'{0}' version is too low".format(constants.CIRCUITS_PACKAGE_NAME),
        "fail_msg": "'{0}=={1}' is not supported".format(constants.CIRCUITS_PACKAGE_NAME, "{0}"),
        "fail_solution": "Upgrade '{0}' by running 'pip install {0}>={1}'".format(constants.RESILIENT_LIBRARIES_VERSION, "{0}"),

        "missing_name": "'{0}' not found".format(constants.CIRCUITS_PACKAGE_NAME),
        "missing_msg": "'{0}' is not installed in your python environment".format(constants.CIRCUITS_PACKAGE_NAME),
        "missing_solution": "Please install '{0}' by running 'pip install {0}'".format(constants.CIRCUITS_PACKAGE_NAME),

        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        
        "pass_name": "'{0}' found in env".format(constants.CIRCUITS_PACKAGE_NAME),
        "pass_msg": "'{0}' was found in the python environment with the minimum version installed".format(constants.CIRCUITS_PACKAGE_NAME)
    },
    { # check 2: check that the given package is acutally installed in the env
        "func": selftest_validate_package_installed,

        "fail_name": "'{0}' not found",
        "fail_msg": "'{0}' is not installed in your python environment",
        "solution": "Please install '{0}' by running 'pip install {1}'",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        
        "pass_name": "'{0}' found in env",
        "pass_msg": "'{0}' is correctly installed in your python environment",
    },
    { # check 3: validate that the selftest file exists
        "func": selftest_validate_selftestpy_file_exists,

        "fail_name": "selftest.py not found",
        "fail_msg": "selftest.py is a required file",
        "solution": "Please run codegen --reload and implement the templated selftest function",
        "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        
        "pass_name": "selftest.py found",
        "pass_msg": "selftest.py file found at path '{0}'",
    },
    { # check 4: execute selftest and check how it went
        "func": selftest_run_selftestpy,

        # if selftest returncode == 1
        "fail_name": "selftest.py failed",
        "fail_msg": "selftest.py failed  for {0}. Details: {1}",
        "fail_solution": "Please check your configuration values and make sure selftest.py is properly implemented",
        "fail_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        # if 'unimplemented' is the return value from selftest
        "missing_name": "selftest.py not implemented",
        "missing_msg": "selftest.py not implemented for {0}",
        "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
        "missing_solution": "selftest.py is a recommended check that should be implemented. More info <TODO: LINK>", # TODO: documentation link

        # if a returncode > 1 comes from running selftest.py
        "error_name": "selftest.py failed",
        "error_msg": "While running selftest.py, 'resilient-circuits' failed to connect to server. Details: {0}",
        "error_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,

        # if selftest.py succeeds (i.e. returncode == 0)
        "pass_name": "selftest.py success",
        "pass_msg": "selftest.py successfully ran for {0}",
    }
]
