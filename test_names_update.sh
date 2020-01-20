#!/usr/bin/env bash
# This script is used to update the names of the packages before uploading them to test.pypi.org,
# because currently, there's no access to the original packages
declare -a PackageArray=("resilient" "resilient-lib" "resilient-circuits" "pytest-resilient-circuits")

latestTag=$(git tag --list | tail -n 1)
libVersion=$(echo $latestTag | cut -d "." -f 1,2)

if [[ $latestTag =~ "dev" ]]
then
	nextVersion=$(echo "$libVersion.$BUILD_NUMBER.dev")
else
	nextVersion=$(echo "$libVersion.$BUILD_NUMBER.dev")
fi

for pkg in "${PackageArray[@]}"; do
	# translate the name of the directory to package name by replacing all '-' with '_'
	pkgName=$(echo $pkg | tr - _)
	sed -i "s/name='$pkgName',/name='test_$pkgName',/g" $pkg/setup.py
	sed -i "s/use_scm_version={\"root\": \"\.\.\/\", \"relative_to\": __file__},/version=\"$nextVersion\",/g" $pkg/setup.py
done
