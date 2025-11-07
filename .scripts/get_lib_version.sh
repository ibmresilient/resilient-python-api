#!/bin/bash
set -euo pipefail

## ----------------------------------------------------------------------------
## get_lib_version.sh
## ----------------------------------------------------------------------------
## Description:
##   Determines the lib version from the latest GitHub tags
##
## Prerequisites:
##   - The following environment variables must be set:
##       - BRANCH (set by SPS) 
## ----------------------------------------------------------------------------

LATEST_TAG=$(git describe --abbrev=0 --tags)
CLEAN_TAG=${LATEST_TAG##*/} # strip any prefix
IS_MASTER=$([[ "$BRANCH" != *"master"* ]]; echo $?)
IS_RELEASE=$([[ "$BRANCH" != *"release/"* ]]; echo $?)

if [[ $IS_RELEASE -eq 1 ]]; then
    LIB_VERSION=$(echo ${BRANCH##*/} | cut -d "." -f 1,2,3,4)
else
    LIB_VERSION=$(echo $CLEAN_TAG | cut -d "." -f 1,2,3,4)
fi

echo "$LIB_VERSION"
