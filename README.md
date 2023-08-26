# Plug P100
This is a fork of original work of [@K4CZP3R](https://github.com/K4CZP3R/tapo-p100-python)

The purpose of this fork is to provide the library as PyPi package. 

# How to install
```pip install plugp100```

# Code example

```python
import asyncio
import os

from plugp100.api.light_effect_preset import LightEffectPreset
from plugp100.api.tapo_client import TapoClient, AuthCredential


async def main():
    # create generic tapo api
    username = os.getenv('USERNAME', '<tapo_email>')
    password = os.getenv('PASSWORD', '<tapo_password>')

    credential = AuthCredential(username, password)
    client = await TapoClient.connect(credential, "<ip_address>")

    print(await client.get_device_info())
    print(await client.get_device_usage())
    print(await client.get_energy_usage())
    print(await client.get_current_power())
    print(await client.get_child_device_list())
    print(await client.get_child_device_component_list())
    print(await client.set_lighting_effect(LightEffectPreset.Aurora.to_effect()))

    # plug = PlugDevice(TapoClient(username, password), "<tapo_device_ip>")
    # light = LightDevice(TapoClient(username, password), "<tapo_device_ip>")
    # ledstrip = LedStripDevice(TapoClient(username, password), "<tapo_device_ip>")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()
```

