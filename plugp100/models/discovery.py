import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class EncryptionSchema:
    is_support_https: Optional[bool] = None
    encrypt_type: Optional[str] = None
    http_port: Optional[int] = None
    lv: Optional[int] = 1


@dataclasses.dataclass
class DiscoveredDevice:
    device_type: str
    device_model: str
    ip: str
    mac: str
    mgt_encrypt_schm: Optional[EncryptionSchema]

    device_id: Optional[str] = None
    owner: Optional[str] = None
    hw_ver: Optional[str] = None
    is_support_iot_cloud: Optional[bool] = None
    obd_src: Optional[str] = None
    factory_default: Optional[bool] = None

    @staticmethod
    def from_dict(values: dict[str, Any]) -> "DiscoveredDevice":
        if enc_schema_info := values.get("mgt_encrypt_schm", None):
            encryption_schema = EncryptionSchema(**enc_schema_info)
        else:
            encryption_schema = None
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
            mgt_encrypt_schm=encryption_schema,
        )

    @property
    def as_dict(self) -> dict[str, Any]:
        return {
            "device_type": self.device_type,
            "device_model": self.device_model,
            "ip": self.ip,
            "mac": self.mac,
            "device_id": self.device_id,
            "owner": self.owner,
            "hw_ver": self.hw_ver,
            "is_support_iot_cloud": self.is_support_iot_cloud,
            "factory_default": self.factory_default,
            "mgt_encrypt_schm": {
                "is_support_https": self.mgt_encrypt_schm.is_support_https,
                "encrypt_type": self.mgt_encrypt_schm.encrypt_type,
                "http_port": self.mgt_encrypt_schm.http_port,
                "lv": self.mgt_encrypt_schm.lv,
            }
            if self.mgt_encrypt_schm is not None
            else None,
        }


__all__ = ["DiscoveredDevice", "EncryptionSchema"]
