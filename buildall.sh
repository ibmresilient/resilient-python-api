#!/bin/bash -e

# TL;DR; Just run this script with "./buildall.sh XXX" where XXX
# is the version number you want.
#
# This script will build all of the projects in this directory tree.
# It finds each directory that contains a setup.py file.  It also
# updates any version.txt files to contain the current version, 
# where the current version is a combination of the major_minor
# values specified here in this file plus the build number passed
# as $1 into this script.  It leaves it up to the project setup.py
# itself to ensure that the version is properly processed.
#

    echo "HERE"


# readonly mydir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# # Find all directories with a setup.py file in them.
# readonly project_dirs=$(find $mydir -name setup.py -exec dirname {} \;)

# # Get the version number from the command line.
# readonly version_number=$1

# if [ ! -z "$version_number" ]; then
#     # Write the version as environment variable.
#     export SETUPTOOLS_SCM_PRETEND_VERSION=$version_number
# else
#     echo "Version number not specified - skipping version processing."
# fi

# # Build each of the projects.
# for dir in $project_dirs; do
#     echo "Building directory $dir"

#     # Remove any old dist files.
#     rm -rf $dir/dist/*

#     # Build the source distribution.
#     (cd $dir && python setup.py sdist --formats=gztar)
# done

# # Build the documentation.
# # (cd docs && make clean html)
