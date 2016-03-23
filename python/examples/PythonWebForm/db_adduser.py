#!/usr/bin/env python
# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.


import os
import sys
from config import SQLALCHEMY_DATABASE_URI
from WebForm import db,models  # bring in the local db module

import argparse
import hashlib

usemessage ='''
usage: db_adduser.py [-h] [--user USER] [--password PASSWORD]

optional arguments:
  -h, --help           show this help message and exit
  --user USER          Users Name
  --password PASSWORD  Users PW
'''
def usage(rv):
    print(usemessage)
    sys.exit(rv)

parser = argparse.ArgumentParser()
parser.add_argument("--user",help="Users Name",default=None)
parser.add_argument("--password",help="Users PW",default=None)
args = parser.parse_args()

if args.user is None:
    usage(1)

if args.password is None:
    usage(2)

h = hashlib.sha256()
h.update(args.password)
hd = h.hexdigest()

user = models.User(username=args.user,password=hd)

db.session.add(user)
db.session.commit()
