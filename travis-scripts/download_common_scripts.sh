#!/bin/bash -e

# param $1: (required) absolute path to save common scripts e.g. "$app_repo_dir/common_scripts"
# param $2: (required) raw.github.ibm.com to file to download e.g. "https://raw.github.ibm.com/Resilient/hydra-common-scripts/main/download_files_from_other_repo.py"
# param $3: (required) script to run to get the file e.g. "$app_repo_dir/download_common_scripts.py"
# Usage:
#   ./download_common_scripts.sh "$PATH_COMMON_SCRIPTS_DIR" "$GH_PATH_COMMON_SCRIPTS_REPO" "$PATH_DOWNLOAD_SCRIPT_SAVE_LOC"

# Dependencies on:
#   the environmental variable GITHUB_AUTH_TOKEN is set and has read permissions of the repo to download from
#   the environmental variable PATH_SCRIPTS_DIR is set

###############
## Variables ##
###############
PATH_COMMON_SCRIPTS_SAVE_LOC=$1
PATH_COMMON_SCRIPTS_REPO=$2
PATH_DOWNLOAD_SCRIPT_SAVE_LOC=$3
COMMON_SCRIPTS_BRANCH=$4

##################
## Check params ##
##################
if [ -z "$1" ] ; then
    echo "ERROR: Must provide absolute path to save common scripts to as first parameter"
    exit 1
fi

if [ -z "$2" ] ; then
    echo "ERROR: Must provide raw.github.ibm.com to file to download e.g. https://raw.github.ibm.com/Resilient/hydra-common-scripts/main/download_files_from_other_repo.py"
    exit 1
fi

if [ -z "$3" ] ; then
    echo "ERROR: Must provide PATH_DOWNLOAD_SCRIPT_SAVE_LOC"
    exit 1
fi

if [ -z "$4" ] ; then
    COMMON_SCRIPTS_BRANCH=main
fi

wget --header 'Authorization: token '$GITHUB_AUTH_TOKEN \
    -O $PATH_DOWNLOAD_SCRIPT_SAVE_LOC \
    $PATH_COMMON_SCRIPTS_REPO

python $PATH_DOWNLOAD_SCRIPT_SAVE_LOC "Resilient/hydra-common-scripts" "common" $PATH_COMMON_SCRIPTS_SAVE_LOC --branch_name $COMMON_SCRIPTS_BRANCH
python $PATH_DOWNLOAD_SCRIPT_SAVE_LOC "Resilient/hydra-common-scripts" "common-app-build-scripts" $PATH_SCRIPTS_DIR --branch_name $COMMON_SCRIPTS_BRANCH