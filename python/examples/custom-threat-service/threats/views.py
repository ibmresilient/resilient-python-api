""" View definition for threats app """
# We're overriding methods here that include certain args in the function signature which we are choosing to ignore
# We're also modelling requests using a view class, yet some of the methods do not use 'self'
# pylint: disable=unused-argument,no-self-use
from __future__ import unicode_literals

import json

from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from threats.controller import search_artifacts, SearchContext
from threats.serializers import ThreatSerializer


def process_threat_results(matching_threats, context):
    """ prepare response from threat results """
    threats = [ThreatSerializer(threat).data for threat in matching_threats]

    response_data = {
        "id": context.id,
        "hits": threats,
    }
    status_code = status.HTTP_200_OK
    if context.pending_searches:
        response_data["retry_secs"] = 60
        status_code = status.HTTP_303_SEE_OTHER

    return Response(response_data, status_code)


class ScanView(APIView):

    """ Scan service for matching threat artifacts """

    def options(self, request):  # pylint: disable=no-self-use
        """ Get the options exposed by this service instance """
        return Response({'upload_file': settings.SUPPORT_UPLOAD_FILE})

    def post(self, request):  # pylint: disable=no-self-use
        """ receive artifact information, and locate all threats that match it """
        response = None

        def check_required_value(
                arg_name,
                dictionary=request.data,
                description_format='Required parameter "{arg_name}" was not provided'):
            """
            Check that a required value has been provided by the client

            Arguments:
                arg_name - name of the value that should be present
                description_format - format specification of descriptive message
            """
            if arg_name not in dictionary:
                raise ValueError(
                    "{} - {}".format(
                        description_format.format(arg_name=arg_name),
                        json.dumps(dictionary),
                    )
                )

        try:
            context_data = request.data
            if request.content_type.startswith('multipart/form-data'):
                check_required_value('artifact')
                context_data = json.loads(request.data['artifact'])
                check_required_value('type', context_data)
                if context_data['type'] == "file.content":
                    check_required_value('file', request.FILES)
                    context_data['value'] = request.FILES['file']
                check_required_value('value', context_data)
            else:
                check_required_value('type')
                check_required_value('value')

            # Generate a search context
            context = SearchContext(context_data)
            matching_threats = search_artifacts(context_data['type'], context_data['value'], True, context=context)
            response = process_threat_results(matching_threats, context)
            context.save()

        except ValueError as ve:
            response = Response({'error': '{}'.format(str(ve))}, status.HTTP_400_BAD_REQUEST)

        # Keep broad exception handler, as this is an entry point to the service interface
        except Exception as ex:  # pylint: disable=broad-except
            response = Response({'error': '{}'.format(str(ex))}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response


class RetrieveView(APIView):  # pylint: disable=too-few-public-methods

    """ Retrieve next set of results for value """

    def get(self, request, request_id):
        """ Fetch results corresponding to given request id """
        request_id = request_id.rstrip('/')
        context = SearchContext.load(request_id)
        if context is None:
            # We return "no content" because we have none
            # 404 will cause the custom threat service caller to stop processing
            return Response({"error": "'{}' was not found".format(request_id)}, status.HTTP_204_NO_CONTENT)

        try:
            matching_threats = search_artifacts(context.type, context.value)
            response = process_threat_results(matching_threats, context)

        # Keep broad exception handler, as this is an entry point to the service interface
        except Exception as ex:  # pylint: disable=broad-except
            response = Response({'error': '{}'.format(str(ex))}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response
