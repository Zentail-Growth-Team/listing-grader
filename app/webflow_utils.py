import logging
import json
import requests
from django.conf import settings
from django.forms.models import model_to_dict
from .models import Submission, AnalysisResult, ProductAnalysisResult

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = 'https://api.webflow.com'
VERSION = '1.0.0'


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
    }

    data = {'fields': fields}
    json_data = json.dumps(data)
    print(data)
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer {token}'.format(token=settings.WEBFLOW_TOKEN),
        'accept-version': VERSION,
        'Content-Type': 'application/json',
    }
    print('FIRST POST')
    item = requests.post(url=f"{DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items?live=true", data=json_data,
                         headers=headers)
    item_json = item.json()
    print(item_json)
    logger.info(item_json)
    if 'problems' in item_json:
        if "Unique value is already in database" in item_json['problems'][0]:
            item_id = item['path'].split('/')[-1]
            print('FIRST PUT')
            item = requests.put(url=f"{DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items/{item_id}?live=true",
                                data=json_data,
                                headers=headers)
            item_json = item.json()
            print(item_json)
            logger.info(item_json)
    if '_id' in item_json:
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
        response = requests.put(url=f"{DEFAULT_ENDPOINT}/collections/{settings.WEBFLOW_COLLECTION}/items/{item_json['_id']}?live=true",
                                data=json_data,
                                headers=headers)
        print(response.json())
        logger.info(response)
    else:
        logger.error(f"Problem uploading: {item_json}")

