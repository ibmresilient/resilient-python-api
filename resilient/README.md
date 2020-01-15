## resilient

This package is a Python client module for the Resilient REST API.

### Changelog

### Installation  
Instructions for building and installing this package can be found in the 
[repository README](https://github.com/ibmresilient/resilient-python-api/blob/master/README.md).


### Tests  
python setup.py test [-a "<optional co3argparse args>"] [-c <config file>] [-p "<optional pytest args>"]  
e.g. `python setup.py test -a "--org=Test" -c ~/my.config -p "-s"`

### Code coverage
#### pytest-cov
First need to install pytest-cov
`pip install pytest-cov`
`pip3 install pytest-cov`
#### Make folder to store coverage data
`mkdir cov`
#### run test and collect code coverage data
You need the template_test.json file from the tests folder.
`python setup.py test -a "--org=TestOrg" -c ./app.config -p "-s --cov=./resilient --cov-report=html:./cov"`
#### View coverage data
`firefox ./cov/index.html`
   
