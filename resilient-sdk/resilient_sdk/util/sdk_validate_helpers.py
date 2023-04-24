#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2021. All Rights Reserved.

import difflib
import logging
import os
import re
import sys
import xml.etree.ElementTree as ET

# in py2 StringIO is base module for StringIO
# in py3 io is the base module for StringIO
if sys.version_info.major < 3:
    from StringIO import StringIO
else:
    from io import StringIO

import pkg_resources
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue

LOG = logging.getLogger(constants.LOGGER_NAME)

try:
    from pylint import lint
    from pylint.reporters import text
except ImportError as err:
    LOG.debug("Failed to import 'pylint' that is needed for 'validate' to run a full validation")
    LOG.debug("ERROR: %s", err)

# float value in range [0, 1] that determines the cutoff at which two files are a match
MATCH_THRESHOLD = 1.0

def check_display_name_not_equal_to_name(display_name, path_setup_py_file):
    """
    Fail func to verify that 'display_name' does not equal 'name' in setup.py

    :param display_name: display_name value from setup.py
    :type display_name: str
    :param path_setup_py_file: path to setup.py file of package
    :type path_setup_py_file: str
    :return: True if the two values equal (i.e. True when it should fail the check)
    :rtype: bool
    """
    if not display_name:
        return False
    name = package_helpers.parse_setup_py(path_setup_py_file, ["name"]).get("name")
    return name.lower() == display_name.lower()

def check_dependencies_version_specifiers(install_requires_list):
    """
    Check if all dependencies given in the "install_requires" list from setup.py
    have the appropriate version specifiers. The allowed specifiers are "~=" and "=="
    except for "resilient-circuits".
    :param install_requires_list: list of dependencies as specified in setup.py file's install_requires list
    :type install_requires_list: list(str)
    :return: returns a list of all the dependencies that are mis-formatted or an empty list if all are correctly specified
    :rtype: list
    """

    # need to allow for underscore versions too
    circuits_name_with_under_score = constants.CIRCUITS_PACKAGE_NAME.replace("-", "_")

    allowed_specifiers = ["~=", "=="]

    deps_need_fixing = []
    for dep in install_requires_list:
        if constants.CIRCUITS_PACKAGE_NAME not in dep and circuits_name_with_under_score not in dep:
            if all(specifier not in dep for specifier in allowed_specifiers):
                deps_need_fixing.append(dep)

    return deps_need_fixing

def selftest_validate_resilient_circuits_installed(attr_dict, **_):
    """
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


    res_circuits_version = sdk_helpers.get_package_version(constants.CIRCUITS_PACKAGE_NAME)

    if res_circuits_version and res_circuits_version >= pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION):
        # installed and correct version
        return True, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )
    elif res_circuits_version and res_circuits_version < pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION):
        # resilient-circuits installed but version not supported 
        return False, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(res_circuits_version),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution")
        )
    elif not res_circuits_version:
        # if 'resilient-circuits' not installed
        return False, SDKValidateIssue( 
            name=attr_dict.get("name"),
            description=attr_dict.get("missing_msg"),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("missing_solution")
        )
    else:
        # unknown other error
        raise SDKException("Unknown error while checking for {0}".format(constants.CIRCUITS_PACKAGE_NAME))

def selftest_validate_package_installed(attr_dict, package_name, path_package, **_):
    """
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
            name=attr_dict.get("name").format(package_name),
            description=attr_dict.get("pass_msg").format(package_name),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )
    else:
        return False, SDKValidateIssue(
            name=attr_dict.get("name").format(package_name),
            description=attr_dict.get("fail_msg").format(package_name),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("solution").format(package_name, path_package)
        )

