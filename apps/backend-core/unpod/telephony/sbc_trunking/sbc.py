from django.conf import settings
from django.utils.functional import SimpleLazyObject
from unpod.telephony.models import BridgeProviderConfig
from unpod.subscription.models import ActiveSubscription
import logging
import urllib3
from unpod.common.utils import get_global_configs
from rest_framework.response import Response
from rest_framework import status
from unpod.common.utils import api_request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_sip_config_cache = SimpleLazyObject(lambda: get_global_configs("unpod_sip_config"))


class SBC:
    def __init__(self):
        self.bridge = None
        self.configs = None
        self.creds = None
        self.credentials = None
        self.provider_list = []
        self.bpc = []
        self.routing_record = None
        self.interconnections = None
        self.creds = _sip_config_cache
        self.inbound_record = None
        self.default_name = None
        self.char_limit = 32
        self.test_mode = getattr(settings, 'TELEPHONY_TEST_MODE', False)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        self.logging = logging.getLogger("SBC")

        if self.test_mode:
            self.logging.info("SBC initialized in TEST MODE - external API calls will be bypassed")

    def get_routing_record(self):
        if self.test_mode:
            self.logging.info("[TEST MODE] Skipping routing record retrieval")
            self.routing_record = []
            self.inbound_record = []
            return

        self.logging.info("Retrieving routing record")
        res = api_request(
            f"{settings.LIBRESBC_URL}routing/table/{self.creds.get('routing_table')}",
            verify=False,
            request_type="get",
        )
        self.routing_record = res.get("records", [])
        res = api_request(
            f"{settings.LIBRESBC_URL}routing/table/{self.creds.get('inbound_routing')}",
            verify=False,
            request_type="get",
        )
        self.inbound_record = res.get("records", [])

    def routing_record_exist(self, number, record=None):
        if not self.routing_record and not self.inbound_record:
            self.get_routing_record()

        if record == "inbound":
            for i in self.inbound_record:
                if i.get("value") == number:
                    return True
        else:
            for i in self.routing_record:
                if i.get("value") == number:
                    return True

        return False

    def capacity_exist(self, token):
        data = api_request(
            f"{settings.LIBRESBC_URL}class/capacity/{token}",
            verify=False,
            request_type="get",
        )
        return True if data and data.get("name") else False

    def interconnect_exist(self, provider, direction):
        name = f"{self.bridge.slug}_{provider}"[: self.char_limit]
        data = api_request(
            f"{settings.LIBRESBC_URL}interconnection/{direction}/{name}",
            verify=False,
            request_type="get",
        )
        return True if data and data.get("name") else False

    def gateway_exist(self, provider):
        name = f"{self.bridge.slug}_{provider}"[: self.char_limit]
        data = api_request(
            f"{settings.LIBRESBC_URL}base/gateway/{name}",
            verify=False,
            request_type="get",
        )
        return True if data and data.get("name") else False

    def create_gateway(self):
        # self.bpc = BridgeProviderConfig.objects.filter(bridge=self.bridge.id)
        #
        # for i in self.bpc:
        provider = self.credentials.provider.name.lower()
        if provider == "livekit":
            if not self.credentials.sip_url:
                return Response(
                    {
                        "success": False,
                        "message": "pls provide sip url in credentials",
                    },
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )
            url = self.credentials.sip_url.replace("sip:", "")
            self.configs["gateway_ip"] = self.configs.get("address", "")
            domain = self.creds.get("up_sip_url", "")

        elif provider == "vapi":
            bpc = BridgeProviderConfig.objects.filter(
                provider_credential=self.credentials
            ).first()
            if bpc:
                url = f"{bpc.sip_credentials_id}.sip.vapi.ai"
            else:
                url = f"sip.vapi.ai"
            self.configs["gateway_ip"] = self.configs.get("address", "")
            domain = self.creds.get("up_sip_ip", "")
        else:
            return

        self.provider_list.append(
            self.credentials.name
        ) if self.credentials.name not in self.provider_list else None

        self.default_name = f"{self.bridge.slug}_{self.credentials.name}"[
            : self.char_limit
        ]
        payload = {
            "name": self.default_name,
            "desc": f"Gateway to Unpod {self.bridge.slug}_{self.credentials.name}",
            "username": self.configs.get("username", self.creds.get("id")),
            "realm": url,
            "from_user": self.configs.get("username", self.creds.get("id")),
            "from_domain": self.configs.get("gateway_ip", domain).replace(" ", ""),
            "password": self.configs.get("password", self.creds.get("secret")),
            "proxy": url,
            "port": 5060,
            "transport": "tcp",
            "do_register": False,
            "register_proxy": url,
            "register_transport": "tcp",
            "expire_seconds": 60,
            "retry_seconds": 30,
            "caller_id_in_from": True,
            "cid_type": "none",
            "contact_params": url,
            "extension_in_contact": True,
            "ping": 40,
            "ping_max": 1,
            "ping_min": 1,
        }

        # print(payload)
        try:
            if self.gateway_exist(self.credentials.name):
                self.logging.info(f"gateway already exists updating it")
                res = api_request(
                    f"{settings.LIBRESBC_URL}base/gateway/{self.default_name}",
                    payload=payload,
                    verify=False,
                    request_type="put",
                )

                self.logging.info(f"updating gateway response {res}")

            else:
                self.logging.info(f"creating gateway")
                res = api_request(
                    f"{settings.LIBRESBC_URL}base/gateway",
                    payload=payload,
                    verify=False,
                    request_type="post",
                )
                self.logging.info(f"creating gateway response {res}")

        except Exception as e:
            self.logging.error(e)

    def create_outbound_interconnect(self):
        self.default_name = f"{self.bridge.slug}_{self.credentials.name}"[
            : self.char_limit
        ]
        sub = (
            ActiveSubscription.objects.filter(
                organization=self.bridge.organization, is_active=True, expired=False
            )
            .order_by("-valid_from")
            .first()
        )

        if sub:
            metadata = sub.subscription_metadata
            channels = (
                metadata.get("modules", {}).get("Channels", {}).get("quantity", 1)
            )
        else:
            subscription_data = {}
            channels = 1
        capacity_name = f"{self.bridge.organization.name}_{self.bridge.organization.token}".replace(
            " ", "_"
        )[: self.char_limit]

        try:
            channels = int(channels) if channels is not None else 1
        except Exception as e:
            channels = 1

        payload = {
            "name": capacity_name,
            "desc": f"{self.bridge.organization.token} capacity class",
            "cps": 2,
            "concurentcalls": channels,
        }

        try:
            if self.capacity_exist(capacity_name):
                self.logging.info(f"capacity already exists updating it")
                res = api_request(
                    f"{settings.LIBRESBC_URL}class/capacity/{capacity_name}",
                    payload=payload,
                    verify=False,
                    request_type="put",
                )
                self.logging.info(f"capacity already exist update res {res}")

            else:
                self.logging.info(f"creating capacity class")
                res = api_request(
                    f"{settings.LIBRESBC_URL}class/capacity",
                    payload=payload,
                    verify=False,
                    request_type="post",
                )
                self.logging.info(f"creating capacity class response {res}")

        except Exception as e:
            self.logging.error(e)

        if self.credentials.provider.name.lower() == "vapi":
            ips = self.creds.get("vapi_sip_addrs")
        elif self.credentials.provider.name.lower() == "livekit":
            ips = self.creds.get("livekit_sip_addrs")
        payload = {
            "name": self.default_name,
            "desc": f"{self.bridge.slug} outbound",
            "sipprofile": "public",
            "distribution": "weight_based",
            "sipaddrs": ips,
            "rtpaddrs": ips,
            "media_class": "default",
            "capacity_class": capacity_name,
            "translation_classes": [],
            "manipulation_classes": [],
            "privacy": ["none"],
            "cid_type": "none",
            "nofailover_sip_codes": [],
            "nodes": ["_ALL_"],
            "enable": True,
            "gateways": [{"name": self.default_name, "weight": 1}],
        }
        try:
            if self.interconnect_exist(self.credentials.name, "outbound"):
                self.logging.info(
                    f"interconnect already exist updating it {self.bridge.slug}_{self.credentials.name}"
                )
                res = api_request(
                    f"{settings.LIBRESBC_URL}interconnection/outbound/{self.default_name}",
                    payload=payload,
                    verify=False,
                    request_type="put",
                )
                self.logging.info(f"interconnect already exist update response {res}")

            else:
                self.logging.info(f"creating interconnect ")
                res = api_request(
                    f"{settings.LIBRESBC_URL}interconnection/outbound",
                    payload=payload,
                    request_type="post",
                    verify=False,
                )
                self.logging.info(f"creating interconnect{res}")

        except Exception as e:
            self.logging.error(e)

    def create_inbound_interconnect(self):
        self.default_name = f"{self.bridge.slug}_{self.credentials.name}"[
            : self.char_limit
        ]
        try:
            payload = {
                "name": self.default_name,
                "desc": f"{self.bridge.slug}_{self.credentials.name} inbound interconnect",
                "sipprofile": "public",
                "routing": "routing_to_telecom",
                "sipaddrs": ["159.65.144.179/32"],
                "rtpaddrs": ["159.65.144.179/32"],
                "ringready": False,
                "media_class": "default",
                "capacity_class": f"{self.bridge.organization.name}_{self.bridge.organization.token}".replace(
                    " ", "_"
                )[
                    : self.char_limit
                ],
                "translation_classes": [],
                "manipulation_classes": [],
                "authscheme": "IP",
                "nodes": ["_ALL_"],
                "enable": True,
            }

            if self.interconnect_exist(self.credentials.name, "inbound"):
                self.logging.info(f"interconnect already exist updating it")
                res = api_request(
                    f"{settings.LIBRESBC_URL}interconnection/inbound",
                    payload=payload,
                    request_type="put",
                    verify=False,
                )
                self.logging.info(f"interconnect already exist update response: {res}")
            else:
                self.logging.info(f"creating interconnect")
                res = api_request(
                    f"{settings.LIBRESBC_URL}interconnection/inbound",
                    payload=payload,
                    request_type="post",
                    verify=False,
                )
                self.logging.log(f"interconnection inbound: {res}")

        except Exception as e:
            self.logging.error(e)

    def create_outbound_routing(self):
        vbns = self.configs.get("numbers", [])

        for i in vbns:
            try:
                payload = {
                    "table": self.creds.get("routing_table"),
                    "match": "em",
                    "value": i,
                    "action": "route",
                    "routes": {
                        "primary": self.default_name,
                        "secondary": self.default_name,
                        "load": 50,
                    },
                }

                if self.routing_record_exist(i):
                    self.logging.info(
                        f"outbound routing record already exist updating it {i}"
                    )
                    res = api_request(
                        f"{settings.LIBRESBC_URL}routing/record",
                        payload=payload,
                        request_type="put",
                        verify=False,
                    )
                    self.logging.info(f"outbound routing record update response {res}")

                else:
                    self.logging.info(
                        f"creating routing record {i} on {self.bridge.slug}_{self.credentials.name}"
                    )
                    res = api_request(
                        f"{settings.LIBRESBC_URL}routing/record",
                        payload=payload,
                        request_type="post",
                        verify=False,
                    )
                    self.logging.info(f"create routing record response {res}")

            except Exception as e:
                self.logging.error(e)

    def create_inbound_routing(self):
        vbns = self.configs.get("numbers", [])

        for i in vbns:
            payload = {
                "table": self.creds.get("inbound_routing"),
                "match": "em",
                "value": i,
                "action": "route",
                "routes": {
                    "primary": f"uptv_outbound",
                    "secondary": f"uptv_outbound",
                    "load": 50,
                },
            }

            if self.routing_record_exist(i, "inbound"):
                self.logging.info(
                    f"inbound routing record already exist updating it {i}"
                )
                res = api_request(
                    f"{settings.LIBRESBC_URL}routing/record",
                    payload=payload,
                    request_type="put",
                    verify=False,
                )
                self.logging.info(f"inbound routing record updated response {res}")
            else:
                self.logging.info(
                    f"creating inbound routing record {i} on {self.bridge.slug}_{self.credentials.name}"
                )
                res = api_request(
                    f"{settings.LIBRESBC_URL}routing/record",
                    payload=payload,
                    request_type="post",
                    verify=False,
                )
                self.logging.info(f"inbound routing record response {res}")
                return res

    def create_configs(self, config, bridge, credential):
        if self.test_mode:
            self.logging.info(f"[TEST MODE] Skipping SBC create_configs for bridge {bridge.id}")
            return {
                "capacity_name": f"{bridge.hub.name}_{bridge.hub.token}"[:32],
                "gateway_name": f"{bridge.slug}_{credential.provider.name}"[:32],
                "provider": credential.provider.name,
                "credentials": {},
                "test_mode": True
            }

        self.bridge = bridge
        self.configs = config
        self.credentials = credential
        self.create_gateway()
        self.create_outbound_interconnect()
        self.create_outbound_routing()
        res = self.create_inbound_routing()
        try:
            if res.get("passed", None):
                return {
                    "capacity_name": f"{self.bridge.organization.name}_{self.bridge.organization.token}"[
                        : self.char_limit
                    ],
                    "gateway_name": self.default_name,
                    "provider": self.credentials.provider.name,
                    "credentials": self.creds,
                }
            else:
                return {}
        except Exception as e:
            return {}

    def delete_sbc(self, number, bridge, credential):
        if self.test_mode:
            self.logging.info(f"[TEST MODE] Skipping SBC delete_sbc for number {number}")
            return

        self.bridge = bridge
        self.credentials = credential

        if not self.credentials:
            return

        self.default_name = f"{self.bridge.slug}_{self.credentials.name}"[
            : self.char_limit
        ]
        try:
            self.logging.info(f"deleting sbc {self.bridge.slug}")
            self.get_routing_record()
            self.logging.info(f"deleting routing record")
            routes = []

            for i in self.routing_record:
                routes.append(i.get("routes", {}).get("primary"))

                if int(i.get("value")) == int(number):
                    routes.remove(i.get("routes", {}).get("primary", None))
                    self.logging.info(f"deleting routing record {i}")
                    res = api_request(
                        f"{settings.LIBRESBC_URL}routing/record/{self.creds.get('routing_table','routing_livekit')}/{i.get('match')}/{number}",
                        request_type="delete",
                        verify=False,
                    )
                    self.logging.info(f"deleting routing record response {res}")

            for i in self.inbound_record:
                routes.append(i.get("routes", {}).get("primary"))
                if int(i.get("value")) == int(number):
                    routes.remove(i.get("routes", {}).get("primary", None))

                    self.logging.info(f"deleting routing record {i}")
                    res = api_request(
                        f"{settings.LIBRESBC_URL}routing/record/{self.creds.get('inbound_routing', 'routing_to_telecom')}/{i.get('match')}/{number}",
                        request_type="delete",
                        verify=False,
                    )
                    self.logging.info(f"deleting inbound routing record response {res}")

            if f"{self.default_name}" not in routes:
                self.logging.info(
                    f"deleting interconnect {self.bridge.slug}_{self.credentials.name}"
                )
                res = api_request(
                    f"{settings.LIBRESBC_URL}interconnection/outbound/{self.default_name}",
                    request_type="delete",
                    verify=False,
                )
                self.logging.info(f"deleting interconnect {res}")

                self.logging.info("deleting gateway")
                res = api_request(
                    f"{settings.LIBRESBC_URL}base/gateway/{self.default_name}",
                    request_type="delete",
                    verify=False,
                )
                self.logging.info(f"gateway delete api response {res}")

                res = api_request(
                    f"{settings.LIBRESBC_URL}class/capacity/"
                    + f"{self.bridge.organization.name}_{self.bridge.organization.token}".replace(
                        " ", "_"
                    )[: self.char_limit],
                    request_type="delete",
                    verify=False,
                )
                self.logging.info(f"capacity delete api response {res}")

        except Exception as e:
            self.logging.error(e)

    def delete_configs(self, number, bridge, credentials):
        if self.test_mode:
            self.logging.info(f"[TEST MODE] Skipping SBC delete_configs for number {number}")
            return

        self.logging.info(f"deleting configs start")
        self.delete_sbc(number, bridge, credentials)
