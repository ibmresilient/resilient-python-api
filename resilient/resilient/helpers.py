#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common Helper Functions for the resilient library"""

import copy
import io
import json
import logging
import os
import shutil
import sys

from resilient import constants

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    from urllib import unquote

    from urlparse import urlparse
    JSONDecodeError = None  # JSONDecodeError is not available in PY2.7 so we set it to None
else:
    # Handle PY 3 specific imports
    from json.decoder import JSONDecodeError
    from urllib.parse import unquote, urlparse
    from jwcrypto import jwk, jwe


LOG = logging.getLogger(__name__)

CHARS_TO_MASK = [("?", "%3F"), ("#", "%23"), ("/", "%2F")]
MASK = "_*_{0}_*_"


def str_to_bool(value):
    """
    Convert value to either a ``True`` or ``False`` boolean

    Returns ``False`` if ``value`` is anything
    other than: ``'1', 'true', 'yes' or 'on'``

    :param value: the value to convert
    :type value: str
    :return: ``True`` or ``False``
    :rtype: bool
    """
    value = str(value).lower()
    return value in ('1', 'true', 'yes', 'on')


def mask_special_chars(s):
    """
    For any chars in CHARS_TO_MASK found in s
    replace them with their mask: _*_<URL Encoding minus the %>_*_

    Example:
    ```
    s = 'http://mockusername:mockpw%23%24%25%5E%26%2A%28%29-%2B_%3F%60%7E@192.168.0.5:3128'
    s = mask_special_chars(s)
    print(s)
    >>> 'http://mockusername:mockpw_*_23_*_%24%25%5E%26%2A%28%29-%2B__*_3F_*_%60%7E@192.168.0.5:3128'
    ```
    :param s: The string a urlencoded sting that may have characters to mask
    :type s: str
    :return: s replacing and special chars with their respective mask
    :rtype: str
    """
    if not s:
        return ""

    for c in CHARS_TO_MASK:
        mask = MASK.format(c[1][1:])
        s = s.replace(c[1], mask)
    return s


def unmask_special_chars(s):
    """
    Find any masked chars in s and replace them with their
    equivlent original character
    Example:
    ```
    s = 'mockpw_*_23_*_$%^&*()_*_3F_*_`~'
    s = unmask_special_chars(s)
    print(s)
    >>> 'mockpw#$%^&*()?`~'
    ```
    :param s: The string wanting to unmask
    :type s: str
    :return: s replaced with original chars if any
    :rtype: str
    """
    if not s:
        return ""

    for c in CHARS_TO_MASK:
        mask = MASK.format(c[1][1:])
        s = s.replace(mask, c[0])
    return s


def is_env_proxies_set():
    """
    :return: True/False if HTTP_PROXY or HTTPS_PROXY has a value
    :rtype: bool
    """
    if os.getenv(constants.ENV_HTTPS_PROXY) or os.getenv(constants.ENV_HTTP_PROXY):
        return True

    return False


def unquote_str(s):
    """
    Returns a string with the %xx replaced with their single-character
    equivalent

    If `s` None or an empty str, will just return an empty str

    :param s: String you want to unquote
    :type s: str

    :return: `s` with all %xx character replaced
    :rtype: str
    """
    if not s:
        return ""

    return unquote(s)


def get_and_parse_proxy_env_var(var_to_get=constants.ENV_HTTP_PROXY):
    """
    Get the `var_to_get` environment variable,
    and parse it returning a dictionary with the attributes:
    `scheme`, `hostname`, `port`, `username` and `password`

    `username` and `password` will be empty strings if not provided in the var

    `var_to_get` is by default HTTP_PROXY

    :param var_to_get: A str of the name of the env var to get and parse
    :type var_to_get: str
    :return: a dict included attributes with information of the proxy
    :rtype: dict
    """

    var = os.getenv(var_to_get)

    if not var:
        return {}

    var = mask_special_chars(var)
    var = unquote_str(var)
    parsed_var = urlparse(var)

    return {
        "scheme": parsed_var.scheme,
        "hostname": parsed_var.hostname,
        "port": parsed_var.port,
        "username": unmask_special_chars(parsed_var.username),
        "password": unmask_special_chars(parsed_var.password)
    }


