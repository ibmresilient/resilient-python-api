# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""
    Script to call SonarQube API and get the current status of a Project
    for the specific branch

    Takes 4 parameters:
        1: SONAR_QUBE_URL: "https://sonarqube.secintel.intranet.ibm.com"
        2: SONAR_QUBE_TOKEN: "xxxxxxxxxxxx"
        3: SONAR_QUBE_PROJ_KEY: same as in the sonar-project.properties file e.g. "apps-team-soarapps:python-api"
        4: SONAR_QUBE_BRANCH: the branch name the analysis is associated with

    Usage:
        $ python "https://sonarqube.secintel.intranet.ibm.com" "<SONAR_QUBE_TOKEN>" "<SONAR_QUBE_PROJ_KEY>" "<SONAR_QUBE_BRANCH>"

    Dependencies on:
    pip install requests
"""

import sys

import requests
from retry import retry

if sys.version_info.major == 3:
    from urllib.parse import quote_plus

else:
    from urllib import quote_plus

args = sys.argv

assert len(args) == 5

SCRIPT_NAME = args[0]

SONAR_QUBE_URL = args[1]
SONAR_QUBE_TOKEN = args[2]
SONAR_QUBE_PROJ_KEY = args[3]
SONAR_QUBE_BRANCH = args[4]
SONAR_QUBE_API_ENDPOINT = "api/qualitygates/project_status"
SONAR_QUBE_PROJ_STATUS_OK = "OK"


def print_msg(msg):
    div = "-----------------------"
    print("\n{0}\n{1}\n{0}\n".format(div, msg))


def get_analysis_url(base_url, project_key, branch):
    """
    Returns a safe url for the SonarQube analysis
    """
    quoted_key = quote_plus(project_key)
    quoted_branch = quote_plus(branch)

    the_url = "{0}/dashboard?id={1}&branch={2}".format(base_url, quoted_key, quoted_branch)

    return the_url


@retry(tries=3, delay=5)
def get_analysis_status(url, auth, params):
    """
    Calls GET method on ``url`` with the given auth and params

    If a HTTPException is raised, will retry the call 3 times every 5 seconds
    to see if gets result - as sometimes the report may not be ready straight away
    """
    r = requests.get(url=url, auth=auth, params=params)
    r.raise_for_status()
    return r


print_msg("Getting SonarQube analysis status for '{0}' on branch '{1}'".format(SONAR_QUBE_PROJ_KEY, SONAR_QUBE_BRANCH))

url = "{0}/{1}".format(SONAR_QUBE_URL, SONAR_QUBE_API_ENDPOINT)

params = {
    "projectKey": SONAR_QUBE_PROJ_KEY,
    "branch": SONAR_QUBE_BRANCH
}

auth = requests.auth.HTTPBasicAuth(SONAR_QUBE_TOKEN, "")

try:
    response = get_analysis_status(url, auth, params)
except requests.exceptions.HTTPError as err:
    print_msg(u"Error getting project status.\nError Code: {0}\nError: {1}".format(err.response.status_code, err.response.text))
    exit(1)

response_json = response.json()

status = response_json.get("projectStatus", {}).get("status", "ERROR")

analysis_url = get_analysis_url(SONAR_QUBE_URL, SONAR_QUBE_PROJ_KEY, SONAR_QUBE_BRANCH)

print_msg("SonarQube analysis for '{0}' on branch '{1}' is '{2}' and can be viewed at: {3}".format(SONAR_QUBE_PROJ_KEY, SONAR_QUBE_BRANCH, status, analysis_url))

if status != SONAR_QUBE_PROJ_STATUS_OK:
    exit(1)
