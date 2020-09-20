import logging
import traceback

import requests
from django.conf import settings
from requests.exceptions import RequestException


def validate_recaptcha(response):
    if settings.DEBUG:
        return True

    try:
        r = requests.post(settings.RECAPTCHA_URL, {
            'secret': settings.RECAPTCHA_KEY,
            'response': response,
        })
        data = r.json()
    except (ConnectionError, RequestException) as e:
        logger = logging.getLogger(__name__)
        logger.error(traceback.format_exc())
        return False

    return data.get('success', False)
