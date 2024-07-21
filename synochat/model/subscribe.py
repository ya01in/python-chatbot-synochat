# all the dataclass for sub related service
import dataclasses
import datetime


@dataclasses.dataclass
class SubInfo:
    wait_for_reply: bool
    wait_time: datetime.datetime
    u_id: int
    u_name: str
    sub_time: datetime.datetime
    on_time: datetime.datetime
    idx_hour: int
