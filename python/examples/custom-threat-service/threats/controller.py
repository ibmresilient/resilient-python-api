""" Useful programming-API functionality """
from __future__ import unicode_literals

import base64
import copy
import uuid
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import TemporaryUploadedFile

from threats.models import Threat, Property, Artifact, ARTIFACT_TYPES

# thread pool
_thread_pool_executor = ThreadPoolExecutor(max_workers=settings.THREAD_POOL_SIZE)


def postpone(func):
    """ decorator to enqueue called operation """
    def decorator(*args, **kwargs):
        """ put it in the queue """
        _thread_pool_executor.submit(func, *args, **kwargs)
    return decorator


def search_artifacts(search_type, search_value, spawn_searches_from_other_sources=False, **kwargs):
    """
    Find threats that include the given artifact

    Arguments:
    search_type - Specified artifact type upon which to match
    search_value - Specified search term for searching within artifacts of given type
    """
    if spawn_searches_from_other_sources:
        async_searchers = settings.ASYNC_SEARCHERS
        sync_searchers = settings.SYNC_SEARCHERS
    else:
        async_searchers = []
        sync_searchers = [InternalArtifactSearch]

    hits = []
    for searcher in sync_searchers:
        if searcher.supports(search_type):
            hits.extend(searcher.search(search_type, search_value, **kwargs))

    for searcher in async_searchers:
        if searcher.supports(search_type):
            hits.extend(searcher.async_search(search_type, search_value, **kwargs))

    return hits


class BaseArtifactSearch(object):

    """
    Base class to search sources of information

    Override and implement `search`, adding threat informaiton to the database using `store_threat_info`
    """
    SUPPORTED_TYPES = ARTIFACT_TYPES

    @classmethod
    def supports(cls, artifact_type):
        """ Which type is supported by specific class """
        return artifact_type in cls.SUPPORTED_TYPES

    @classmethod
    def search(cls, artifact_type, search_term, **kwargs):
        """
        Perform a search of information to find matches

        kwargs may contain a context object that is used to co-ordinate asynchronous searches; if not present then
        search should occur synchronously

        Returns:
            continuing_to_search (boolean), threat_list ([Threat])
            where:
                continuing_to_search - indicates if this searcher is still searching
                threat_list - matches that have already been found

        """
        raise NotImplementedError("Must implement 'search' method")

    # pylint: disable=too-many-locals
    @classmethod
    def store_threat_info(cls, name, source_artifact, properties_list, artifacts_list=None):
        """
        Create a threat record that records properties and artifacts
        If information is found, the related threat information should be stored using this method so that the results
        may be found

        Arguments:
        name - name of the threat record (not currently exposed in REST interface)
        properties_list - List of properties one would like to add, each item in the list is either of:
            * an unsaved models.Property object, or
            * a python dict object that includes the following fields - name, type, value
        artifacts_list - List of artifacts one would like to include, each item in the list is either of:
            * an unsaved models.Artifact object, or
            * a python dict object that includes the following fields - type, value
        """

        def build_object_from_dict(object_type, object_dict, fields):
            """ create object of type given a dict containing the desired fields """
            new_object = object_type()
            for field in fields:
                if field not in object_dict or not object_dict[field]:
                    return None
                setattr(new_object, field, object_dict[field])

            return new_object

        def key_name(key_object, fields):
            """ build the key_name from the concatenation of field values to identify duplicates """
            field_values = [unicode(getattr(key_object, field)) for field in fields]
            return "_".join(field_values)

        def new_threat_child(data_obj, threat, object_type, fields, existing):
            """ add dict/object to threat record """
            new_object = None
            if isinstance(data_obj, object_type):
                new_object = data_obj
            elif isinstance(data_obj, dict):
                new_object = build_object_from_dict(object_type, data_obj, fields)

            if new_object:
                if key_name(new_object, fields) in existing:
                    return
                if hasattr(new_object, "source_class"):
                    new_object.source_class = str(cls)
                new_object.threat = threat
                new_object.save()

        # does it already exist in the database already
        prop_fields = ["name", "type", "value"]
        artifact_fields = ["type", "value"]
        if not isinstance(source_artifact, Artifact):
            source_artifact = build_object_from_dict(Artifact, source_artifact, artifact_fields)
        match_artifacts = Artifact.objects.filter(
            type=source_artifact.type,
            value__contains=source_artifact.value,
            source_class=str(cls)
        )
        if match_artifacts:
            threat = match_artifacts[0].threat
        else:
            threat = Threat.objects.create(name=name)

        props = {key_name(p, prop_fields): True for p in threat.props.all()}
        for prop in properties_list:
            new_threat_child(prop, threat, Property, prop_fields, props)

        if not artifacts_list:
            artifacts_list = []
        if not match_artifacts:
            artifacts_list.insert(0, source_artifact)

        artifacts = {key_name(a, artifact_fields): True for a in threat.artifacts.all()}
        for artifact in artifacts_list:
            new_threat_child(artifact, threat, Artifact, artifact_fields, artifacts)

        return threat

    @classmethod
    def _search_and_done(cls, artifact_type, search_term, **kwargs):
        """ perform the search and indicate to the context object when complete """
        cls.search(artifact_type, search_term, **kwargs)
        if "context" in kwargs:
            search_context = kwargs["context"]
            search_context.remove_searcher(cls)

    @classmethod
    @postpone
    def kickoff_search(cls, artifact_type, search_term, **kwargs):
        """ kick off the search, this is performed in the separate thread """
        cls._search_and_done(artifact_type, search_term, **kwargs)

    @classmethod
    def async_search(cls, artifact_type, search_term, **kwargs):
        """ perform the search asynchronously on a different thread """
        hits = []
        if "context" in kwargs:
            search_context = kwargs["context"]
            search_context.add_searcher(cls)

            cls.kickoff_search(artifact_type, search_term, **kwargs)
        else:
            # Just do it syncronously anyway
            hits = cls.search(artifact_type, search_term, **kwargs)

        return hits


