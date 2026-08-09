import abc
from typing import Any


class DeviceComponent(abc.ABC):
    @abc.abstractmethod
    async def update(self, current_state: dict[str, Any] | None = None):
        pass
