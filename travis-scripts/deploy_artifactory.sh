#!/bin/bash -e

readonly package_names=(
    "resilient"
    "resililent-circuits"
    "resilient-sdk"
)

# Get the version number from the command line.
readonly version_number=$1
echo "version_number: $version_number"

# Get this directory
readonly this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "this_dir: $this_dir"

if [ ! -z "$version_number" ]; then
    # Write the version as environment variable.
    export SETUPTOOLS_SCM_PRETEND_VERSION=$version_number
else
    echo "Version number not specified - skipping version processing."
fi

for p in "${package_names[@]}"; do
    # Get directory of package
    dir=$(echo $this_dir/$p)
    echo "Building directory $dir"

    # Remove any old dist files.
    rm -rf $dir/dist/*

    # Build the source distribution.
    (cd $dir && python setup.py sdist --formats=gztar)

    # Copy source distribution to $this_dir
    sdist_path=$(ls $dir/dist/*.tar.gz)
    echo "Path to sdist: $sdist_path"
    cp $sdist_path $this_dir
done

echo "Built source distributions:"
cd $this_dir
ls -l *.tar.gz