class InternalArtifactSearch(BaseArtifactSearch):

    """
    Search implentation that returns that results that we have in the local database
    Other searchers will insert data into the database asynchronously
    """
    @classmethod
    def search(cls, artifact_type, search_term, **kwargs):
        """ fetch the related threats from the artifact information in our local database"""
        artifact_matches = Artifact.objects.filter(type=artifact_type, value__contains=search_term)
        return [artifact.threat for artifact in artifact_matches]


class SearchContext(object):

    """ Class to hold context of searches, so that asynchronous searches can be co-ordinated """

    def __init__(self, context):
        self._context = copy.copy(context)
        self._active_searches = []
        self._id = uuid.uuid4().__str__()

    def __getstate__(self):
        pickle_dictionary = self.__dict__.copy()
        if self.type == "file.content":
            if isinstance(self.value, TemporaryUploadedFile):
                with open(self.value.temporary_file_path(), "r") as temp_file:
                    file_data = temp_file.read()
            else:
                file_data = self.value.read()

            # File data info, especially useful for test pickling
            self.file_data_len = len(file_data)
            self.base64_file_data_len = len(base64.b64encode(file_data))

            pickle_dictionary["_context"]["value"] = {
                "name": self.value.name,
                "content_type": self.value.content_type,
                "size": self.value.size,
                "charset": self.value.charset,
                "content": base64.b64encode(file_data),
            }

        return pickle_dictionary

    def __setstate__(self, pickle_dictionary):
        if pickle_dictionary["_context"]["type"] == "file.content" and \
                isinstance(pickle_dictionary["_context"]["value"], dict):
            arguments = pickle_dictionary["_context"]["value"]

            # File data info, especially useful for test pickling
            self.base64_file_data_len = len(arguments["content"])

            file_content = base64.b64decode(arguments.pop("content"))

            # File data info, especially useful for test pickling
            self.file_data_len = len(file_content)

            file_object = TemporaryUploadedFile(**arguments)
            file_object.write(file_content)
            file_object.flush()
            pickle_dictionary["_context"]["value"] = file_object

        self.__dict__.update(pickle_dictionary)

    @property
    def id(self):
        """ search context id, this will get used to lookup the pending results """
        return self._id

    @property
    def type(self):
        """ type requested in the initial search """
        return self._context['type']

    @property
    def value(self):
        """ value requested in the initial search """
        return self._context['value']

    @property
    def pending_searches(self):
        """ are there any searches still working """
        return len(self._active_searches) > 0

    def add_searcher(self, searcher):
        """ add a searcher to the context """
        self._active_searches.append(str(searcher))

    def remove_searcher(self, searcher):
        """ remove the searcher """
        name = str(searcher)
        if name in self._active_searches:
            self._active_searches.remove(name)

        self.save()

    def save(self):
        """ store context into cache """
        cache.set(self.id, self)

    @staticmethod
    def load(context_id):
        """ load a context object from the cache """
        return cache.get(context_id)
