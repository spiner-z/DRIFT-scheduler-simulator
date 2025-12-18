from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from enum import Enum
class PodStatus(str, Enum):
    Pending = "Pending"
    Running = "Running"
    Completed = "Completed"
    Failed = "Failed"

@dataclass
class Pod:
    name: str
    cpu_milli: int
    memory_mib: int
    num_gpu: int = 0
    gpu_milli: int = 0

    bound_node: Optional[str] = None
    # gpu_id -> milli
    gpu_alloc: Dict[int, int] = field(default_factory=dict)

    creation_time: Optional[int] = None
    duration: Optional[int] = None
    scheduled_time: Optional[int] = None
    completion_time: Optional[int] = None

    status: PodStatus = PodStatus.Pending