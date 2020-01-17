# This script will create a git tag adding the jenkins build number.
# If the latest tag 
latestTag=$(git tag --list | tail -n 1)
libVersion=$(echo $latestTag | cut -d "." -f 1,2)
echo "Latest tag $latestTag"

if [[ $latestTag =~ "dev" ]]
then
	git tag -a $libVersion.$BUILD_NUMBER.dev -m "$libVersion dev Build $BUILD_NUMBER"
	echo "Creating tag... $libVersion.$BUILD_NUMBER.dev"
else
	git tag -a $libVersion.$BUILD_NUMBER -m "$libVersion Build $BUILD_NUMBER"
	echo "Creating tag $libVersion.$BUILD_NUMBER"
fi


