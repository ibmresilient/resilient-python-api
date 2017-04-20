""" Searcher to look through file of known phishing sites (downloaded from phishtank.com) """
import os
import csv

from django.conf import settings

from threats.controller import BaseArtifactSearch


def data_file_path():
    """ Which is the file that I want to read """
    return os.path.join(os.path.dirname(__file__), "phish_tank", settings.PHISH_TANK_FILE)


class PhishingRecord(object):  # pylint: disable=too-many-instance-attributes

    """ Data fields for phishing record """
    _required_fields = [
        "phish_id",
        "url",
        "phish_detail_url",
        "submission_time",
        "target",
    ]

    def __init__(self, csv_record):
        for required_field in self._required_fields:
            if required_field not in csv_record:
                raise ValueError("record does not contain required field {}".format(required_field))
        self.__dict__.update(csv_record)

    @property
    def name(self):
        """ return name to use for this record """
        return "PhishTank Record {}".format(self.phish_id)

    @property
    def source_artifact(self):
        """ source_artifact for this record """
        return {
            "type": "net.uri",
            "value": self.url
        }

    @property
    def properties(self):
        """ property information for this record """
        return [
            {
                "type": "number",
                "name": "id",
                "value": self.phish_id,
            },
            {
                "type": "uri",
                "name": "url",
                "value": self.url,
            },
            {
                "type": "uri",
                "name": "detail_url",
                "value": self.phish_detail_url,
            },
            {
                "type": "string",
                "name": "submission_time",
                "value": self.submission_time,
            },
            {
                "type": "string",
                "name": "target",
                "value": self.target,
            },
        ]


class PhishTankArtifactSearch(BaseArtifactSearch):

    """ implements base searcher by looking through phishtank list """
    @classmethod
    def search(cls, artifact_type, search_term, **kwargs):
        if not cls.supports(artifact_type):
            raise ValueError("PhishTankArtifactSearch does not support artifact type {}".format(artifact_type))

        threats = []
        with open(data_file_path()) as phishing_file:
            phishing_records = csv.DictReader(phishing_file)
            for phishing_record_info in phishing_records:
                try:
                    phishing_record = PhishingRecord(phishing_record_info)
                    if search_term in phishing_record.url:
                        threat = cls.store_threat_info(
                            phishing_record.name,
                            phishing_record.source_artifact,
                            phishing_record.properties)
                        threats.append(threat)
                except ValueError:
                    pass
        return threats

    @classmethod
    def supports(cls, artifact_type):
        return artifact_type == "net.uri"
