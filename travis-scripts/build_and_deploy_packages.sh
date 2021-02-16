#!/bin/bash -e

cd $TRAVIS_BUILD_DIR

###############
## Variables ##
###############
ARTIFACTORY_API_KEY=$ARTIFACTORY_API_KEY_SHANE
ARTIFACTORY_USERNAME=$ARTIFACTORY_USERNAME_SHANE

# Write the version as environment variable.
export SETUPTOOLS_SCM_PRETEND_VERSION=$NEW_VERSION

paths_to_copy_to_artifactory=()

# readonly package_names=(
#     "resilient"
#     "resilient-circuits"
#     "resilient-sdk"
#     "resilient-lib"
#     "pytest-resilient-circuits"
#     "rc-cts"
#     "rc-webserver"
# )

readonly package_names=(
    "resilient-sdk"
)

##################
## Check params ##
##################
if [ $1 == "do_deploy" ]; then
    deploy=true
else
    deploy=false
fi

###########
## Start ##
###########

# Write .pypirc file
sed -e "s|{{ARTIFACTORY_PYPI_REPO_URL}}|$ARTIFACTORY_PYPI_REPO_URL|" \
-e "s|{{ARTIFACTORY_USERNAME}}|$ARTIFACTORY_USERNAME|" \
-e "s|{{ARTIFACTORY_API_KEY}}|$ARTIFACTORY_API_KEY|" \
$PATH_TEMPLATE_PYPIRC > $HOME/.pypirc

for p in "${package_names[@]}"; do
    # Get directory of package
    dir=$(echo $TRAVIS_BUILD_DIR/$p)
    echo "Building source distribution of $dir"

    # Remove any old dist files.
    rm -rf $dir/dist/*

    cd $dir

    # Build the source distribution.
    if [ "$deploy" = true ] ; then
        python setup.py sdist --formats=gztar upload -r artifactory

    else
        python setup.py sdist --formats=gztar
    fi

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
        # curl -H [header including the Artifactory API Key] -T [path to the file to upload to Artifactory] "https://na.artifactory.swg-devops.com/artifactory/<repo-name>/<path-in-repo>"
        # curl -H "X-JFrog-Art-Api:${ARTIFACTORY_API_KEY}" -T $p "$ARTIFACTORY_REPO_LINK/$artifactory_path"
    done
fi
