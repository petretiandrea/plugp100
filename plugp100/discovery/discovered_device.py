import dataclasses
from typing import Optional, Any


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


@dataclasses.dataclass
class EncryptionScheme:
    """Base model for encryption scheme of discovery result."""

    is_support_https: Optional[bool] = None
    encrypt_type: Optional[str] = None
    http_port: Optional[int] = None
    lv: Optional[int] = 1
