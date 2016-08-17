""" Tests for custom threat service sample """
from __future__ import unicode_literals

import hashlib
import json
import threading
import tempfile
try:
    from mock import patch
except:  # pylint: disable=bare-except
    # in 3.4.x unittest.mock is present, but pylint does not understand that it is good
    from unittest.mock import patch  # pylint: disable=no-name-in-module

from django.test import TestCase
from django.test.utils import override_settings
from django.core.files.uploadedfile import TemporaryUploadedFile
from rest_framework.test import APIClient

from threats.controller import search_artifacts, BaseArtifactSearch, SearchContext, InternalArtifactSearch
from threats.models import Threat, Artifact, Property
from threats.serializers import ThreatSerializer


class JsonTestCase(TestCase):  # pylint: disable=too-few-public-methods

    """ Mixin to support Json comparison of objects"""

    def assertJsonEquivalent(self, data_object, comparison_dict):
        """ Takes data object, converts it to json and then back to dict to compare with comparison_dict """
        json_string = json.dumps(data_object)
        json_dict = json.loads(json_string)

        self.assertEqual(json_dict, comparison_dict)


class IncompleteTestArtifactSearch(BaseArtifactSearch):  # pylint: disable=abstract-method

    """ instance that does not implement search, it will generate an exception """
    pass


class TestSearchContextCache(TestCase):

    def test_regular_context(self):
        context = SearchContext({"type": "net.ip", "value": "192.168.1.1", })
        context.save()

        loaded_context = SearchContext.load(context.id)

        self.assertEqual(context.type, loaded_context.type)
        self.assertEqual(context.value, loaded_context.value)
        self.assertEqual(context.id, loaded_context.id)

    def test_file_context(self):
        with open("threats/test_data/boss.gif", "r") as boss_reader:
            file_data = boss_reader.read()

        upload_file_args = {
            "name": "boss.gif",
            "content_type": "application/octet-stream",
            "size": 29927,
            "charset": None,
        }

        temp_file = TemporaryUploadedFile(**upload_file_args)
        temp_file.write(file_data)
        temp_file.flush()

        context = SearchContext({"type": "file.content", "value": temp_file, })
        context.save()

        self.assertEqual(context.file_data_len, len(file_data))

        loaded_context = SearchContext.load(context.id)
        self.assertEqual(loaded_context.base64_file_data_len, context.base64_file_data_len)
        self.assertEqual(loaded_context.file_data_len, context.file_data_len)

        with open(loaded_context.value.temporary_file_path(), "r") as temp_file:
            loaded_file_data = temp_file.read()

        for counter in range(0, len(loaded_file_data) / 100):
            begin = counter * 100
            end = begin + 100
            self.assertEqual(file_data[begin:end], loaded_file_data[begin:end])

        self.assertEqual(len(file_data), len(loaded_file_data))


class TestArtifactSearch(BaseArtifactSearch):

    """ test search implementation to test operation adding results after initial search execution """
    @classmethod
    def supports(cls, artifact_type):
        return artifact_type == "net.ip"

    @classmethod
    def search(cls, artifact_type, search_term, **kwargs):
        if "context" in kwargs:
            # simply wait until we are marked externally as done
            cls.search_complete_event.wait(2)
        else:
            # Delegate to Internal search for testing purposes
            return InternalArtifactSearch.search(artifact_type, search_term, **kwargs)

    @classmethod
    def async_search(cls, artifact_type, search_term, **kwargs):
        cls.search_complete_event = threading.Event()
        # cls.fake_search_running = True
        return super(TestArtifactSearch, cls).async_search(artifact_type, search_term, **kwargs)

    @classmethod
    def add_result(cls, name, artifact_type, artifact_value):
        """ create threat record at a moment in time to confirm value """
        test_property = Property(name="test_property", type="string", value="ABC")
        artifact = Artifact(type=artifact_type, value=artifact_value)
        cls.store_threat_info(name, artifact, [test_property])

    @classmethod
    def search_complete_flag(cls):
        """ indicate that the search has completed """
        cls.search_complete_event.set()
        cls.search_closed = threading.Event()
        return cls.search_closed

    @classmethod
    def _search_and_done(cls, artifact_type, search_term, **kwargs):
        super(TestArtifactSearch, cls)._search_and_done(artifact_type, search_term, **kwargs)
        cls.search_closed.set()


