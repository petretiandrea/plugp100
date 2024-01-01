import dataclasses
from typing import Optional, Any

import aiohttp

from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, connect_from_discovery
from plugp100.new.tapodevice import TapoDevice
from plugp100.protocol.klap_protocol import KlapProtocol
from plugp100.protocol.passthrough_protocol import PassthroughProtocol


@dataclasses.dataclass
class DiscoveredDevice:
    device_type: str
    device_model: str
    ip: str
    mac: str
    mgt_encrypt_schm: "EncryptionScheme"

    device_id: Optional[str] = None
    owner: Optional[str] = None
    hw_ver: Optional[str] = None
    is_support_iot_cloud: Optional[bool] = None
    obd_src: Optional[str] = None
    factory_default: Optional[bool] = None

    @staticmethod
    def from_dict(values: dict[str, Any]) -> "DiscoveredDevice":
        return DiscoveredDevice(
            device_type=values.get("device_type", values.get("device_type_text")),
            device_model=values.get("device_model", values.get("model")),
            ip=values.get("ip", values.get("alias")),
            mac=values.get("mac"),
            device_id=values.get("device_id", values.get("device_id_hash", None)),
            owner=values.get("owner", values.get("device_owner_hash", None)),
            hw_ver=values.get("hw_ver", None),
            is_support_iot_cloud=values.get("is_support_iot_cloud", None),
            obd_src=values.get("obd_src", None),
            factory_default=values.get("factory_default", None),
            mgt_encrypt_schm=EncryptionScheme(**values.get("mgt_encrypt_schm")),
        )

    async def get_tapo_device(
        self, credentials: AuthCredential, session: aiohttp.ClientSession
    ) -> TapoDevice:
        encryption_type = self.mgt_encrypt_schm.encrypt_type
        if encryption_type is not None and encryption_type.lower() == "klap":
            protocol_type = KlapProtocol
        elif encryption_type is not None and encryption_type.lower() == "aes":
            protocol_type = PassthroughProtocol
        else:
            raise Exception(f"Unsupported encryption type for {self}")
        return await connect_from_discovery(
            host=self.ip,
            port=self.mgt_encrypt_schm.http_port,
            device_type=self.device_type,
            device_model=self.device_model,
            session=session,
            credentials=credentials,
            protocol_type=protocol_type,
        )


@dataclasses.dataclass
class EncryptionScheme:
    """Base model for encryption scheme of discovery result."""

    is_support_https: Optional[bool] = None
    encrypt_type: Optional[str] = None
    http_port: Optional[int] = None
    lv: Optional[int] = 1
