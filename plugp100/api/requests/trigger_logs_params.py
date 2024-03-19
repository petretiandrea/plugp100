from dataclasses import dataclass


@dataclass
class GetTriggerLogsParams:
    page_size: int
    start_id: int