def is_in_no_proxy(host, no_proxy_var=constants.ENV_NO_PROXY):
    """
    Return True if `host` is found in `no_proxy_var`
    else returns False

    :param host: must be a str and a fully qualified domain name or an IPv4 Address
    :type host: str
    :return: a bool whether or not `host` is in NO_PROXY env var
    :rtype: bool
    """
    if not host or not isinstance(host, str):
        return False

    no_proxy = os.getenv(no_proxy_var)

    if not no_proxy or not isinstance(no_proxy, str):
        return False

    if host in no_proxy:
        return True

    return False


def remove_tag(original_res_obj):
    """
    Return the original_res_obj with any of the "tags"
    attribute set to an empty list

    Example:
    ```
    mock_res_obj = {
        "tags": [{"tag_handle": "fn_tag_test", "value": None}],
        "functions": [
            {"export_key": "fn_tag_test_function",
            "tags": [{'tag_handle': 'fn_tag_test', 'value': None}]}
        ]
    }

    new_res_obj = remove_tag(mock_res_obj)

    Returns: {
        "tags": [],
        "functions": [
            {"export_key": "fn_tag_test_function", "tags": []}
        ]
    }
    ```
    :param original_res_obj: the res_obj you want to remove the tags attribute from
    :type original_res_obj: dict
    :return: new_res_obj: a dict with the tag attribute removed
    :rtype: dict
    """
    ATTRIBUTE_NAME = "tags"

    new_res_obj = copy.deepcopy(original_res_obj)

    if isinstance(new_res_obj, dict):

        # Set "tags" to empty list
        if new_res_obj.get(ATTRIBUTE_NAME):
            new_res_obj[ATTRIBUTE_NAME] = []

        # Recursively loop the dict
        for obj_name, obj_value in new_res_obj.items():

            if isinstance(obj_value, list):
                for index, obj in enumerate(obj_value):
                    new_res_obj[obj_name][index] = remove_tag(obj)

            elif isinstance(obj_value, dict):
                new_res_obj[obj_name] = remove_tag(obj_value)

    return new_res_obj


def is_running_in_app_host(env_var=constants.ENV_VAR_APP_HOST_CONTAINER):
    """
    Checks if the APP_HOST_CONTAINER environmental variable
    is set

    :param env_var: name of the APP_HOST_CONTAINER environmental variable, defaults to constants.ENV_VAR_APP_HOST_CONTAINER
    :type env_var: str, optional
    :return: True if it is set to 1, else False
    :rtype: bool
    """
    if not str_to_bool(get_config_from_env(env_var)):
        LOG.debug("Not running in an App Host environment")
        return False

    return True


def protected_secret_exists(secret_name, path_secrets_dir=constants.PATH_SECRETS_DIR, path_jwk_file=constants.PATH_JWK_FILE):
    """
    Check to see if the APP_HOST_CONTAINER env var is set, the /etc/secrets directory,
    the SECRET_FILE with the encrypted token and the key.jwk file all exist and
    the user has the correct permissions to read them

    :param secret_name:  Name of the protected secret file
    :type secret_name: str
    :param path_secrets_dir: Path to the location of the encrypted secret files, defaults to constants.PATH_SECRETS_DIR, defaults to constants.PATH_SECRETS_DIR
    :type path_secrets_dir: str, optional
    :param path_jwk_file: Path to the location of the jwk.key file in a JSON format as per https://www.ietf.org/rfc/rfc7517.txt, defaults to constants.PATH_JWK_FILE
    :type path_jwk_file: str
    :return: True if all files are found and the user has the correct permission, False otherwise
    :rtype: bool
    """
    path_secret = os.path.join(path_secrets_dir, secret_name)

    if not is_running_in_app_host():
        return False

    if sys.version_info.major < 3:
        LOG.warning(constants.WARNING_PROTECTED_SECRETS_NOT_SUPPORTED)
        return False

    if not os.path.isdir(path_secrets_dir) or not os.access(path_secrets_dir, os.R_OK):
        LOG.debug("Protected secrets directory at '%s' does not exist or you do not have the correct permissions. No value found for '%s'", path_secrets_dir, secret_name)
        return False

    if not os.path.isfile(path_secret) or not os.access(path_secret, os.R_OK):
        LOG.warning("No protected secret found for '%s' or you do not have the correct permissions to read the file. No value found for '%s'", secret_name, secret_name)
        return False

    if not os.path.isfile(path_jwk_file) or not os.access(path_jwk_file, os.R_OK):
        LOG.warning("Could not find JWK at '%s' or you do not have the correct permissions. No value found for '%s'", path_jwk_file, secret_name)
        return False

    return True


