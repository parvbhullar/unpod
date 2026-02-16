"""
Background tasks for telephony operations.

These tasks handle long-running operations like provider configuration
that should not block API responses.
"""
import logging

from .models import VoiceBridge
from ..subscription.services import SubscriptionService

logger = logging.getLogger(__name__)


def configure_bridge_providers(bridge_id, number_ids, product_id=None, request_data=None):
    """
    Background task to configure bridge numbers and providers.

    This task handles all the slow external API calls (SBC, LiveKit, VAPI)
    without blocking the main API response.

    Args:
        bridge_id: ID of the VoiceBridge to configure
        number_ids: List of TelephonyNumber IDs to associate
        product_id: Optional product ID for subscription updates
        request_data: Optional dict with additional configuration data
    """
    try:
        logger.info(f"Starting provider configuration for bridge {bridge_id}")

        # Get the bridge
        try:
            bridge = VoiceBridge.objects.select_related('hub').get(id=bridge_id)
        except VoiceBridge.DoesNotExist:
            logger.error(f"Bridge {bridge_id} not found")
            return {
                'success': False,
                'error': f'Bridge {bridge_id} not found'
            }

        # Import the view's _save_bridge_number logic
        # We'll refactor this to be usable from the task
        from .views import VoiceBridgeViewSet

        # Create a mock request object with the necessary data
        class MockRequest:
            def __init__(self, data):
                self.data = data or {}
                self.headers = {}

        mock_request = MockRequest({'numberIds': number_ids, **(request_data or {})})

        # Create a temporary view instance to use its method
        view = VoiceBridgeViewSet()
        view.request = mock_request

        # Call the _save_bridge_number method
        view._save_bridge_number(bridge)

        # Update consumed channels count if needed
        if product_id:
            try:
                subService = SubscriptionService(
                    organization=bridge.hub,
                    product_id=product_id
                )
                subService.update_consumed_channels(0)
                logger.info(f"Updated channel consumption for bridge {bridge_id}")
            except Exception as e:
                logger.warning(f"Failed to update channel consumption: {e}")

        logger.info(f"Successfully configured providers for bridge {bridge_id}")
        return {
            'success': True,
            'bridge_id': bridge_id,
            'message': 'Provider configuration completed'
        }

    except Exception as e:
        logger.error(f"Error configuring bridge {bridge_id}: {str(e)}", exc_info=True)
        return {
            'success': False,
            'bridge_id': bridge_id,
            'error': str(e)
        }
