#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
# pylint: disable=line-too-long

""" Python Module that exposes the Ext class """

import logging
import os
import re
import hashlib
import uuid
from resilient_circuits.util.ext.ExtException import ExtException

# Get the same logger object that is used in resilient_circuits_cmd.py
LOG = logging.getLogger("resilient_circuits_cmd_logger")


class Ext(object):
    """ The is the Super class that contains methods that are shared
    among all classes that handle creating, converting, (and in the future installing)
    Extensions"""

    def __init__(self, cmd):
        # Set the command_ran in our custom ExtException
        ExtException.command_ran = cmd

    @staticmethod
    def __write_file__(path, contents):
        """Writes the String contents to a file at path"""
        # If contents is type str, encode to bytes. Needed to support PY3
        if isinstance(contents, str):
            contents = contents.encode("utf-8")
        with open(path, "wb") as the_file:
            the_file.write(contents)

    @staticmethod
    def __read_file__(path):
        """Returns all the lines of a file at path as a List"""
        file_lines = []
        with open(path, "r") as the_file:
            file_lines = the_file.readlines()
        return file_lines

    @staticmethod
    def __has_permissions__(permissions, path):
        """Raises an exception if the user does not have the given permissions to path"""

        if not os.access(path, permissions):

            if permissions is os.R_OK:
                permissions = "READ"
            elif permissions is os.W_OK:
                permissions = "WRITE"

            raise ExtException("User does not have {0} permissions for: {1}".format(permissions, path))

    @staticmethod
    def __validate_directory__(permissions, path_to_dir):
        """Check the given path is absolute, exists and has the given permissions, else raises an Exception"""

        # Check the path is absolute
        if not os.path.isabs(path_to_dir):
            raise ExtException("The path to the directory must be an absolute path: {0}".format(path_to_dir))

        # Check the directory exists
        if not os.path.isdir(path_to_dir):
            raise ExtException("The path does not exist: {0}".format(path_to_dir))

        # Check we have the correct permissions
        Ext.__has_permissions__(permissions, path_to_dir)

    @staticmethod
    def __validate_file_paths__(permissions=None, *args):
        """Check the given *args paths exist and has the given permissions, else raises an Exception"""

        # For each *args
        for path_to_file in args:
            # Check the file exists
            if not os.path.isfile(path_to_file):
                raise ExtException("Could not find file: {0}".format(path_to_file))

            if permissions:
                # Check we have the correct permissions
                Ext.__has_permissions__(permissions, path_to_file)

    @staticmethod
    def __is_valid_url__(url):
        """Returns True if url is valid, else False. Accepted url examples are:
            "http://www.example.com", "https://www.example.com", "www.example.com", "example.com" """

        if not url:
            return False

        regex = re.compile(
            r'^(https?://)?'  # optional http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?)'  # domain/hostname
            r'(?:/?|[/?]\S+)$',  # .com etc.
            re.IGNORECASE)

        return regex.search(url) is not None

    @staticmethod
    def __is_valid_package_name__(name):
        """Returns True if name is valid, else False. Accepted name examples are:
            "fn_my_new_package" """

        if not name:
            return False

        regex = re.compile(r'^[0-9A-Z_]+$', re.IGNORECASE)

        return regex.match(name) is not None

    @staticmethod
    def __is_valid_version_syntax__(version):
        """Returns True if version is valid, else False. Accepted version examples are:
            "1.0.0" "1.1.0" "123.0.123" """
        if not version:
            return False

        regex = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')

        return regex.match(version) is not None

    @staticmethod
    def __generate_uuid_from_string__(the_string):
        """Returns String representation of the UUID of a hex md5 hash of the given string"""

        # Instansiate new md5_hash
        md5_hash = hashlib.md5()

        # Pass the_string to the md5_hash as bytes
        md5_hash.update(the_string.encode("utf-8"))

        # Generate the hex md5 hash of all the read bytes
        the_md5_hex_str = md5_hash.hexdigest()

        # Return a String repersenation of the uuid of the md5 hash
        return str(uuid.UUID(the_md5_hex_str))

    @staticmethod
    def __generate_md5_uuid_from_file__(path_to_file):
        """Returns String representation of the UUID of a hex md5 hash of the given file"""

        # Instansiate new md5_hash
        md5_hash = hashlib.md5()

        # Open a stream to the file. Read 4096 bytes at a time. Pass these bytes to md5_hash object
        with open(path_to_file, mode="rb") as the_file:
            for chunk in iter(lambda: the_file.read(4096), b''):
                md5_hash.update(chunk)

        # Generate the hex md5 hash of all the read bytes
        the_md5_hex_str = md5_hash.hexdigest()

        # Return a String repersenation of the uuid of the md5 hash
        return str(uuid.UUID(the_md5_hex_str))
