import logging
import json
import requests
from django.conf import settings
from django.forms.models import model_to_dict
from .models import Submission, AnalysisResult, ProductAnalysisResult
from .zapier_utils import send_to_zapier

logger = logging.getLogger(__name__)

RESULTS_BASE_URL = "https://gradier.webflow.io/analysis-result/"


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



