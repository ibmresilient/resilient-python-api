#!/bin/bash

set -Eeuo pipefail

# functions
function debug_python_environment(){
    local python_version=$1

    if [[ "$DEBUG_PYTHON_ENVIRONMENT" == "true" ]]; then
        python"${python_version}" --version
        command -v "python"${python_version}" --version"

        echo "command -v \"python${python_version}\""
        command -v "python${python_version}"

        echo "pip list"
        pip list
    fi
}

# SPS workspace
app_repo_dir="$WORKSPACE/$(load_repo app-repo path)"
GIT_PAGES_BRANCH_REGEX="^pages/.+"
DEBUG_PYTHON_ENVIRONMENT="$(get_env debug_python_environment)"

# hydra common scripts
PATH_COMMON_SCRIPTS_DIR="$app_repo_dir/common_scripts"
PATH_DOWNLOAD_SCRIPT_SAVE_LOC="$app_repo_dir/download_common_scripts.py"
branch_hydra_common_scripts="$(get_env branch-hydra-common-scripts)"
GH_PATH_COMMON_SCRIPTS_REPO="https://raw.github.ibm.com/Resilient/hydra-common-scripts/$branch_hydra_common_scripts/download_files_from_other_repo.py"

# Artifactory vars
ARTIFACTORY_URL="artifactory.swg-devops.com"
ARTIFACTORY_BASE_URL="https://na.$ARTIFACTORY_URL/artifactory"
ARTIFACTORY_REPO_URL=$ARTIFACTORY_BASE_URL/sec-resilient-team-integrations-generic-local/resilient-python-api
ARTIFACTORY_COV_LOCATION=$ARTIFACTORY_REPO_URL/coverage/$BUILD_NUMBER

# environment variables
export GITHUB_AUTH_TOKEN="$(get_env GITHUB_AUTH_TOKEN)"
export ARTIFACTORY_API_TOKEN="$(get_env ARTIFACTORY_API_TOKEN)"
export PATH_SCRIPTS_DIR="$app_repo_dir/.scripts"
export TEST_RESILIENT_APPLIANCE="staging2.internal.resilientsystems.com"

# build info
LIB_VERSION=$("${PATH_SCRIPTS_DIR}/get_lib_version.sh")
NEW_VERSION="${LIB_VERSION}.${BUILD_NUMBER}"
export SETUPTOOLS_SCM_PRETEND_VERSION=$NEW_VERSION

# Full patch versions matching the tarballs uploaded to Artifactory.
# Update these when new patch tarballs are uploaded.
# See: build_docker_base_image.sh PYTHON_312_VERSION / PYTHON_313_VERSION / PYTHON_314_VERSION
PYTHON_312_VERSION="3.12.14"
PYTHON_313_VERSION="3.13.15"
PYTHON_314_VERSION="3.14.7"
# UBI flavour used to select the correct tarball filename (must match the SPS RHEL 8 environment)
PYTHON_TARBALL_UBI_VERSION="ubi8-minimal"
ARTIFACTORY_PYTHON_TARBALLS_URL="$ARTIFACTORY_BASE_URL/sec-resilient-team-integrations-generic-local/python_tarballs"

function print_msg () {
    local msg=$1

    printf "\n--------------------\n%s\n--------------------\n" "$msg"
}

function install_python_from_artifactory(){
    local full_version=$1   # e.g. 3.13.15
    local minor_version     # e.g. 3.13
    minor_version=$(echo "$full_version" | cut -d. -f1,2)

    local tarball="python${full_version}-${PYTHON_TARBALL_UBI_VERSION}-x86_64.tar.gz"
    local url="$ARTIFACTORY_PYTHON_TARBALLS_URL/${tarball}"

    echo "Downloading Python ${full_version} from Artifactory..."
    curl --fail -L \
        -H "Authorization: Bearer ${ARTIFACTORY_API_TOKEN}" \
        -o /tmp/python.tar.gz \
        "$url"

    tar xzf /tmp/python.tar.gz -C /usr/local
    rm /tmp/python.tar.gz

    local pybin="/usr/local/bin/python${minor_version}"
    local pipbin="/usr/local/bin/pip${minor_version}"

    if [[ ! -x "$pybin" ]] || [[ ! -x "$pipbin" ]]; then
        echo "ERROR: Python ${full_version} could not be installed from Artifactory tarball." >&2
        exit 1
    fi

    # update the python3 / pip3 symlinks to point at the newly installed version
    ln -sf "$pybin" /usr/bin/python3
    ln -sf "$pipbin" /usr/bin/pip3
}

function debug_python_environment(){
    local python_version=$1

    if [[ "$DEBUG_PYTHON_ENVIRONMENT" == "true" ]]; then
        python"${python_version}" --version
        command -v "python"${python_version}" --version"

        echo "command -v \"python${python_version}\""
        command -v "python${python_version}"

        echo "pip list"
        pip list
    fi
}

