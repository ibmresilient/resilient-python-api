# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""
Helper script for managing Artifactory. Ensure that the environmental variable ARTIFACTORY_API_KEY is set
"""

import os
import sys
from argparse import ArgumentParser

import requests
from retry import retry

SCRIPT_NAME = os.path.basename(sys.argv[0])

SUPPORTED_ARTIFACTORY_METHODS = ["UPLOAD", "DOWNLOAD", "DELETE"]
ARTIFACTORY_ENV_VAR_API_KEY = "ARTIFACTORY_API_KEY"
ARTIFACTORY_API_STORAGE = "/artifactory/api/storage/"
ARTIFACTORY_KEYWORD = "/artifactory/"

RETRY_TRIES = 3
RETRY_DELAY = 5  # in seconds
REQUESTS_TIMEOUT = 10  # in seconds

PARSER_DESC = """
Helper script for managing Artifactory. Ensure that the environmental variable ARTIFACTORY_API_KEY is set
"""

PARSER_USAGE = """
$ python {0} UPLOAD "https://na.artifactory.swg-devops.com/artifactory/<path_to_artifactory_dir>" --upload-files "absolute/path_to_file_1.txt"
$ python {0} UPLOAD "https://na.artifactory.swg-devops.com/artifactory/<path_to_artifactory_dir>" --upload-files "absolute/path_to_file_1.txt" "absolute/path_to_file_2.txt"

$ python {0} DOWNLOAD "https://na.artifactory.swg-devops.com/artifactory/<path_to_artifactory_dir>" --save-location "absolute/path_to_dir/on_this_instace"

