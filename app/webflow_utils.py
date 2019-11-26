import logging
import json
from django.conf import settings
from django.forms.models import model_to_dict
from webflowpy.Webflow import Webflow
from .models import Submission, AnalysisResult, ProductAnalysisResult

logger = logging.getLogger(__name__)


def send_to_webflow(submission_id):
    submission = Submission.objects.get(id=submission_id)
    analysis = AnalysisResult.objects.get(submission=submission)
    products = ProductAnalysisResult.objects.filter(submission=submission)

    webflow_api = Webflow(token=settings.WEBFLOW_TOKEN)

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
        '_draft': False
    }

    data = {'fields': fields}
    json_data = json.dumps(data)
    item = webflow_api.createItem(settings.WEBFLOW_COLLECTION, json_data, live=True)
    logger.info(item)
    fields = {
        'header-image': analysis.seller_image_url,
        '_archived': False,
        '_draft': False,
        'name': submission.seller.seller_id,
        'slug': submission.seller.seller_id,
    }

    data = {'fields': fields}
    json_data = json.dumps(data)
    response = webflow_api.updateItem(settings.WEBFLOW_COLLECTION, item['_id'],
                                      json_data, live=True)
    logger.info(response)
