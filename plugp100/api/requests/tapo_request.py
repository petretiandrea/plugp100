from dataclasses import dataclass
from typing import TypeVar, Any, List

from plugp100.api.light_effect import LightEffect
from plugp100.common.credentials import AuthCredential
from plugp100.api.requests.handshake_params import HandshakeParams
from plugp100.api.requests.login_device import LoginDeviceParams, LoginDeviceParamsV2, LoginDeviceParamsH200
from plugp100.api.requests.secure_passthrough_params import SecurePassthroughParams
from plugp100.api.requests.trigger_logs_params import GetTriggerLogsParams

T = TypeVar("T")


class TapoRequest(object):
    @staticmethod
    def handshake(params: HandshakeParams) -> "TapoRequest":
        return TapoRequest(method="handshake", params=params)

    @staticmethod
    def login(credential: AuthCredential, v2: bool = False) -> "TapoRequest":
        return TapoRequest(
            method="login_device",
            params=LoginDeviceParams(credential.username, credential.password)
            if not v2
            else LoginDeviceParamsV2(credential.username, credential.password),
        )

    @staticmethod
    def secure_passthrough(params: SecurePassthroughParams) -> "TapoRequest":
        return TapoRequest(method="securePassthrough", params=params)

    @staticmethod
    def get_device_info() -> "TapoRequest":
        return TapoRequest(method="get_device_info", params=None)

    @staticmethod
    def get_device_usage() -> "TapoRequest":
        return TapoRequest(method="get_device_usage", params=None)

    @staticmethod
    def get_energy_usage() -> "TapoRequest":
        return TapoRequest(method="get_energy_usage", params=None)

    @staticmethod
    def set_device_info(params: dict[str, Any]):
        return TapoRequest(method="set_device_info", params=params)

    @staticmethod
    def get_current_power() -> "TapoRequest":
        return TapoRequest(method="get_current_power", params=None)

    @staticmethod
    def set_lighting_effect(effect: LightEffect) -> "TapoRequest":
        return TapoRequest(method="set_lighting_effect", params=effect.as_dict())

    @staticmethod
    def get_child_device_list(start_index: int = 0) -> "TapoRequest":
        return TapoRequest(
            method="get_child_device_list", params=PaginationParams(start_index)
        )

    @staticmethod
    def get_child_device_component_list(start_index: int = 0) -> "TapoRequest":
        return TapoRequest(method="get_child_device_component_list", params=None)

    @staticmethod
    def multiple_request(requests: "MultipleRequestParams") -> "TapoRequest":
        return TapoRequest(method="multipleRequest", params=requests)

    @staticmethod
    def control_child(device_id: str, request: "TapoRequest") -> "TapoRequest":
        return TapoRequest(
            method="control_child", params=ControlChildParams(device_id, request)
        )

    @staticmethod
    def get_child_event_logs(trigger_log_params: GetTriggerLogsParams) -> "TapoRequest":
        return TapoRequest(method="get_trigger_logs", params=trigger_log_params)

    @staticmethod
    def get_temperature_humidity_records() -> "TapoRequest":
        return TapoRequest(method="get_temp_humidity_records", params=None)

    @staticmethod
    def get_latest_firmware() -> "TapoRequest":
        return TapoRequest(method="get_latest_fw", params=None)

    @staticmethod
    def get_firmware_download_state() -> "TapoRequest":
        return TapoRequest(method="get_fw_download_state", params=None)

    @staticmethod
    def start_firmware_upgrade() -> "TapoRequest":
        return TapoRequest(method="fw_download", params=None)

    @staticmethod
    def component_negotiation() -> "TapoRequest":
        return TapoRequest(method="component_nego", params=None)

    def __init__(self, method: str, params):
        self.method = method
        self.params = params

    def with_request_id(self, request_id: int) -> "TapoRequest":
        self.requestID = request_id
        return self

    def with_request_time_millis(self, t: float) -> "TapoRequest":
        self.request_time_milis = t
        return self

    def with_terminal_uuid(self, uuid: str) -> "TapoRequest":
        self.terminal_uuid = uuid
        return self

    def get_params(self):
        return self.params

    def get_method(self):
        return self.method

    def __eq__(self, other) -> bool:
        if not isinstance(other, TapoRequest):
            return False

        return self.method == other.method and self.params == other.params


class TapoRequestH200(TapoRequest):
    @staticmethod
    def login(cnonce=None, password=None, hashed=None, digest_passwd=None) -> "TapoRequest":
        return TapoRequest(
            method="login",
            params=LoginDeviceParamsH200(cnonce, password, hashed, digest_passwd)
        )

    @staticmethod
    def get_device_info() -> "TapoRequest":
        return TapoRequest(method="getDeviceInfo", params={"device_info": {"name": ["basic_info"]}})

    @staticmethod
    def get_child_device_list(start_index: int = 0) -> "TapoRequest":
        return TapoRequest(
            method="getChildDeviceList", params={"childControl": PaginationParams(start_index)}
        )

    @staticmethod
    def get_child_device_component_list(start_index: int = 0) -> "TapoRequest":
        return TapoRequest(method="getChildDeviceComponentList", params={"childControl": PaginationParams(start_index)})

    @staticmethod
    def control_child(device_id: str, request: "TapoRequest") -> "TapoRequest":
        return TapoRequest(
            method="controlChild", params={'childControl': ControlChildParamsH200(device_id, request) }
        )

    @staticmethod
    def get_latest_firmware() -> "TapoRequest":
        raise Exception("Not yet supported")

    @staticmethod
    def get_firmware_download_state() -> "TapoRequest":
        raise Exception("Not yet supported")

    @staticmethod
    def start_firmware_upgrade() -> "TapoRequest":
        raise Exception("Not yet supported")

# moved here to avoid circular import in python
@dataclass
class ControlChildParams:
    device_id: str
    requestData: "TapoRequest"

@dataclass
class ControlChildParamsH200:
    device_id: str
    request_data: "TapoRequest"

@dataclass
class MultipleRequestParams:
    requests: List[TapoRequest]


@dataclass
class PaginationParams:
    start_index: int
