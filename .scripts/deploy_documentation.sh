#!/bin/bash -e

# functions
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

git clone --branch gh-pages "https://$GITHUB_AUTH_TOKEN@github.ibm.com/Resilient/resilient-python-api.git" gh-pages

cd gh-pages

rm -rf *
cp -r "$app_repo_dir/docs/_build/." .

git add .
git commit -m "Deploy Resilient/resilient-python-api to github.ibm.com/Resilient/resilient-python-api.git:gh-pages"

git push origin gh-pages

print_msg "Deployment complete."

cd ../

rm -r gh-pages