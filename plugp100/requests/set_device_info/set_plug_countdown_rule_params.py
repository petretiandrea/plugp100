from dataclasses import dataclass
from typing import Dict


@dataclass
class SetPlugCountdownRuleParams(object):
    desired_states: Dict[str, str]
    delay: int
    enable: bool = True