from plugp100.api.base_tapo_device import _BaseTapoDevice
from plugp100.api.tapo_client import TapoClient
from plugp100.common.functional.tri import Try
from plugp100.requests.set_device_info.set_light_color_info_params import (
    LightColorDeviceInfoParams,
)
from plugp100.requests.set_device_info.set_light_info_params import (
    LightDeviceInfoParams,
)
from plugp100.requests.set_device_info.set_plug_info_params import SetPlugInfoParams
from plugp100.responses.device_state import LightDeviceState


class LightDevice(_BaseTapoDevice):
    def __init__(self, api: TapoClient):
        super().__init__(api)

    async def get_state(self) -> Try[LightDeviceState]:
        """
        The function `get_state` asynchronously retrieves the device information from an API and returns either the device
        state or an exception.
        @return: an instance of the `Either` class, which can hold either a `LightDeviceState` object or an `Exception`
        object.
        """
        return (await self._api.get_device_info()).flat_map(
            LightDeviceState.try_from_json
        )

    async def on(self) -> Try[bool]:
        """
        The function `on` turns on light
        @return: an instance of the `Either` class, which can hold either a `True` value or an `Exception` object.
        """
        return await self._api.set_device_info(SetPlugInfoParams(True))

    async def off(self) -> Try[bool]:
        """
        The function `off` turns off light
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(SetPlugInfoParams(False))

    async def set_brightness(self, brightness: int) -> Try[bool]:
        """
        The function sets the brightness of a device using an API call and returns either True if successful or an Exception
        if there is an error.

        @param brightness: The brightness parameter is an integer value that represents the desired brightness level for a
        light device
        @type brightness: int
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(
            LightDeviceInfoParams(brightness=brightness)
        )

    async def set_hue_saturation(self, hue: int, saturation: int) -> Try[bool]:
        """
        The function sets the hue and saturation of a light device using the provided values.

        @param hue: The "hue" parameter represents the hue value of the light color. It is an integer value ranging from 0
        to 360, where 0 represents red, 120 represents green, and 240 represents blue. The hue value determines the dominant
        color of the light
        @type hue: int
        @param saturation: The saturation parameter represents the intensity or purity of the color. It determines how vivid
        or dull the color appears. A higher saturation value results in more vibrant colors, while a lower saturation value
        produces more muted or grayscale colors. The saturation value is typically specified as an integer between 0 and
        100,
        @type saturation: int
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(
            LightColorDeviceInfoParams(hue=hue, saturation=saturation, color_temp=0)
        )

    async def set_color_temperature(self, color_temperature: int) -> Try[bool]:
        """
        The function sets the color temperature of a light device using the provided color temperature value.

        @param color_temperature: The `color_temperature` parameter is an integer that represents the desired color
        temperature for a light. Color temperature is typically measured in Kelvin and is used to describe the color
        appearance of a light source. A lower color temperature (e.g., 2700K) produces a warm, yellowish light,
        @type color_temperature: int
        @return: an `Either` object, which can either be `True` or an `Exception`.
        """
        return await self._api.set_device_info(
            LightColorDeviceInfoParams(color_temp=color_temperature)
        )
