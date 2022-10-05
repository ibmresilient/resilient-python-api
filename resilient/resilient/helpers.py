#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common Helper Functions for the resilient library"""

import io
import json
import logging
import os
import sys

from jose import jwe

from resilient import constants

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    from urllib import unquote

    from urlparse import urlparse
else:
    # Handle PY 3 specific imports
    from urllib.parse import unquote, urlparse

LOG = logging.getLogger(__name__)

CHARS_TO_MASK = [("?", "%3F"), ("#", "%23"), ("/", "%2F")]
MASK = "_*_{0}_*_"


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


def protected_secret_exists(secret_name: str, path_secrets_dir: str = constants.PATH_SECRETS_DIR, path_jwk_file: str = constants.PATH_JWK_FILE) -> bool:
    """
    Check to see if the /etc/secrets directory, SECRET_FILE and the key.jwk file
    all exist and the user has the correct permissions to read them

    :param secret_name:  Name of the protected secret file
    :type secret_name: str
    :param path_secrets_dir: Path to the location of the encrypted secret files, defaults to constants.PATH_SECRETS_DIR, defaults to constants.PATH_SECRETS_DIR
    :type path_secrets_dir: str, optional
    :param path_jwk_file: Path to the location of the jwk.key file in a JSON format as per https://www.ietf.org/rfc/rfc7517.txt, defaults to constants.PATH_JWK_FILE
    :type path_jwk_file: str
    :return: True if all files are found and the user has the correct permission, False otherwise
    :rtype: bool
    """
    # TODO: add test
    path_secret = os.path.join(path_secrets_dir, secret_name)

    if not os.path.isdir(path_secrets_dir) or not os.access(os.R_OK):
        LOG.info("Secrets directory at '%s' does not exist or you do not have the correct permissions", path_secrets_dir)
        return False

    if not os.path.isfile(path_secret) or not os.access(os.R_OK):
        LOG.info("No protected secret found for found for '%s' or you do not have the correct permissions to read the file", secret_name)
        return False

    if not os.path.isfile(path_jwk_file) or not os.access(os.R_OK):
        LOG.info("Could not find JWK at '%s' or you do not have the correct permissions", path_jwk_file)
        return False

    return True


def get_protected_secret(secret_name: str, path_secrets_dir: str = constants.PATH_SECRETS_DIR, path_jwk_file: str = constants.PATH_JWK_FILE) -> bytes:
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
    :rtype: bytes
    """
    # TODO: add test
    LOG.info("Reading Protected Secret '%s'", secret_name)

    path_secret = os.path.join(path_secrets_dir, secret_name)
    tkn = None
    key = get_jwk(path_jwk_file)

    if not key:
        return None

    with open(path_secret, mode="r") as f:
        tkn = f.readline()

    if not tkn:
        LOG.info("File for protected secret '%s' is empty or corrupt", secret_name)
        return None

    # We need to remove new line and carriage return characters
    tkn = tkn.splitlines()[0]

    decrypted_value = jwe.decrypt(tkn, key)

    return decrypted_value


def get_jwk(path_jwk_file: str = constants.PATH_JWK_FILE) -> dict:
    """
    If the contents of the file at path is valid JSON,
    returns the contents of the file as a dictionary else
    returns None

    :param path_jwk_file: Path to JSON JWK file to read
    :type path_jwk_file: str
    :return: File contents as a dictionary or None
    :rtype: dict
    """
    # TODO: add test
    LOG.info("Getting JWK from '%s'", path_jwk_file)

    jwk = None

    with io.open(path_jwk_file, mode="rt", encoding="utf-8") as the_file:

        try:
            jwk = json.load(the_file)

        # In PY2.7 it raises a ValueError and in PY3.6 it raises
        # a JSONDecodeError if it cannot load the JSON from the file
        except (ValueError, JSONDecodeError) as err:
            LOG.info(str(err))

    if not jwk or not jwk.get("k"):
        LOG.info("JWK JSON file at '%s' is corrupt or does not in include the required 'k' attribute.\njwk: %s", path_jwk_file, jwk)
        return None

    return jwk.get("k")


def get_config_from_env(config_name: str) -> str:
    """
    Read a variable from the environment given it's
    config_name. If it does not exist, it returns None

    :param config_name: Name of the env var to get
    :type config_name: str
    :return: The value of the env var
    :rtype: str
    """
    # TODO: add test
    LOG.info("Getting environmental variable '%s'", config_name)
    return os.environ.get(config_name)