$ python {0} DELETE "https://na.artifactory.swg-devops.com/artifactory/<path_to_artifactory_dir>"
$ python {0} DELETE "https://na.artifactory.swg-devops.com/artifactory/<path_to_artifactory_dir>/specific_file.txt"
""".format(SCRIPT_NAME)


def _get_args():
    """
    Setup and return the arguments used in this script
    """
    parser = ArgumentParser(description=PARSER_DESC)

    parser.usage = PARSER_USAGE

    parser.add_argument("artifactory_method",
                        help="Any one of the following supported methods: " + ", ".join(SUPPORTED_ARTIFACTORY_METHODS),
                        nargs="?",
                        type=str,
                        choices=SUPPORTED_ARTIFACTORY_METHODS)

    parser.add_argument("artifactory_location",
                        help="Location of directory in Artifactory to either upload/download/delete files to/from. If downloading a single file, can be the absolute path to that file",
                        nargs="?",
                        type=str)

    parser.add_argument("-u", "--upload-files",
                        help="Paths to files to upload",
                        nargs="*")

    parser.add_argument("-s", "--save-location",
                        help="Location of directory on the instance this script is ran to save the files to",
                        nargs="?",
                        type=str)

    return parser.parse_args()


def _get_headers():
    return {
        "X-JFrog-Art-Api": os.getenv(ARTIFACTORY_ENV_VAR_API_KEY)
    }


def _add_api_storage_to_url(url):
    """
    Returns the url with the ARTIFACTORY_API_STORAGE inserted
    """
    return url.replace(ARTIFACTORY_KEYWORD, ARTIFACTORY_API_STORAGE)


@retry(tries=RETRY_TRIES, delay=RETRY_DELAY)
def _artifactory_upload_file(url, file_obj):
    """
    Upload the given file to artifactory

    :param url: The location in artifactory to save the file
    :type url: str
    :param file_obj: An open() file stream
    :type file_obj: str
    :return: The response from artifactory
    :rtype: requests.response
    """
    r = requests.put(url=url, headers=_get_headers(), data=file_obj, timeout=REQUESTS_TIMEOUT)
    r.raise_for_status()
    return r


@retry(tries=RETRY_TRIES, delay=RETRY_DELAY)
def _artifactory_download_file(url):
    """
    Download the file from artifactory at the given url

    :param url: The location in artifactory to download the file
    :type url: str
    :return: The response from artifactory
    :rtype: requests.response
    """
    r = requests.get(url=url, headers=_get_headers(), timeout=REQUESTS_TIMEOUT)
    r.raise_for_status()
    return r


@retry(tries=RETRY_TRIES, delay=RETRY_DELAY)
def _artifactory_delete_dir_or_file(url):
    """
    Delete a location in artifactory

    If artifactory cannot find anything at ``url``, it returns a 404,
    we catch it, print a message and just return ``None``

    :param url: The location in artifactory to delete. Can be either a specific file or a directory
    :type url: str
    :return: The response from artifactory
    :rtype: requests.response
    """
    r = requests.delete(url=url, headers=_get_headers(), timeout=REQUESTS_TIMEOUT)

    if r.status_code == 404:
        msg = r.json().get("errors", [{}])[0].get("message", "Nothing to delete")
        print_msg(msg)
        return None

    r.raise_for_status()

    return r


@retry(tries=RETRY_TRIES, delay=RETRY_DELAY)
def _artifactory_get_file_list(url):
    """
    Get the list of files in a directory in artifactory

    :param url: The location in artifactory to to get a list of files for
    :type url: str
    :return: A list of strs of all files found in that directory
    :rtype: [str, str ...]
    """
    if ARTIFACTORY_API_STORAGE not in url:
        url = _add_api_storage_to_url(url)
    r = requests.get(url=url, headers=_get_headers(), timeout=REQUESTS_TIMEOUT)
    r.raise_for_status()
    file_list = r.json()

    if not file_list.get("children", {}):
        print_msg("No children found - treating this URL as a single file")
        return file_list.get("uri")

    return [f.get("uri") for f in file_list.get("children", {})]


def print_msg(msg):
    """
    Print a nicely formatted message surrounded by a divider

    :param msg: The message to print
    :type msg: str
    """
    div = "-----------------------"
    print("\n{0}\n{1}\n{0}\n".format(div, msg))


def upload_files(file_paths, base_upload_url):
    """
    Upload all files in ``file_paths`` to the location at ``base_upload_url``
    in artifactory

    :param file_paths: A list of strs of valid file paths
    :type file_paths: [str, str ...]
    :param base_upload_url: The location in artifactory to save the files
    :type base_upload_url: str
    """
    for file_path in file_paths:

        if not os.path.isfile(file_path):
            print_msg("'{0}' is not a valid file location".format(file_path))
            exit(1)

        upload_url = "{0}/{1}".format(base_upload_url, os.path.basename(file_path))

        with open(file_path, mode="r") as file_obj:

            try:
                print_msg("Attempting to upload file to '{0}'".format(upload_url))
                _artifactory_upload_file(upload_url, file_obj)
                print_msg("'{0}' uploaded!".format(upload_url))
            except requests.exceptions.HTTPError as err:
                print_msg(u"WARNING: There was an error uploading coverage report to Artifactory. \nError Code: {0}\nError: {1}".format(err.response.status_code, err.response.text))


def delete_dir_or_file(url):
    """
    Delete a location in artifactory

    If artifactory cannot find anything at ``url``, it returns a 404,
    we catch it, print a message

    :param url: The location in artifactory to delete. Can be either a specific file or a directory
    :type url: str
    """
    print_msg("Attempting to delete directory/file from '{0}'".format(url))

    r = _artifactory_delete_dir_or_file(url)

    if r:
        print_msg("Deleted: '{0}'".format(url))


def download_and_save_file(file_url, file_name, dir_save_location):
    """
    Download the file from artifactory at the given url and save it

    :param file_url: The location in artifactory to download the file
    :type file_url: str
    :param file_name: The name of the file
    :type file_name: str
    :param dir_save_location: The absolute location on this instance to save the file.
        If the directory does not exist, creates it
    :type dir_save_location: str
    """
    print_msg("Attempting to download file from '{0}'".format(file_url))

    r = _artifactory_download_file(url=file_url)

    print_msg("'{0}' downloaded!".format(file_url))

    if not os.path.isdir(dir_save_location):

        print_msg("'{0}' did not exist so creating it".format(dir_save_location))
        os.makedirs(dir_save_location)

    print_msg("Saving '{0}' to '{1}'".format(file_name, dir_save_location))

    with open("{0}/{1}".format(dir_save_location, file_name), mode="wb") as the_file:
        the_file.write(r.content)

    print_msg("Saved!")


def download_and_save_all_files(dir_url, dir_save_location):
    """
    Download all files from artifactory at the given url and save them

    If the ``dir_url`` is a single file, just download that file

    :param file_url: The location in artifactory of the directory to download the files from
    :type file_name: str
    :param dir_save_location: The absolute location on this instance to save the files.
        If the directory does not exist, creates it
    :type dir_save_location: str
    """
    print_msg("Attempting to download all files from '{0}'".format(dir_url))

    list_of_files = _artifactory_get_file_list(dir_url)

    # If its a str, its a single file
    if isinstance(list_of_files, str):
        file_url = list_of_files
        file_name = os.path.basename(file_url)
        download_and_save_file(file_url=file_url, file_name=file_name, dir_save_location=dir_save_location)

    else:
        for f in list_of_files:
            print_msg("Found '{0}'. Attempting to download and save it!".format(f))
            file_name = f[1:]
            file_url = "{0}/{1}".format(dir_url, file_name)
            download_and_save_file(file_url=file_url, file_name=file_name, dir_save_location=dir_save_location)


def main():
    """Main entry point"""

    args = _get_args()

    if args.artifactory_method == "UPLOAD":

        print_msg("'UPLOAD' Artifactory method was chosen")

        if not args.upload_files:
            print_msg("Error: No files were found to upload")
            exit(1)

        upload_files(file_paths=args.upload_files, base_upload_url=args.artifactory_location)

    elif args.artifactory_method == "DOWNLOAD":

        print_msg("'DOWNLOAD' Artifactory method was chosen")

        if not args.save_location:
            print_msg("Error: No --save-location was specified")
            exit(1)

        download_and_save_all_files(dir_url=args.artifactory_location, dir_save_location=args.save_location)

    elif args.artifactory_method == "DELETE":

        print_msg("'DELETE' Artifactory method was chosen")

        delete_dir_or_file(url=args.artifactory_location)


if __name__ == "__main__":
    main()
