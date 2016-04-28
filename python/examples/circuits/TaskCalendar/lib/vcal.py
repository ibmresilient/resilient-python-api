# -*- coding: utf-8 -*-
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
""" Helper for creating ICS files """


class Vcal(object):
    ''' For creating data for ics files '''
    end = '''END:VEVENT
END:VCALENDAR
'''
    header = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-/resilientsystems.com/Resilient IRT
METHOD:PUBLISH
BEGIN:VEVENT
FBTYPE:BUSY
'''

    def __init__(self):
        ''' Initialize Vcal calendar data object '''
        self.content = ""
        # variables to keep track of what components have been added

        self.url = False
        self.uid = False
        self.startd = False
        self.endd = False
        self.url = False
        self.location = False
        self.summary = False


    def add_start(self, startdate):
        ''' add start datetime to calendar data '''
        if not self.startd:
            self.content += "DTSTART:{}\n".format(startdate)
            self.startd = True

    def add_end(self, enddate):
        ''' add end datetime to calendar data '''
        if not self.endd:
            self.content += "DTEND:{}\n".format(enddate)
            self.endd = True

    def add_summary(self, summary):
        ''' add summary to calendar data '''
        if not self.summary:
            self.content += "SUMMARY:{}\n".format(summary)
            self.summary = True

    def add_uid(self, uid):
        ''' add unique identifier to calendar data '''
        if not self.uid:
            self.content += "UID:{}\n".format(uid)
            self.uid = True

    def build_event(self):
        ''' construct the completed calendar data string '''
        return self.header+self.content+self.end

    def add_url(self, url):
        ''' add start URL to calendar data '''
        if not self.url:
            self.content += "URL:{}\n".format(url)
            self.url = True

    def add_location(self, location):
        ''' add task location to calendar data '''
        if not self.location:
            self.content += "LOCATION:{}".format(location)
            self.location = True
