"""
Django-Q hooks for telephony background tasks.

These hooks are called when background tasks complete.
"""
import logging

logger = logging.getLogger(__name__)


def provider_configuration_complete(task):
    """
    Hook called when provider configuration task completes.

    Args:
        task: Django-Q Task object with result and metadata
    """
    try:
        result = task.result

        if result and result.get('success'):
            bridge_id = result.get('bridge_id')
            logger.info(
                f"Provider configuration completed successfully for bridge {bridge_id}"
            )
            # TODO: Send notification to user/frontend if needed
            # Example: send_sse_notification(bridge_id, 'configuration_complete')

        else:
            error = result.get('error') if result else 'Unknown error'
            bridge_id = result.get('bridge_id') if result else 'unknown'
            logger.error(
                f"Provider configuration failed for bridge {bridge_id}: {error}"
            )
            # TODO: Send error notification to user/frontend
            # Example: send_sse_notification(bridge_id, 'configuration_failed', error)

    except Exception as e:
        logger.error(f"Error in provider_configuration_complete hook: {e}", exc_info=True)
