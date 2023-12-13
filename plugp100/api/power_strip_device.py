from plugp100.api.base_tapo_device import _BaseTapoDevice
from plugp100.api.tapo_client import TapoClient, Json
from plugp100.common.functional.tri import Try
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.child_device_list import PowerStripChild
from plugp100.responses.components import Components
from plugp100.responses.device_state import PlugDeviceState


class PowerStripDevice(_BaseTapoDevice):
    def __init__(self, api: TapoClient):
        super().__init__(api)

    async def get_state(self) -> Try[PlugDeviceState]:
        """
        The function `get_state` asynchronously retrieves device information and returns either the device state or an
        exception.
        @return: an instance of the `Either` class, which can hold either a `PlugDeviceState` object or an `Exception`
        object.
        """
        return (await self._api.get_device_info()).flat_map(PlugDeviceState.try_from_json)

    async def get_children(self) -> Try[dict[str, PowerStripChild]]:
        return (
            (await self._api.get_child_device_list())
            .map(
                lambda sub: sub.get_children(lambda x: PowerStripChild.try_from_json(**x))
            )
            .map(lambda x: {child.device_id: child for child in x})
        )

    async def on(self, child_device_id: str) -> Try[bool]:
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=True))
        )
        return (await self._control_child(child_device_id, request)).map(lambda _: True)

    async def off(self, child_device_id: str) -> Try[bool]:
        request = TapoRequest.set_device_info(
            dataclass_encode_json(SetPlugInfoParams(device_on=False))
        )
        return (await self._control_child(child_device_id, request)).map(lambda _: True)

    async def _control_child(self, device_id: str, request: TapoRequest) -> Try[Json]:
        return await self._api.control_child(device_id, request)

    async def get_component_negotiation_child(self, child_device_id) -> Try[Components]:
        return (
            await self._control_child(
                child_device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)
