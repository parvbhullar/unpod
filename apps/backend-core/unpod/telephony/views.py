from collections import defaultdict
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .filters import TrunkFilter
from .models import (
    ProviderCredential,
    VoiceBridge,
    VoiceBridgeNumber,
    BridgeProviderConfig,
)
from .providers.livekit import LivekitProvider
from .providers.vapi import VapiProvider
from .sbc_trunking.sbc import SBC
from .serializers import (
    ProviderCredentialSerializer,
    VoiceBridgeSerializer,
    VoiceBridgeNumberSerializer,
    TrunkSerializer,
    TrunkDetailSerializer,
)
from .utils import (
    update_trunk,
    delete_trunk,
    delete_trunks,
    update_trunks_numbers,
    save_bridge_config,
    create_livekit_trunks,
    update_livekit_trunks,
    update_pilot_number,
    create_number,
    is_valid_credentials,
)
from ..common.datetime import get_datetime_now
from ..common.enum import TrunkDirection, TrunkType, TrunkStatus
from ..common.exception import APIException206
from ..common.pagination import UnpodCustomPagination
from ..common.renderers import UnpodJSONRenderer
from ..core_components.serializers import TelephonyNumberSerializer
from ..documents.models import Document
from ..space.models import SpaceOrganization
from ..space.utils import checkSpaceOrg
from ..core_components.models import Pilot, TelephonyNumber
from django.utils.functional import SimpleLazyObject
from unpod.common.utils import get_global_configs
from ..subscription.services import SubscriptionService

sip_config = SimpleLazyObject(lambda: get_global_configs("unpod_sip_config"))