class TestDictArtifactSearch(TestArtifactSearch):

    """ version of test that uses dict instead of object instacnes """
    @classmethod
    def add_result(cls, name, artifact_type, artifact_value):
        """ create threat record using dict instead of object instances """
        test_property = {"name": "test_property", "type": "string", "value": "ABC", }
        artifact = {"type": artifact_type, "value": artifact_value, }
        related_artifact = {"type": "net.uri", "value": "http://www.somelocation.com/", }
        cls.store_threat_info(name, artifact, [test_property, {"fake": "should get removed"}], [related_artifact])


class TestFileContentArtifactSearch(BaseArtifactSearch):

    """ test searcher that looks for the word 'bad' in the file contents """

    @classmethod
    def supports(cls, artifact_type):
        return artifact_type == "file.content"

    @classmethod
    def search(cls, artifact_type, search_term, **kwargs):
        """ The "search_term" is a file """
        search_term.seek(0)
        file_content = search_term.read()

        threat = None
        if "bad" in file_content:
            properties = [
                {"name": "file_name", "type": "string", "value": search_term.name, },
                {"name": "file_size", "type": "number", "value": search_term.size, },
            ]

            file_md5 = hashlib.md5()
            file_md5.update(file_content)
            file_sha1 = hashlib.sha1()
            file_sha1.update(file_content)
            related_artifacts = [
                {"type": "hash.md5", "value": file_md5.hexdigest(), },
                {"type": "hash.sha1", "value": file_sha1.hexdigest(), },
            ]

            threat = cls.store_threat_info(
                "Bad file content",
                {"type": "file.content", "value": file_content, },
                properties,
                related_artifacts,
            )

        if threat:
            return [threat]
        else:
            return []


