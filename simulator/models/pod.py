from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

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