from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

@dataclass
class Node:
    name: str
    cpu_milli_total: int
    memory_mib_total: int
    gpu_count: int = 0
    gpu_share_enabled: bool = True

    cpu_milli_free: int = field(init=False)
    memory_mib_free: int = field(init=False)

    # per-gpu remaining milli, length=gpu_count
    gpu_free_milli: List[int] = field(init=False)
    # per-gpu {pod_name: milli}
    gpu_pods: List[Dict[str, int]] = field(init=False)

    def __post_init__(self):
        self.cpu_milli_free = self.cpu_milli_total
        self.memory_mib_free = self.memory_mib_total
        self.gpu_free_milli = [1000] * self.gpu_count
        self.gpu_pods = [dict() for _ in range(self.gpu_count)]