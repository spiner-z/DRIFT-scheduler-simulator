from simulator.plugins.interface import QueueSortPlugin
from simulator.models.etcd_mock import EtcdMock
from simulator.models.pod import Pod
from typing import List

class QueueSortShortJobFirst(QueueSortPlugin):
    def sort(self, e: EtcdMock) -> List[Pod]:
        pending_pods = [e.pods[pod_name] for pod_name in e.pending_pods]
        return sorted(pending_pods, key=lambda p: (p.duration, p.creation_time, p.name))