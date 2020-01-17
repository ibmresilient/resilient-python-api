latestTag=$(git tag --list | tail -n 1)
libVersion=$(echo $latestTag | cut -d "." -f 1,2)

if [[ $latestTag =~ "dev" ]]
then
	nextVersion=$(echo "$libVersion.$BUILD_NUMBER.dev")
else
	nextVersion=$(echo "$libVersion.$BUILD_NUMBER.dev")
fi


sed -i "s/name='resilient',/name='test_resilient',/g" resilient/setup.py
sed -i "s/use_scm_version={\"root\": \"\.\.\/\", \"relative_to\": __file__},/version=\"$nextVersion\",/g" resilient/setup.py

sed -i "s/name='resilient_lib',/name='test_resilient_lib',/g" resilient-lib/setup.py
sed -i "s/use_scm_version={\"root\": \"\.\.\/\", \"relative_to\": __file__},/version=\"$nextVersion\",/g" resilient-lib/setup.py

sed -i "s/name='resilient_circuits',/name='test_resilient_circuits',/g" resilient-circuits/setup.py
sed -i "s/use_scm_version={\"root\": \"\.\.\/\", \"relative_to\": __file__},/version=\"$nextVersion\",/g" resilient-circuits/setup.py

sed -i "s/name='pytest_resilient_circuits',/name='test_pytest_resilient_circuits',/g" pytest-resilient-circuits/setup.py
sed -i "s/use_scm_version={\"root\": \"\.\.\/\", \"relative_to\": __file__},/version=\"$nextVersion\",/g" pytest-resilient-circuits/setup.py