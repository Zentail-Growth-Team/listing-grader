import csv
import logging
from datetime import timedelta
from django.http.response import HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from urllib.parse import urlparse, parse_qs
from validate_email import validate_email
from .models import (
    Seller,
    Submission,
    AnalysisResult,
    ProductAnalysisResult
)
from .tasks import process_submission

logger = logging.getLogger(__name__)

IP_WHITELIST = ['71.127.147.142', '96.234.206.182']


@api_view(['POST'])
def create_submission(request):
    seller_profile_url = request.data.get('seller_profile_url', None)
    seller_email = request.data.get('seller_email', None)
    limit_results = request.data.get('limit_results', None)

    # Parameter validation
    if not seller_profile_url or not seller_email:
        return Response('Bad request. Missing parameters', status=status.HTTP_400_BAD_REQUEST)
    if not validate_email(seller_email):
        return Response('Invalid email address', status=status.HTTP_400_BAD_REQUEST)
    seller_profile_url = seller_profile_url.strip()
    if len(seller_profile_url) == 14 or len(seller_profile_url) == 13:
        seller_id = seller_profile_url
    else:
        if 'amazon.com' not in seller_profile_url.lower() or 'seller' not in seller_profile_url.lower():
            return Response('Invalid seller profile url', status=status.HTTP_424_FAILED_DEPENDENCY)
        parsed_url = urlparse(seller_profile_url)
        parsed_url_qs = parse_qs(parsed_url.query)
        if 'seller' not in parsed_url_qs:
            return Response('Invalid seller profile url', status=status.HTTP_424_FAILED_DEPENDENCY)
        else:
            seller_id = parsed_url_qs['seller'][0]

    # IP address submission check
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    ip_submissions = Submission.objects.filter(ip_address=ip_address,
                                               timestamp__gte=(timezone.now() -
                                                               timedelta(days=settings.SUBMISSIONS_TIMEDELTA_DAYS)))
    if "zentail.com" not in seller_email and ip_address not in IP_WHITELIST:
        if ip_submissions.count() > settings.SUBMISSIONS_ALLOWED:
            return Response('It looks like you have already requested a listing analysis from Zentail',
                            status=status.HTTP_409_CONFLICT)

    # Seller submission check
    try:
        seller = Seller.objects.get(email=seller_email, seller_id=seller_id)
        seller_submissions = Submission.objects.filter(seller=seller,
                                                       timestamp__gte=(timezone.now() -
                                                                       timedelta(
                                                                           days=settings.SUBMISSIONS_TIMEDELTA_DAYS)))
        if "zentail.com" not in seller_email and ip_address not in IP_WHITELIST:
            if seller_submissions.count() > settings.SUBMISSIONS_ALLOWED:
                return Response('It looks like you have already requested a listing analysis from Zentail',
                                status=status.HTTP_409_CONFLICT)
    except Seller.DoesNotExist:
        seller = Seller.objects.create(email=seller_email, seller_id=seller_id)

    # Create submission
    if limit_results and limit_results >= 0:
        submission = Submission.objects.create(seller=seller, ip_address=ip_address,
                                               source=Submission.WEBSITE, limit_results=limit_results)
    else:
        submission = Submission.objects.create(seller=seller, ip_address=ip_address,
                                               source=Submission.WEBSITE)
    process_submission(submission.id)
    return Response('Thank you for your submission. We\'ll email your results within 1 business day',
                    status=status.HTTP_201_CREATED)


@api_view(['GET'])
def resubmit(request, submission_pk):
    if request.user.is_staff:
        try:
            submisson = Submission.objects.get(id=submission_pk)
            new_submission = Submission.objects.create(seller=submisson.seller,
                                                       ip_address=submisson.ip_address,
                                                       source=Submission.RESUBMISSION)
            process_submission(new_submission.id)
        except Submission.DoesNotExist:
            return Response('Bad request.', status=status.HTTP_400_BAD_REQUEST)
        return HttpResponseRedirect(reverse('admin:app_submission_changelist'))
    return Response('Unauthorized', status=status.HTTP_401_UNAUTHORIZED)
