"""
Django-Q2 tasks for wallet app
Migrated from django_cron
"""
import logging

from unpod.wallet.services import processGenerateHistory

logger = logging.getLogger(__name__)


def generate_task_transaction_history():
    """
    Generate transaction history task
    Runs every 60 minutes
    """
    try:
        logger.info("Starting transaction history generation")
        message = processGenerateHistory()
        logger.info(f"Transaction history generation completed: {message}")
        return message
    except Exception as e:
        logger.exception(f"Error in generate_task_transaction_history: {e}")
        raise
