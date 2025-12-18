from simulator.plugins.interface import ScorePlugin
from simulator.models.pod import Pod
from simulator.models.node import Node
import random
import math
from typing import List, Optional
from simulator.models.etcd_mock import EtcdMock

class ScoreKubernetes(ScorePlugin):
    def name(self) -> str:
        return "k8s"

    def score(self, pod: Pod, node: Node, e: EtcdMock) -> float:
        pod_count = len(e.pods_on_node(node.name))
        return 1.0 / (pod_count + 1) * 100.0