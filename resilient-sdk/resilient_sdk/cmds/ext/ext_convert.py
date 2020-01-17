#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk ext:convert` """

import logging
import os
import zipfile
import tarfile
import tempfile
import shutil
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.package_file_helpers import create_extension

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


class CmdExtConvert(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "ext:convert"
    CMD_HELP = "Convert an old (built) Integration that can be in .tar.gz or .zip format into a Resilient Extension"
    CMD_USAGE = """
    $ resilient-sdk ext:convert -p <path_to_old_built_distribution>
    $ resilient-sdk ext:convert -p <path_to_old_built_distribution> --display_name "My Custom Extension" """
    CMD_DESCRIPTION = CMD_HELP

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 type=ensure_unicode,
                                 help="(required) Path to the (old) Integration that can be in .tar.gz or .zip format",
                                 required=True)

        self.parser.add_argument("--display-name",
                                 help="The Display Name to give the Extension",
                                 nargs="?")

    @staticmethod
    def get_tar_file_path_to_extract(tar_members, file_name):
        """
        Loop all the tar_members and return the path to the member that matcheds file_name.
        Raise an SDKException if cannot find file_name in the tar package

        :param tar_members: List of members of a tar package
        :type tar_members: list

        :param file_name: Name of file to match on
        :type file_name: str

        :return: Path to the member that matcheds file_name
        :rtype: str

        :raises: SDKException
        """
        for member in tar_members:
            tar_file_name = os.path.split(member.name)

            if tar_file_name[1] == file_name:
                return member.name

        raise SDKException("Invalid built distribution. Could not find {0}".format(file_name))

    @staticmethod
    def extract_file_from_tar(filename_to_extract, tar_file, output_dir):
        """
        Extract the filename from the tar_file to the output_dir.
        Return the path to the extracted file

        :param filename_to_extract: Name of file to extract
        :type filename_to_extract: str

        :param tar_file: Filename in tar to extract
        :type tar_file: str

        :param output_dir: Path to extract file to
        :type output_dir: str

        :return: Path to extracted file
        :rtype: str
        """

        tar_members = tar_file.getmembers()

        tar_path = CmdExtConvert.get_tar_file_path_to_extract(tar_members, filename_to_extract)
        tar_file.extract(member=tar_path, path=output_dir)

        return os.path.join(output_dir, tar_path)

    @staticmethod
    def get_required_files_from_tar_file(path_tar_file, dict_required_files, output_dir):
        """
        Loop the keys of dict_required_files (which will be file names).
        Extract each file and get the path to the extracted file.
        Return a dict of each file name and its extracted path

        :param path_tar_file: Path to tar archive
        :type path_tar_file: str

        :param dict_required_files: Dictionary whose keys are file names
        :type dict_required_files: dict

        :param output_dir: Path to extract file to
        :type output_dir: str

        :return: Dictionary of file names and path to extracted file
        :rtype: dict
        """
        return_dict = {}

        with tarfile.open(name=path_tar_file, mode="r") as tar_file:

            for file_name in dict_required_files.keys():
                return_dict[file_name] = CmdExtConvert.extract_file_from_tar(file_name, tar_file, output_dir)

        return return_dict

    def execute_command(self, args):
        """
        Function that converts an (old) Integration into a Resilient Extension.
        Validates then converts the given built_distribution (either .tar.gz or .zip).
        Returns the path to the new Extension.zip.
        The Extension.zip will be produced in the same directory as path_built_distribution.

        :param args: Arguments from command line:

            -  **args.package**: path to the built distribution
                - If a .tar.gz: must include a setup.py, customize.py and config.py file.
                - If a .zip: must include a valid .tar.gz.
            -   **args.cmd**: `ext:convert` in this case
            -   **args.display_name**: will give the Extension that display name. Default: name from setup.py file
        :type args: argparse Namespace

        :return: Path to new Extension.zip
        :rtype: str
        """

        # Set name for SDKException
        SDKException.command_ran = self.CMD_NAME

        # Get absolute path_built_distribution
        path_built_distribution = os.path.abspath(args.package)

        LOG.info("Converting extension from: %s", path_built_distribution)

        path_tmp_built_distribution, path_extracted_tar = None, None

        # Dict of the required files we need to try extract in order to create an Extension
        extracted_required_files = {
            "setup.py": None,
            "customize.py": None,
            "config.py": None
        }

        # Raise Exception if the user tries to pass a Directory
        if os.path.isdir(path_built_distribution):
            raise SDKException("You must specify a Built Distribution. Not a Directory\nDirectory Specified: {0}".format(path_built_distribution))

        # Raise Exception if not a .tar.gz or .zip file
        if not os.path.isfile(path_built_distribution) or (not tarfile.is_tarfile(path_built_distribution) and not zipfile.is_zipfile(path_built_distribution)):
            raise SDKException("File corrupt. Supported Built Distributions are .tar.gz and .zip\nInvalid Built Distribution provided: {0}".format(path_built_distribution))

        # Validate we can read the built distribution
        sdk_helpers.validate_file_paths(os.R_OK, path_built_distribution)

        # Create a tmp directory
        path_tmp_dir = tempfile.mkdtemp(prefix="resilient-circuits-tmp-")

        try:
            # Copy built distribution to tmp directory
            shutil.copy(path_built_distribution, path_tmp_dir)

            # Get the path of the built distribution in the tmp directory
            path_tmp_built_distribution = os.path.join(path_tmp_dir, os.path.split(path_built_distribution)[1])

            # Handle if it is a .tar.gz file
            if tarfile.is_tarfile(path_tmp_built_distribution):

                LOG.info("A .tar.gz file was provided. Will now attempt to convert it to a Resilient Extension.")

                # Extract the required files to the tmp dir and return a dict of their paths
                extracted_required_files = self.get_required_files_from_tar_file(
                    path_tar_file=path_tmp_built_distribution,
                    dict_required_files=extracted_required_files,
                    output_dir=path_tmp_dir)

                path_extracted_tar = path_tmp_built_distribution

            # Handle if is a .zip file
            elif zipfile.is_zipfile(path_tmp_built_distribution):

                LOG.info("A .zip file was provided. Will now attempt to convert it to a Resilient Extension.")

                with zipfile.ZipFile(file=path_tmp_built_distribution, mode="r") as zip_file:

                    # Get a List of all the members of the zip file (including files in directories)
                    zip_file_members = zip_file.infolist()

                    LOG.info("\nValidating Built Distribution: %s", path_built_distribution)

                    # Loop the members
                    for zip_member in zip_file_members:

                        LOG.info("\t- %s", zip_member.filename)

                        # Extract the member
                        path_extracted_member = zip_file.extract(member=zip_member, path=path_tmp_dir)

                        # Handle if the member is a directory
                        if os.path.isdir(path_extracted_member):

                            LOG.debug("\t\t- Is a directory.\n\t\t- Skipping...")

                            # delete the extracted member
                            shutil.rmtree(path_extracted_member)
                            continue

                        # Handle if it is a .tar.gz file
                        elif tarfile.is_tarfile(path_extracted_member):

                            LOG.info("\t\t- Is a .tar.gz file!")

                            # Set the path to the extracted .tar.gz file
                            path_extracted_tar = path_extracted_member

                            # Try to extract the required files from the .tar.gz
                            try:
                                extracted_required_files = self.get_required_files_from_tar_file(
                                    path_tar_file=path_extracted_member,
                                    dict_required_files=extracted_required_files,
                                    output_dir=path_tmp_dir)

                                LOG.info("\t\t- Found files: %s\n\t\t- Its path: %s\n\t\t- Is a valid Built Distribution!", ", ".join(extracted_required_files.keys()), path_extracted_tar)
                                break

                            except SDKException as err:
                                # If "invalid" is in the error message,
                                # then we did not find one of the required files in the .tar.gz
                                # so we warn the user, delete the extracted member and continue the loop
                                if "invalid" in err.message.lower():
                                    LOG.warning("\t\t- Failed to extract required files: %s\n\t\t- Invalid format.\n%s", ", ".join(extracted_required_files.keys()), err.message)
                                    os.remove(path_extracted_member)
                                else:
                                    raise SDKException(err)

                        # Handle if it is a regular file
                        elif os.path.isfile(path_extracted_member):

                            # Get the file name
                            file_name = os.path.basename(path_extracted_member)

                            # If the file is a required one, add its path to the dict
                            if file_name in extracted_required_files:
                                LOG.info("\t\t- Found %s file", file_name)
                                extracted_required_files[file_name] = path_extracted_member

                                # Set the path to extracted tar to this zip file
                                path_extracted_tar = zip_file.filename

                            # Else its some other file, so skip
                            else:
                                LOG.debug("\t\t- It is not a .tar.gz file\n\t\t- Skipping...")
                                os.remove(path_extracted_member)

                        # if extracted_required_files contains values for all required files, then break
                        if all(extracted_required_files.values()):
                            LOG.info("\t\t- This is a valid Built Distribution!")
                            break

                        else:
                            LOG.debug("\t\t- Is not a valid .tar.gz built distribution\n\t\t- Skipping...")

            # If we could not get all the required files to create an Extension, raise an error
            if not all(extracted_required_files.values()):
                raise SDKException("Could not extract required files from given Built Distribution\nRequired Files: {0}\nDistribution: {1}".format(
                    ", ".join(extracted_required_files.keys()), path_built_distribution))

            # Create the extension
            path_tmp_the_extension_zip = create_extension(
                path_setup_py_file=extracted_required_files.get("setup.py"),
                path_customize_py_file=extracted_required_files.get("customize.py"),
                path_config_py_file=extracted_required_files.get("config.py"),
                output_dir=path_tmp_dir,
                path_built_distribution=path_extracted_tar,
                custom_display_name=args.display_name
            )

            # Copy the extension.zip to the same directory as the original built distribution
            shutil.copy(path_tmp_the_extension_zip, os.path.dirname(path_built_distribution))

            # Get the path to the final extension.zip
            path_the_extension_zip = os.path.join(os.path.dirname(path_built_distribution), os.path.basename(path_tmp_the_extension_zip))

            LOG.info("Extension created at: %s", path_the_extension_zip)

            return path_the_extension_zip

        except Exception as err:
            raise SDKException(err)

        finally:
            # Remove the tmp directory
            shutil.rmtree(path_tmp_dir)
