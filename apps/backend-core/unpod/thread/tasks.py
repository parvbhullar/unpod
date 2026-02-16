"""
Django-Q2 tasks for thread app
Migrated from django_cron
"""
import logging

from django.core.cache import cache
from unpod.thread.crons import fetch_create_cron_post

logger = logging.getLogger(__name__)


def create_cron_post():
    """
    Create cron posts task
    Runs every 1 minute
    Uses cache lock to prevent concurrent execution
    """
    try:
        check_key = cache.get("check_cron_post")
        if check_key and check_key == "1":
            logger.info("Cron Post Generation is already in progress")
            return "Cron Post Generation is already in progress"

        cache.set("check_cron_post", "1")
        logger.info("Starting cron post generation")
        message = fetch_create_cron_post()
        logger.info("Successfully generated Posts")
        cache.set("check_cron_post", "0")
        return message
    except Exception as e:
        cache.set("check_cron_post", "0")
        logger.exception(f"Error in create_cron_post: {e}")
        raise
