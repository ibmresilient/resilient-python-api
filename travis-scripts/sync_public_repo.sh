#!/bin/bash -e

# param $1: (required) branch name to push to. Accepted values are: ALL, gh-pages or master.

###############
## Variables ##
###############
BRANCHES_TO_SYNC=$1

cd $TRAVIS_BUILD_DIR

###############
## Functions ##
###############
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

###########
## Start ##
###########
print_msg "\
BRANCHES_TO_SYNC:\t$BRANCHES_TO_SYNC \n\
"

if [ "$BRANCHES_TO_SYNC" == "ALL" ] || [ "$BRANCHES_TO_SYNC" == "gh-pages" ] ; then
    git clone --branch=gh-pages git@github.ibm.com:Resilient/resilient-python-api.git gh-pages-dir
    cd gh-pages-dir
    git checkout gh-pages
    git fetch && git pull
    git push https://$GH_TOKEN_PUBLIC@github.com:/ibmresilient/resilient-python-api.git gh-pages:gh-pages
    cd $TRAVIS_BUILD_DIR
fi

cd $TRAVIS_BUILD_DIR
