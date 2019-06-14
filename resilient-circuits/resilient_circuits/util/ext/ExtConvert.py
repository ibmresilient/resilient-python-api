#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
# pylint: disable=line-too-long

""" Python Module that exposes the ExtConvert class """

import logging
import os
import tempfile
import shutil
import zipfile
import tarfile
from resilient_circuits.util.ext.ExtCreate import ExtCreate
from resilient_circuits.util.ext.ExtException import ExtException

# Get the same logger object that is used in resilient_circuits_cmd.py
LOG = logging.getLogger("resilient_circuits_cmd_logger")


class ExtConvert(ExtCreate):
    """ ExtConvert is a subclass of ExtCreate. It exposes one
    method: package_extension() """

    @staticmethod
    def __get_tar_file_path_to_extract__(tar_members, file_name):
        """Loop all the tar_members and return the path to the member that matcheds file_name.
        Raise an Exception if cannot find file_name in the tar package"""

        for member in tar_members:
            tar_file_name = os.path.split(member.name)

            if tar_file_name[1] == file_name:
                return member.name

        raise ExtException("Invalid built distribution. Could not find {0}".format(file_name))

    @staticmethod
    def __extract_file_from_tar__(filename_to_extract, tar_file, output_dir):
        """Extract the given filename to the output_dir from the given tar_file
        and return the path to the extracted file"""

        tar_members = tar_file.getmembers()

        tar_path = ExtConvert.__get_tar_file_path_to_extract__(tar_members, filename_to_extract)
        tar_file.extract(member=tar_path, path=output_dir)

        return os.path.join(output_dir, tar_path)

    @staticmethod
    def __get_required_files_from_tar_file__(path_tar_file, dict_required_files, output_dir):
        """Loop the keys of dict_required_files (which will be file names).
        Extract each file and get the path to the extracted file.
        Return a dict of each file name and its extracted path"""

        return_dict = {}

        with tarfile.open(name=path_tar_file, mode="r") as tar_file:

            for file_name in dict_required_files.keys():
                return_dict[file_name] = ExtConvert.__extract_file_from_tar__(file_name, tar_file, output_dir)

        return return_dict

    @classmethod
    def convert_to_extension(cls, path_built_distribution, custom_display_name=None):
        """ Function that converts an (old) Integration into a Resilient Extension.
        Validates then converts the given built_distribution (either .tar.gz or .zip).
        Returns the path to the new Extension.zip
        - path_built_distribution [String]:
            - If a .tar.gz: must include a setup.py, customize.py and config.py file.
            - If a .zip: must include a valid .tar.gz.
        - custom_display_name [String]: will give the Extension that display name. Default: name from setup.py file
        - The Extension.zip will be produced in the same directory as path_built_distribution"""

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
            raise ExtException("You must specify a Built Distribution. Not a Directory\nDirectory Specified: {0}".format(path_built_distribution))

        # Raise Exception if not a .tar.gz or .zip file
        if not os.path.isfile(path_built_distribution) or (not tarfile.is_tarfile(path_built_distribution) and not zipfile.is_zipfile(path_built_distribution)):
            raise ExtException("File corrupt. Supported Built Distributions are .tar.gz and .zip\nInvalid Built Distribution provided: {0}".format(path_built_distribution))

        # Validate we can read the built distribution
        cls.__validate_file_paths__(os.R_OK, path_built_distribution)

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
                extracted_required_files = cls.__get_required_files_from_tar_file__(
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
                                extracted_required_files = cls.__get_required_files_from_tar_file__(
                                    path_tar_file=path_extracted_member,
                                    dict_required_files=extracted_required_files,
                                    output_dir=path_tmp_dir)

                                LOG.info("\t\t- Found files: %s\n\t\t- Its path: %s\n\t\t- Is a valid Built Distribution!", ", ".join(extracted_required_files.keys()), path_extracted_tar)
                                break

                            except ExtException as err:
                                # If "invalid" is in the error message,
                                # then we did not find one of the required files in the .tar.gz
                                # so we warn the user, delete the extracted member and continue the loop
                                if "invalid" in err.message.lower():
                                    LOG.warning("\t\t- Failed to extract required files: %s\n\t\t- Invalid format.\n%s", ", ".join(extracted_required_files.keys()), err.message)
                                    os.remove(path_extracted_member)
                                else:
                                    raise ExtException(err)

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
                raise ExtException("Could not extract required files from given Built Distribution\nRequired Files: {0}\nDistribution: {1}".format(
                    ", ".join(extracted_required_files.keys()), path_built_distribution))

            # Create the extension
            path_tmp_the_extension_zip = cls.create_extension(
                path_setup_py_file=extracted_required_files.get("setup.py"),
                path_customize_py_file=extracted_required_files.get("customize.py"),
                path_config_py_file=extracted_required_files.get("config.py"),
                output_dir=path_tmp_dir,
                path_built_distribution=path_extracted_tar,
                custom_display_name=custom_display_name
            )

            # Copy the extension.zip to the same directory as the original built distribution
            shutil.copy(path_tmp_the_extension_zip, os.path.dirname(path_built_distribution))

            # Get the path to the final extension.zip
            path_the_extension_zip = os.path.join(os.path.dirname(path_built_distribution), os.path.basename(path_tmp_the_extension_zip))

            LOG.info("Extension created at: %s", path_the_extension_zip)

            return path_the_extension_zip

        except Exception as err:
            raise ExtException(err)

        finally:
            # Remove the tmp directory
            shutil.rmtree(path_tmp_dir)
