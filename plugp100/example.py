import asyncio
import os

import aiohttp

from plugp100.api.tapo_client import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.protocol.camera_like_protocol import CameraLikeProtocol
from plugp100.requests.tapo_request import TapoRequest


async def main():
    # print("Scanning network...")
    # print(TapoDeviceFinder.classify(TapoDeviceFinder.scan(5)))

    # create generic tapo api
    username = os.getenv("USERNAME", "<tapo_email>")
    password = os.getenv("PASSWORD", "<tapo_password>")
    credentials = AuthCredential("admin", "")
    # client = TapoClient.create(credentials, "192.168.1.10")
    # print(await client.execute_raw_request(TapoRequest(method="get_sysinfo", params=None)))

    protocol = CameraLikeProtocol(
        credentials, "4.tcp.eu.ngrok.io", 18938, aiohttp.ClientSession()
    )

    print(await protocol.send_request(TapoRequest.get_device_info()))

    #
    # components = await client.get_component_negotiation()
    # print(components)

    # print(await client.get_device_info())
    # print(await client.get_energy_usage())
    # print(await client.get_current_power())
    # print(await client.get_child_device_list())
    # print(await client.get_child_device_component_list())
    # print(await client.set_lighting_effect(LightEffectPreset.Aurora.to_effect()))
    # plug = PlugDevice(TapoClient(username, password), "<tapo_device_ip>")
    # light = LightDevice(TapoClient(username, password), "<tapo_device_ip>")
    # ledstrip = LedStripDevice(TapoClient(username, password), "<tapo_device_ip>")

    # - hub example
    # hub = HubDevice(client)
    # print(await hub.get_children())
    # print(await hub.get_state_as_json())


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
