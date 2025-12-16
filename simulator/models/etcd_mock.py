from typing import Dict, Optional, Set

from simulator.models.node import Node
from simulator.models.pod import Pod

class EtcdMock:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.pods: Dict[str, Pod] = {}
        self.node_pods: Dict[str, Set[str]] = {}
        self.pod_node: Dict[str, str] = {}

    # --- basic CRUD ---
    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node
        self.node_pods.setdefault(node.name, set())

    def add_pod(self, pod: Pod) -> None:
        self.pods[pod.name] = pod

    # --- O(1) queries ---
    def get_node(self, node_name: str) -> Node:
        return self.nodes[node_name]

    def get_pod(self, pod_name: str) -> Pod:
        return self.pods[pod_name]

    def pods_on_node(self, node_name: str) -> Set[str]:
        # O(1) 返回集合引用（遍历输出是 O(k) 的不可避免成本）
        return self.node_pods[node_name]

    def node_of_pod(self, pod_name: str) -> Optional[str]:
        return self.pod_node.get(pod_name)

    # --- binding helpers (GPU allocation is O(<=8)) ---
    def _alloc_gpus_on_node(self, node: Node, pod: Pod) -> Dict[int, int]:
        if pod.num_gpu == 0:
            return {}

        if node.gpu_count < pod.num_gpu:
            raise ValueError("insufficient GPU count on node")

        need = pod.num_gpu
        per = pod.gpu_milli
        if not (0 <= per <= 1000):
            raise ValueError("gpu_milli must be in [0,1000]")

        chosen: Dict[int, int] = {}

        if node.gpu_share_enabled:
            # best-fit: pick GPUs that are already fuller (smaller free milli),
            # but still can fit 'per'
            eligible = [(node.gpu_free_milli[gid], gid)
                        for gid in range(node.gpu_count)
                        if node.gpu_free_milli[gid] >= per]
            eligible.sort(key=lambda x: (x[0], x[1]))  # fuller first, then gid

            if len(eligible) < need:
                raise ValueError("insufficient GPU milli / GPU slots on node")

            for _, gid in eligible[:need]:
                chosen[gid] = per

        else:
            # no sharing: each GPU can bind at most one pod
            eligible = [gid for gid in range(node.gpu_count)
                        if len(node.gpu_pods[gid]) == 0 and node.gpu_free_milli[gid] >= per]
            # deterministic
            eligible.sort()

            if len(eligible) < need:
                raise ValueError("insufficient GPU milli / GPU slots on node")

            for gid in eligible[:need]:
                chosen[gid] = per

        # commit
        for gid, milli in chosen.items():
            node.gpu_free_milli[gid] -= milli
            node.gpu_pods[gid][pod.name] = milli

        return chosen

    # --- bind / unbind ---
    def bind(self, pod_name: str, node_name: str) -> None:
        pod = self.pods[pod_name]
        node = self.nodes[node_name]

        if pod.bound_node is not None:
            raise ValueError("pod already bound")

        # check cpu/mem O(1)
        if node.cpu_milli_free < pod.cpu_milli or node.memory_mib_free < pod.memory_mib:
            raise ValueError("insufficient cpu/mem")

        # allocate GPUs (<=8 scan)
        gpu_alloc = self._alloc_gpus_on_node(node, pod)

        # commit cpu/mem
        node.cpu_milli_free -= pod.cpu_milli
        node.memory_mib_free -= pod.memory_mib

        # commit indices O(1)
        pod.bound_node = node_name
        pod.gpu_alloc = gpu_alloc

        self.node_pods[node_name].add(pod_name)
        self.pod_node[pod_name] = node_name

    def unbind(self, pod_name: str) -> None:
        pod = self.pods[pod_name]
        node_name = pod.bound_node
        if node_name is None:
            return  # or raise

        node = self.nodes[node_name]

        # restore cpu/mem
        node.cpu_milli_free += pod.cpu_milli
        node.memory_mib_free += pod.memory_mib

        # restore GPUs (<=8)
        for gid, milli in pod.gpu_alloc.items():
            # safety: if data corrupted, KeyError will expose it early
            node.gpu_pods[gid].pop(pod.name)
            node.gpu_free_milli[gid] += milli

        # update indices
        self.node_pods[node_name].remove(pod_name)
        self.pod_node.pop(pod_name, None)

        pod.bound_node = None
        pod.gpu_alloc.clear()
