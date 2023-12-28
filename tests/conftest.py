import json
from pathlib import Path
from typing import Any, cast

import aiohttp
import pytest

from plugp100.api.tapo_client import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.common.functional.tri import Try
from plugp100.new.device_factory import _get_device_class_from_info
from plugp100.new.tapodevice import TapoDevice
from plugp100.protocol.tapo_protocol import TapoProtocol
from plugp100.requests.tapo_request import (
    TapoRequest,
    ControlChildParams,
    MultipleRequestParams,
)
from plugp100.responses.tapo_response import TapoResponse

plug = pytest.mark.parametrize("device", ["p100.json", "p105.json"], indirect=True)

plug_strip = pytest.mark.parametrize("device", ["p300.json"], indirect=True)

bulb = pytest.mark.parametrize(
    "device", ["l930.json", "l630.json", "l530.json"], indirect=True
)

bulb_led_strip = pytest.mark.parametrize("device", ["l930.json"], indirect=True)

hub = pytest.mark.parametrize("device", ["h100.json"], indirect=True)

trv = pytest.mark.parametrize(
    "device",
    [("h100.json", "hub_children/trv_ke100.json")],
    indirect=True,
    ids=lambda x: (x[1]),
)


@pytest.fixture
async def device(request) -> TapoDevice:
    if isinstance(request.param, tuple):
        data = load_fixture_with_merge(list(request.param))
    else:
        data = load_fixture(request.param)
    protocol = FakeProtocol(data)
    credential = AuthCredential("", "")
    client = TapoClient(
        auth_credential=credential,
        url="",
        protocol=protocol,
        http_session=aiohttp.ClientSession(),
    )
    factory = _get_device_class_from_info((await client.get_device_info()).get_or_raise())
    device = factory("", 80, client)
    await device.update()
    return device


def load_fixture_with_merge(files: list[str]):
    data = {}
    for file in files:
        data.update(load_fixture(file))
    return data


def load_fixture(file: str):
    """Return raw discovery file contents as JSON. Used for discovery tests."""
    p = Path(file)
    if not p.is_absolute():
        folder = Path(__file__).parent / "fixtures"
        p = folder / file

    with open(p) as f:
        fixture_data = json.load(f)
    return fixture_data


class FakeProtocol(TapoProtocol):
    def __init__(self, data: dict[str, Any]):
        self._data = data

    async def send_request(
        self, request: TapoRequest, retry: int = 3
    ) -> Try[TapoResponse[dict[str, Any]]]:
        print(f"Requesting data for method {request.method}, with {request.params}")
        method = request.method
        if method.startswith("set_lighting_effect"):
            self._data["get_device_info"]["lighting_effect"] = request.params
            return _tapo_response_of({})
        elif method.startswith("set_"):
            target_method = f"get_{method[4:]}"
            self._data[target_method].update(request.params)
            return _tapo_response_of({})
        elif method.startswith("control_child"):
            return await self._control_child(request)
        elif method.startswith("play_alarm"):
            self._data["get_device_info"]["in_alarm"] = True
            return _tapo_response_of({})
        elif method.startswith("stop_alarm"):
            self._data["get_device_info"]["in_alarm"] = False
            return _tapo_response_of({})
        else:
            response = self._data.get(method, Try.of(TapoResponse(0, {}, None)))
            return _tapo_response_of(response)

    async def close(self):
        pass

    async def _control_child(
        self, request: TapoRequest
    ) -> Try[TapoResponse[dict[str, Any]]]:
        params = cast(ControlChildParams, request.params)
        device_id = params.device_id
        nested_request = cast(MultipleRequestParams, params.requestData.params).requests[
            0
        ]
        new_request = TapoRequest(
            method=f"{nested_request.method}_{device_id}", params=nested_request.params
        )
        return (await self.send_request(new_request)).flat_map(
            lambda x: _tapo_response_child_of(x.result)
        )


def _tapo_response_of(payload: dict[str, any]) -> Try[TapoResponse]:
    return Try.of(TapoResponse(error_code=0, result=payload, msg=""))


def _tapo_response_child_of(payload: dict[str, any]) -> Try[TapoResponse]:
    return _tapo_response_of(
        {"responseData": {"result": {"responses": [{"result": payload}]}}}
    )