@override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[])
class ArtifactSearchTest(TestCase):

    """
    Tests the ability to find a matching threat record from a given artifact value
    """

    def test_simple_search(self):
        """
        Test the search with property results for each kind of property
        """
        threat = Threat.objects.create(name="test_threat")
        self.assertEqual(str(threat), threat.name)
        ip_artifact = Artifact.objects.create(type="net.ip", value="192.168.1.1", threat=threat)
        self.assertEqual(str(ip_artifact), "{} - 192.168.1.1 (net.ip)".format(ip_artifact.id))
        filename_artifact = Artifact.objects.create(type="file.name", value="badprogram.exe", threat=threat)
        prop1 = Property.objects.create(name="P1", type="string", value="test value test value", threat=threat)
        self.assertEqual(str(prop1), "P1 (string)")
        prop2 = Property.objects.create(name="P2", type="number", value="52", threat=threat)
        prop3 = Property.objects.create(
            name="P3",
            type="uri",
            value="http://www.flightview.com/TravelTools/FlightTrackerQueryResults.asp",
            threat=threat
        )
        prop4 = Property.objects.create(name="P4", type="ip", value="192.168.1.1", threat=threat)
        prop5 = Property.objects.create(
            name="P5",
            type="latlng",
            value='{"lat": 42.398506, "lng": -71.139872}',
            threat=threat
        )

        results = search_artifacts("file.name", "badprogram")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, threat.id)

        artifacts = results[0].artifacts.all()
        self.assertTrue(ip_artifact in artifacts)
        self.assertTrue(filename_artifact in artifacts)

        properties = results[0].props.all()
        self.assertTrue(prop1 in properties)
        self.assertTrue(prop2 in properties)
        self.assertTrue(prop3 in properties)
        self.assertTrue(prop4 in properties)
        self.assertTrue(prop5 in properties)

    def test_filter_search(self):
        """
        Tests how searches match upon the correct threats only
        """
        threat1 = Threat.objects.create(name="test_threat")
        Artifact.objects.create(type="net.ip", value="192.168.1.1", threat=threat1)
        Artifact.objects.create(type="file.name", value="badprogram.exe", threat=threat1)

        threat2 = Threat.objects.create(name="another_threat")
        Artifact.objects.create(type="net.ip", value="192.168.1.1", threat=threat2)
        Artifact.objects.create(type="file.path", value="C:\\Program Files\\Bad", threat=threat2)

        results = search_artifacts("file.name", "badprogram")
        self.assertEqual(len(results), 1)
        self.assertTrue(threat1 in results)

        results = search_artifacts("file.path", "C:\\")
        self.assertEqual(len(results), 1)
        self.assertTrue(threat2 in results)

        results = search_artifacts("net.ip", "192.168.1")
        self.assertEqual(len(results), 2)
        self.assertTrue(threat1 in results)
        self.assertTrue(threat2 in results)

    @override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[TestArtifactSearch])
    def test_async_search(self):
        """ test search operation flagged within search context """
        artifact_type = "net.ip"
        artifact_value = "192.168.1.1"
        context = SearchContext({"type": artifact_type, "value": artifact_value})

        hits = search_artifacts(artifact_type, artifact_value, True, context=context)
        self.assertTrue(len(hits) == 0)
        context.save()

        # try again, still should find nothing
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 0)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)
        # now should find something, other search engine should've added something
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 1)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestArtifactSearch.search_complete_flag().wait(2)
        context = SearchContext.load(context.id)
        self.assertFalse(context.pending_searches)

    @override_settings(SYNC_SEARCHERS=[], ASYNC_SEARCHERS=[TestArtifactSearch])
    def test_sync_search_other(self):
        """ if no context is provided, then search will be synchronous """
        artifact_type = "net.ip"
        artifact_value = "192.168.1.1"

        TestArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)

        hits = search_artifacts(artifact_type, artifact_value, True)
        # no context, so search should be synchronous, and we should get a hit
        self.assertTrue(len(hits) == 1)

    @override_settings(SYNC_SEARCHERS=[IncompleteTestArtifactSearch], ASYNC_SEARCHERS=[])
    def test_bad_searcher(self):
        """ should raise error """
        artifact_type = "net.ip"
        artifact_value = "192.168.1.1"

        with self.assertRaises(NotImplementedError):
            search_artifacts(artifact_type, artifact_value, True)

    @override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[TestDictArtifactSearch])
    def test_async_dict_search(self):
        """ test adding threat info using dict objects instead of instances """
        artifact_type = "net.ip"
        artifact_value = "192.168.1.1"
        context = SearchContext({"type": artifact_type, "value": artifact_value})

        hits = search_artifacts(artifact_type, artifact_value, True, context=context)
        self.assertTrue(len(hits) == 0)
        context.save()

        # try again, still should find nothing
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 0)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestDictArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)
        TestDictArtifactSearch.search_complete_flag().wait(2)

        # now should find something, other search engine should've added something
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 1)
        context = SearchContext.load(context.id)
        self.assertFalse(context.pending_searches)

        self.assertEqual(len(hits[0].props.all()), 1)

    @override_settings(
        SYNC_SEARCHERS=[InternalArtifactSearch],
        ASYNC_SEARCHERS=[TestArtifactSearch, TestDictArtifactSearch]
    )
    def test_2_async_searchers(self):
        """ test adding threat info using dict objects instead of instances """
        artifact_type = "net.ip"
        artifact_value = "192.168.1.1"
        context = SearchContext({"type": artifact_type, "value": artifact_value})

        hits = search_artifacts(artifact_type, artifact_value, True, context=context)
        self.assertTrue(len(hits) == 0)
        context.save()

        # try again, still should find nothing
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 0)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestDictArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 1)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestArtifactSearch.add_result("Another test result", artifact_type, artifact_value)
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 2)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestDictArtifactSearch.search_complete_flag().wait(2)
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 2)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestArtifactSearch.search_complete_flag().wait(2)
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 2)
        context = SearchContext.load(context.id)
        self.assertFalse(context.pending_searches)

    @override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[TestArtifactSearch])
    def test_results_already_stored(self):
        """ Test duplicate entries from same searcher """
        artifact_type = "net.ip"
        artifact_value = "192.168.1.1"
        context = SearchContext({"type": artifact_type, "value": artifact_value})

        hits = search_artifacts(artifact_type, artifact_value, True, context=context)
        self.assertTrue(len(hits) == 0)
        context.save()

        # try again, still should find nothing
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 0)
        context = SearchContext.load(context.id)
        self.assertTrue(context.pending_searches)

        TestArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)

        # now should find something, other search engine should've added something
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 1)

        # add the same result again from the same searcher - should still only get 1 result due to duplicate detection
        TestArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)
        TestArtifactSearch.search_complete_flag().wait(2)

        # now should find something, other search engine should've added something
        hits = search_artifacts(artifact_type, artifact_value)
        self.assertTrue(len(hits) == 1)


