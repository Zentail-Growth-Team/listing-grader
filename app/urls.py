from django.urls import path
from .api_views import create_submission, resubmit

urlpatterns = [
    path('submission', create_submission),
    path('resubmit/<int:submission_pk>', resubmit, name='resubmit')
]