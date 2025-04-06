import dataclasses
from typing import Any, TypeVar, Generic

from plugp100.api.requests.tapo_request import TapoRequest
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.new.components.device_component import DeviceComponent


class Countdown(DeviceComponent):

    def __init__(self, client: TapoClient):
        self._client = client
        self._rules: TapoRuleList[RuleTimer] = TapoRuleList(enable=True, countdown_rule_max_count=1, rule_list=[])

    async def update(self, current_state: dict[str, Any] | None = None):
        request = TapoRequest(method="get_countdown_rules", params={"start_index": 0})
        self._rules = (await self._client.execute_raw_request(request)) \
            .map(lambda x: TapoRuleList.from_json(x, RuleTimer)) \
            .get_or_else(self._rules)

    def get_countdown_rules(self) -> "TapoRuleList[RuleTimer]":
        return self._rules

    async def add_countdown_on(self, timer_seconds: int) -> Try[bool]:
        return await self._add_countdown_rule(timer_seconds, {
            'on': True
        })

    async def add_countdown_off(self, timer_seconds: int) -> Try[bool]:
        return await self._add_countdown_rule(timer_seconds, {
            'on': False
        })

    async def _add_countdown_rule(self, timer_seconds: int, desired_state: dict[str, Any]) -> Try[bool]:
        request = TapoRequest(method="add_countdown_rule", params={
            "delay": timer_seconds,
            "desired_states": desired_state,
            "enable": True,
        })
        return (await self._client.execute_raw_request(request)) \
            .map(lambda _: True)


T = TypeVar("T")


@dataclasses.dataclass
class TapoRuleList(Generic[T]):
    enable: bool
    countdown_rule_max_count: int
    rule_list: [T]

    @staticmethod
    def from_json(data: dict[str, Any], constructor: T) -> "TapoRuleList[T]":
        return TapoRuleList(
            enable=data.get("enable", False),
            countdown_rule_max_count=data.get("countdown_rule_max_count", 1),
            rule_list=list(map(
                lambda x: constructor(**x),
                data.get('rule_list', [])
            ))
        )


@dataclasses.dataclass
class RuleTimer:
    enable: bool
    id: str
    delay: int
    remain: int
    desired_states: dict[str, Any]
