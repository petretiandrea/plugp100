import asyncio
import os
import sys

from plugp100.api.tapo_client import TapoClient
from plugp100.common.credentials import AuthCredential
from plugp100.api.plug_device import PlugDevice

async def main(ip_address, action):
    # create generic tapo api
    username = os.getenv("USERNAME", "youremail")
    password = os.getenv("PASSWORD", "yourpassword")

    credentials = AuthCredential(username, password)
    client = TapoClient.create(credentials, ip_address)

    plug = PlugDevice(client)
    if action.lower() == "on":
        print("Turning plug on...")
        print(await plug.on())
    elif action.lower() == "off":
        print("Turning plug off...")
        print(await plug.off())
    elif action.lower() == "watt":
        print("Wattage:")
        print(await client.get_current_power())
    elif action.lower() == "info":
        print("Info:")
        print(await client.get_device_info())
    elif action.lower() == "energy":
        print("Energy Usage:")
        print(await client.get_energy_usage())
    elif action.lower() == "childlist":
        print("Child Device List:")
        print(await client.get_child_device_list())
    elif action.lower() == "componentlist":
        print("Child Device Component List:")
        print(await client.get_child_device_component_list())
    else:
        print("Invalid action. Please specify 'on', 'off', 'watt', 'info', 'energy', 'childlist', or 'componentlist'.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python plugp100helper.py <ip_address> <action>")
        sys.exit(1)

    ip_address = sys.argv[1]
    action = sys.argv[2]
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(ip_address, action))
    loop.close()
