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
