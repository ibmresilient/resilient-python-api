""" url routing for threats app """
from django.conf.urls import url
from threats.views import ScanView, RetrieveView

# pylint: disable=invalid-name
urlpatterns = [
    url(r'(?P<request_id>.+)$', RetrieveView.as_view()),
    url(r'', ScanView.as_view()),
]
