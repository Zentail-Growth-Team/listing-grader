from django.urls import path
from .api_views import create_submission

urlpatterns = [
    path('submission', create_submission),
]