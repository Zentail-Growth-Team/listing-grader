import json
from django.conf import settings
from django.forms.models import model_to_dict
from webflowpy.Webflow import Webflow
from .models import Submission, AnalysisResult, ProductAnalysisResult


def send_to_webflow(submission_id):
    submission = Submission.objects.get(id=submission_id)
    analysis = AnalysisResult.objects.get(submission=submission)
    products = ProductAnalysisResult.objects.filter(submission=submission)

    webflow_api = Webflow(token=settings.WEBFLOW_TOKEN)
    print(webflow_api.sites())
    print(webflow_api.collections(settings.WEBFLOW_SITE_ID))
    # print(webflow_api.items(collection_id='5d07dc9098631121897d2d02'))

    products_list = []
    for product in products:
        products_list.append(model_to_dict(product))
    fields = {
        'name': 'Analysis-results',
        'Seller ID': submission.seller_id,
        'Copy Score': analysis.copy_score,
        'Media Score': analysis.media_score,
        'Feedback Score': analysis.feedback_score,
        'Extra Content Score': analysis.extra_content_score,
        'Submission Timestamp': submission.timestamp.strftime('%m/$d/%Y %I:%M %p'),
        'Product JSON Blob': products_list,
        '_archived': False,
        '_draft': False
    }

    data = {'fields': fields}
    json_data = json.dumps(data)
    item = webflow_api.createItem('5db07b5331da36426bfa34f1', json_data, live=True)