def get_protected_secret(secret_name, path_secrets_dir=constants.PATH_SECRETS_DIR, path_jwk_file=constants.PATH_JWK_FILE):
    """
    Get the JWK, read the token from a file with
    the secret_name and decrypt it using the JWK

    :param secret_name: Name of the protected secret file
    :type secret_name: str
    :param path_secrets_dir: Path to the location of the encrypted secret files, defaults to constants.PATH_SECRETS_DIR
    :type path_secrets_dir: str, optional
    :param path_jwk_file: Path to the location of the jwk.key file in a JSON format as per https://www.ietf.org/rfc/rfc7517.txt, defaults to constants.PATH_JWK_FILE
    :type path_jwk_file: str
    :return: The decrypted value of the protected secret
    :rtype: str
    """
    LOG.info("Reading Protected Secret '%s'", secret_name)

    if sys.version_info.major < 3:
        LOG.warning(constants.WARNING_PROTECTED_SECRETS_NOT_SUPPORTED)
        return None

    path_secret = os.path.join(path_secrets_dir, secret_name)
    tkn = None
    key = get_jwk(path_jwk_file)

    if not key:
        return None

    with io.open(path_secret, mode="r", encoding="utf-8") as f:
        tkn = f.readline()

    if not tkn:
        LOG.error("File for protected secret '%s' is empty or corrupt", secret_name)
        return None

    # We need to remove new line and carriage return characters
    tkn = tkn.splitlines()[0]

    try:
        jwetoken = jwe.JWE()
        jwetoken.deserialize(tkn)
        jwetoken.decrypt(key)
        decrypted_value = jwetoken.payload
    except Exception as err:
        LOG.error("Could not decrypt the secret. Invalid key used to decrypt the protected secret '%s'. Error Message: %s", secret_name, str(err))
        return None

    return decrypted_value.decode("utf-8")


def get_jwk(path_jwk_file=constants.PATH_JWK_FILE):
    """
    If the contents of the file at path is valid JSON,
    reads the file and uses the jwcrypto.jwk.JWK class
    get the JWK and returns it else returns None

    :param path_jwk_file: Path to JSON JWK file to read
    :type path_jwk_file: str
    :return: File contents as a jwcrypto.jwk.JWK or None
    :rtype: jwcrypto.jwk.JWK
    """
    LOG.debug("Getting JWK from '%s'", path_jwk_file)

    file_contents = None

    if not os.path.isfile(path_jwk_file) or not os.access(path_jwk_file, os.R_OK):
        LOG.warning("Could not find JWK at '%s' or you do not have the correct permissions.", path_jwk_file)
        return None

    with io.open(path_jwk_file, mode="rt", encoding="utf-8") as the_file:

        try:
            file_contents = json.load(the_file)

        except JSONDecodeError as err:
            LOG.error("JWK JSON file at '%s' is corrupt.\njwk: %s\nError: %s", path_jwk_file, jwk, str(err))
            return None

    if not file_contents:
        LOG.error("The provided JWK file at '%s' is empty", path_jwk_file)
        return None

    try:
        aes_key = jwk.JWK.from_json(json.dumps(file_contents))

    except Exception as err:
        LOG.error("Error getting JWK: %s", str(err))
        return None

    return aes_key


def remove_secrets_dir(path_secrets_dir=constants.PATH_SECRETS_DIR):
    """
    Check if we running in App Host and if the secrets directory
    exists, remove it

    :param path_secrets_dir: Path to the location of the encrypted secret files, defaults to constants.PATH_SECRETS_DIR
    :type path_secrets_dir: str, optional
    """
    if is_running_in_app_host() and os.path.isdir(path_secrets_dir):
        LOG.debug("Removing secrets directory at: '%s'", path_secrets_dir)
        shutil.rmtree(path_secrets_dir, ignore_errors=True)


def get_config_from_env(config_name):
    """
    Read a variable from the environment given it's
    config_name. If it does not exist, it returns None

    :param config_name: Name of the env var to get
    :type config_name: str
    :return: The value of the env var
    :rtype: str
    """
    LOG.debug("Getting environmental variable '%s'", config_name)
    return os.environ.get(config_name)
