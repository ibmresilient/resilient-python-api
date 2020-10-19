#!/bin/bash -e

readonly package_names=(
    "resilient"
    "resilient-circuits"
    "resilient-sdk"
)

# Get the version number from the command line.
readonly version_number=$1
echo "version_number: $version_number"

# Get this directory
readonly repo_dir="$( cd "$( dirname "../${BASH_SOURCE[0]}" )" && pwd )"
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

    # Copy source distribution to $repo_dir
    sdist_path=$(ls $dir/dist/*.tar.gz)
    echo "Path to sdist: $sdist_path"
    cp $sdist_path $repo_dir
done

echo "Built source distributions:"
cd $repo_dir
ls -l *.tar.gz