function delete_python_from_tox(){
    local -r python_version=$1

    for dir in resilient resilient-circuits resilient-lib; do
        rm -rf "./${dir}/.tox/${python_version}"
    done
}

function run_python_unit_tests(){
    "$PATH_SCRIPTS_DIR/install_unit_tests_deps.sh"
    "$PATH_SCRIPTS_DIR/run_unit_tests.sh"
}

function set_up_environment(){
    # common scripts use python command rather than python3 - create a symbolic link
    sudo ln -s /usr/bin/python3 /usr/local/bin/python

    # install python to call script to upload .tgz file to artifactory
    source "$WORKSPACE/$PIPELINE_CONFIG_REPO_PATH/scripts/utilities/python_utils.sh"
    install_python3 "3.11"
    debug_python_environment "3.11"

    pip install requests retry2
    print_msg "Downloading hydra-common-scripts with parameters"
    
    "$PATH_SCRIPTS_DIR/download_common_scripts.sh" \
        "$PATH_COMMON_SCRIPTS_DIR" \
        "$GH_PATH_COMMON_SCRIPTS_REPO" \
        "$PATH_DOWNLOAD_SCRIPT_SAVE_LOC" \
        "$branch_hydra_common_scripts" 

    export TEST_RESILIENT_ORG="Resilient PS - Test2"
}

function upload_coverage_reports_to_artifactory(){
    python "$PATH_COMMON_SCRIPTS_DIR/manage_artifactory_sps.py" "UPLOAD" "$ARTIFACTORY_COV_LOCATION" \
    --upload-files \
    "$app_repo_dir/resilient/cov_resilient.xml" \
    "$app_repo_dir/resilient-lib/cov_resilient_lib.xml" \
    "$app_repo_dir/resilient-circuits/cov_resilient_circuits.xml" \
    "$app_repo_dir/resilient-sdk/cov_resilient_sdk.xml"
}

function run_python_311_unit_tests(){
    install_python3 "3.11"
    debug_python_environment "3.11"

    export RUN_TYPE=unit_test
    export TOXENV=py311

    echo "Starting Python 3.11 Tests"
    run_python_unit_tests
    upload_coverage_reports_to_artifactory

    # remove python 3.11 in tox directory
    delete_python_from_tox $TOXENV
}

function run_python_312_unit_tests(){
    install_python_from_artifactory "$PYTHON_312_VERSION"
    debug_python_environment "3.12"

    export RUN_TYPE=unit_test
    export TOXENV=py312

    echo "Starting Python 3.12 Tests"
    run_python_unit_tests

    # remove python 3.12 in tox directory
    delete_python_from_tox $TOXENV
}

function run_python_313_unit_tests(){
    install_python_from_artifactory "$PYTHON_313_VERSION"
    debug_python_environment "3.13"

    export RUN_TYPE=unit_test
    export TOXENV=py313

    echo "Starting Python 3.13 Tests"
    run_python_unit_tests

    # remove python 3.13 in tox directory
    delete_python_from_tox $TOXENV
}

function run_python_314_unit_tests(){
    install_python_from_artifactory "$PYTHON_314_VERSION"
    debug_python_environment "3.14"

    export RUN_TYPE=unit_test
    export TOXENV=py314

    echo "Starting Python 3.14 Tests"
    run_python_unit_tests

    # remove python 3.14 in tox directory
    delete_python_from_tox $TOXENV
}

function create_code_coverage_report() {
    # Python code coverage must go in test/coverage.xml
    coverage_dir="${app_repo_dir}/test"
    coverage_file="${coverage_dir}/coverage.xml"
    mkdir -p "$coverage_dir"

    # combine each individual coverage report xml for scanning
    python "${PATH_SCRIPTS_DIR}/merge_coverage.py" \
        "$app_repo_dir/resilient/cov_resilient.xml" \
        "$app_repo_dir/resilient-lib/cov_resilient_lib.xml" \
        "$app_repo_dir/resilient-circuits/cov_resilient_circuits.xml" \
        "$app_repo_dir/resilient-sdk/cov_resilient_sdk.xml"

    mv coverage.xml "$coverage_file"
    echo "Combined coverage written to $coverage_file"
}


function main(){
    set_up_environment

    run_python_311_unit_tests
    run_python_312_unit_tests
    run_python_313_unit_tests
    run_python_314_unit_tests

    create_code_coverage_report
}

if [[ ! "$BRANCH" =~ $GIT_PAGES_BRANCH_REGEX ]]; then
    main
else
    print_msg "Skipping unit tests for GitHub branch $BRANCH"
fi
