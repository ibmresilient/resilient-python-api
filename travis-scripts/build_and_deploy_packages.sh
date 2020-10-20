#!/bin/bash -e

if [ $1 == "do_deploy" ]; then
    deploy=true
else
    deploy=false
fi

paths_to_copy_to_artifactory=()

cd $TRAVIS_BUILD_DIR

readonly package_names=(
    "resilient"
    "resilient-circuits"
    "resilient-sdk"
    "resilient-lib"
    "pytest-resilient-circuits"
    "rc-cts"
    "rc-webserver"
)

# Write the version as environment variable.
export SETUPTOOLS_SCM_PRETEND_VERSION=$NEW_VERSION

for p in "${package_names[@]}"; do
    # Get directory of package
    dir=$(echo $TRAVIS_BUILD_DIR/$p)
    echo "Building source distribution of $dir"

    # Remove any old dist files.
    rm -rf $dir/dist/*

    # Build the source distribution.
    (cd $dir && python setup.py sdist --formats=gztar)

    # Append path to sdist to paths_to_copy_to_artifactory array
    sdist_path=$(ls $dir/dist/*.tar.gz)
    echo "Path to sdist: $sdist_path"
    paths_to_copy_to_artifactory+=($sdist_path)

done

if [ "$deploy" = true ] ; then
    # Loop paths_to_copy_to_artifactory and copy to Artifactory using curl
    for p in "${paths_to_copy_to_artifactory[@]}"; do
        package_name=$(basename $p)
        artifactory_path=$BASE_ARTIFACTORY_PATH/$package_name
        echo "copying $package_name to Artifactory at: $ARTIFACTORY_REPO_LINK/$artifactory_path"
        curl -H "X-JFrog-Art-Api:${ARTIFACTORY_API_KEY_SHANE}" -T $p "$ARTIFACTORY_REPO_LINK/$artifactory_path"
    done
fi
