import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'