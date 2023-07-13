import asyncio
import logging
from logging import Logger
from typing import TypeVar, Generic, Optional, List

State = TypeVar("State")
StateChange = TypeVar("StateChange")


class StateTracker(Generic[State, StateChange]):

    def __init__(self, logger: Logger = None):
        self._last_state: Optional[State] = None
        self._change_queue = asyncio.Queue()
        self._logger = logger if logger is not None else logging.getLogger("StateTracker")

    def _compute_state_changes(self, new_state: State, last_state: Optional[State]) -> List[StateChange]:
        pass

    async def get_next_state_change(self) -> StateChange:
        return await self._change_queue.get()

    async def notify_state_update(self, new_state: State):
        changes = self._compute_state_changes(new_state, self._last_state)
        self._last_state = new_state
        if len(changes) > 0:
            self._logger.info(f"Detected {len(changes)} changes")
            for change in changes:
                await self._change_queue.put(change)
        else:
            self._logger.info("No changes detected")
