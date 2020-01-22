import logging
import json
import requests
from django.conf import settings
from django.forms.models import model_to_dict
from .models import Submission, AnalysisResult, ProductAnalysisResult
from .zapier_utils import send_to_zapier

logger = logging.getLogger(__name__)

RESULTS_BASE_URL = "https://gradier.webflow.io/analysis-result/"


def get_letter_score(value):
    if value >= 94:
        return "A"
    elif 93 >= value >= 90:
        return "A-"
    elif 87 >= value >= 89:
        return "B+"
    elif 83 >= value >= 86:
        return "B"
    elif 80 >= value >= 82:
        return "B-"
    elif 77 >= value >= 79:
        return "C+"
    elif 73 >= value >= 76:
        return "C"
    elif 70 >= value >= 72:
        return "C-"
    elif 67 >= value >= 69:
        return "D+"
    elif 60 >= value >= 66:
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
    if AnalysisResult.objects.filter(seller=submission.seller).count() > 1:
        prev_results = AnalysisResult.objects.filter(seller=submission.seller).order_by('-submission__timestamp')
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
                else:
                    logger.info(item_json)
                    send_to_zapier(submission.seller.email,
                                   submission.seller.seller_id,
                                   f"{RESULTS_BASE_URL}{submission.seller.seller_id}")
                break

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
        else:
            analysis.webflow_cms_id = item_json['_id']
            analysis.save()
            logger.info(item_json)
            send_to_zapier(submission.seller.email,
                           submission.seller.seller_id,
                           f"{RESULTS_BASE_URL}{submission.seller.seller_id}")



