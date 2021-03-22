#!/bin/bash
#
# An example script to do linting on the repo.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#

print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}
print_start() {
    print_msg "\
PACKAGES_TO_SCAN:\t\t\t$1 \n\
RCFILE:\t\t\t$2 \n\
"
}

print_msg "Starting a script to run pylint on python files."
readonly MIN_PASSING_SCORE=6.25
readonly ERROR_MSG="Aborting commit. Your commit has a pylint score lower than ${MIN_PASSING_SCORE}"
DEFAULT_RCFILE="./configs/.pylintrc"
RCFILE="${2:-$DEFAULT_RCFILE}"
status=0
for package in $1; do
    print_msg "[$package]"
    print_msg "Running Pylint scan for $package python package"
    # Lint all the python files;
    # **/**/*.py catches every dir such as cmds, util, tests 
    pylint --rcfile=${RCFILE} ./${package}/**/**/*.py \; |
        # Only get the number values
        grep -oE "\-?[0-9]+\.[0-9]+" |
        # Extract the score
        awk 'NR==1 || NR % 4 == 0' |
        # For score lines
        while read line; do
            print_msg "Pylint score for $package is $line"
            # If the line contains a score lower than MIN_PASSING_SCORE throw a problem.
            if (($(print_msg "$line < ${MIN_PASSING_SCORE}" | bc -l))); then 
                # and print the error message
                print_msg ">$ERROR_MSG" >&2
                # and save the last_status as failure
                last_status=1
            else 
                print_msg "Pylint score $line greater than min required score: ${MIN_PASSING_SCORE}; Success!"
                last_status=0
            fi
            # Update the status if any pylint scan for a package fails
            if [ $last_status -ne 0 ]; then
                print_msg "FAILURE $toxfile: [$last_status]"
                status=$last_status;
            fi
        done
done
print_msg "Pylint Run Complete.  Final Status $status"
exit $status
