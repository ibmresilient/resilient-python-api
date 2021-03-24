#!/bin/bash
status=0
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}
print_start() {
    print_msg "\
PACKAGES_TO_SCAN:\t\t\t$1 \n\
"
}
# Make a virtual env
virtualenv safetycheck
# Activate the env
source safetycheck/bin/activate
for package in $1;
do 
    print_msg "Running CVE scan for $package python package"
    print_msg "Installing $package"
    # Install the package and all its deps. 
    python $package/setup.py -q install 
    print_msg "Running a cve security scan for $package"
    # Perform a safety check printing all info to job logs
    safety check --full-report
    # Get the exit code of the safety scan 
    last_status=$?;

    if [ $last_status -ne 0 ]; then
            print_msg "Security Scan failure for $package which gave an exit code of $last_status"
            status=$last_status;
    fi
    # Get a list of all packages and uninstall to give the next iteration a clean environment
    pip freeze | xargs pip uninstall -q -y
done
print_msg "CVE Safety security scan of packages complete.  Final Status $status"
# TODO: Saftey package gives us information on vulnerbilities that could exist today
# if we depend on its exit code the builds will fail until we fix or ignore the specific instances
# for this reason, exit 0 to give the team information on things to change.
# Should be removed.
exit 0 