class TelephonyNumberViewSet(viewsets.GenericViewSet):
    queryset = TelephonyNumber.objects.all()
    serializer_class = TelephonyNumberSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def unlink_provider(self, request, number_id):
        try:
            telephony_number = TelephonyNumber.objects.filter(id=number_id).first()
            if not telephony_number:
                return Response(
                    {
                        "message": "Number not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            vbNumber = VoiceBridgeNumber.objects.filter(
                number_id=telephony_number.id
            ).first()

            if not vbNumber:
                return Response(
                    {
                        "message": "No provider linked to this number.",
                    },
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )

            # Check if trunks are created for this number, then update them
            trunks = BridgeProviderConfig.objects.filter(
                bridge=vbNumber.bridge, numbers__contains=vbNumber.number.number
            )
            update_trunks_numbers(trunks, vbNumber)
            try:
                sbc = SBC()
                sbc.delete_sbc(
                    vbNumber.number.number,
                    vbNumber.bridge,
                    vbNumber.provider_credential,
                )
            except Exception as e:
                pass

            # Delete the provider credential
            vbNumber.provider_credential_id = None
            vbNumber.save()

            return Response(
                {
                    "status_code": 200,
                    "message": f"Provider unlinked from number {telephony_number.number}",
                    "data": TelephonyNumberSerializer(telephony_number).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to unlink provider.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


    def create(self, request, *args, **kwargs):
        serializer = TelephonyNumberSerializer(data=create_number(request.data))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoiceBridgeViewSet(viewsets.ModelViewSet):
    queryset = VoiceBridge.objects.all()
    serializer_class = VoiceBridgeSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]
    lookup_field = "slug"

    def get_list_queryset(self):
        queryset = super().get_queryset()

        # Optional query params for filtering
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        product_id = self.request.headers.get("Product-Id", None)
        if not product_id:
            raise APIException206({"message": "Please provide Product-Id in headers"})

        queryset = queryset.filter(product_id=product_id)

        domain_handle = self.request.headers.get("Org-Handle", None)
        if not domain_handle or domain_handle == "":
            raise APIException206({"message": "Please provide organization handle"})

        spaceOrg = checkSpaceOrg(domain_handle)
        queryset = queryset.filter(organization=spaceOrg)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_list_queryset())
        paginator = UnpodCustomPagination(request, queryset, self.get_serializer)
        return paginator.get_paginated_response()

    def _save_bridge_number(self, bridge):
        """
        Update bridge numbers. This method separates database operations from external API calls
        to avoid holding database locks during slow external requests.
        """
        data = self.request.data.copy()
        number_ids = data.get("numberIds", [])
        sbc = SBC()

        # Collect external API operations to run after database commits
        external_api_calls = []

        if number_ids:
            # Step 1: Collect data about numbers to delete (read-only, no lock)
            vbNumbers = VoiceBridgeNumber.objects.filter(bridge=bridge).exclude(
                number_id__in=number_ids
            ).select_related('number', 'provider_credential', 'bridge', 'provider_credential__provider')

            delNumberIDs = list(vbNumbers.values_list("number_id", flat=True))
            vbNumbers_list = list(vbNumbers)  # Evaluate queryset to avoid repeated queries

            # Step 2: Update trunk configurations (can be slow)
            if vbNumbers_list:
                for vbn in vbNumbers_list:
                    print("number:", vbn, [vbn.number.number], vbn.id)
                    trunks = BridgeProviderConfig.objects.filter(
                        bridge=bridge, numbers__contains=vbn.number.number
                    )
                    update_trunks_numbers(trunks, vbn)

            # Step 3: Delete SBC configurations (external API calls, not in transaction)
            if delNumberIDs:
                for vbn in vbNumbers_list:
                    if vbn.number:
                        try:
                            sbc.delete_configs(vbn.number.number, vbn.bridge, vbn.provider_credential)
                        except Exception as e:
                            print(f"Warning: SBC delete_configs failed for {vbn.number.number}: {e}")

                # Step 4: Database cleanup (fast transaction)
                with transaction.atomic():
                    VoiceBridgeNumber.objects.filter(
                        bridge=bridge, number_id__in=delNumberIDs
                    ).delete()
                    TelephonyNumber.objects.filter(id__in=delNumberIDs).update(
                        state="NOT_ASSIGNED"
                    )

            # get existing VoiceBridgeNumber records for this bridge
            existingVbNumbers = VoiceBridgeNumber.objects.filter(bridge=bridge).exclude(
                number_id__in=delNumberIDs if delNumberIDs else []
            ).select_related('number', 'provider_credential', 'provider_credential__provider')

            existing_ids = set(existingVbNumbers.values_list("number_id", flat=True))

            # Batch fetch available numbers and bulk create VoiceBridgeNumber objects
            new_number_ids = set(number_ids) - existing_ids
            if new_number_ids:
                # Fast database transaction for creating new associations
                with transaction.atomic():
                    available_numbers = set(
                        TelephonyNumber.objects.filter(
                            id__in=new_number_ids,
                            state="NOT_ASSIGNED",
                            active=True
                        ).values_list('id', flat=True)
                    )

                    # Bulk create VoiceBridgeNumber objects
                    if available_numbers:
                        vbn_objects = [
                            VoiceBridgeNumber(
                                bridge=bridge,
                                number_id=num_id,
                                status="active",
                                config_json=data.get("config_json", {}),
                                connectivity_type=data.get(
                                    "connectivity_type", "voice_infra_provider"
                                ),
                                agent_id=data.get("agent_id"),
                            )
                            for num_id in available_numbers
                        ]
                        VoiceBridgeNumber.objects.bulk_create(vbn_objects)

                        # Bulk update TelephonyNumber state
                        TelephonyNumber.objects.filter(id__in=available_numbers).update(
                            state="ASSIGNED",
                            active=True
                        )

                # Refresh existingVbNumbers to include newly created ones
                existingVbNumbers = VoiceBridgeNumber.objects.filter(bridge=bridge).select_related(
                    'number', 'provider_credential', 'provider_credential__provider'
                )

            # Process provider configurations (LiveKit, VAPI, etc.)
            # These operations include external API calls, so they're outside transactions
            existingVbNumbers_list = list(existingVbNumbers)
            if existingVbNumbers_list:
                # Group existing VoiceBridgeNumbers by provider_credential
                provider_groups = defaultdict(list)

                for vbn in existingVbNumbers_list:
                    if vbn.number and vbn.provider_credential:
                        provider_groups[vbn.provider_credential].append(vbn)

                for credential, vbns in provider_groups.items():
                    provider_name = credential.provider.name.lower()
                    print(
                        "provider_credential",
                        credential,
                        "provider_name",
                        provider_name,
                        number_ids,
                        vbns,
                    )
                    print("==================================")

                    if provider_name == "livekit":
                        print("provider_name", provider_name)
                        nums = [vbn.number.number for vbn in vbns]
                        ids = [vbn.number.id for vbn in vbns]
                        trunks = BridgeProviderConfig.objects.filter(
                            bridge=bridge, provider_credential=credential
                        )
                        if trunks.exists():
                            # If trunks exist, update them
                            payload = {
                                "name": data.get("name"),
                                "numbers": nums,
                                "vbn_ids": ids,
                            }

                            print("nums", nums, payload)
                            print("==================================")

                            update_livekit_trunks(trunks, bridge, credential, payload)

                            payload["provider"] = credential.name

                            # External API call (not in transaction)
                            res = sbc.create_configs(payload, bridge, credential)

                            # Database update (fast transaction)
                            with transaction.atomic():
                                VoiceBridgeNumber.objects.filter(
                                    number__number__in=nums
                                ).update(sbc_config=res)

                        else:
                            # If no trunks exist, create them
                            payload = {
                                "name": data.get("name") or bridge.name,
                                "numbers": nums,
                                "vbn_ids": ids,
                                "address": sip_config.get("up_sip_url", ""),
                            }

                            print("payload", payload)

                            create_livekit_trunks(bridge, credential, payload)

                            payload["provider"] = credential.name

                            # External API call (not in transaction)
                            res = sbc.create_configs(payload, bridge, credential)

                            # Database update (fast transaction)
                            with transaction.atomic():
                                VoiceBridgeNumber.objects.filter(
                                    number__number__in=nums
                                ).update(sbc_config=res)

                    if provider_name == "vapi":
                        print("provider_name", provider_name)
                        print("==================================")
                        vapi = VapiProvider()
                        for record in vbns:
                            payload = {
                                "name": data.get("name") or bridge.name,
                                "numbers": [record.number.number],
                                "vbn_ids": [record.number.id],
                                "address": sip_config.get("up_sip_ip", ""),
                            }
                            print("record", record.number.number)

                            print("==================================")
                            trunk = (
                                BridgeProviderConfig.objects.filter(
                                    bridge=bridge,
                                    provider_credential=credential,
                                    numbers__contains=record.number.number,
                                )
                            ).first()

                            if trunk:
                                # If trunk exist, update it
                                print("trunk exist", trunk)
                                print("==================================")

                                payload["provider"] = credential.name

                                sbc.create_configs(payload, bridge, credential)
                            else:
                                # If no trunks exist, create them
                                config = {
                                    "name": payload.get("name"),
                                    "provider": "Vapi",
                                    "number": record.number.number,
                                    "gateway_ip": record.config_json.get(
                                        "gateway_ip", sip_config.get("up_sip_ip", "")
                                    ),
                                    "api_key": credential.api_key,
                                    "api_secret": credential.api_secret or "",
                                }
                                result = vapi.set_inbound(config)

                                if result.get("success"):
                                    record.has_trunks = True

                                print(
                                    "set_inbound result:", result.data, payload, config
                                )
                                print("==================================")
                                save_bridge_config(
                                    result, bridge, credential, payload, "both"
                                )

                                payload["provider"] = credential.name

                                # External API call (not in transaction)
                                res = sbc.create_configs(payload, bridge, credential)

                                # Database update (fast transaction)
                                with transaction.atomic():
                                    record.sbc_config = res
                                    record.save(update_fields=['sbc_config', 'has_trunks'])

        else:
            # If no numberIds provided, delete all associated numbers records
            print("deleting records")
            vbn_qs = VoiceBridgeNumber.objects.filter(bridge=bridge).select_related(
                'number', 'provider_credential'
            )

            deletable_ids = list(vbn_qs.values_list("id", flat=True))
            update_numbers = list(vbn_qs.values_list("number", flat=True))
            vbn_list = list(vbn_qs)  # Evaluate queryset once

            # External API calls (not in transaction)
            for vbn in vbn_list:
                if vbn.number:
                    try:
                        sbc.delete_configs(vbn.number.number, bridge, vbn.provider_credential)
                    except Exception as e:
                        print(f"Warning: SBC delete_configs failed: {e}")

            # Database operations (fast transaction)
            with transaction.atomic():
                VoiceBridgeNumber.objects.filter(
                    bridge=bridge, id__in=deletable_ids
                ).delete()

                TelephonyNumber.objects.filter(id__in=update_numbers).update(
                    state="NOT_ASSIGNED"
                )

            trunks = BridgeProviderConfig.objects.filter(bridge=bridge)
            delete_trunks(trunks)

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            number_ids = data.pop("numberIds", None)
            handle_domain = request.headers.get("Org-Handle", None)

            if number_ids is not None:
                if not isinstance(number_ids, list):
                    return Response(
                        {"error": "NumberIds must be a list of integers."}, status=400
                    )

            if not handle_domain:
                return Response({"error": "Missing 'Org-Handle' header."}, status=400)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            return self.perform_create(serializer)

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to create bridge.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        with transaction.atomic():
            handle_domain = self.request.headers.get("Org-Handle")
            product_id = self.request.headers.get("Product-Id", None)

            try:
                organization = SpaceOrganization.objects.filter(
                    domain_handle=handle_domain
                ).first()

                if not organization:
                    return Response(
                        {"detail": f"No organization found for domain: {handle_domain}"}
                    )

                bridge = serializer.save(organization=organization, product_id=product_id)
                data = self.request.data.copy()
                number_ids = data.get("numberIds", [])

                for num_id in number_ids:
                    number = TelephonyNumber.objects.filter(
                        id=num_id, state="NOT_ASSIGNED", active=True
                    )

                    if number.first():
                        VoiceBridgeNumber.objects.create(
                            bridge=bridge,
                            number_id=num_id,
                            status="active",
                            config_json=data.get("config_json", {}),
                            connectivity_type=data.get(
                                "connectivity_type", "voice_infra_provider"
                            ),
                            agent_id=data.get("agent_id"),
                        )

                        number.update(state="ASSIGNED", active=True)

            except SpaceOrganization.DoesNotExist:
                return Response(
                    {"message": f"No organization found for domain: {handle_domain}"},
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )

            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"data": serializer.data, "message": "Bridge created successfully."},
                status=status.HTTP_201_CREATED,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        data = request.data.copy()

        number_ids = data.pop("numberIds", None)

        if number_ids is not None:
            if not isinstance(number_ids, list):
                return Response(
                    {"error": "NumberIds must be a list of integers."}, status=400
                )

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_update(serializer)
            return Response(
                {"data": serializer.data, "message": "Bridge updated successfully."},
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, "args") and e.args else str(e),
                    "data": serializer.data,
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        except Exception as e:
            return Response(
                {"message": str(e), "data": serializer.data},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_update(self, serializer):
        """
        Update VoiceBridge and queue provider configuration as a background task.

        This method saves the bridge metadata immediately and returns a response,
        while external API calls (SBC, LiveKit, VAPI) are processed asynchronously.
        """
        from django_q.tasks import async_task

        product_id = self.request.headers.get("Product-Id", None)

        # Save bridge metadata (fast operation)
        with transaction.atomic():
            bridge = serializer.save()

            if product_id and not bridge.product_id:
                bridge.product_id = product_id
                bridge.save(update_fields=['product_id'])

        # Queue provider configuration as background task if numbers are being updated
        data = self.request.data.copy()
        number_ids = data.pop("numberIds", None)

        if number_ids is not None:
            # Queue the task asynchronously
            task_id = async_task(
                'unpod.telephony.tasks.configure_bridge_providers',
                bridge.id,
                number_ids,
                product_id,
                data,
                task_name=f'configure_bridge_{bridge.id}',
                hook='unpod.telephony.hooks.provider_configuration_complete'
            )

            # Log the task queuing
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Queued provider configuration task {task_id} for bridge {bridge.id}")
        else:
            # No number changes, update channels synchronously
            if product_id:
                subService = SubscriptionService(
                    organization=bridge.organization, product_id=product_id
                )
                subService.update_consumed_channels(0)

    @staticmethod
    def create_update_bridge_config(
        result, bridge, credential, direction, data, numbers
    ):
        if result.status_code != 200:
            if result.status_code == status.HTTP_206_PARTIAL_CONTENT:
                raise serializers.ValidationError(result.data.get("message"))
            raise ValueError(
                result.data.get(
                    "message", f"trunk update failed for provider {credential.name}"
                )
            )

        print(
            "create_update_bridge_config address:",
            data.get("address", sip_config.get("domain", "")),
        )
        nums = [vbn.number.number for vbn in numbers]
        obj, created = BridgeProviderConfig.objects.update_or_create(
            bridge=bridge,
            provider_credential=credential,
            direction=direction,
            sip_refer=result.data.get("sip_refer"),
            defaults={
                "numbers": nums,
                "vbn_ids": [vbn.number.id for vbn in numbers],
                "direction": direction,
                "sip_credentials_id": result.data.get("credentials_id", ""),
                "name": data.get("name", bridge.name),
                "address": data.get("address", sip_config.get("domain")),
                "trunk_type": TrunkType.voice_infra.value,
                "sip_refer": result.data.get("sip_refer"),
                "service_type": "service" if direction != "" else "rule",
                "config": {"source": "auto-created on bridge", "updated": True},
            },
        )

        return obj, created

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            organization = instance.organization
            self.perform_destroy(instance)

            """
            Update consumed channels count.
            """
            product_id = self.request.headers.get("Product-Id")
            if product_id:
                subService = SubscriptionService(
                    organization=organization, product_id=product_id
                )
                subService.update_consumed_channels(0)

            return Response(
                {"message": "Bridge deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, "args") and e.args else str(e),
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        except Exception as e:
            return Response(
                {
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_destroy(self, instance):
        sbc = SBC()
        with transaction.atomic():
            # Delete all associated VoiceBridgeNumbers
            trunks = BridgeProviderConfig.objects.filter(bridge=instance)

            for i in trunks:
                numbers = i.numbers
                for num in numbers:
                    sbc.delete_configs(num, instance, i.provider_credential)

            delete_trunks(trunks)

            existing_ids = set(
                VoiceBridgeNumber.objects.filter(bridge=instance).values_list(
                    "number_id", flat=True
                )
            )
            # Unassign all associated numbers
            TelephonyNumber.objects.filter(id__in=existing_ids).update(
                state="NOT_ASSIGNED"
            )

            # Manually set bridge to NULL in metrics to avoid cascade issues
            try:
                from unpod.metrics.models import Metrics, CallLog

                Metrics.objects.filter(bridge=instance).update(bridge=None)
                CallLog.objects.filter(bridge=instance).update(bridge=None)
            except Exception as e:
                print(f"Warning: Could not update metrics: {str(e)}")

            instance.delete()

    @action(detail=True, methods=["post", "patch"], url_path="numbers")
    def numbers(self, request, slug=None):
        try:
            bridge = self.get_object()
            data = request.data.copy()
            number_id = data.get("number_id")
            credential_id = data.get("provider_credential_id")

            if not number_id:
                return Response({"message": "Number is required"}, status=400)

            if not credential_id:
                return Response({"message": "Provider is required"}, status=400)

            number = TelephonyNumber.objects.filter(id=number_id, state="ASSIGNED")

            if not number:
                return Response(
                    {"message": "Number is not assigned or does not exist."},
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )

            # Fetch existing VoiceBridgeNumber for this bridge and number_id
            vbns = VoiceBridgeNumber.objects.filter(number_id=number_id, bridge=bridge)

            if vbns.exists():
                # If exists, update it
                vbn = vbns.first()

                # Check if trunks are created for this number, then update them
                trunks = BridgeProviderConfig.objects.filter(
                    bridge=bridge, numbers__contains=vbn.number.number
                )
                if trunks.exists():
                    update_trunks_numbers(trunks, vbn)

                vbn.provider_credential_id = credential_id
                vbn.save()

                serializer = VoiceBridgeNumberSerializer(vbn)
                return Response(
                    {
                        "data": serializer.data,
                        "message": "Number linked with provider successfully.",
                        "number": number,
                    },
                    status=201,
                )
            # If not exists, check if the number is linked with another bridge
            else:
                return Response(
                    {
                        "message": "Provided number is already assigned to another bridge.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to link provider.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["delete"], url_path="numbers/(?P<number_id>[^/.]+)")
    def remove_number(self, request, pk=None, number_id=None):
        try:
            vbn = VoiceBridgeNumber.objects.get(bridge_id=pk, number_id=number_id)
            vbn.delete()
            return Response({"message": "Detached number from bridge."})
        except VoiceBridgeNumber.DoesNotExist:
            return Response({"error": "Number not found in bridge."}, status=404)


class ProviderCredentialViewSet(viewsets.ModelViewSet):
    queryset = ProviderCredential.objects.all()
    serializer_class = ProviderCredentialSerializer
    permission_classes = [AllowAny]
    renderer_classes = [UnpodJSONRenderer]

    def get_organization_from_request(self, request):
        domain_handle = request.headers.get("Org-Handle")
        if not domain_handle:
            raise ValidationError({"detail": "Missing 'Org-Handle' header."})

        try:
            return SpaceOrganization.objects.filter(domain_handle=domain_handle).first()
        except SpaceOrganization.DoesNotExist:
            raise ValidationError(
                {"detail": f"No organization found for domain: {domain_handle}"}
            )

    def perform_create(self, serializer):
        organization = self.get_organization_from_request(self.request)
        serializer.save(organization=organization, is_valid=is_valid_credentials(self.request.data))

    def perform_update(self, serializer):
        organization = self.get_organization_from_request(self.request)
        serializer.save(organization=organization, is_valid=is_valid_credentials(self.request.data))

    def get_queryset(self):
        organization = self.get_organization_from_request(self.request)
        queryset = ProviderCredential.objects.filter(organization=organization)

        provider_type = self.request.query_params.get("type")
        if provider_type:
            provider_type = provider_type.strip().upper()
            queryset = queryset.filter(provider__type__iexact=provider_type)

        return queryset

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)

            return Response(
                {"message": "Provider credential deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, "args") and e.args else str(e),
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        except Exception as e:
            return Response(
                {
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            # Delete all associated VoiceBridgeNumbers
            trunks = BridgeProviderConfig.objects.filter(provider_credential=instance)

            sbc = SBC()
            for i in trunks:
                numbers = i.numbers
                for number in numbers:
                    sbc.delete_configs(number, i.bridge, i.provider_credential)

            delete_trunks(trunks)

            # Delete the ProviderCredential itself
            instance.delete()


class VoiceBridgeNumberViewSet(viewsets.ModelViewSet):
    queryset = VoiceBridgeNumber.objects.all()
    serializer_class = VoiceBridgeNumberSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        product_id = request.headers.get("Product-Id")
        instance = self.get_object()
        data = request.data.copy()
        agent_id = data.get("agent_id", None)
        channelsCount = data.get("channels_count", 0)

        if agent_id:
            query = Q(handle=agent_id)
            agent = Pilot.objects.filter(query).first()
            if agent:
                update_pilot_number(agent, instance)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            if product_id and channelsCount != instance.channels_count:
                newCount = channelsCount - instance.channels_count
                subService = SubscriptionService(
                    organization=instance.bridge.organization, product_id=product_id
                )
                updated, message = subService.update_consumed_channels(newCount)

                if not updated:
                    raise serializers.ValidationError(message)

            self.perform_update(serializer)
            return Response(
                {
                    "data": serializer.data,
                    "message": "Voice Bridge Number updated successfully.",
                },
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, "args") and e.args else str(e),
                    "data": serializer.data,
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        except Exception as e:
            return Response(
                {"message": str(e), "data": serializer.data},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TrunkViewSet(viewsets.ModelViewSet):
    queryset = BridgeProviderConfig.objects.all()
    # serializer_class = TrunkSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TrunkFilter

    def get_serializer_class(self):
        if self.action == "list":
            return TrunkSerializer
        elif self.action == "retrieve":
            return TrunkDetailSerializer
        return TrunkDetailSerializer  # default fallback

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            bridge = request.query_params.get("bridge", None)

            if bridge:
                queryset = queryset.filter(bridge__slug=bridge)
                serializer = self.get_serializer(queryset, many=True)
            else:
                return Response(
                    {"data": [], "message": "No Trunks Found."},
                )

            return Response(
                {"data": serializer.data, "message": "Trunks fetched successfully."},
            )

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to fetch data.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        trunk = self.get_object()
        data = request.data.copy()
        data["numbers"] = trunk.numbers
        serializer = self.get_serializer(trunk, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        result = update_trunk(trunk, data)

        if result.status_code == status.HTTP_200_OK:
            config = data.get("config", {})
            config["source"] = "auto-created on bridge"
            config["updated"] = True
            config["updated_at"] = get_datetime_now()
            serializer.validated_data["config"] = config

            serializer.save()

            return Response(
                {"data": serializer.data, "message": "Trunk updated successfully."},
                status=status.HTTP_200_OK,
            )

        if result.status_code == status.HTTP_206_PARTIAL_CONTENT:
            return Response(
                {
                    "message": result.data.get("message"),
                    "data": request.data,
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

        return Response(
            {"data": request.data, "message": result.data.get("message")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        trunk = self.get_object()
        sbc = SBC()
        numbers = trunk.numbers
        for number in numbers:
            sbc.delete_configs(number, trunk.bridge, trunk.provider_credential)

        result = delete_trunk(trunk)

        if result.status_code == status.HTTP_200_OK:
            trunk.delete()

            return Response(
                {"message": "Trunk delete successfully."}, status=status.HTTP_200_OK
            )

        if result.status_code == status.HTTP_206_PARTIAL_CONTENT:
            return Response(
                {"message": result.data.get("message")},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

        return Response(
            {"message": result.data.get("message")}, status=status.HTTP_400_BAD_REQUEST
        )


class CreateTrunkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        renderer_classes=[UnpodJSONRenderer],
        url_path="create-outbound-trunk",
    )
    def create_vapi_outbound(self, request):
        """
        Creates a Vapi SIP Trunk (outbound) and saves it in the DB.
        """
        bridge_id = request.data.get("bridge_id")
        credential_id = request.data.get("provider_credential_id")
        if not bridge_id or not credential_id:
            return Response(
                {"error": "bridge_id and provider_credential_id are required."},
                status=400,
            )

        try:
            bridge = VoiceBridge.objects.get(id=bridge_id)
            credential = ProviderCredential.objects.get(id=credential_id)
        except VoiceBridge.DoesNotExist:
            return Response({"error": "VoiceBridge not found."}, status=404)
        except ProviderCredential.DoesNotExist:
            return Response({"error": "ProviderCredential not found."}, status=404)

        # Fetch an associated number
        vb_number = VoiceBridgeNumber.objects.filter(
            bridge=bridge, provider_credential=credential
        ).first()
        if not vb_number or not vb_number.number:
            return Response(
                {
                    "error": "No associated telephony number found for this bridge/credential."
                },
                status=404,
            )

        telephony_number = vb_number.number.number
        gateway_ip = vb_number.config_json.get("gateway_ip") or sip_config.get(
            "domain"
        )  # fallback IP or extract from config

        config = {
            "provider": credential.provider.name,
            "authUsername": telephony_number,
            "authPassword": telephony_number,  # Replace if password stored in secure field
            "gateway_ip": gateway_ip,
        }

        vapi = VapiProvider()
        outbound_res = vapi.set_outbound(config)

        if outbound_res.status_code != 200:
            return outbound_res

        # Save the trunk to DB
        sip_refer = outbound_res.data.get("sip_refer")
        trunk = BridgeProviderConfig.objects.create(
            bridge=bridge,
            provider_credential=credential,
            direction=TrunkDirection.OUTBOUND.value,
            trunk_type=TrunkType.VOICE_INFRA.value,
            address=gateway_ip,
            sip_refer=sip_refer,
            numbers={"primary": telephony_number},
            status=TrunkStatus.ACTIVE,
        )

        return Response(
            {"success": True, "trunk_id": trunk.id, "sip_refer": sip_refer}, status=200
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_path="create-inbound-trunk",
    )
    def create_inbound(self, request):
        """
        Creates a Vapi SIP Trunk (inbound) and saves it in the DB.
        """

        bridge_id = request.data.get("bridge_id")
        credential_id = request.data.get("provider_credential_id")

        # provider type is whether we are using vapi or livekit as provider
        provider_type = request.data.get("provider_type")

        if not bridge_id or not credential_id:
            return Response(
                {"error": "bridge_id and provider_credential_id are required."},
                status=400,
            )

        try:
            bridge = VoiceBridge.objects.get(id=bridge_id)
            credential = ProviderCredential.objects.get(id=credential_id)
        except VoiceBridge.DoesNotExist:
            return Response({"error": "VoiceBridge not found."}, status=404)
        except ProviderCredential.DoesNotExist:
            return Response({"error": "ProviderCredential not found."}, status=404)

        # Fetch an associated number
        vb_number = VoiceBridgeNumber.objects.filter(
            bridge=bridge, provider_credential=credential
        ).first()
        if not vb_number or not vb_number.number:
            return Response(
                {
                    "error": "No associated telephony number found for this bridge/credential."
                },
                status=404,
            )

        telephony_number = vb_number.number.number
        inbound_res = None

        if provider_type == "livekit":
            config = {
                "name": "livekit",
                "numbers": telephony_number
                if isinstance(telephony_number, list)
                else [telephony_number],
            }
            livekit = LivekitProvider()
            inbound_res = livekit.set_inbound(config)
            if inbound_res.get("success"):
                vb_number.has_trunks = True
                vb_number.save()
            else:
                vb_number.has_trunks = False
                vb_number.save()

        elif provider_type == "vapi":
            config = {
                "provider": credential.provider.name,
                "number": telephony_number,
            }
            vapi = VapiProvider()
            inbound_res = vapi.set_inbound(config)

            if inbound_res.get("success"):
                vb_number.has_trunks = True
                vb_number.save()
            else:
                vb_number.has_trunks = False
                vb_number.save()

        if inbound_res.status_code != 200:
            return inbound_res

        # Save the inbound trunk
        sip_refer = inbound_res.data.get("sip_refer")

        trunk = BridgeProviderConfig.objects.create(
            bridge=bridge,
            provider_credential=credential,
            direction=TrunkDirection.inbound.value,
            trunk_type=TrunkType.voice_infra.value,
            address="sip.vapi.ai",
            sip_refer=sip_refer,
            numbers={"primary": telephony_number},
            status=TrunkStatus.ACTIVE,
        )

        return Response(
            {"success": True, "trunk_id": trunk.id, "sip_refer": sip_refer}, status=200
        )


@staff_member_required
def update_document_status(request, bridge_id, doc_id, doc_status):
    try:
        contact = Document.objects.get(id=doc_id)
        contact.status = doc_status
        contact.save()

        messages.success(
            request, f"Contact {contact.id} is registered as a user successfully."
        )
    except Document.DoesNotExist:
        messages.error(request, f"Contact with ID {doc_id} does not exist.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
