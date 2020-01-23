import logging
import json
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_to_zapier(seller_email, seller_id, results_url, seller_name, status):
    data = {
        "seller_email": seller_email,
        "seller_id": seller_id,
        "results_url": results_url,
        "seller_name": seller_name,
        "status": status
    }
    json_data = json.dumps(data)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    response = requests.post(settings.ZAPIER_WEBHOOK, data=json_data, headers=headers)
    print(response.content)
    if response.status_code == 200:
        logger.info(f"{seller_id} - {seller_email} - {results_url} sent to Zapier")
    else:
        logger.error(f"Failed to send {seller_id} - {seller_email} - {results_url} to Zapier")
