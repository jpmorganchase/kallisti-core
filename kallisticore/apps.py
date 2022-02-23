from django.apps import AppConfig
import logging


class KallistiCoreConfig(AppConfig):
    name = 'kallisticore'
    logger = logging.getLogger(__name__)

    def ready(self):
        import kallisticore.signals  # noqa: F401
