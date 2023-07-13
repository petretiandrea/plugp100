from dataclasses import dataclass
from typing import TypeVar, Any, List

from plugp100.api.light_effect import LightEffect
from plugp100.requests.handshake_params import HandshakeParams
from plugp100.requests.login_device import LoginDeviceParams
from plugp100.requests.secure_passthrough_params import SecurePassthroughParams
from plugp100.requests.trigger_logs_params import GetTriggerLogsParams

T = TypeVar("T")


class TapoRequest(object):

    @staticmethod
    def handshake(params: HandshakeParams) -> 'TapoRequest':
        return TapoRequest(method="handshake", params=params)

    @staticmethod
    def login(params: LoginDeviceParams) -> 'TapoRequest':
        return TapoRequest(method="login_device", params=params)

    @staticmethod
    def secure_passthrough(params: SecurePassthroughParams) -> 'TapoRequest':
        return TapoRequest(method="securePassthrough", params=params)

    @staticmethod
    def get_device_info() -> 'TapoRequest':
        return TapoRequest(method='get_device_info', params=None)

    @staticmethod
    def get_device_usage() -> 'TapoRequest':
        return TapoRequest(method='get_device_usage', params=None)

    @staticmethod
    def get_energy_usage() -> 'TapoRequest':
        return TapoRequest(method='get_energy_usage', params=None)

    @staticmethod
    def set_device_info(params: dict[str, Any]):
        return TapoRequest(method='set_device_info', params=params)

    @staticmethod
    def get_current_power() -> 'TapoRequest':
        return TapoRequest(method='get_current_power', params=None)

    @staticmethod
    def set_lighting_effect(effect: LightEffect) -> 'TapoRequest':
        return TapoRequest(method='set_lighting_effect', params=effect.as_dict())

    @staticmethod
    def get_child_device_list() -> 'TapoRequest':
        return TapoRequest(method='get_child_device_list', params=None)

    @staticmethod
    def get_child_device_component_list() -> 'TapoRequest':
        return TapoRequest(method='get_child_device_component_list', params=None)

    @staticmethod
    def multiple_request(requests: 'MultipleRequestParams') -> 'TapoRequest':
        return TapoRequest(method='multipleRequest', params=requests)

    @staticmethod
    def control_child(device_id: str, request: 'TapoRequest') -> 'TapoRequest':
        return TapoRequest(method='control_child', params=ControlChildParams(device_id, request))

    @staticmethod
    def get_child_event_logs(trigger_log_params: GetTriggerLogsParams) -> 'TapoRequest':
        return TapoRequest(method='get_trigger_logs', params=trigger_log_params)

    @staticmethod
    def get_temperature_humidity_records() -> 'TapoRequest':
        return TapoRequest(method='get_temp_humidity_records', params=None)

    def __init__(self, method: str, params):
        self.method = method
        self.params = params

    def with_request_time_millis(self, t: float) -> 'TapoRequest':
        self.request_time_milis = t
        return self

    def with_terminal_uuid(self, uuid: str) -> 'TapoRequest':
        self.terminal_uuid = uuid
        return self

    def get_params(self):
        return self.params

    def get_method(self):
        return self.method


# moved here to avoid circular import in python
@dataclass
class ControlChildParams:
    device_id: str
    requestData: 'TapoRequest'


@dataclass
class MultipleRequestParams:
    requests: List[TapoRequest]
