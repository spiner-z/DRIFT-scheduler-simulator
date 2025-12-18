
from enum import Enum, auto
from dataclasses import dataclass, field
from simulator.models.pod import Pod

class EventType(Enum):
    ARRIVAL = auto()
    COMPLETION = auto()

# =========================
# 事件定义
# =========================
@dataclass(order=True)
class Event:
    time: int
    order: int
    type: EventType = field(compare=False)
    pod: Pod = field(compare=False)