import asyncio

from plugp100 import TapoApiClient, TapoApiDiscover


async def main():
    # create generic tapo api
    # is_valid_device = await TapoApiDiscover.is_tapo_device("192.168.1.10")
    # print(is_valid_device)

    sw = TapoApiClient("192.168.1.104", "andreapedro96@gmail.com", "Andbea9671!")
    await sw.login()
    print(await sw.get_state_as_dict())
    print(await sw.get_state())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()