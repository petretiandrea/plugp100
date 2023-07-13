import logging
from dataclasses import dataclass
from time import time
from typing import Optional, Any, cast

import aiohttp
import jsons

from plugp100.api.light_effect import LightEffect
from plugp100.common.functional.either import Either, Right, Left
from plugp100.common.utils.http_client import AsyncHttp
from plugp100.common.utils.json_utils import dataclass_encode_json, Json
from plugp100.requests.handshake_params import HandshakeParams
from plugp100.requests.login_device import LoginDeviceParams
from plugp100.requests.secure_passthrough_params import SecurePassthroughParams
from plugp100.requests.tapo_request import TapoRequest, MultipleRequestParams
from plugp100.responses.child_device_list import ChildDeviceList
from plugp100.responses.energy_info import EnergyInfo
from plugp100.responses.power_info import PowerInfo
from plugp100.responses.tapo_response import TapoResponse
from plugp100.encryption.key_pair import KeyPair
from plugp100.encryption.tp_link_cipher import TpLinkCipher, TpLinkCipherCryptography

logger = logging.getLogger(__name__)


@dataclass
class Session:
    url: str
    key_pair: KeyPair
    chiper: TpLinkCipher
    cookie_token: Optional[str]
    token: Optional[str]


class TapoClient:
    TERMINAL_UUID = "88-00-DE-AD-52-E1"

    def __init__(
            self,
            username: str,
            password: str,
            http_session: Optional[aiohttp.ClientSession] = None,
    ):
        self._username = username
        self._password = password
        self._http = AsyncHttp(aiohttp.ClientSession() if http_session is None else http_session)
        self._session = None

    async def login(self, url: str) -> Either[True, Exception]:
        """
        The `login` function performs a handshake with a given URL, and if successful, sends a login request with a username
        and password, returning a token if successful or an exception if not.

        @param url: The `url` parameter is a string that represents the URL of the login endpoint
        @type url: str
        @return: The login function returns an Either type, which can either be a Right containing True if the login is
        successful, or a Right containing an Exception if there is an error during the login process.
        """
        handshake = await self._handshake(url)
        if isinstance(handshake, Right):
            token_or_error = await self._login_request(self._username, self._password)
            self._session.token = token_or_error.value if isinstance(token_or_error, Right) else None
            return token_or_error.map(lambda _: True)

        return handshake

    async def execute_raw_request(self, request: 'TapoRequest') -> Either[Json, Exception]:
        request.with_terminal_uuid(self.TERMINAL_UUID).with_request_time_millis(time())
        return (await self._execute_with_passthrough(request, require_token=True)).map(lambda x: x.result)

    async def get_device_info(self) -> Either[Json, Exception]:
        """
        The function `get_device_info` sends a request to retrieve device information and returns the result or an
        exception.
        @return: an `Either` object that contains either a `Json` object or an `Exception`.
        """
        get_info_request = TapoRequest.get_device_info()
        return (await self._execute_with_passthrough(get_info_request, require_token=True)) \
            .map(lambda x: x.result)

    async def get_device_usage(self) -> Either[Json, Exception]:
        """
        The function `get_device_usage` retrieves the usage information of a device and returns it as a JSON object or an
        exception.
        @return: an `Either` object, which can contain either a `Json` object or an `Exception`.
        """
        get_usage_request = TapoRequest.get_device_usage()
        response = await self._execute_with_passthrough(get_usage_request, require_token=True)
        return response.map(lambda x: x.result)

    async def get_energy_usage(self) -> Either[EnergyInfo, Exception]:
        """
        The function `get_energy_usage` makes a request to get energy usage information and returns either the energy info
        or an exception.
        @return: an `Either` type, which can either contain an `EnergyInfo` object or an `Exception` object.
        """
        get_energy_request = TapoRequest.get_energy_usage()
        response = await self._execute_with_passthrough(get_energy_request, require_token=True)
        return response.map(lambda x: EnergyInfo(x.result))

    async def get_current_power(self) -> Either[PowerInfo, Exception]:
        """
        The function `get_current_power` asynchronously retrieves the current power information and returns it as a
        `PowerInfo` object, or an `Exception` if an error occurs.
        @return: an `Either` object that contains either a `PowerInfo` object or an `Exception`.
        """
        get_current_power = TapoRequest.get_current_power()
        response = await self._execute_with_passthrough(get_current_power, require_token=True)
        return response.map(lambda x: PowerInfo(x.result))

    async def set_device_info(self, device_info: Any) -> Either[True, Exception]:
        """
        The function `set_device_info` encodes the `device_info` object into JSON format and returns either `True` or an
        `Exception`.

        @param device_info: The `device_info` parameter is an object that contains information about a device. It is passed
        to the `set_device_info` method as an argument
        @return: an `Either` type, which can either be `True` or an `Exception`.
        """
        return await self._set_device_info(dataclass_encode_json(device_info))

    async def set_lighting_effect(self, light_effect: LightEffect) -> Either[True, Exception]:
        """
        The function `set_lighting_effect` sets a lighting effect for a device and returns either `True` or an exception.

        @param light_effect: The `light_effect` parameter is of type `LightEffect`. It represents the desired lighting
        effect that you want to set for a device
        @type light_effect: LightEffect
        @return: an `Either` object that contains either a `True` value or an `Exception`.
        """
        request = TapoRequest.set_lighting_effect(light_effect) \
            .with_terminal_uuid(self.TERMINAL_UUID) \
            .with_request_time_millis(time())
        response = await self._execute_with_passthrough(request, require_token=True)
        return response.map(lambda _: True)

    async def get_child_device_list(self) -> Either[ChildDeviceList, Exception]:
        """
        The function `get_child_device_list` retrieves a list of child devices asynchronously and returns either the list or
        an exception.
        @return: an `Either` object, which can contain either a `ChildDeviceList` or an `Exception`.
        """
        request = TapoRequest.get_child_device_list() \
            .with_terminal_uuid(self.TERMINAL_UUID) \
            .with_request_time_millis(time())
        response = await self._execute_with_passthrough(request, require_token=True)
        return response.map(lambda x: ChildDeviceList.try_from_json(**x.result))

    async def get_child_device_component_list(self) -> Either[Json, Exception]:
        """
        The function `get_child_device_component_list` retrieves a list of child device components asynchronously and
        returns either the JSON response or an exception.
        @return: an `Either` object, which can contain either a `Json` object or an `Exception`.
        """
        request = TapoRequest.get_child_device_component_list() \
            .with_terminal_uuid(self.TERMINAL_UUID) \
            .with_request_time_millis(time())
        response = await self._execute_with_passthrough(request, require_token=True)
        return response.map(lambda x: x.result)

    async def control_child(self, child_id: str, request: TapoRequest) -> Either[Json, Exception]:
        """
        The function `control_child` is an asynchronous method that sends a control request to a child device and returns
        the response or an exception.

        @param child_id: The `child_id` parameter is a string that represents the ID of a child device
        @type child_id: str
        @param request: The `request` parameter is an instance of the `TapoRequest` class. It represents a request to be
        sent to the Tapo device.
        @type request: TapoRequest
        @return: an instance of the `Either` class, which can contain either a `Json` object or an `Exception`.
        """
        multiple_request = TapoRequest.multiple_request(MultipleRequestParams([request])) \
            .with_terminal_uuid(self.TERMINAL_UUID) \
            .with_request_time_millis(time())
        request = TapoRequest.control_child(child_id, multiple_request)
        response = await self._execute_with_passthrough(request, require_token=True)
        if isinstance(response, Right):
            try:
                responses = response.value.result['responseData']['result']['responses']
                if len(responses) > 0:
                    return Right(responses[0]['result'])
                else:
                    return Left(Exception("Empty responses from child"))
            except Exception as e:
                return Left(e)
        return cast(Left, response)

    async def _login_request(self, username: str, password: str) -> Either[str, Exception]:
        login_device_params = LoginDeviceParams(username, password)
        login_request = TapoRequest.login(login_device_params) \
            .with_request_time_millis(time())
        response_as_dict = await self._execute_with_passthrough(login_request)
        return response_as_dict.map(lambda x: x.result['token'])

    async def _handshake(self, url: str) -> Either[True, Exception]:
        logger.debug("Will perform handshaking...")
        logger.debug("Generating keypair")

        url = f"http://{url}/app"
        key_pair = KeyPair.create_key_pair()

        handshake_params = HandshakeParams(key_pair.get_public_key())
        logger.debug(f"Handshake params: {jsons.dumps(handshake_params)}")

        request = TapoRequest.handshake(handshake_params)
        request_body = jsons.loads(jsons.dumps(request))
        logger.debug(f"Request {request_body}")

        response = await self._http.async_make_post(url, json=request_body)
        resp_dict = await response.json(content_type=None)
        logger.debug(f"Device responded with: {resp_dict}")
        response_or_error = TapoResponse.try_from_json(resp_dict).map(lambda _: True)

        if isinstance(response_or_error, Right):
            cookie_token = response.cookies.get('TP_SESSIONID').value
            logger.debug(f"Got TP_SESSIONID token: ...{cookie_token[5:]}")

            logger.debug("Decoding handshake key...")
            handshake_key = resp_dict['result']['key']
            tp_link_cipher = TpLinkCipherCryptography.create_from_keypair(handshake_key, key_pair)

            self._session = Session(url, key_pair, tp_link_cipher, cookie_token, token=None)
            return Right(True)
        else:
            return response_or_error

    async def _execute_with_passthrough(
            self,
            request: TapoRequest,
            require_token: bool = False
    ) -> Either[TapoResponse[Json], Exception]:
        encrypted_request = self._session.chiper.encrypt(jsons.dumps(request))
        passthrough_request = TapoRequest.secure_passthrough(SecurePassthroughParams(encrypted_request))
        request_body = jsons.loads(jsons.dumps(passthrough_request))

        logger.debug(f"Request body: {request_body}")

        response_encrypted = await self._http.async_make_post_cookie(
            self._session.url if not require_token else f"{self._session.url}?token={self._session.token}",
            request_body,
            {'TP_SESSIONID': self._session.cookie_token}
        )
        response_as_dict: dict = await response_encrypted.json(content_type=None)
        logger.debug(f"Device responded with: {response_as_dict}")

        return TapoResponse.try_from_json(response_as_dict) \
            .map(lambda response: jsons.loads(self._session.chiper.decrypt(response.result['response']))) \
            .bind(lambda decrypted_response: TapoResponse.try_from_json(decrypted_response))

    async def _set_device_info(self, device_info: Json) -> Either[True, Exception]:
        request = TapoRequest.set_device_info(device_info) \
            .with_terminal_uuid(self.TERMINAL_UUID) \
            .with_request_time_millis(time())
        response = await self._execute_with_passthrough(request, require_token=True)
        return response.map(lambda _: True)
