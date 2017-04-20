""" test phish tank source """
import os

from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from sources.phish_tank import PhishingRecord, PhishTankArtifactSearch
from threats.controller import InternalArtifactSearch
from sources.phish_tank import data_file_path

# Create your tests here.


class PhishingRecordTest(TestCase):

    """ tests for the PhishingRecord class """

    def test_parse_record(self):
        """ test that the record is parsed from the provided comma-separated string """
        test_data = {
            "phish_id": "1234567",
            "url": "http://baddns.com",
            "phish_detail_url": "http://www.viewdetails.com/1234567",
            "submission_time": "2015-07-20T12:45:49+00:00",
            "verified": "yes",
            "verification_time": "2015-07-20T12:47:35+00:00",
            "online": "no",
            "target": "Fancy Bank plc.",
        }

        phishing_record = PhishingRecord(test_data)

        self.assertEqual(phishing_record.url, "http://baddns.com")

        self.assertEqual(phishing_record.phish_id, test_data["phish_id"])
        self.assertEqual(phishing_record.url, test_data["url"])
        self.assertEqual(phishing_record.phish_detail_url, test_data["phish_detail_url"])
        self.assertEqual(phishing_record.submission_time, test_data["submission_time"])
        self.assertEqual(phishing_record.verified, test_data["verified"])
        self.assertEqual(phishing_record.verification_time, test_data["verification_time"])
        self.assertEqual(phishing_record.online, test_data["online"])
        self.assertEqual(phishing_record.target, test_data["target"])

        self.assertEqual(phishing_record.name, "PhishTank Record 1234567")

        self.assertEqual(phishing_record.source_artifact["type"], "net.uri")
        self.assertEqual(phishing_record.source_artifact["value"], phishing_record.url)

        self.assertIn(
            {"type": "number", "name": "id", "value": phishing_record.phish_id, },
            phishing_record.properties
        )
        self.assertIn(
            {"type": "uri", "name": "url", "value": phishing_record.url, },
            phishing_record.properties
        )
        self.assertIn(
            {"type": "uri", "name": "detail_url", "value": phishing_record.phish_detail_url, }, phishing_record.
            properties
        )
        self.assertIn(
            {"type": "string", "name": "submission_time", "value": phishing_record.submission_time, },
            phishing_record.properties
        )
        self.assertIn(
            {"type": "string", "name": "target", "value": phishing_record.target, },
            phishing_record.properties
        )

    def test_bad_record(self):
        """ test that a bad record yields an error """
        test_data = {
            "phish_id": "1234567",
            "url": "http://bad data",
        }

        with self.assertRaises(ValueError):
            PhishingRecord(test_data)


@override_settings(PHISH_TANK_FILE="test_records.csv")
class PhishTankTest(TestCase):

    """ base test class to write out test data to be used to run tests against """

    def setUp(self):  # pylint: disable=no-self-use
        """Write test records to test file """
        with open(data_file_path(), 'w') as test_records:
            test_records.write("phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target")
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3337192",
                    "http://nastyphishingsite.com",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3337192",
                    "2015-07-20T12:45:49+00:00",
                    "yes",
                    "2015-07-20T12:47:35+00:00",
                    "yes",
                    "Other"
                ])
            )
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3337191",
                    "http://nastyphishingsite.com.br/minimal/atx/atxcm1.html",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3337191",
                    "2015-07-20T12:44:41+00:00",
                    "yes",
                    "2015-07-20T12:46:21+00:00",
                    "yes",
                    "Other"
                ]))
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3337172",
                    "http://nastyphishingsite.com/caixa/BLS/",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3337172",
                    "2015-07-20T12:04:42+00:00",
                    "yes",
                    "2015-07-20T12:10:55+00:00",
                    "yes",
                    "Other",
                ]))
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3337007",
                    "http://nastyphishingsite.com.ua/scn/neb.rec/csn/rnop.php",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3337007",
                    "2015-07-20T10:29:04+00:00",
                    "yes",
                    "2015-07-20T11:06:53+00:00",
                    "yes",
                    "Capitec Bank",
                ]))
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3337003",
                    "http://nastyphishingsite.com.com/atoc.php",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3337003",
                    "2015-07-20T10:26:54+00:00",
                    "yes",
                    "2015-07-20T11:08:07+00:00",
                    "yes",
                    "Capitec Bank",
                ]))
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3337000",
                    "http://badphishingsite.com/tmp/standardbank5/inet.php",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3337000",
                    "2015-07-20T10:16:38+00:00",
                    "yes",
                    "2015-07-20T11:08:43+00:00",
                    "yes",
                    "Other",
                ]))
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3336999",
                    "http://nastyphisshingsite.com/tmp/standardbank4/inet.php",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3336999",
                    "2015-07-20T10:16:35+00:00",
                    "yes",
                    "2015-07-20T11:08:43+00:00",
                    "yes",
                    "Other",
                ]))
            test_records.write('\n')
            test_records.write(
                ",".join([
                    "3336988",
                    "http://nastyphishingsite.com/language/en-GB/verification/online.htm",
                    "http://www.phishtank.com/phish_detail.php?phish_id=3336988",
                    "2015-07-20T10:11:21+00:00",
                    "yes",
                    "2015-07-20T10:36:36+00:00",
                    "yes",
                    "Other"
                ]))
            test_records.write('\n')

    def tearDown(self):  # pylint: disable=no-self-use
        """ remove test file """
        os.remove(data_file_path())


class SomethingPhishyTest(PhishTankTest):

    """ client request based tests """

    def setUp(self):  # pylint: disable=super-on-old-class
        """ Configure a client app to query interface """
        super(SomethingPhishyTest, self).setUp()
        self.client = APIClient()

    def confirm_result_list(self, hits):
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].name, "PhishTank Record 3337000")

        artifacts = hits[0].artifacts.all()
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].type, "net.uri")
        self.assertEqual(artifacts[0].value, "http://badphishingsite.com/tmp/standardbank5/inet.php")

        properties = hits[0].props.all()
        self.assertEqual(len(properties), 5)

    def test_search_async(self):
        """ Test search through API endpoint"""
        PhishTankArtifactSearch.search("net.uri", "badphishingsite.com")

        # Now search database match records and retrieve them
        hits = InternalArtifactSearch.search("net.uri", "badphishingsite.com")

        self.confirm_result_list(hits)

    def test_search_sync(self):
        """ Test search through API endpoint"""
        hits = PhishTankArtifactSearch.search("net.uri", "badphishingsite.com")

        self.confirm_result_list(hits)

    def test_multiple(self):
        """ Test search through API endpoint"""
        PhishTankArtifactSearch.search("net.uri", "nastyphishingsite.com")

        # Now search database match records and retrieve them
        hits = InternalArtifactSearch.search("net.uri", "nastyphishingsite.com")

        self.assertEqual(len(hits), 6)

        for hit in hits:
            properties = hit.props.all()
            self.assertEqual(len(properties), 5)

    def test_unsupported_search(self):
        """ Test ValueError appears if type is unsupported """
        with self.assertRaises(ValueError):
            PhishTankArtifactSearch.search("net.ip", "badphishingsite.com")
