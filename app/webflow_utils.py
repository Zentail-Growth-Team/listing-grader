import logging
import json
import requests
from django.conf import settings
from django.forms.models import model_to_dict
from django.utils import timezone
from .models import Submission, AnalysisResult, ProductAnalysisResult
from .exceptions import ProcessingException

logger = logging.getLogger(__name__)


def get_letter_score(value):
    if value >= 94:
        return "A"
    elif 93 >= value >= 90:
        return "A-"
    elif 89 >= value >= 87:
        return "B+"
    elif 86 >= value >= 83:
        return "B"
    elif 82 >= value >= 80:
        return "B-"
    elif 79 >= value >= 77:
        return "C+"
    elif 76 >= value >= 73:
        return "C"
    elif 72 >= value >= 70:
        return "C-"
    elif 69 >= value >= 67:
        return "D+"
    elif 66 >= value >= 60:
        return "D"
    else:
        return "F"


def get_score_color(value):
    if value >= 90:
        return "#4BD2E1"
    elif value >= 80:
        return "#428AE7"
    elif value >= 70:
        return "#FDBE38"
    elif value >= 60:
        return "#ED8919"
    else:
        return "#F70D49"


def send_to_webflow(submission_id):
    submission = Submission.objects.get(id=submission_id)
    analysis = AnalysisResult.objects.get(submission=submission)
    products = ProductAnalysisResult.objects.filter(submission=submission)

    products_list = []
    for product in products:
        products_list.append(model_to_dict(product))

    fields = {
        'name': submission.seller.seller_id,
        'copy-score': analysis.copy_score,
        'media-score': analysis.media_score,
        'feedback-score': analysis.feedback_score,
        'extra-content-score': analysis.extra_content_score,
        'submission-timestamp': submission.timestamp.isoformat(),
        'product-json-blob': json.dumps(products_list),
        'seller-title': submission.seller.seller_name,
        'copy-letter': get_letter_score(analysis.copy_score),
        'media-letter': get_letter_score(analysis.media_score),
        'feedback-letter': get_letter_score(analysis.feedback_score),
        'extra-content-letter': get_letter_score(analysis.extra_content_score),
        'copy-score-color': get_score_color(analysis.copy_score),
        'media-score-color': get_score_color(analysis.media_score),
        'feedback-score-color': get_score_color(analysis.feedback_score),
        'extra-content-score-color': get_score_color(analysis.extra_content_score),
        '_archived': False,
        '_draft': False,
        'slug': submission.seller.seller_id,
    }

    data = {'fields': fields}
    json_data = json.dumps(data)
    print(data)
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer {token}'.format(token=settings.WEBFLOW_TOKEN),
        'accept-version': settings.WEBFLOW_VERSION,
        'Content-Type': 'application/json',
    }

    # Check for existing analysis
    existing_analysis = False
    if AnalysisResult.objects.filter(seller__seller_id=submission.seller.seller_id, submission__status='success').count() > 1:
        prev_results = AnalysisResult.objects.filter(seller__seller_id=submission.seller.seller_id).order_by('-submission__timestamp')
        for result in prev_results:
            if result.webflow_cms_id:
                print('FIRST PUT')
                item = requests.put(
                    url=f"{settings.WEBFLOW_DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items/{result.webflow_cms_id}?live=true",
                    data=json_data,
                    headers=headers)
                item_json = item.json()
                print(item_json)
                if 'problems' in item_json:
                    logger.error(f"Problem uploading: {item_json}")
                    submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Problem uploading to webflow\n"
                    submission.save()
                    raise ProcessingException
                else:
                    analysis.webflow_cms_id = item_json['_id']
                    analysis.save()
                    logger.info(item_json)
                fields = {
                    'header-image': analysis.seller_image_url,
                    '_archived': False,
                    '_draft': False,
                    'name': submission.seller.seller_id,
                    'slug': submission.seller.seller_id,
                }
                data = {'fields': fields}
                json_data = json.dumps(data)
                print('SECOND PUT')
                response = requests.put(
                    url=f"{settings.WEBFLOW_DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items/{item_json['_id']}?live=true",
                    data=json_data,
                    headers=headers)
                print(response.json())
                if 'problems' in item_json:
                    logger.error(f"Problem uploading: {item_json}")
                    submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Problem uploading to webflow\n"
                    submission.save()
                    raise ProcessingException
                else:
                    logger.info(item_json)
                existing_analysis = True
                break
        if not existing_analysis:
            logger.error('Existing analysises with no CMS id on Webflow')
    else:
        print('FIRST POST')
        item = requests.post(url=f"{settings.WEBFLOW_DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items?live=true", data=json_data,
                             headers=headers)
        item_json = item.json()
        print(item_json)
        logger.info(item_json)
        fields = {
            'header-image': analysis.seller_image_url,
            '_archived': False,
            '_draft': False,
            'name': submission.seller.seller_id,
            'slug': item_json['slug'],
        }

        data = {'fields': fields}
        json_data = json.dumps(data)
        print('SECOND PUT')
        response = requests.put(
            url=f"{settings.WEBFLOW_DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items/{item_json['_id']}?live=true",
            data=json_data,
            headers=headers)
        print(response.json())
        if 'problems' in item_json:
            logger.error(f"Problem uploading: {item_json}")
            submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Problem uploading to webflow\n"
            submission.save()
            raise ProcessingException
        else:
            analysis.webflow_cms_id = item_json['_id']
            analysis.save()
            logger.info(item_json)



