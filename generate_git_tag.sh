# This script will create a git tag adding the jenkins build number.
# If the latest tag 
latestTag=$(git tag --list | tail -n 1)
libVersion=$(echo $latestTag | cut -d "." -f 1,2)
echo "Latest tag: $latestTag"

if [ $TRAVIS ]
then
	BUILD_NUMBER=$TRAVIS_BUILD_NUMBER
fi

if [[ $latestTag =~ "dev" ]]
then
	echo "Creating dev tag $libVersion.$BUILD_NUMBER.dev"
	git tag -a $libVersion.$BUILD_NUMBER.dev -m "$libVersion dev Build $BUILD_NUMBER"
elif [[ $latestTag =~ "rc" ]]
then
	echo "Creating rc tag $libVersion.$BUILD_NUMBER.rc"
	git tag -a $libVersion.$BUILD_NUMBER.rc -m "$libVersion rc Build $BUILD_NUMBER"
else	
	echo "Creating tag $libVersion.$BUILD_NUMBER"
	git tag -a $libVersion.$BUILD_NUMBER -m "$libVersion Build $BUILD_NUMBER"
fi


