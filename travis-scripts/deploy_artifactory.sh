#!/bin/bash -e

ARTIFACTORY_REPO_LINK=https://na.artifactory.swg-devops.com/artifactory/sec-resilient-team-integrations-generic-local

# Array to hold paths of packages to copy to Artifactory
paths_to_copy_to_artifactory=()

readonly package_names=(
    "resilient"
    "resilient-circuits"
    "resilient-sdk"
    "resilient-lib"
)

# Get the version number from the command line.
readonly version_number=$1
echo "version_number: $version_number"

# Get the repo directory
readonly repo_dir=$TRAVIS_BUILD_DIR
echo "repo_dir: $repo_dir"

if [ ! -z "$version_number" ]; then
    # Write the version as environment variable.
    export SETUPTOOLS_SCM_PRETEND_VERSION=$version_number
else
    echo "Version number not specified - skipping version processing."
fi

for p in "${package_names[@]}"; do
    # Get directory of package
    dir=$(echo $repo_dir/$p)
    echo "Building directory $dir"

    # Remove any old dist files.
    rm -rf $dir/dist/*

    # Build the source distribution.
    (cd $dir && python setup.py sdist --formats=gztar)

    # Append path to sdist to paths_to_copy_to_artifactory array
    sdist_path=$(ls $dir/dist/*.tar.gz)
    echo "Path to sdist: $sdist_path"
    paths_to_copy_to_artifactory+=($sdist_path)

done

cd $repo_dir

# Loop paths_to_copy_to_artifactory and copy to Artifactory using curl
for p in "${paths_to_copy_to_artifactory[@]}"; do
    package_name=$(basename $p)
    artifactory_path=resilient-python-api/$version_number/$package_name
    echo "copying $package_name to Artifactory at: $ARTIFACTORY_REPO_LINK/$artifactory_path"
    curl -H "X-JFrog-Art-Api:${ARTIFACTORY_API_KEY_SHANE}" -T $p "$ARTIFACTORY_REPO_LINK/$artifactory_path"
done