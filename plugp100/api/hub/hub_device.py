import asyncio
import logging
from asyncio import iscoroutinefunction
from logging import Logger
from typing import Callable, Any, Optional, List

from plugp100.api.tapo_client import TapoClient, Json
from plugp100.common.functional.either import Either, Right, Left
from plugp100.requests.tapo_request import TapoRequest
from plugp100.responses.child_device_list import ChildDeviceList
from plugp100.responses.device_state import HubDeviceState

HubSubscription = Callable[[], Any]


# The HubDevice class is a blueprint for creating hub devices.
class HubDevice:

    def __init__(self, api: TapoClient, address: str, logger: Logger = None):
        self._api = api
        self._address = address
        self._is_tracking = False
        self._tracking_task: Optional[asyncio.Task] = None
        self._tracking_subscriptions: List[Callable[[ChildDeviceList], Any]] = []
        self._logger = logger if logger is not None else logging.getLogger("HubDevice")

    async def login(self) -> Either[True, Exception]:
        """
        The function `login` attempts to log in to an API using a given address and returns either `True` if successful or
        an `Exception` if there is an error.
        @return: The login method is returning an Either type, which can either be True or an Exception.
        """
        return await self._api.login(self._address)

    async def get_state(self) -> Either[HubDeviceState, Exception]:
        """
        The function `get_state` asynchronously retrieves device information and returns either the device state or an
        exception.
        @return: an instance of the `Either` class, which can hold either a `HubDeviceState` object or an `Exception`
        object.
        """
        return (await self._api.get_device_info()) | HubDeviceState.try_from_json

    async def get_state_as_json(self) -> Either[Json, Exception]:
        return await self._api.get_device_info()

    async def control_child(self, device_id: str, request: TapoRequest) -> Either[Json, Exception]:
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

    def start_tracking(self, interval_millis: int = 10_000):
        """
        The function `start_tracking` starts a background task that periodically polls for updates.

        @param interval_millis: The `interval_millis` parameter is an optional integer that specifies the time interval in
        milliseconds at which the `_poll` method will be called. The default value is 10,000 milliseconds (or 10 seconds),
        @defaults to 10_000
        @type interval_millis: int (optional)
        """
        if self._tracking_task is None:
            self._is_tracking = True
            self._tracking_task = asyncio.create_task(self._poll(interval_millis))

    def stop_tracking(self):
        """
        The function `stop_tracking` cancels a background task and sets the `is_observing` attribute to False.
        """
        if self._tracking_task:
            self._is_tracking = False
            self._tracking_task.cancel()
            self._tracking_task = None

    def subscribe(self, callback: Callable[[ChildDeviceList], Any]) -> HubSubscription:
        """
        The `subscribe` function adds a callback function to the list of subscriptions and returns an unsubscribe function.

        @param callback: The `callback` parameter is a function that takes a `ChildDeviceList` object as input and returns
        any value
        @type callback: Callable[[ChildDeviceList], Any]
        @return: The function `unsubscribe` is being returned.
        """
        self._tracking_subscriptions.append(callback)

        def unsubscribe():
            self._tracking_subscriptions.remove(callback)

        return unsubscribe

    def _emit(self, data: ChildDeviceList):
        for sub in self._tracking_subscriptions:
            if iscoroutinefunction(sub):
                asyncio.create_task(sub(data))
            else:
                sub(data)

    async def _poll(self, interval_millis: int):
        while self._is_tracking:
            new_state = await self._api.get_child_device_list()
            if isinstance(new_state, Right):
                self._emit(new_state.value)
            elif isinstance(new_state, Left):
                self._logger.error(new_state.error)
            await asyncio.sleep(interval_millis / 1000)  # to seconds
