#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2021. All Rights Reserved.

import difflib
import logging
import os
import re
import tempfile
import shutil
import xml.etree.ElementTree as ET

import pkg_resources
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue

LOG = logging.getLogger(constants.LOGGER_NAME)

# float value in range [0, 1] that determines the cutoff at which two files are a match
MATCH_THRESHOLD = 1.0

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
    file_rendered = sdk_helpers.setup_env_and_render_jinja_file(constants.PACKAGE_TEMPLATE_PATH, filename, package_name=package_name)

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
    file_rendered = sdk_helpers.setup_env_and_render_jinja_file(constants.PACKAGE_TEMPLATE_PATH, filename, 
                    package_name=package_name, version=package_version, resilient_libraries_version=sdk_helpers.get_resilient_libraries_version_to_use())
    
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
    codegen_readme_rendered = sdk_helpers.setup_env_and_render_jinja_file(constants.PACKAGE_TEMPLATE_PATH, filename)
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

def tox_tests_validate_py36_only(path_package, attr_dict, **__):
    """
    Helper method for to validate that tox.ini file doesn't have any invalid envlist values

    Here we check for any amount of ``py3[x]`` where ``x in [6, 7, 8, 9]``
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
    LOG.debug("Validating that envlist = py36 in {0} file".format(constants.TOX_INI_FILENAME))

    # this regex allows for any number of py36 envs (3.6 or greater) in the envlist
    contents_to_check = r"(envlist\s*=\s*(py3[6-9]),*\s*(py3[6-9],*)*)$"

    path_tox_ini_file = os.path.join(path_package, constants.TOX_INI_FILENAME)
    tox_ini_contents = " ".join(line for line in sdk_helpers.read_file(path_tox_ini_file) if not line.startswith("#"))

    matches = re.findall(contents_to_check, tox_ini_contents, flags=re.MULTILINE)

    if "envlist" not in tox_ini_contents:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("missing_msg").format("envlist=", constants.TOX_INI_FILENAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("missing_solution").format("envlist=py36")
        )
    elif not matches:
        return 1, SDKValidateIssue(
            name=attr_dict.get("name"),
            description=attr_dict.get("fail_msg").format(constants.TOX_INI_FILENAME),
            severity=attr_dict.get("severity"),
            solution=attr_dict.get("fail_solution")
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
            args.append("--{0}".format(attr))
            args.append(val)

    elif path_sdk_settings and os.path.exists(path_sdk_settings):
        # if path to sdk settings JSON file was given and it exists
        # this check for existence is necessary as validate._validate_tox_tests will
        # call this with the default path; so we have to check
        # that the sdk settings file exists
        LOG.debug("Reading tox args from sdk settings JSON file {0}".format(path_sdk_settings))

        setting_file_contents = sdk_helpers.read_json_file(path_sdk_settings)
        for arg in setting_file_contents.get("tox-args"):
            # append attr, val at the end the args list [..., "--attr", "val", ...]
            args.append("--{0}".format(arg))
            args.append(setting_file_contents.get("tox-args").get(arg))

    else:
        # defaults for SOAR apps, custom values can be passed in using the --tox flag which
        # is parsed above
        LOG.warn("Mock args {0} are being used for tox args. -h for more info".format(constants.TOX_TESTS_DEFAULT_ARGS))
        args.extend(constants.TOX_TESTS_DEFAULT_ARGS)

    # a small class for safe use of tempfile mkdtemp() which requires cleanup on
    # exit. better to use this context manager class to safely create the file
    # and automatically delete on exit
    class ContextMangerForTemporaryDirectory():
        def __init__(self):  self.dir = tempfile.mkdtemp()
        def __enter__(self): return self.dir
        def __exit__(self, exc_type, exc_value, exc_traceback):  shutil.rmtree(self.dir)


    # open a temporary directory where the temp xml report file will be created
    with ContextMangerForTemporaryDirectory() as path_temp_test_report_dir:
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
    if error_count < 0 and failure_count < 0:
        description += u"Something went wrong... Details:\n\n\t\t{0}\n".format(details.replace("\n", "\n\t\t"))

    return 0, SDKValidateIssue(
        name=attr_dict.get("name"),
        description=description,
        severity=attr_dict.get("severity"),
        solution=attr_dict.get("solution")
    )


def _tox_tests_parse_xml_report(path_xml_file):
    """
    Assumes that the file coming in has "testsuites" at the root.
    The xml tree then should follow this format

    .. code-block:: xml
        <testsuites>
            <testsuite>
                <testcase>
                    <failure>
                    <error>

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



    return num_tests, num_failures, num_errors, error_str, failure_str
