#!/bin/bash -e

cd $TRAVIS_BUILD_DIR

paths_all_dists=()

readonly package_names=(
    "resilient"
    "resilient-lib"
    "resilient-circuits"
    "pytest-resilient-circuits"
    "resilient-sdk"
)

###############
## Functions ##
###############
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

##################
## Check params ##
##################
if [ $1 == "do_deploy" ]; then
    deploy=true
else
    deploy=false
fi

if [ $2 == "do_release" ]; then
    do_release=true
else
    do_release=false
fi

if [ $3 == "deploy_docs" ]; then
    deploy_docs=true
else
    deploy_docs=false
fi

###########
## Start ##
###########

print_msg "Installing app config plugins package"
pip install $TRAVIS_BUILD_DIR/resilient-app-config-plugins


print_msg "Writing .pypirc file"

# Write .pypirc file
sed -e "s|{{ARTIFACTORY_PYPI_REPO_URL}}|$ARTIFACTORY_PYPI_REPO_URL|" \
-e "s|{{ARTIFACTORY_USERNAME}}|$ARTIFACTORY_USERNAME|" \
-e "s|{{ARTIFACTORY_API_KEY}}|$ARTIFACTORY_API_KEY|" \
-e "s|{{PYPI_API_KEY}}|$PYPI_API_KEY|" \
$PATH_TEMPLATE_PYPIRC > $HOME/.pypirc

for p in "${package_names[@]}"; do
    # Get directory of package
    dir=$(echo $TRAVIS_BUILD_DIR/$p)
    print_msg "Building source distribution of $dir"

    # Remove any old dist files.
    rm -rf $dir/dist/*

    cd $dir

    # Build the source distribution.
    print_msg "building $p with 'python -m build'"
    python -m build

    # if deploy to artifactory
    if [ "$deploy" = true ] ; then
        print_msg "uploading $p to Artifactory with 'twine upload'"
        twine upload --config-file $HOME/.pypirc -r artifactory $dir/dist/*
        print_msg "uploaded $p to Artifactory"
    fi

    # if release to PyPi
    if [ "$do_release" = true ] ; then
        print_msg "uploading $p to PyPi with 'twine upload'"
        twine upload --config-file $HOME/.pypirc $dir/dist/*
        print_msg "released $p to PyPi"
    fi

    if [ "$deploy_docs" = true ] ; then
        print_msg "Docs are required so pip installing '$p' with version $SETUPTOOLS_SCM_PRETEND_VERSION"
        pip install .
    fi

    # Append path to sdist to paths_all_dists array
    sdist_path=$(ls $dir/dist/*.tar.gz)
    print_msg "Path to sdist: $sdist_path"
    paths_all_dists+=($sdist_path)
    # Append path to .whl to paths_all_dists array
    whl_path=$(ls $dir/dist/*.whl)
    print_msg "Path to Wheel build: $whl_path"
    paths_all_dists+=($whl_path)

done

# Go back to main directory when done building
cd $TRAVIS_BUILD_DIR

if [ "$deploy" = true ] ; then
    # Loop paths_all_dists and copy to Artifactory using curl
    # this includes both .tar.gz sdist files, as well as .whl wheel files
    for p in "${paths_all_dists[@]}"; do
        package_name=$(basename $p)
        artifactory_path=$ARTIFACTORY_LIB_LOCATION/$package_name
        print_msg "copying $package_name to Artifactory at: $artifactory_path"
        # curl -H [header including the Artifactory API Key] -T [path to the file to upload to Artifactory] "https://na.artifactory.swg-devops.com/artifactory/<repo-name>/<path-in-repo>"
        curl -H "Authorization: Bearer ${ARTIFACTORY_API_KEY}" -T $p "$artifactory_path"
    done
fi

if [ "$deploy_docs" = true ] ; then
    print_msg "Docs are requried so building them \n sphinx-build -b html -a docs docs/_build"
    sphinx-build -b html -a docs docs/_build
    touch docs/_build/.nojekyll
fi

cd $TRAVIS_BUILD_DIR