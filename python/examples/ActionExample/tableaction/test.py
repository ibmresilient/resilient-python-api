
from __future__ import print_function

import requests  # SAB add to suppress
requests.packages.urllib3.disable_warnings()  # SAB Should suppress any warnings

import co3 as resilient
import json
import sys
import collections

import os
import os.path
import re
import logging

from ResilientOrg import ResilientOrg as ResOrg

#turn off logging for urllib
logging.getLogger("requests.packages.urllib3").setLevel(logging.WARNING)
logfname =  __file__.rsplit(".",1)[0]+".log"
logging.basicConfig(filename=logfname,level=logging.DEBUG,
                format='%(asctime)s:%(name)s:%(levelname)-8s:%(lineno)s:%(message)s'
                )
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)-8s:%(lineno)s:%(message)s'))
console.setLevel(logging.DEBUG)
logger.addHandler(console)

# stdlib
from pprint import pprint

class FinfoArgumentParser(resilient.ArgumentParser):
    def __init__(self,config_file=None):
        super(FinfoArgumentParser, self).__init__(config_file=config_file)


        self.add_argument('--instix',
                help="Input spreadsheet file") 


def main():

    # Parse commandline arguments
    APP_CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", "app.config")
    if not os.path.isfile(APP_CONFIG_FILE):
        logger.debug("{} is not a valid file for a configuration file".format(APP_CONFIG_FILE))
        sys.exit(2)

    parser = FinfoArgumentParser(config_file=APP_CONFIG_FILE)
    opts = parser.parse_args()

    reso = ResOrg(opts=vars(opts))

    try:
        tabledef=reso.get_table_definition('dt2')
    except Exception as e:
        print(e)

    pprint(tabledef,indent=5)

    (tabledata,error) = reso.get_table_data(2096,tabledef.get('id'))
    if error is not None:
        print(error)





if __name__ == '__main__':
    main()
