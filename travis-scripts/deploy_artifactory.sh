#!/bin/bash -e

cd $TRAVIS_BUILD_DIR

# Loop PATHS_TO_COPY_TO_ARTIFACTORY and copy to Artifactory using curl
for p in "${PATHS_TO_COPY_TO_ARTIFACTORY[@]}"; do
    package_name=$(basename $p)
    artifactory_path=$BASE_ARTIFACTORY_PATH/$package_name
    echo "copying $package_name to Artifactory at: $ARTIFACTORY_REPO_LINK/$artifactory_path"
    curl -H "X-JFrog-Art-Api:${ARTIFACTORY_API_KEY_SHANE}" -T $p "$ARTIFACTORY_REPO_LINK/$artifactory_path"
done