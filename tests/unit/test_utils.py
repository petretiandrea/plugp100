import random
from typing import Any, List

from plugp100.common.functional.tri import Try
from plugp100.responses.child_device_list import ChildDeviceList
from plugp100.responses.tapo_response import TapoResponse


def wrap_as_tapo_response(result) -> Try[TapoResponse[dict[str, Any]]]:
    return TapoResponse.try_from_json(
        {"error_code": 0, "result": result.__dict__, "msg": ""}
    )


def generate_random_children(partition_size: int, total: int) -> List[ChildDeviceList]:
    lists = []
    iterations = total // partition_size
    remaining = total % partition_size
    rnd = random.Random()
    for i in range(0, iterations):
        children = [{"id": rnd.random()} for _ in range(0, partition_size)]
        lists.append(ChildDeviceList(children, i * partition_size, total))

    last_children = [{"id": rnd.random()} for j in range(0, remaining)]
    lists.append(ChildDeviceList(last_children, total - remaining, total))
    return lists
