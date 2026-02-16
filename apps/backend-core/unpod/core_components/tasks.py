"""
Django-Q2 tasks for core_components app
Migrated from django_cron
"""
import logging

from unpod.core_components.services import process_event_cron

logger = logging.getLogger(__name__)


def event_trigger_cron():
    """
    Process event triggers
    Runs every 1 minute
    """
    try:
        logger.info("Starting event trigger processing")
        message = process_event_cron()
        logger.info(f"Event trigger processing completed: {message}")
        return message
    except Exception as e:
        logger.exception(f"Error in event_trigger_cron: {e}")
        raise
