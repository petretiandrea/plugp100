import logging
from logging import Logger
from typing import Callable, Any, Set

from plugp100.api.base_tapo_device import _BaseTapoDevice
from plugp100.api.hub.hub_device_tracker import (
    HubConnectedDeviceTracker,
    HubDeviceEvent,
)
from plugp100.api.tapo_client import TapoClient, Json
from plugp100.common.functional.tri import Try
from plugp100.common.poll_tracker import PollTracker, PollSubscription
from plugp100.common.utils.json_utils import dataclass_encode_json
from plugp100.requests.set_device_info.play_alarm_params import PlayAlarmParams
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.alarm_type_list import AlarmTypeList
from plugp100.responses.child_device_list import ChildDeviceList
from plugp100.responses.components import Components
from plugp100.responses.device_state import HubDeviceState

HubSubscription = Callable[[], Any]


# The HubDevice class is a blueprint for creating hub devices.
class HubDevice(_BaseTapoDevice):
    def __init__(
        self,
        api: TapoClient,
        subscription_polling_interval_millis: int = 5000,
        logger: Logger = None,
    ):
        super().__init__(api)
        self._logger = logger if logger is not None else logging.getLogger("HubDevice")
        self._tracker = HubConnectedDeviceTracker(self._logger)
        self._poll_tracker = PollTracker(
            state_provider=self._poll_device_list,
            state_tracker=self._tracker,
            interval_millis=subscription_polling_interval_millis,
            logger=self._logger,
        )

    async def turn_alarm_on(self, alarm: PlayAlarmParams = None) -> Try[bool]:
        request = TapoRequest(
            method="play_alarm",
            params=dataclass_encode_json(alarm) if alarm is not None else None,
        )
        return (await self._api.execute_raw_request(request)).map(lambda _: True)

    async def turn_alarm_off(self) -> Try[bool]:
        return (
            await self._api.execute_raw_request(
                TapoRequest(method="stop_alarm", params=None)
            )
        ).map(lambda _: True)

    async def get_state(self) -> Try[HubDeviceState]:
        """
        The function `get_state` asynchronously retrieves device information and returns either the device state or an
        exception.
        @return: an instance of the `Either` class, which can hold either a `HubDeviceState` object or an `Exception`
        object.
        """
        return (await self._api.get_device_info()).flat_map(HubDeviceState.try_from_json)

    async def get_supported_alarm_tones(self) -> Try[AlarmTypeList]:
        return (
            await self._api.execute_raw_request(
                TapoRequest(method="get_support_alarm_type_list", params=None)
            )
        ).flat_map(AlarmTypeList.try_from_json)

    async def get_state_as_json(self) -> Try[Json]:
        return await self._api.get_device_info()

    async def get_children(self) -> Try[ChildDeviceList]:
        return await self._api.get_child_device_list(all_pages=True)

    async def control_child(self, device_id: str, request: TapoRequest) -> Try[Json]:
        """
        The function `control_child` is an asynchronous method that takes a device ID and a TapoRequest object as
        parameters, and it returns either a JSON response or an Exception.

        @param device_id: A string representing the ID of the device that needs to be controlled
        @type device_id: str
        @param request: The `request` parameter is an instance of the `TapoRequest` class. It is used to specify the details
        of the control operation to be performed on a child device
        @type request: TapoRequest
        @return: an `Either` object, which can contain either a `Json` object or an `Exception`.
        """
        return await self._api.control_child(device_id, request)

    def subscribe_device_association(
        self, callback: Callable[[HubDeviceEvent], Any]
    ) -> PollSubscription:
        return self._poll_tracker.subscribe(callback)

    async def _poll_device_list(self, last_state: Set[str]) -> Set[str]:
        return (
            (await self._api.get_child_device_list())
            .map(lambda x: x.get_device_ids())
            .get_or_else(set())
        )

    async def get_component_negotiation_child(self, child_device_id) -> Try[Components]:
        return (
            await self._api.control_child(
                child_device_id, TapoRequest.component_negotiation()
            )
        ).map(Components.try_from_json)
