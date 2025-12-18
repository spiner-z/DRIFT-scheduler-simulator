from simulator.core.scheduler import Scheduler
from simulator.plugins.queue_sort.fifo import QueueSortFIFO
from simulator.plugins.filter.resource_fit import FilterResourceFit
from simulator.plugins.score.k8s import ScoreKubernetes
from simulator.plugins.score.drift import ScoreDrift
from simulator.models.node import Node
from simulator.models.pod import Pod
from simulator.models.etcd_mock import EtcdMock
from typing import List
from simulator.models.resource import get_target_pod_list_from_pods
from simulator.utils.reader import get_h_nodes, get_h_pods

def demo_nodes(allow_gpu_share: bool) -> List[Node]:
    return get_h_nodes(count=10, allow_gpu_share=allow_gpu_share)

def demo_pods() -> List[Pod]:
    return get_h_pods(count=800)

def build_k8s_scheduler() -> Scheduler:
    nodes = demo_nodes(allow_gpu_share=False)
    pods = demo_pods()
    queue_sorter = QueueSortFIFO()
    filter_plugin = FilterResourceFit()
    score_plugin = ScoreKubernetes()
    scheduler = Scheduler(nodes, pods, queue_sorter, filter_plugin, score_plugin)
    return scheduler


def build_drift_scheduler() -> Scheduler:
    nodes = demo_nodes(allow_gpu_share=True)
    pods = demo_pods()

    queue_sorter = QueueSortFIFO()
    filter_plugin = FilterResourceFit()
    typical_pods = get_target_pod_list_from_pods(pods)
    score_plugin = ScoreDrift(typical_pods=typical_pods)
    scheduler = Scheduler(nodes, pods, queue_sorter, filter_plugin, score_plugin)
    return scheduler

if __name__ == "__main__":
    print("=== K8s Scheduler ===")
    k8s_scheduler = build_k8s_scheduler()
    k8s_scheduler.run()

    print("\n=== DRIFT Scheduler ===")
    drift_scheduler = build_drift_scheduler()
    drift_scheduler.run()