#!/bin/bash -e

# TL;DR; Just run this script with "./buildall.sh XXX" where XXX
# is the build number you want.
#
# This script will build all of the projects in this directory tree.
# It finds each directory that contains a setup.py file.  It also
# updates any version.txt files to contain the current version, 
# where the current version is a combination of the major_minor
# values specified here in this file plus the build number passed
# as $1 into this script.  It leaves it up to the project setup.py
# itself to ensure that the version is properly processed.
#

readonly major_minor=27.1

readonly mydir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Find all directories with a setup.py file in them.
readonly project_dirs=$(find $mydir -name setup.py -exec dirname {} \;)

# Get the build number from the command line.
readonly bldno=$1

if [[ ! -z "$bldno" ]] && [[ $bldno -gt 0 ]]; then
    # Write the build number to each project.
    readonly version=$major_minor.$bldno

    for dir in $project_dirs; do
        version_file=$(find "$dir" -name version.txt)

        echo "Writing version $version to $version_file"

        if [[ ! -z "$version_file" ]]; then
            echo $version > $version_file
        fi
    done
else
    echo "Build number not specified - skipping version processing."
fi

# Build each of the projects.
for dir in $project_dirs; do
    # Remove any old dist files.
    rm -rf $dir/dist/*

    # Build the source distribution.
    (cd $dir && python setup.py sdist --formats=gztar)
done

