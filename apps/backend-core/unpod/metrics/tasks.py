"""
Phase 3.3: Background tasks for metrics calculation using Django-Q2.

These tasks move expensive metrics calculations off the request path,
improving API response times and reducing database load during peak hours.
"""

from django.db.models import Q
from unpod.common.logger import UnpodLogger
from unpod.metrics.models import CallLog, Metrics
from unpod.metrics.utils import create_update_metric
from unpod.space.models import SpaceOrganization

metrics_logger = UnpodLogger("metrics.tasks")


def calculate_metrics_for_organization(organization_id, product_id):
    """
    Background task to calculate metrics for a specific organization.

    Args:
        organization_id: SpaceOrganization primary key
        product_id: Product identifier

    This task aggregates call logs and updates Metrics records.
    Should be called asynchronously via Django-Q.
    """
    try:
        org = SpaceOrganization.objects.get(id=organization_id)
        metrics_logger.info(
            f"Starting metrics calculation for organization {org.domain_handle} "
            f"(ID: {organization_id}, product: {product_id})"
        )

        # Use existing utility function for metrics calculation
        create_update_metric(org, product_id)

        metrics_logger.info(
            f"Completed metrics calculation for organization {org.domain_handle}"
        )

    except SpaceOrganization.DoesNotExist:
        metrics_logger.error(f"Organization with ID {organization_id} not found")
    except Exception as e:
        metrics_logger.error(
            f"Error calculating metrics for organization {organization_id}: {str(e)}",
            exc_info=True
        )


def process_uncalculated_call_logs(batch_size=100):
    """
    Background task to process call logs marked as uncalculated.

    Args:
        batch_size: Number of call logs to process in one batch

    This task finds CallLog records with calculated=False,
    groups them by organization/product, and triggers metrics recalculation.

    Expected to run every 5-15 minutes via Django-Q schedule.
    """
    try:
        # Find uncalculated call logs using the new index: calculated + creation_time
        uncalculated_logs = (
            CallLog.objects.filter(calculated=False)
            .select_related('organization')
            .order_by('creation_time')[:batch_size]
        )

        if not uncalculated_logs:
            metrics_logger.info("No uncalculated call logs found")
            return

        # Group by organization and product for batch processing
        org_product_pairs = set()
        log_ids = []

        for log in uncalculated_logs:
            if log.organization:
                org_product_pairs.add((log.organization.id, log.product_id))
                log_ids.append(log.id)

        metrics_logger.info(
            f"Found {len(log_ids)} uncalculated logs across "
            f"{len(org_product_pairs)} organization/product combinations"
        )

        # Trigger metrics calculation for each org/product pair
        for org_id, product_id in org_product_pairs:
            calculate_metrics_for_organization(org_id, product_id)

        # Mark processed logs as calculated
        CallLog.objects.filter(id__in=log_ids).update(calculated=True)

        metrics_logger.info(f"Marked {len(log_ids)} call logs as calculated")

    except Exception as e:
        metrics_logger.error(
            f"Error processing uncalculated call logs: {str(e)}",
            exc_info=True
        )


def recalculate_all_organization_metrics():
    """
    Background task to recalculate metrics for all active organizations.

    This is a heavy operation and should only run during off-peak hours
    (e.g., daily at 2 AM).

    Useful for:
    - Periodic data consistency checks
    - Recovering from calculation errors
    - Refreshing metrics after data corrections
    """
    try:
        active_orgs = SpaceOrganization.objects.filter(
            status='active'
        ).values_list('id', 'domain_handle')

        metrics_logger.info(
            f"Starting full metrics recalculation for {len(active_orgs)} organizations"
        )

        for org_id, domain_handle in active_orgs:
            try:
                # Get unique product_ids for this organization
                product_ids = (
                    CallLog.objects.filter(organization_id=org_id)
                    .values_list('product_id', flat=True)
                    .distinct()
                )

                for product_id in product_ids:
                    if product_id:  # Skip null product_ids
                        calculate_metrics_for_organization(org_id, product_id)

            except Exception as e:
                metrics_logger.error(
                    f"Error recalculating metrics for {domain_handle}: {str(e)}"
                )
                continue

        metrics_logger.info("Completed full metrics recalculation")

    except Exception as e:
        metrics_logger.error(
            f"Error in full metrics recalculation: {str(e)}",
            exc_info=True
        )
