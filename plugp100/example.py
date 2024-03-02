import asyncio
import os

from plugp100.api.light_effect_preset import LightEffectPreset
from plugp100.api.tapo_client import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.discovery.arp_lookup import ArpLookup
from plugp100.discovery.tapo_discovery import TapoDiscovery


async def main():
    print("Scanning network...")
    discovered_devices = list(TapoDiscovery.scan(5))
    for x in discovered_devices:
        print(x)

    if len(discovered_devices) > 0:
        print("Trying to lookup with mac address")
        lookup = await ArpLookup.lookup(
            discovered_devices[0].mac.replace("-", ":"),
            "192.168.1.0/24",
            allow_promiscuous=False,
        )
        print(lookup)

    # create generic tapo api
    username = os.getenv("USERNAME", "<tapo_email>")
    password = os.getenv("PASSWORD", "<tapo_password>")

    credentials = AuthCredential(username, password)
    client = TapoClient.create(credentials, "<tapo_device_ip>")

    print(await client.get_device_info())
    print(await client.get_energy_usage())
    print(await client.get_current_power())
    print(await client.get_child_device_list())
    print(await client.get_child_device_component_list())
    print(await client.set_lighting_effect(LightEffectPreset.Aurora.to_effect()))
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