def selftest_validate_selftestpy_file_exists(attr_dict, path_selftest_py_file, **_):
    """
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
        return True, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg").format(path_selftest_py_file),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )
    except SDKException:
        # if it can't be read then create the appropriate SDKValidateIssue and return False immediately
        return False, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg"),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("solution")
        )

def selftest_run_selftestpy(attr_dict, package_name, **kwargs):
    """
    selftest.py validation helper method.
    Runs selftest.py and validates the output. There are a few paths this method can take.

    * If the ``returncode==1``, selftest failed. 
    * Else if ``returncode==0``
        * If selftest ``unimplemented`` 
        * else if 0, then selftest succeeded.
    * Else if ``returncode>1`` there was a connection error while starting up ``resilient-circuits``. The error string is parsed and output in the appropriate ``SDKValidateIssue`` object

    :param attr_dict: (required) dictionary of attributes defined in ``selftest_attributes``
    :type attr_dict: dict
    :param package_name: (required) name of package being validated
    :type package_name: str
    :param path_app_config: (optional) path of app config file; pass None if not used
    :type path_app_config: str
    :param path_selftest_py_file: (optional) path to selftest.py
    :type path_selftest_py_file: str
    :param path_package: (optional) path to package
    :type path_package: str
    :return: returns a tuple with the status of the validation and an associated SDKValidateIssue
    :rtype: (bool, SDKValidateIssue)
    """

    # Set env var
    path_app_config = kwargs.get("path_app_config")
    if not path_app_config:
        path_app_config = ""
    LOG.debug("\nSetting $APP_CONFIG_FILE to '%s'\n", path_app_config)
    os.environ[constants.ENV_VAR_APP_CONFIG_FILE] = path_app_config

    # run resilient-circuits selftest in a subprocess
    selftest_cmd = ['resilient-circuits', 'selftest', '-l', package_name.replace("_", "-")]
    returncode, details = sdk_helpers.run_subprocess(selftest_cmd, cmd_name="selftest")

    # Unset env var
    os.environ[constants.ENV_VAR_APP_CONFIG_FILE] = ""

    # details is grabbed from output and currently in different formats based on the return code.
    #
    # if returncode==1: details="<resilient-circuits run details>...<details on selftest run>...""
    #                   the important part come in the section between the last two '{' '}'
    #                   which is where the 'state' and 'reason' values are output (see below:)
    #                   ...
    #                   <package_name>: 
    #                       selftest: success
    #                       selftest output:
    #                       {'state': 'failure', 'reason': '<some reason for failure>'}
    #                       Elapsed time: x.xyz seconds
    #                   ...
    # 
    # in resilient-circuits <43.1, "unimplemented" returns a error code 0 so:
    # if returncode==0: same as if ==1, except the 'state' is 'success' and there is no 'reason' field
    #                   NOTE (<v43.1 only): it is possible for there to be 'state': 'unimplemented' if which case we fail
    #                   the validation and let the user know that they should implement selftest
    # 
    # in resilient-circuits >=43.1, "unimplemented" returns an error code 2 so:
    # if returncode==2: "unimplemented" is the status of the selftest run so we fail and let the user know they
    #                   should implement selftest
    #
    # if returncode>2:  details=<some error about REST or STOMP connection failed to SOAR server>
    #                   the important part occurs after "ERROR: ..." so we parse from there on to the end
    
    # if selftest failed (see details of the return codes @ resilient-circuits.cmds.selftest)
    if returncode == 1:
        details = details[details.rfind("{")+1:details.rfind("}")].strip().replace("\n", ". ").replace("\t", " ")
        return False, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(package_name, details),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )
    elif returncode > 2:
        # return code is a failure of REST or STOMP connection

        # parse out the ERROR line and then take the 5 lines that came before it
        i = [i for i, line in reversed(list(enumerate(details.splitlines()))) if "ERROR" in line]
        i = i[0] if i else 0

        details_parsed = u"\n\t\t...\n\t\t" + u"\n\t\t".join(details.splitlines()[max(0, i - 5):])

        return False, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("error_msg").format(details_parsed),
            severity=attr_dict.get("error_severity"),
            solution=""
        )
    elif returncode == 2:
        # in resilient-circuits >=v43.1 returncode == 2 means "unimplemented"
        # NOTE: that for <43.1 we still have to check and parse the output
        return False, SDKValidateIssue(
                name=attr_dict.get("missing_name"),
                description=attr_dict.get("missing_msg").format(package_name),
                severity=attr_dict.get("missing_severity"),
                solution=attr_dict.get("missing_solution")
            )
    elif returncode == 0:
        # look to see if output has "'state': 'unimplemented'" in it -- that means that user hasn't
        # implemented selftest yet. warn that they should implement selftest
        if details.find("'state': 'unimplemented'") != -1:
            return False, SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("missing_msg").format(package_name),
                severity=attr_dict.get("missing_severity"),
                solution=attr_dict.get("missing_solution")
            )
        else:
            # finally, if exit code was 0 and unimplemented was not found, the selftest passed
            return True, SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("pass_msg").format(package_name),
                severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
                solution=details[details.rfind("{'state"):].replace("\r", "").replace("\n", " ").replace("-", "")
            )
    else:
        raise SDKException("Unknown error while running '{0}'".format(" ".join(selftest_cmd)))



def package_files_manifest(package_name, path_file, filename, attr_dict, **_):
    """
    Helper method for package files to validate that at least the templated manifests are included in MANIFEST.in.
    Creates a list of missing template manifest lines.

    Does a fuzzy match of lines with cutoff=0.9 for matching between lines. More info on the matching
    here: https://docs.python.org/3.6/library/difflib.html#difflib.get_close_matches

    :param package_name: (required) the name of the package
    :type package_name: str
    :param path_file: (required) the path to the file
    :type path_file: str
    :param filename: (required) the name of the file to be validated
    :type filename: str
    :param attr_dict: (required) dictionary of attributes for the MANIFEST.in file defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a passing issue if the file exists and has the templated manifests; a warning issue if the file doesn't exist or if the manifest template lines aren't all found
    :rtype: list[SDKValidateIssue]
    """

    # render jinja file of MANIFEST
    file_rendered = sdk_helpers.setup_env_and_render_jinja_file(
        constants.PACKAGE_TEMPLATE_PATH,
        filename,
        package_name=package_name,
        sdk_version=sdk_helpers.get_resilient_sdk_version()
    )

    # read the contents of the package's MANIFEST file
    file_contents = sdk_helpers.read_file(path_file)

    # split template file into list of lines
    template_contents = file_rendered.splitlines(True)
    
    # compare given file to template
    diffs = []
    for line in template_contents:
        if line.strip() == "":
            continue
        matches = difflib.get_close_matches(line, file_contents, cutoff=0.90)
        if not matches:
            diffs.append(str(line.strip()))

    if diffs:
        # some lines from template weren't in the given file so this validation fails
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(diffs),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )]
    else:
        # all template lines were in given MANIFEST.in so this validation passes
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )]

def package_files_apikey_pem(path_file, attr_dict, **_):
    """
    Helper method for package files to validate that at least the BASE_PERMISSIONS defined in the package helpers
    are present in the apikey_permissions.txt file.

    :param path_file: (required) the path to the file
    :type path_file: str
    :param attr_dict: (required) dictionary of attributes for the apikey_permissions.txt file defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a passing issue if the file exists and has the minimum permissions; a warning issue if the file doesn't exist or if the base permissions aren't found
    :rtype: list[SDKValidateIssue]
    """
    
    # read package's apikey_permissions.txt file
    file_contents = sdk_helpers.read_file(path_file)

    # filter out commented lines
    file_contents = [line.strip() for line in file_contents if not line.startswith("#")]
    
    # compare given file to constant BASE_PERMISSIONS
    missing_permissions = []
    for perm in package_helpers.BASE_PERMISSIONS:
        if perm not in file_contents:
            missing_permissions.append(perm)

    if missing_permissions:
        # missing the base perimissions
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(missing_permissions),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )]
    else:
        # apikey_permissions file has _at least_ all of the base permissions
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=attr_dict.get("pass_solution").format(file_contents)
        )]

def package_files_template_match(package_name, package_version, path_file, filename, attr_dict, **_):
    """
    Helper method for package files to validate files against their templates.
    Designed for use with Dockerfile and entrypoint.sh, however, could be adjusted to work with 
    other jinja2 templated files as long as the goal is to check a full match against the template.

    :param package_name: (required) the name of the package
    :type package_name: str
    :param package_version: (required) the version of the package (required for formatting the Dockerfile template)
    :type package_version: str
    :param path_file: (required) the path to the file
    :type path_file: str
    :param filename: (required) the name of the file to be validated
    :type filename: str
    :param attr_dict: (required) dictionary of attributes for templated files defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a passing issue if the file exists and matches the template; a warning issue if the file doesn't exist or if the template doesn't match the given file
    :rtype: list[SDKValidateIssue]
    """

    # render jinja file
    file_rendered = sdk_helpers.setup_env_and_render_jinja_file(
        constants.PACKAGE_TEMPLATE_PATH,
        filename,
        package_name=package_name,
        version=package_version,
        resilient_libraries_version=sdk_helpers.get_resilient_libraries_version_to_use(),
        sdk_version=sdk_helpers.get_resilient_sdk_version()
    )
    
    # read the package's file
    # strip each line of its newline but then add it back in for consistency between this and the rendered file
    file_contents = [line.strip("\n") + "\n" for line in sdk_helpers.read_file(path_file)]

    # split template file into list of lines
    # strip each line of its newline but then add it back in for consistency
    template_contents = [line.strip("\n") + "\n" for line in file_rendered.splitlines()]
    
    # compare given file to template (ignoring blanks and hard tabs)
    s_diff = difflib.SequenceMatcher(lambda x: x in " \t", file_contents, template_contents)

    # check match between the two files
    # if less than a perfect match, the match fails
    comp_ratio = s_diff.ratio()
    if comp_ratio < MATCH_THRESHOLD:
        diff = difflib.unified_diff(template_contents, file_contents, 
                                    fromfile=filename + " template", tofile=filename, n=0) # n is number of context lines
        diff = package_helpers.color_diff_output(diff) # add color to diff output

        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(comp_ratio*100, "\t\t".join(diff)),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )]
    else:
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )]

def package_files_validate_config_py(path_file, attr_dict, **_):
    """
    Helper method for package files to validate the config.py file.
    This works by using the get_configs_from_config_py from package_file_helpers.
    That method returns either an empty string if no config data, or a config string.
    It is also possible that the get_configs method will raise an Exception;
    if that happens, fail the validation.
    The validation passes with a successful parse of the config string or warns
    if there is no string found.

    :param path_file: (required) the path to the file
    :type path_file: str
    :param attr_dict: (required) dictionary of attributes for the config.py file defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a issue that describes the validity of the config.py file
    :rtype: list[SDKValidateIssue]
    """

    try:
        # parse the config_str and config_list with helper method
        # if the config.py file is corrupt an exception will be thrown
        config_str = package_helpers.get_configs_from_config_py(path_file)[0]

        if config_str != "":
            # if config data was found
            return [SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("pass_msg"),
                severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
                solution=attr_dict.get("pass_solution").format("\n\t\t".join(config_str.split("\n")))
            )]

        else:
            # if there is no config data give warning
            # it is allowed to not have any configs, just uncommon
            return [SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("warn_msg"),
                severity=attr_dict.get("warn_severity"),
                solution=attr_dict.get("warn_solution")
            )]

    except SDKException as e:
        # if fails for some other reason output the SDKException messages
        # the reasons here may include misformatted config data, syntax errors in the file, ...
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(str(e).replace("\n", " ")),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )]

def package_files_validate_customize_py(path_file, attr_dict, **_):
    """
    Helper method for package files to validate the import definition from customize.py.
    This works by using the get_import_definition_from_customize_py helper method from package_file_helpers.
    That method is designed to look first for an export.res file in <package_path>/<package_name>/<util>/<data>/<export.res>.
    If that file exists, it returns a simple dict object from reading the JSON there. If not, it goes and looks
    in the customize.py file and tries to read out the import definition from there. In either case, if
    something goes wrong an SDKException is raised. This method catches that exception and fails the customize.py
    validation. If the definition is successfully parsed, the validation passes.

    :param path_file: (required) the path to the file
    :type path_file: str
    :param attr_dict: (required) dictionary of attributes for the customize.py file defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a passing issue if the customize.py file can yield a successful ImportDefinition; a critical issue if the parse fails
    :rtype: list[SDKValidateIssue]
    """
    
    try:
        # parse import definition information from customize.py file
        # this will raise an SDKException if something goes wrong
        import_def = package_helpers.get_import_definition_from_customize_py(path_file)
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=attr_dict.get("pass_solution").format(str(import_def)[:75], path_file)
        )]
    except SDKException as e:
        # something went wrong in reading the import definition.
        # for more info on what raises an error see the package_helpers
        # method get_import_definition_from_customize_py called above.
        
        # parse out the exception message from "ERROR" to the end
        message = str(e).replace("\n", " ")
        message = message[message.index("ERROR"):]

        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(message),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution")
        )]

def package_files_validate_script_python_versions(path_file, attr_dict, **_):
    """
    Validate that no scripts packaged with this app are written in Python 2.

    To do this, we look in all the places a script could be defined:
        - Globally
        - Locally in a Playbook
        - In a workflow's pre-processing script for a function
        - In a workflows's post-processing script for a function

    The global scripts and playbook scripts are nice and easy to handle as they
    are represented well in the export.res JSON file, with a "language" attribute.
    That attribute will be "python" for PY2 and "python3" for PY3.

    For workflow pre-/post-processing scripts, however, we need to scan the
    XML definition of the workflow to determine the language of the script
    as that is the only place in the export.res contains that information.
    The key item that we look for is "pre_processing_script_language":"python"
    (for pre-processing scripts and the same logic follows for post-processing).
    If that is found, we know that there is a PY2 script associated with a function
    in that workflow. For the moment, the scan is not smart enough to count
    the number of PY2 scripts in the workflow. Just smart enough to tell
    whether there is a PY2 pre-processing script and a PY2 post-processing
    script in the workflow.

    For each PY2 script found in the export (with the noted caveat explained above
    for counting workflow function scripts), a SDKValidateIssue is returned.
    Each issue has relevant information about the PY2 script and where to find it
    and gives suggestions on how to fix it, while warning that updating to PY3
    from PY2 can cause breaking changes and the user should use caution when
    updating those scripts.

    :param path_file: (required) the path to the file
    :type path_file: str
    :param attr_dict: (required) dictionary of attributes for the customize.py file defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a list of issues containing the PY2 scripts to be updated; or a passing issue if no scripts were found
    :rtype: list[SDKValidateIssue]
    """
    try:
        # parse import definition information from customize.py file
        # this will raise an SDKException if something goes wrong
        export_res = package_helpers.get_import_definition_from_customize_py(path_file)
    except SDKException:
        # something went wrong in reading the import definition.
        # since this is already checked in another function elsewhere,
        # ignore and return an empty list
        return []

    issues = []

    # validate GLOBAL scripts are all python3 only.
    # for each non-python3 script we find, create an issue
    for script in export_res.get("scripts") or []:
        if script.get("language", "") not in constants.EXPORT_RES_SCRIPTS_ALLOWED_LANGUAGE_TYPES:
            issues.append(SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("fail_msg").format(script.get("name", "UNKNOWN SCRIPT NAME")),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution")
            ))

    # do very similar check for local scripts in playbooks
    for playbook in export_res.get("playbooks") or []:
        for local_script in playbook.get("local_scripts") or []:
            if local_script.get("language", "") not in constants.EXPORT_RES_SCRIPTS_ALLOWED_LANGUAGE_TYPES:
                issues.append(SDKValidateIssue(
                    name=attr_dict.get("name"),
                    description=attr_dict.get("fail_msg_playbooks").format(
                        local_script.get("name", "UNKNOWN SCRIPT NAME"), playbook.get("display_name", "UNKNOWN PLAYBOOK NAME")),
                    severity=attr_dict.get("fail_severity"),
                    solution=attr_dict.get("fail_solution")
                ))

        # check for input scripts calling subplaybooks
        if constants.EXPORT_RES_SUB_PLAYBOOK_PRE_PROCESSING_UNALLOWED_LANGUAGE in playbook.get("content", {}).get("xml", ""):
            issues.append(SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("fail_msg_sub_playbooks_input").format(playbook.get("name", "UNKNOWN SCRIPT NAME")),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution")
            ))
        # check for output scripts from subplaybooks
        if constants.EXPORT_RES_SUB_PLAYBOOK_OUTPUT_UNALLOWED_LANGUAGE in playbook.get("content", {}).get("xml", ""):
            issues.append(SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("fail_msg_sub_playbooks_output").format(playbook.get("name", "UNKNOWN SCRIPT NAME")),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution")
            ))

    # workflows are harder, but we can simply look into the XML for what we know should be there:
    # there should be a line in there that says "post_processing_script_language":"python3" for PY3
    # or "post_processing_script_language":"python" for Python 2 scripts (same goes for pre_processing...)
    # so we scan the workflows and their xml properties
    for workflow in export_res.get("workflows") or []:
        # check for bad pre processing scripts
        if constants.EXPORT_RES_WORKFLOW_PRE_PROCESSING_UNALLOWED_LANGUAGE in workflow.get("content", {}).get("xml", ""):
            issues.append(SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("fail_msg_pre_processing").format(workflow.get("name", "UNKNOWN SCRIPT NAME")),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution")
            ))
        # check for bad post processing scripts
        if constants.EXPORT_RES_WORKFLOW_POST_PROCESSING_UNALLOWED_LANGUAGE in workflow.get("content", {}).get("xml", ""):
            issues.append(SDKValidateIssue(
                name=attr_dict.get("name"),
                description=attr_dict.get("fail_msg_post_processing").format(workflow.get("name", "UNKNOWN SCRIPT NAME")),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution")
            ))

    if not issues:
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=attr_dict.get("pass_solution")
        )]
    else:
        return issues

def package_files_validate_icon(path_file, attr_dict, filename, **__):
    """
    Helper method for package files to validate an icon
    This works by using the get_icon helper method from package_file_helpers.
    That method loads in a given icon, checks the contents for the correct size,
    and returns the contents if the file is valid.

    This helper method loads in the given icon and the default icon associated with it
    and compares the two. If they are equivalent, the validation INFO's to the user that
    the given icon is still the default.

    :param path_file: (required) the path to the file
    :type path_file: str
    :param attr_dict: (required) dictionary of attributes for each icon png defined in ``package_files``
    :type attr_dict: dict
    :param filename: (required) name of the icon
    :type filename: str
    :param _: (unused) other unused named args
    :type _: dict
    :return: a passing issue if the icon exists and is not the default, a info issue if the icon is the default, and a failing issue if the icon doesn't exist or is not the correct dimensions
    :rtype: list[SDKValidateIssue]
    """

    # using the get_icon method from the package_file_helpers
    # which throws exceptions when icon's aren't correct
    try:
        # load the icon
        encoded_icon = package_helpers.get_icon(filename, path_file,
            attr_dict.get("width"), attr_dict.get("height"), attr_dict.get("default_path"))

    except SDKException as sdk_err:
        # the get_icon method threw an exception - parse it out and use
        # it as the message for the SDK issue

        # parse out the exception message from "ERROR" to the end
        message = str(sdk_err).replace("\n", " ")
        message = message[message.index("ERROR"):]

        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=message,
            severity=attr_dict.get("fail_severity"),
            solution=""
        )]

    # load in the default icon from the sdk data path
    default_icon = package_helpers.get_icon(filename, attr_dict.get("default_path"),
        attr_dict.get("width"), attr_dict.get("height"), attr_dict.get("default_path"))

    # check if given icon is the default icon
    if encoded_icon == default_icon:
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("default_icon_msg").format(filename, path_file),
            severity=attr_dict.get("default_icon_severity"),
            solution=attr_dict.get("solution")
        )]

    # icon was loaded with no issues and was not the default
    return [SDKValidateIssue(
        name=attr_dict.get("name"),
        description=attr_dict.get("pass_msg").format(filename, path_file),
        severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
        solution=attr_dict.get("solution")
    )]

def package_files_validate_license(path_file, attr_dict, filename, **__):
    """
    Helper method for package files to validate the LICENSE file of the app
    This does a simple check to see if the file matches the template (which is nearly
    blank). If it is the template, the check fails.
    Otherwise it passes, although it will INFO out that the LICENSE file should
    be manually checked to make sure it is one of the accepted licenses...

    :param path_file: (required) the path to the file
    :type path_file: str
    :param attr_dict: (required) dictionary of attributes for the LICENSE file defined in ``package_files``
    :type attr_dict: dict
    :param filename: (required) name of the license file
    :type filename: str
    :param _: (unused) other unused named args
    :type _: dict
    :return: a failing issue if the license is the default, a info issue otherwise telling the validator to manually check the license for correctness
    :rtype: list[SDKValidateIssue]
    """

    # render jinja file of LICENSE
    template_rendered = sdk_helpers.setup_env_and_render_jinja_file(
        constants.PACKAGE_TEMPLATE_PACKAGE_DIR,
        filename,
        license_content=constants.CODEGEN_DEFAULT_LICENSE_CONTENT
    )

    # read the contents of the package's LICENSE file
    file_contents = "".join(sdk_helpers.read_file(path_file))

    if template_rendered in file_contents:
        # the template is still in the file
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg"),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution").format(path_file)
        )]
    else:
        # the license given in the package is not the default.
        # still infos because the validator should manually check that
        # the license is one of the acceptable formats (MIT, apache, or BSD)
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_INFO,
            solution=attr_dict.get("pass_solution")
        ),
        SDKValidateIssue(
            name=attr_dict.get("name"),
            description="LICENSE contents:\n\t\t" + file_contents.replace("\n", "\n\t\t"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )]

def package_files_validate_readme(path_package, path_file, filename, attr_dict, **_):
    """
    Validates a given README.md file.
    Checks the following:
      - Does the file match the **codegen** template? If yes, fail as that means *docgen* hasn't been run
      - Does the file still contain the secret docgen placeholder string? If so, fail as that means the dev hasn't manually updated
      - Does the file still have any TODO's? If so, fail as those must be manually implemented
      - Does the file have any incorrect or ghost links to screenshot files? If so, fail as those need to be correct
      - Else the validation passes

    It is possible for multiple checks to fail in this validation thus the use of the 
    list[SDKValidateIssue] return type.

    :param path_package: (required) the path to the package
    :type path_package: str
    :param path_file: (required) the path to the file
    :type path_file: str
    :param filename: (required) the name of the file being validated
    :type filename: str
    :param attr_dict: (required) dictionary of attributes for the customize.py file defined in ``package_files``
    :type attr_dict: dict
    :param _: (unused) other unused named args
    :type _: dict
    :return: a passing issue if the README.md passes the validations outlined above; failing issue otherwise
    :rtype: list[SDKValidateIssue]
    """

    # list of issues from README
    issues = []

    # read the package's file
    file_contents = sdk_helpers.read_file(path_file)
    # render codegen jinja file
    codegen_readme_rendered = sdk_helpers.setup_env_and_render_jinja_file(
        constants.PACKAGE_TEMPLATE_PATH,
        filename,
        sdk_version=sdk_helpers.get_resilient_sdk_version()
    )
    # split template file into list of lines
    template_contents = codegen_readme_rendered.splitlines(True)
    # compare given file to template from codegen
    s_diff = difflib.SequenceMatcher(None, file_contents, template_contents)

    # check match between the two files
    # if the package file matches the codegen template, fail
    comp_ratio = s_diff.ratio()
    if comp_ratio == MATCH_THRESHOLD:
        # if it matches the codegen template, we return immediately and don't run any other checks
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_codegen_msg"),
            severity=attr_dict.get("fail_codegen_severity"),
            solution=attr_dict.get("fail_codegen_solution").format(path_package)
        )]

    # if placeholder string is still in the readme
    if any("<!-- {0} -->".format(constants.DOCGEN_PLACEHOLDER_STRING) in line for line in file_contents):
        issues.append(SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_placeholder_msg").format(constants.DOCGEN_PLACEHOLDER_STRING),
            severity=attr_dict.get("fail_placeholder_severity"),
            solution=attr_dict.get("fail_placeholder_solution").format(constants.DOCGEN_PLACEHOLDER_STRING)
        ))

    # fail if there are any "TODO"'s remaining
    if any("TODO" in line for line in file_contents):
        issues.append(SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_todo_msg"),
            severity=attr_dict.get("fail_todo_severity"),
            solution=attr_dict.get("fail_todo_solution")
        ))

    # check that linked screenshots are in the /docs/screenshots folder

    # gather list of screenshots in the readme file
    try:
        screenshot_paths = package_helpers.parse_file_paths_from_readme(file_contents)
        invalid_paths = []
    except SDKException as e:
        # if links aren't properly formatted in the readme, they won't pass
        err_msg = str(e).replace("\n", " ")
        err_msg = err_msg[err_msg.index("ERROR: ")+len("ERROR: "):]
        issues.append([SDKValidateIssue("README.md link syntax error", err_msg)])

    # for each gathered path, check if the file path is valid
    for path in screenshot_paths:
        try:
            sdk_helpers.validate_file_paths(os.R_OK, os.path.join(path_package, path))
        except SDKException:
            invalid_paths.append(path)

    if invalid_paths:
        issues.append(SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_screenshots_msg").format(invalid_paths),
            severity=attr_dict.get("fail_screenshots_severity"),
            solution=attr_dict.get("fail_screenshots_solution")
        ))

    if not issues:
        # if the issues list is empty
        # the readme passes our checks -- note that this should still be manually validated for correctness!
        return [SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=attr_dict.get("pass_solution")
        )]
    else:
        # if there is at least one issue in the list
        return issues

def package_files_validate_base_image(path_file, attr_dict,**_):
    """
    Validates that the Dockerfile is using the correct base image 

    Checks the following:
      - Is a FROM statement missing
      - Are there too many FROM statements
      - If there is only one FROM statement, is it pullling from the right repo
      - Else the validation passes

    It is possible for multiple checks to fail in this validation thus the use of the 
    list[SDKValidateIssue] return type.

    :param path_file: (required) the path to the file 
    """

    # list of issues found
    issues = []
    # gets a dictionary that maps Dockercommands to all of their arguments
    # e.g. if the Dockerfile has lines "RUN yum clean", "RUN yum update", "USER 0"
    # then command_dict = {"RUN":["yum clean","yum update"],"USER":["0"]}
    command_dict = package_helpers.parse_dockerfile(path_file)

    from_command = constants.DOCKER_COMMAND_DICT["from_command"]

    if len(command_dict[from_command]) == 0: # if no FROM commands found

        issue = [SDKValidateIssue(
            attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format("Cannot find a FROM command in Dockerfile"),
            severity=attr_dict.get("fail_severity"),
            solution=attr_dict.get("fail_solution").format("adding the following line to the top of your Dockerfile - FROM {0}").format(constants.DOCKER_BASE_REPO)
        )]

    elif len(command_dict[from_command]) == 1:
        if command_dict[from_command][0] != constants.DOCKER_BASE_REPO: # if only one FROM command found but it is incorrect
            issue = [SDKValidateIssue(
                attr_dict.get("name"),
                attr_dict.get("fail_msg").format("FROM command found but it is pointing to the wrong repo"),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution").format("changing the repo to '{0}'").format(constants.DOCKER_BASE_REPO)
            )]

        else: # if only one FROM command is found but it is correct
            issue = [SDKValidateIssue(
                attr_dict.get("name"),
                attr_dict.get("pass_msg"),
                severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            )]
        
    elif len(command_dict[from_command]) > 1: # if more than one FROM command found

            issue = [SDKValidateIssue(
                attr_dict.get("name"),
                attr_dict.get("fail_msg").format("More than one FROM command found"),
                severity=attr_dict.get("fail_severity"),
                solution=attr_dict.get("fail_solution").format("removing any extra FROM commands")
            )]

            for command in command_dict[from_command]:
                if command != constants.DOCKER_BASE_REPO:
                    issue.extend([SDKValidateIssue(
                    attr_dict.get("name"),
                    attr_dict.get("fail_msg").format("FROM command found but it is pointing to the wrong repo"),
                    severity=attr_dict.get("fail_severity"),
                    solution=attr_dict.get("fail_solution").format("changing the repo to '{0}'").format(constants.DOCKER_BASE_REPO)
                    )])
                    break

    issues.extend(issue)
    return issues
    
def payload_samples_validate_payload_samples(path_package, package_name, attr_dict):
    """
    This function verifies:
    - (WARNING) the customize file is readable and the import definition from it contains a "functions" section
    - for each function
      - (CRITICAL) check it has a name, i.e. "fn_name"
      - (CRITICAL) investigate payload_samples/fn_name/output_json_[example|schema].json with helper method

    Returns a successful issue if all the above were valid.
    Returns an issue with the noted level if anything in the above fails.

    The function returns a list of an issue for each payload sample.
    NOTE: this function could return a list of 1 item if the customize is unreadable...

    :param path_package: the path to the package
    :type path_package: str
    :param package_name: name of the package i.e. fn_my_app
    :type package_name: str
    :param attr_dict: dictionary of attributes for the payload samples defined in ``payload_samples_attributes``
    :type attr_dict: dict
    :return: a list (this can be a mix) of passing issues and/or a critical issues
    :rtype: list[SDKValidateIssue]
    """

    # get function list from import definition in customize.py file
    path_customize = os.path.join(path_package, package_name, package_helpers.PATH_CUSTOMIZE_PY)
    try:
        # parse import definition information from customize.py file
        # this will raise an SDKException if something goes wrong
        sdk_helpers.validate_file_paths(os.R_OK, path_customize)
        import_def = package_helpers.get_import_definition_from_customize_py(path_customize)
    except SDKException:
        return [SDKValidateIssue(
            name=package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR,
            description=attr_dict.get("no_import_def_msg").format(path_customize),
            severity=attr_dict.get("no_import_def_severity"),
            solution=attr_dict.get("reload_solution").format(path_package)
        )]

    # if nothing went wrong in try-except above
    # grab functions list from import_def
    functions = import_def.get("functions")

    # make sure that the import def has a "functions" section
    if not functions:
        return [SDKValidateIssue(
            name=package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR,
            description=attr_dict.get("no_func_msg").format(path_customize),
            severity=attr_dict.get("no_func_severity"),
            solution=attr_dict.get("reload_solution").format(path_package)
        )]

    # loop through each function to get the name
    # it is unlikely but possible that the name is missing from the
    # import def so that is checked for here just in case and will
    # create an appropriate issue for that function but will then continue on
    # to the next function
    issues = []
    for function in functions:
        func_name = function.get("name")

        # if the name is missing
        if not func_name:
            issues.append(SDKValidateIssue(
                name=package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR,
                description=attr_dict.get("no_func_name_msg").format(function),
                severity=attr_dict.get("no_func_name_severity"),
                solution=attr_dict.get("reload_solution").format(path_package)
            ))
        else:
            issues.append(_validate_payload_samples(path_package, func_name, attr_dict))

    return issues

def _validate_payload_samples(path_package, func_name, attr_dict):
    """
    Helper method to validate a payload sample set for a given function.

    Looks in payload_samples/func_name/output_json_[example|schema].json
    and verifies that each file is:
    - present
    - valid json
    - not empty

    If all the above pass, a passing issue is given for the function and its associated payloads.
    If one of the above fails, a critical issue is raised.

    It is worth noting the implementation of this will fail once one of the two files fails
    but it will check the second file before returning an issue. Example:
    If the example is invalid JSON but the schema is valid, youd get a message like:
        'output_json_example.json' for 'mock_function_one' not valid JSON

    But if both were invalid JSON the message would say:
        'output_json_example.json' and 'output_json_schema.json' for 'mock_function_one' not valid JSON

    :param path_package: path to the package
    :type path_package: str
    :param func_name: name of the function, i.e. fn_my_func_1
    :type func_name: str
    :param attr_dict: dictionary of attributes for the payload samples defined in ``payload_samples_attributes``
    :type attr_dict: dict
    :return: one SDKValidateIssue indicating the validity of the samples for a payload
    :rtype: SDKValidateIssue
    """

    path_samples_dir = os.path.join(path_package, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR, func_name)
    issue_name = "'{0}'".format(os.path.join(package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR, func_name))

    path_samples_example = os.path.join(path_samples_dir, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)
    path_samples_schema = os.path.join(path_samples_dir, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)

    example_str = "'{0}'".format(package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)
    schema_str = "'{0}'".format(package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)

    ## check that the samples are present ##
    # list used to generate message that might include both or just one
    # this way we can get message that say something like 'example' and 'schema' are missing
    # rather than just 'schema' is missing
    samples_missing = []
    try: 
        sdk_helpers.validate_file_paths(os.R_OK, path_samples_example)
    except SDKException:
        samples_missing.append(example_str)
    try:
        sdk_helpers.validate_file_paths(os.R_OK, path_samples_schema)
    except SDKException:
        samples_missing.append(schema_str)

    if samples_missing:
        msg = " and ".join(samples_missing) # if just one element, it will not add the "and"
        return SDKValidateIssue(
            name=issue_name,
            description=attr_dict.get("payload_file_missing_msg").format(msg, func_name),
            severity=attr_dict.get("payload_file_missing_severity"),
            solution=attr_dict.get("reload_solution").format(path_package)
        )

    ## check that the samples are valid JSON ##
    # same idea as above
    samples_invalid = []
    try:
        read_example_json = sdk_helpers.read_json_file(path_samples_example)
    except SDKException:
        samples_invalid.append(example_str)
    try:
        read_schema_json = sdk_helpers.read_json_file(path_samples_schema)
    except SDKException:
        samples_invalid.append(schema_str)

    if samples_invalid:
        msg = " and ".join(samples_invalid)
        return SDKValidateIssue(
            name=issue_name,
            description=attr_dict.get("payload_file_invalid_msg").format(msg, func_name),
            severity=attr_dict.get("payload_file_invalid_severity"),
            solution=attr_dict.get("reload_solution").format(path_package)
        )

    ## finally make sure the samples are not empty ##
    # (which is the codegen default before --gather-results is run)
    samples_empty = []
    if not read_example_json:
        samples_empty.append(example_str)
    if not read_schema_json:
        samples_empty.append(schema_str)
    
    if samples_empty:
        msg = " and ".join(samples_empty)
        return SDKValidateIssue(
            name=issue_name,
            description=attr_dict.get("payload_file_empty_msg").format(msg, func_name),
            severity=attr_dict.get("payload_file_empty_severity"),
            solution=attr_dict.get("payload_file_empty_solution").format(path_package)
        )

    ## return a passing issue here ##
    return SDKValidateIssue(
        name=issue_name,
        description=attr_dict.get("pass_msg").format(func_name),
        severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
        solution=attr_dict.get("pass_solution")
    )




def tox_tests_validate_tox_installed(attr_dict, **__):
    """
    Helper method for to validate that tox is installed in the python environment.

    If tox is not installed, return -1 indicating that the test didn't quite "fail" but rather
    was skipped.

    :param attr_dict: dictionary of attributes for the customize.py file defined in ``tests_attributes``
    :type attr_dict: dict
    :param __: (unused) other unused named args
    :type __: dict
    :return: -1 or 1 and a SDKValidateIssue with details about whether tox was installed in the env
    :rtype: int, SDKValidateIssue
    """
    LOG.debug("Validating that '{0}' is installed in the python env".format(constants.TOX_PACKAGE_NAME))
    

    tox_version = sdk_helpers.get_package_version(constants.TOX_PACKAGE_NAME)

    # not installed
    if not tox_version:
        return -1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(constants.TOX_PACKAGE_NAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution").format(constants.TOX_PACKAGE_NAME)
        )
    elif sdk_helpers.parse_version_object(tox_version) < constants.TOX_MIN_PACKAGE_VERSION:
        return -1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("upgrade_msg").format(constants.TOX_PACKAGE_NAME, tox_version, constants.TOX_MIN_PACKAGE_VERSION),
            severity=attr_dict.get("upgrade_severity"),
            solution=attr_dict.get("upgrade_solution")
        )
    else:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg").format(constants.TOX_PACKAGE_NAME),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )

def tox_tests_validate_tox_file_exists(path_package, attr_dict, **__):
    """
    Helper method for to validate that tox.ini file exists in the package.

    If the file isn't present, return -1 as it is optional to have tests but we 
    don't want to continue validating the tests

    :param path_package: path to package
    :type path_package: str
    :param attr_dict: dictionary of attributes for the customize.py file defined in ``tests_attributes``
    :type attr_dict: dict
    :param __: (unused) other unused named args
    :type __: dict
    :return: -1 or 1 and a SDKValidateIssue with details about whether tox.ini file exists
    :rtype: int, SDKValidateIssue
    """
    LOG.debug("Validating that {0} file is present in package".format(constants.TOX_INI_FILENAME))

    path_tox_ini_file = os.path.join(path_package, constants.TOX_INI_FILENAME)

    try:
        sdk_helpers.validate_file_paths(os.R_OK, path_tox_ini_file)
    except SDKException:
        return -1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(constants.TOX_INI_FILENAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution").format(constants.TOX_INI_FILENAME)
        )

    return 1, SDKValidateIssue(
        name=attr_dict.get("name"),
        description=attr_dict.get("pass_msg").format(constants.TOX_INI_FILENAME),
        severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
        solution=""
    )

def tox_tests_validate_min_env_version(path_package, attr_dict, **__):
    """
    Helper method for to validate that tox.ini file doesn't have any invalid envlist values

    Here we check for any amount of ``py3[x]`` where ``x in [TOX_MIN_ENV_VERSION[-1] - 9]``
    If any envlist value of py27 or other invalid value, WARN the user, however, continue the validation
    (thus the value 1 returned in the first position for each possible outcome)

    :param path_package: path to package
    :type path_package: str
    :param attr_dict: dictionary of attributes for the customize.py file defined in ``tests_attributes``
    :type attr_dict: dict
    :param __: (unused) other unused named args
    :type __: dict
    :return: 1 and a SDKValidateIssue with details about the envlist found in the tox.ini file
    :rtype: int, SDKValidateIssue
    """
    LOG.debug("Validating that valid envlist in {0} file".format(constants.TOX_INI_FILENAME))

    # this regex allows for any number of constants.TOX_MIN_ENV_VERSION[-1] envs (3.x or greater where x is the last character of the constant) in the envlist
    contents_to_check = r"(envlist\s*=\s*(py3[{0}-9]),*\s*(py3[{0}-9],*)*)$".format(constants.TOX_MIN_ENV_VERSION[-1])

    path_tox_ini_file = os.path.join(path_package, constants.TOX_INI_FILENAME)
    tox_ini_contents = " ".join(line for line in sdk_helpers.read_file(path_tox_ini_file) if not line.startswith("#"))

    matches = re.findall(contents_to_check, tox_ini_contents, flags=re.MULTILINE)

    if "envlist" not in tox_ini_contents:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("missing_msg").format(constants.TOX_MIN_ENV_VERSION, constants.TOX_INI_FILENAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("missing_solution").format(constants.TOX_MIN_ENV_VERSION)
        )
    elif not matches:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(constants.TOX_INI_FILENAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution").format(constants.TOX_MIN_ENV_VERSION)
        )
    else:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg").format("envlist=", constants.TOX_INI_FILENAME),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )

def tox_tests_run_tox_tests(path_package, attr_dict, tox_args=None, path_sdk_settings=None, **__):
    """
    Helper method for to run and parse the tox tests

    This method runs tox as a subprocess and parses the results from that test run (those results are
    written to a temporary xml file for easier parsing).

    There are three ways for the tox arguemnts that are necessary for running resilient apps tests
    to get passed in (these are checked in this order as well):
    1. use the --tox-args (see cmds.validate for details)
            given in the format: 

    .. code-block:: bash
        resilient-sdk validate -p . --tests --tox-args arg1="val1" arg2="val2"

    2. use a sdk settings file by either passing the path to the file using --settings or by having a 
       properly configured sdk settings file in the default ~/.resilient/.sdk_settings.json path
            given in JSON format: 

    .. code-block:: json
        {
            "tox-args": {
                "resilient_email": "test@example.org",
                "resilient_password": "pwd_from_json",
                "resilient_host": "example.org",
                "resilient_org": "example org json"
            }
        }

    3. if there is no --tox-args provided and no --settings file found, the validate command will
       provide default tox args using ``constants.TOX_TESTS_DEFAULT_ARGS`` but will warn the user that
       default args are being used

    Whichever way the args are provided, they are all parsed into the correct format that is 
    useable in the subprocess call to tox.

    :param path_package: path to package
    :type path_package: str
    :param attr_dict: dictionary of attributes for the customize.py file defined in ``tests_attributes``
    :type attr_dict: dict
    :param tox_args: (optional) list of tox_args parsed by the argparser from the command line
    :type tox_args: list[str]
    :param path_sdk_settings: (optional) path to a sdk settings JSON file
    :type path_sdk_settings: str
    :param __: (unused) other unused named args
    :type __: dict
    :return: 1 or 0 and a SDKValidateIssue with details about the tox tests
    :rtype: int, SDKValidateIssue
    """
    LOG.debug("Running tox tests")

    # figure out where to parse the args from
    # either from 1. tox-args, 2. sdk_settings.json file, or 3. defaults (more details above)
    args = []
    if tox_args:
        LOG.debug("Reading tox args from command line flag --tox-args")

        # parse --tox-args flag values which come in as <attr1>="<value1>" <attr2>="<value2>" 
        for arg in tox_args:
            match = re.search(r"(\w+)=[\"\']?(\w+)[\"\']?", arg)
            if not match or len(match.groups()) != 2:
                LOG.warn("WARNING: skipping argument '{0}' given in --tox-args flag that doesn't match format attr=\"value\"".format(arg))
                continue

            # append attr, val at the end the args list [..., "--attr", "val", ...]
            attr, val = match.group(1), match.group(2)

            if len(attr) == 1:
                dashes = "-"
            else:
                dashes = "--"
            args.append("{0}{1}".format(dashes, attr))
            args.append(val)

    elif path_sdk_settings and os.path.exists(path_sdk_settings):
        # if path to sdk settings JSON file was given and it exists
        # this check for existence is necessary as validate._validate_tox_tests will
        # call this with the default path; so we have to check
        # that the sdk settings file exists
        LOG.debug("Reading tox args from sdk settings JSON file {0}".format(path_sdk_settings))

        setting_file_contents = sdk_helpers.read_json_file(path_sdk_settings, "validate")
        if setting_file_contents.get("tox-args"):
            for arg in setting_file_contents.get("tox-args"):
                # append attr, val at the end the args list [..., "--attr", "val", ...]
                if len(arg) == 1:
                    dashes = "-"
                else:
                    dashes = "--"
                args.append("{0}{1}".format(dashes, arg))
                args.append(setting_file_contents.get("tox-args").get(arg))
        else:
            # use defaults because given sdk settings file doesn't have the right format
            LOG.warn("WARNING: Given sdk settings file at {1} doesn't contain a 'tox-args' section.\nUsing mock args: {0}. -h for more info".format(constants.TOX_TESTS_DEFAULT_ARGS, path_sdk_settings))
            args.extend(constants.TOX_TESTS_DEFAULT_ARGS)

    else:
        # defaults for SOAR apps, custom values can be passed in using the --tox-args flag which
        # is parsed above
        LOG.warn("Using mock args: {0}. -h for more info".format(constants.TOX_TESTS_DEFAULT_ARGS))
        args.extend(constants.TOX_TESTS_DEFAULT_ARGS)


    # open a temporary directory where the temp xml report file will be created
    with sdk_helpers.ContextMangerForTemporaryDirectory() as path_temp_test_report_dir:
        path_temp_test_report = os.path.join(path_temp_test_report_dir, "tmp_test_report.xml")

        args = ["tox", "--", "--junitxml", "{0}".format(path_temp_test_report)] + args

        # run tox as a subprocess 
        _, details = sdk_helpers.run_subprocess(args, change_dir=path_package, cmd_name="tox tests")

        if os.path.exists(path_temp_test_report):
            # xml report file should still exist
            test_count, failure_count, error_count, error_str, failure_str = _tox_tests_parse_xml_report(path_temp_test_report)
            pass_count = test_count - failure_count

        else:
            # something went wrong during the subprocess execution such that
            # the xml report file was never generated
            # set "error" defaults for the test_count, failure_count, etc...
            test_count, failure_count, error_count, error_str, failure_str = -1, -1, -1, "", ""


    if failure_count == 0 and error_count == 0:
        # no errors or failures, the tests succeeded!
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg").format(pass_count),
            severity=SDKValidateIssue.SEVERITY_LEVEL_INFO,
            solution=""
        )

    # if the tests didn't succeed, we'll need to get the failures (and possibly errors)
    # and construct an SDKValidateIssue with that info
    description = ""

    # gather failure info if present
    if failure_count > 0:
        description += attr_dict.get("fail_msg").format(failure_count, failure_str.replace("\n", "\n\t\t"))

    # gather error info if present
    if error_count > 0:
        description += attr_dict.get("error_msg").format(error_count, error_str.replace("\n", "\n\t\t"))


    # something else - give full log (hopefully this doesn't happen)
    if (error_count < 0 and failure_count < 0) or (failure_str == "" and error_str == ""):
        description += u"Something went wrong... Details:\n\n\t\t{0}\n".format(details.replace("\n", "\n\t\t"))

    return 0, SDKValidateIssue(
        name=attr_dict.get("name"),
        description=description,
        severity=attr_dict.get("severity"),
        solution=attr_dict.get("solution")
    )


def _tox_tests_parse_xml_report(path_xml_file):
    """
    The xml tree then should follow this format

    .. code-block:: xml
        <testsuites>
            <testsuite>
                <testcase>
                    <failure>
                    <error>

    If it is not in the correct format, (-1, -1, -1, "", "") will be returned as a default

    If there are errors, a string of [case_name]: [case_error] is created
    If there are failures, a string of the failure text (usually tracebacks and context code) 
    is created from the xml report text

    :param path_xml_file: path to a pytest xml report
    :type path_xml_file: str
    :return: the count of tests, failures, errors, and error and failure strings
    :rtype: (int, int, int, str, str)
    """

    num_tests, num_failures, num_errors, failure_str, error_str = 0, 0, 0, "", ""

    tree = ET.parse(path_xml_file)
    root = tree.getroot()

    # assure that root element of the xml tree is "testsuites"
    if root.tag == "testsuites":
        # loop over each test suite
        for suite in root:
            # parse out test suite info
            attrs = suite.attrib
            num_tests += int(attrs.get("tests", 0))
            num_failures += int(attrs.get("failures", 0))
            num_errors += int(attrs.get("errors", 0))
            
            # loop over each test case to get failure and error info
            for case in suite:
                for elem in case:
                    if elem.tag == "failure":
                        failure_str += u"{0}\n\n---\n\n".format(elem.text)
                    elif elem.tag == "error":
                        error_str += u"{0}: {1}\n".format(case.attrib.get("classname"), elem.attrib.get("message"))
    else:
        # if the root wasn't test suites 
        LOG.warn("WARNING: XML report generated by tox run was not readable. Consider upgrading tox and pytest to the latest versions")
        return -1, -1, -1, "", ""



    return num_tests, num_failures, num_errors, error_str, failure_str



def pylint_validate_pylint_installed(attr_dict, **__):
    """
    Helper method for to validate that pylint is installed in the python environment.

    If pylint is not installed, return -1 indicating that the pylint scan didn't "fail" but rather
    was skipped.

    :param attr_dict: dictionary of attributes for the pylint scan defined in ``pylint_attributes``
    :type attr_dict: dict
    :param __: (unused) other unused named args
    :type __: dict
    :return: -1 or 1 and a SDKValidateIssue with details about whether pylint was installed in the env
    :rtype: (int, SDKValidateIssue)
    """
    LOG.debug("Validating that '{0}' is installed in the python env".format(constants.PYLINT_PACKAGE_NAME))


    pylint_version = sdk_helpers.get_package_version(constants.PYLINT_PACKAGE_NAME)

    # not installed
    if not pylint_version:
        return -1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(constants.PYLINT_PACKAGE_NAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution").format(constants.PYLINT_PACKAGE_NAME)
        )
    # version needs to be 2.12 or greater in python 3
    # python 2 does not have this issue
    elif sys.version_info.major >= 3 and sdk_helpers.parse_version_object(pylint_version) < constants.PYLINT_MIN_VERSION:
        return -1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("upgrade_msg").format(constants.PYLINT_PACKAGE_NAME, pylint_version, constants.PYLINT_MIN_VERSION),
            severity=attr_dict.get("upgrade_severity"),
            solution=attr_dict.get("upgrade_solution")
        )
    else:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg").format(constants.PYLINT_PACKAGE_NAME),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )

def pylint_run_pylint_scan(path_package, package_name, attr_dict, path_sdk_settings=None, **__):
    """
    Run Pylint Scan on whole package using the .pylintrc file in /data/validate as the default settings.
    Raises a SDKException if ``pylint`` isn't installed. In use with ``validate``, this method should 
    only be called after successfully calling ``pylint_validate_pylint_installed``. If a call to that method
    returns a failing SDKValidateIssue, this method shouldn't be called

    The default enabled pylint levels are [E]rror and [F]atal (which combined are mapped to CRITICAL)

    The user can overwrite the default settings using an SDK Settings JSON file either in the default
    location or by using the --settings flag to pass in a path. The settings file should have a "pylint"
    attribute which is a list of pylint command line options. Example (to enable [R]efactor and [W]arnings
    as well as [E]rrors and [F]atals):
    .. code-block:: json
        {
            "pylint": [
                "--enable=R,W,E,F"
            ]
        }

    NOTE: that you can include more than just the ``enable`` option in the list. Any valid pylint command
    line args will be parsed. It is not recommended to overwrite the ``--output-format`` parameter.
    More info here: https://pylint.pycqa.org/en/latest/user_guide/run.html#command-line-options

    The user can also override the defaults by running in ``verbose`` mode using the ``-v`` flag for the SDK
    This will enable all of R,C,W,E,F and will overwrite any custom sdk settings for ``--enable``

    :param path_package: path to package
    :type path_package: str
    :param package_name: name of the package (i.e. fn_my_package)
    :type package_name: str
    :param attr_dict: dictionary of attributes for the pylint scan defined in ``pylint_attributes``
    :type attr_dict: dict
    :param path_sdk_settings: (optional) path to a sdk settings JSON file
    :type path_sdk_settings: str
    :param __: (unused) other unused named args
    :type __: dict
    :return: 1 or 0 and a SDKValidateIssue with details about the pylint scan
    :rtype: (int, SDKValidateIssue)
    """

    # Because this method requires importing pylint, it must be first installed in the env. In the
    # normal use of this method, validate will only call this if `pylint_validate_pylint_installed` passes
    if not sdk_helpers.get_package_version(constants.PYLINT_PACKAGE_NAME):
        raise SDKException("Cannot call {0} without pylint installed".format(pylint_run_pylint_scan.__name__))

    pylint_args = [os.path.join(path_package, package_name), "--rcfile={0}".format(constants.PATH_VALIDATE_PYLINT_RC_FILE)]

    # grab pylint settings from sdk settings file if given and exists
    if path_sdk_settings and os.path.exists(path_sdk_settings):
        # if a settings file exists, check if that file has a pylint
        # section which will contain a list of custom pylint command line args

        settings_file_contents = sdk_helpers.read_json_file(path_sdk_settings, "validate")

        if settings_file_contents.get("pylint") and isinstance(settings_file_contents.get("pylint"), list):
            LOG.debug("Reading pylint command line args from sdk settings JSON file {0}".format(path_sdk_settings))
            pylint_args.extend(settings_file_contents.get("pylint"))

    # if debugging is enabled, overwrite any possible "enable" flag set by the settings file
    if LOG.isEnabledFor(logging.DEBUG):
        # if debug, then add all levels of pylint "R,C,W,E,F"
        # more info: https://pylint.pycqa.org/en/latest/user_guide/output.html#source-code-analysis-section
        # because pylint support multiple entries of the "--enable" flag, this will add on to what other
        # levels are already enabled if the user is also using a SDK Settings file
        LOG.debug("In DEBUG mode: Running with R,C,W,E,F all enabled")
        pylint_args.append("--enable=R,C,W,E,F") # add in all levels of pylint issues if debugging is on

    LOG.debug("Running pylint with args: %s", str(pylint_args))

    # setup a "Text Reporter" to capture the pylint output
    pylint_output = StringIO()
    reporter = text.ColorizedTextReporter(pylint_output)

    # RUN pylint using the Run class of the pylint module
    run = lint.Run(pylint_args, reporter=reporter, exit=False)

    # capture score and counts of issues from run
    # error and warnings map directly to CRITICAL and WARNING
    # everything else is treated as INFO
    # NOTE: the value of each count will only be non-zero if the level was 
    # included in the run and there was an issue found of that given level
    # (default levels are just [E]rrors and [F]atals)

    # unfortunately, pylint before 2.12 has a different stats object
    # have to check python version first as Version objects (i.e. what is returned
    # from get_pacakge_version) don't have major and minor attributes in python 2.7
    pylint_version = sdk_helpers.get_package_version(constants.PYLINT_PACKAGE_NAME)
    if sys.version_info.major >= 3 and (pylint_version.major, pylint_version.minor) >= constants.PYLINT_MIN_VERSION:
        # python >= 3 and pylint >= 2.12
        score = run.linter.stats.global_note
        info_count = run.linter.stats.info
        refactor_count = run.linter.stats.refactor
        convention_count = run.linter.stats.convention
        warning_count = run.linter.stats.warning
        error_count = run.linter.stats.error + run.linter.stats.fatal # add fatal into error count
    else:
        # python <= 2.7
        score = run.linter.stats.get("global_note")
        info_count = run.linter.stats.get("info")
        refactor_count = run.linter.stats.get("refactor")
        convention_count = run.linter.stats.get("convention")
        warning_count = run.linter.stats.get("warning")
        error_count = run.linter.stats.get("error") + run.linter.stats.get("fatal")

    # capture text output
    run_output = pylint_output.getvalue().replace("\n", "\n\t\t")

    if sum([error_count, warning_count, convention_count, refactor_count, info_count]) > 0:
        return 0, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(score, run_output),
            # severity is based on count of errors/warnings/other
            severity=SDKValidateIssue.SEVERITY_LEVEL_CRITICAL if error_count > 0 else 
                     SDKValidateIssue.SEVERITY_LEVEL_WARN if warning_count > 0 else 
                     SDKValidateIssue.SEVERITY_LEVEL_INFO,
            solution=attr_dict.get("fail_solution") if not LOG.isEnabledFor(logging.DEBUG) else ""
        )
    else:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_INFO,
            solution=attr_dict.get("pass_solution")
        )


def bandit_validate_bandit_installed(attr_dict, **__):
    """
    Helper method for to validate that bandit is installed in the python environment.

    If bandit is not installed, return -1 indicating that the bandit scan didn't "fail" but rather
    was skipped.

    :param attr_dict: dictionary of attributes for the bandit scan defined in ``bandit_attributes``
    :type attr_dict: dict
    :param __: (unused) other unused named args
    :type __: dict
    :return: -1 or 1 and a SDKValidateIssue with details about whether bandit is installed in the env
    :rtype: (int, SDKValidateIssue)
    """
    LOG.debug("Validating that '{0}' is installed in the python env".format(constants.BANDIT_PACKAGE_NAME))


    bandit_version = sdk_helpers.get_package_version(constants.BANDIT_PACKAGE_NAME)

    # not installed
    if not bandit_version:
        return -1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(constants.BANDIT_PACKAGE_NAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution").format(constants.BANDIT_PACKAGE_NAME)
        )
    else:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg").format(constants.BANDIT_PACKAGE_NAME),
            severity=SDKValidateIssue.SEVERITY_LEVEL_DEBUG,
            solution=""
        )

def bandit_run_bandit_scan(attr_dict, path_package, package_name, path_sdk_settings=None, **__):
    """
    Run Bandit Scan on whole package using the settings defined in ``constants.BANDIT_DEFAULT_ARGS``.
    
    Raises a SDKException if ``bandit`` isn't installed. In use with ``validate``, this method should 
    only be called after successfully calling ``bandit_validate_bandit_installed``. If a call to that 
    method returns a failing SDKValidateIssue, this method shouldn't be called

    The default severity level on which the bandit scan fails is "medium" (defined as command line arg "-ll")

    The user can overwrite the default settings using an SDK Settings JSON file either in the default
    location or by using the --settings flag to pass in a path. The settings file should have a "bandit"
    attribute which is a list of bandit command line options. Example (to change level to "low" and 
    give 5 context lines):
    .. code-block:: json
        {
            "bandit": [
                "-l", "-n", "5"
            ]
        }

    NOTE: that you can include more than just the severity level in the list. Any valid bandit command
    line args will be parsed (as seen above with the "-n" arg added in).
    More info here: https://github.com/PyCQA/bandit#readme or by running ``bandit -h``

    The user can run the scan in ``verbose`` mode using the ``-v`` flag for the SDK to get output live as
    the scan is running.

    :param attr_dict: dictionary of attributes for the bandit scan defined in ``bandit_attributes``
    :type attr_dict: dict
    :param path_package: path to package
    :type path_package: str
    :param package_name: name of the package (i.e. fn_my_package)
    :type package_name: str
    :param path_sdk_settings: (optional) path to a sdk settings JSON file
    :type path_sdk_settings: str
    :param __: (unused) other unused named args
    :type __: dict
    :return: 1 or 0 and a SDKValidateIssue with details about the bandit scan
    :rtype: (int, SDKValidateIssue)
    """

    # Because this method requires importing bandit, it must be installed in the env
    if not sdk_helpers.get_package_version(constants.BANDIT_PACKAGE_NAME):
        raise SDKException("Cannot call {0} without bandit installed".format(bandit_run_bandit_scan.__name__))

    bandit_args = [constants.BANDIT_PACKAGE_NAME, "-r", os.path.join(path_package, package_name)]
    bandit_args.extend(constants.BANDIT_DEFAULT_ARGS)

    if LOG.isEnabledFor(logging.DEBUG):
        # if running validate in verbose, append verbose flag to bandit args
        bandit_args.extend(constants.BANDIT_VERBOSE_FLAG)

    # grab bandit settings from sdk settings file if given and exists
    # if either file doesn't exist or file doesn't have "bandit" section
    # append on default severity level
    if path_sdk_settings and os.path.exists(path_sdk_settings):
        # if a settings file exists, check if it has a bandit section

        settings_file_contents = sdk_helpers.read_json_file(path_sdk_settings, "validate")

        # grab the bandit section (should be a list)
        settings_bandit_section = settings_file_contents.get(constants.SDK_SETTINGS_BANDIT_SECTION_NAME)

        if settings_bandit_section and isinstance(settings_bandit_section, list):
            LOG.debug("Reading bandit command line args from sdk settings JSON file {0}".format(path_sdk_settings))
            LOG.debug("Bandit settings found in settings file: {0}".format(settings_bandit_section))
            bandit_args.extend(settings_bandit_section)
        else:
            bandit_args.extend(constants.BANDIT_DEFAULT_SEVERITY_LEVEL)
    else:
        bandit_args.extend(constants.BANDIT_DEFAULT_SEVERITY_LEVEL)

    # run bandit as a subprocess 
    exit_code, details = sdk_helpers.run_subprocess(bandit_args, cmd_name="bandit scan")


    # bandit will return a non-zero exit code if an issue of minimum severity level or higher
    # is found.
    # Example: if "-ll" (our default level which is called "medium") is passed, the process
    #          will only return a non-zero code if there are "medium" or "high" issues.
    #          if only "low" or "uncategorized" issues are found, it will return 0
    if exit_code != 0:
        # all information above the "Test results" are not really relevant
        # but incase that string is not found, we just take the whole details
        details_start_string = "Test results"
        if details.index(details_start_string) != -1:
            details = details[details.index(details_start_string):]
        details = details.replace("\n", "\n\t\t")
        return 0, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(details),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution") if not LOG.isEnabledFor(logging.DEBUG) else ""
        )
    else:
        # success
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("pass_msg"),
            severity=SDKValidateIssue.SEVERITY_LEVEL_INFO,
            solution=attr_dict.get("pass_solution")
        )

