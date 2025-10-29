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
export PATH_SCRIPTS_DIR="$app_repo_dir/travis-scripts"
export TEST_RESILIENT_APPLIANCE="staging2.internal.resilientsystems.com"

function print_msg () {
    local msg=$1

    printf "\n--------------------\n%s\n--------------------\n" "$msg"
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
    install_python3 "3.9"
    debug_python_environment "3.9"

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

run_python_39_unit_tests(){
    export RUN_TYPE=unit_test
    export TOXENV=py39

    print_msg "Starting Python 3.9 Tests"
    run_python_unit_tests

    # remove python 3.9 in tox directory
    delete_python_from_tox $TOXENV
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
    # TODO: revist when install_python3 supports python3.12
    # https://ibm-security.slack.com/archives/C06L36NUEP4/p1750845211295349?thread_ts=1750785640.445799&cid=C06L36NUEP4
    # install_python3 "3.12" 

    yum install -yq python3.12 python3.12-pip python3.12-devel
    unlink /usr/bin/python3

    # prevent errors when pip3 is not available
    unlink /usr/bin/pip3 || true

    ln -s /usr/bin/python3.12 /usr/bin/python3
    ln -s /usr/bin/pip3.12 /usr/bin/pip3

    debug_python_environment "3.12"

    export RUN_TYPE=unit_test
    export TOXENV=py312

    echo "Starting Python 3.12 Tests"
    run_python_unit_tests

    # remove python 3.12 in tox directory
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

    run_python_39_unit_tests

    run_python_311_unit_tests

    run_python_312_unit_tests

    create_code_coverage_report
}

if [[ ! "$BRANCH" =~ $GIT_PAGES_BRANCH_REGEX ]]; then
    main
else
    print_msg "Skipping unit tests for GitHub branch $BRANCH"
fi
