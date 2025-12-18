from simulator.plugins.interface import ScorePlugin
from simulator.models.pod import Pod
from simulator.models.node import Node
import random
import math
from typing import List, Optional
from simulator.models.etcd_mock import EtcdMock

class ScoreBinPack(ScorePlugin):
    def name(self) -> str:
        return "binpack"
    
    def score(self, pod: Pod, node: Node, e: EtcdMock) -> float:
        cpu_util = node.get_cpu_utilization()
        mem_util = node.get_memory_utilization()
        util = max(cpu_util, mem_util)
        return util * 100.0
    