class SerializerTest(JsonTestCase):

    """ Test serialization of models through to REST interface """

    def test_threat_serialization(self):
        """ Test serialization of threat object """
        threat = Threat.objects.create(name="test_threat")

        serializer = ThreatSerializer(threat)
        self.assertJsonEquivalent(serializer.data, {"props": []})

        Property.objects.create(name="P1", type="string", value="test value test value", threat=threat)
        serializer = ThreatSerializer(threat)
        self.assertJsonEquivalent(serializer.data, {"props": [
            {
                "name": "P1",
                "type": "string",
                "value": "test value test value",
            }
        ]})

        Property.objects.create(name="P2", type="number", value="52", threat=threat)
        Property.objects.create(
            name="P3",
            type="uri",
            value="http://www.flightview.com/TravelTools/FlightTrackerQueryResults.asp",
            threat=threat
        )
        Property.objects.create(name="P4", type="ip", value="192.168.1.1", threat=threat)
        # Property.objects.create(
        #     name="P5",
        #     type="latlng",
        #     value='{"lat": 42.398506, "lng": -71.139872}',
        #     threat=threat
        # )

        serializer = ThreatSerializer(threat)
        self.assertJsonEquivalent(serializer.data, {"props": [
            {
                "name": "P1",
                "type": "string",
                "value": "test value test value",
            },
            {
                "name": "P2",
                "type": "number",
                "value": "52",
            },
            {
                "name": "P3",
                "type": "uri",
                "value": "http://www.flightview.com/TravelTools/FlightTrackerQueryResults.asp",
            },
            {
                "name": "P4",
                "type": "ip",
                "value": "192.168.1.1",
            },
            # {
            #     "name": "P5",
            #     "type": "latlng",
            #     "value": {
            #         "lat": "42.398506",
            #         "lng": "-71.139872",
            #     }
            # },
        ]})


