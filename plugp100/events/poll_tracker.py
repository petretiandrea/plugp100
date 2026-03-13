import asyncio
from asyncio import iscoroutinefunction
from logging import Logger
from typing import Any, Callable, Generic, List, Optional, TypeVar

from plugp100.events.state_tracker import StateTracker

State = TypeVar("State")
StateChange = TypeVar("StateChange")
StateProvider = Callable[[Optional[State]], State | None]

PollSubscription = Callable[[], Any]


class PollTracker(Generic[State, StateChange]):
    def __init__(
        self,
        state_provider: StateProvider,
        state_tracker: StateTracker[State, StateChange],
        interval_millis: int = 10_000,
        logger: Logger = None,
    ):
        self._is_tracking = False
        self._tracking_tasks: List[asyncio.Task] = []
        self._tracking_subscriptions: List[Callable[[StateChange], Any]] = []
        self._state_provider = state_provider
        self._interval_millis = interval_millis
        self._state_tracker = state_tracker
        self._logger = logger

    def subscribe(self, callback: Callable[[StateChange], Any]) -> PollSubscription:
        self._tracking_subscriptions.append(callback)
        if len(self._tracking_subscriptions) == 1:
            self._start_tracking()

        def unsubscribe():
            self._tracking_subscriptions.remove(callback)
            if len(self._tracking_subscriptions) == 0:
                self._stop_tracking()

        return unsubscribe

    def _start_tracking(self):
        if not self._is_tracking:
            self._is_tracking = True
            self._tracking_tasks = [
                asyncio.create_task(self._poll(self._interval_millis)),
                asyncio.create_task(self._poll_tracker()),
            ]

    def _stop_tracking(self):
        if self._is_tracking:
            self._is_tracking = False
            for task in self._tracking_tasks:
                task.cancel()
            self._tracking_tasks = []

    def _emit(self, state_change: StateChange):
        for sub in self._tracking_subscriptions:
            if iscoroutinefunction(sub):
                asyncio.create_task(sub(state_change))
            else:
                sub(state_change)

    async def _poll(self, interval_millis: int):
        while self._is_tracking:
            last_state = self._state_tracker.get_last_state()
            new_state = (
                await self._state_provider(last_state)
                if iscoroutinefunction(self._state_provider)
                else self._state_provider(last_state)
            )
            if new_state is not None:
                await self._state_tracker.notify_state_update(new_state)
            elif self._logger is not None:
                self._logger.warning("New state provided is None")
            await asyncio.sleep(interval_millis / 1000)

    async def _poll_tracker(self):
        while self._is_tracking:
            state_change = await self._state_tracker.get_next_state_change()
            self._emit(state_change)