@override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[])
class APIClientTest(JsonTestCase):

    """ Tests using the API endpoints directly """

    def setUp(self):
        """ Configure a client app to query interface """
        self.client = APIClient()

    @override_settings(SUPPORT_UPLOAD_FILE=False)
    def test_options_unsupported(self):
        """ Test OPTIONS of scan endpoint """
        response = self.client.options('/')
        self.assertEqual(response.data, {'upload_file': False})

    @override_settings(SUPPORT_UPLOAD_FILE=True)
    def test_options_supported(self):
        """ Test OPTIONS of scan endpoint """
        response = self.client.options('/')
        self.assertEqual(response.data, {'upload_file': True})

    def _scan(self, response_format):
        """ Test POST to scan threat information for matching artifacts """
        threat1 = Threat.objects.create(name="test_threat")
        Artifact.objects.create(type="net.ip", value="192.168.1.1", threat=threat1)
        Property.objects.create(name="P1", type="string", value="test value test value", threat=threat1)

        threat2 = Threat.objects.create(name="another_test")
        Artifact.objects.create(type="net.ip", value="192.168.1.1", threat=threat2)
        Property.objects.create(name="P2", type="number", value="1024", threat=threat2)

        response = self.client.post('/', {"type": "net.ip", "value": "192.168.1.1"})
        # response has a different id each time, which is a guid
        self.assertTrue("id" in response.data)
        response_id = response.data["id"]
        self.assertTrue(response_id is not None)
        self.assertFalse("retry_secs" in response.data)

        hits = response.data["hits"]
        self.assertEqual(len(hits), 2)

        response = self.client.get(response_format.format(response_id))

        self.assertTrue("id" in response.data)
        self.assertFalse("retry_secs" in response.data)
        self.assertEqual(response_id, response.data["id"])

        hits = response.data["hits"]
        self.assertEqual(len(hits), 2)

    def test_scan(self):
        self._scan('/{}')

    def test_scan_trailing_slash(self):
        self._scan('/{}/')

    @override_settings(SYNC_SEARCHERS=[TestFileContentArtifactSearch], ASYNC_SEARCHERS=[])
    def test_multipart_scan(self):
        """ Test POST with multipart formatted data """

        def post_file_and_artifact(threat_file_content):
            response = None
            my_file = None
            try:
                my_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
                with open(my_file.name, 'w') as writer:
                    writer.write(threat_file_content)
                    writer.close()

                with open(my_file.name) as the_file:
                    the_file.seek(0)
                    response = self.client.post(
                        '/',
                        {'artifact': '{"type": "file.content"}', 'file': the_file},
                        format="multipart"
                    )
            finally:
                my_file.unlink(my_file.name)

            file_name = None
            if my_file:
                file_name = my_file.name.split('/')[-1]

            return response, file_name

        threat_file_content = u"ABC, it's easy as 123"
        response, _ = post_file_and_artifact(threat_file_content)
        self.assertEqual(len(response.data["hits"]), 0)

        threat_file_content = u"ABC, it's as bad as 123"
        response, file_name = post_file_and_artifact(threat_file_content)
        self.assertEqual(len(response.data["hits"]), 1)

        result = response.data["hits"][0]
        result_properties = {prop["name"]: prop["value"] for prop in result['props']}
        self.assertEqual(int(result_properties["file_size"]), 23)
        self.assertEqual(result_properties["file_name"], file_name)

    def test_not_found(self):
        """ Test when trying to retrieve results from scan that is not available """
        response = self.client.get('/test_this_id')
        self.assertEqual(response.status_code, 204)

    @override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[TestArtifactSearch])
    def test_async_scan(self):
        """ Test POST to scan threat information for matching artifacts """
        artifact_value = "192.168.1.1"
        artifact_type = "net.ip"
        response = self.client.post('/', {"type": artifact_type, "value": artifact_value})

        # response has a different id each time, which is a guid
        self.assertTrue("id" in response.data)
        response_id = response.data["id"]
        self.assertTrue(response_id is not None)
        self.assertTrue("retry_secs" in response.data)
        self.assertEqual(response.data["retry_secs"], 60)

        hits = response.data["hits"]
        self.assertEqual(len(hits), 0)

        response = self.client.get('/{}'.format(response_id))
        self.assertTrue("id" in response.data)
        self.assertTrue("retry_secs" in response.data)
        self.assertEqual(response.data["retry_secs"], 60)

        hits = response.data["hits"]
        self.assertEqual(len(hits), 0)

        TestArtifactSearch.add_result("Test result posted", artifact_type, artifact_value)
        TestArtifactSearch.search_complete_flag().wait(2)

        response = self.client.get('/{}'.format(response_id))
        self.assertTrue("id" in response.data)
        self.assertFalse("retry_secs" in response.data)

        hits = response.data["hits"]
        self.assertEqual(len(hits), 1)

    @override_settings(SYNC_SEARCHERS=[IncompleteTestArtifactSearch], ASYNC_SEARCHERS=[])
    def test_exception_handling(self):
        """ Test POST to scan threat information for matching artifacts """
        artifact_value = "192.168.1.1"
        artifact_type = "net.ip"
        response = self.client.post('/', {"type": artifact_type, "value": artifact_value})

        # response should have encountered an error
        self.assertFalse("id" in response.data)
        self.assertTrue("error" in response.data)

        self.assertEqual(response.data["error"], "Must implement 'search' method")

    @override_settings(SYNC_SEARCHERS=[InternalArtifactSearch], ASYNC_SEARCHERS=[])
    def test_exception_responses(self):
        """ ensure that we get a response when some error occurs somewhere in the searcher """
        artifact_value = "192.168.1.1"
        artifact_type = "net.ip"
        response = self.client.post('/', {"type": artifact_type, "value": artifact_value})
        self.assertTrue("id" in response.data)
        self.assertFalse("error" in response.data)
        response_id = response.data["id"]

        response = self.client.get('/{}'.format(response_id))
        self.assertTrue("id" in response.data)
        self.assertFalse("error" in response.data)

        with patch.object(InternalArtifactSearch, 'search', side_effect=RuntimeError("Fake problem")):
            response = self.client.get('/{}'.format(response_id))
            self.assertFalse("id" in response.data)
            self.assertTrue("error" in response.data)
            self.assertEqual(response.data["error"], "Fake problem")

    def test_bad_requests(self):
        """ Make sure that malformed request gets told it is as such """
        def confirm_bad_request_response(response):
            self.assertFalse("id" in response.data)
            self.assertTrue("error" in response.data)
            self.assertEqual(response.status_code, 400)

        # Missing value
        confirm_bad_request_response(self.client.post('/', {"type": "net.ip"}))

        # Missing type
        confirm_bad_request_response(self.client.post('/', {"value": "192.168.1.1"}))

        # Missing artifact in multipart
        confirm_bad_request_response(
            self.client.post('/', {'something_else': '{"type": "file.content"}'}, format="multipart")
        )

        # Missing file in multipart not a problem unless type is file.content
        response = self.client.post('/', {'artifact': '{"type": "net.ip", "value": "192.168.1.1"}'}, format="multipart")
        self.assertEqual(response.status_code, 200)

        # Missing file in multipart is a problem if type is file.content
        confirm_bad_request_response(
            self.client.post('/', {'artifact': '{"type": "file.content", "value": "ignored"}'}, format="multipart")
        )

        # Missing type in multipart
        confirm_bad_request_response(
            self.client.post('/', {'artifact': '{"value": "ignored"}'}, format="multipart")
        )

        # Missing value in multipart with something other than file.content
        confirm_bad_request_response(
            self.client.post('/', {'artifact': '{"type": "net.ip"}'}, format="multipart")
        )

        # Missing value in multipart with file.content, but without file
        confirm_bad_request_response(
            self.client.post('/', {'artifact': '{"type": "file.content"}'}, format="multipart")
        )

        # Missing value in multipart ok if file.content and file is present
        response = None
        try:
            my_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
            with open(my_file.name, 'w') as writer:
                writer.write("This is a test file")
                writer.close()

            with open(my_file.name) as the_file:
                the_file.seek(0)
                response = self.client.post(
                    '/',
                    {'artifact': '{"type": "file.content"}', 'file': the_file},
                    format="multipart"
                )
        finally:
            my_file.unlink(my_file.name)

        self.assertFalse(response is None)
        self.assertEqual(response.status_code, 200)
