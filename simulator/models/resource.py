from simulator.models.node import Node
from simulator.models.pod import Pod
from typing import List

class NodeResource:
    def __init__(self, node: Node):
        self.node_name = node.name
        self.total_cpu = node.cpu_milli_total
        self.free_cpu = node.cpu_milli_free
        self.total_memory = node.memory_mib_total
        self.free_memory = node.memory_mib_free
        self.total_gpus = node.gpu_count
        self.free_gpus_points_list: List[int] = []
        for free_milli in node.gpu_free_milli:
            self.free_gpus_points_list.append(free_milli)
        assert self.total_gpus == len(self.free_gpus_points_list)

    def copy(self):
        new_nr = NodeResource.__new__(NodeResource)  # 绕过 __init__
        new_nr.node_name = self.node_name
        new_nr.total_cpu = self.total_cpu
        new_nr.free_cpu = self.free_cpu
        new_nr.total_memory = self.total_memory
        new_nr.free_memory = self.free_memory
        new_nr.total_gpus = self.total_gpus
        new_nr.free_gpus_points_list = self.free_gpus_points_list.copy()
        return new_nr
        

class PodResource:
    def __init__(self, pod: Pod):
        self.pod_name = pod.name
        self.cpu_request = pod.cpu_milli
        self.memory_request = pod.memory_mib
        self.gpu_count = pod.num_gpu
        self.gpu_points = pod.gpu_milli

    def copy(self):
        new_pr = PodResource.__new__(PodResource)  # 绕过 __init__
        new_pr.pod_name = self.pod_name
        new_pr.cpu_request = self.cpu_request
        new_pr.memory_request = self.memory_request
        new_pr.gpu_count = self.gpu_count
        new_pr.gpu_points = self.gpu_points
        return new_pr

class TargetPod:
    def __init__(self, target_pod_resource: PodResource, percentage: float):
        self.target_pod_resource = target_pod_resource
        self.percentage = percentage

def get_target_pod_list_from_pods(pods: List[Pod]) -> List[TargetPod]:
    """从一组 Pod 中统计出典型的 Pod 规格及其占比"""
    total_pods = len(pods)
    pod_resource_count = {}
    for pod in pods:
        pres = PodResource(pod)
        key = (pres.cpu_request, pres.memory_request, pres.gpu_count, pres.gpu_points)
        if key not in pod_resource_count:
            pod_resource_count[key] = 0
        pod_resource_count[key] += 1
    
    target_pod_list = []
    for key, count in pod_resource_count.items():
        cpu_request, memory_request, gpu_count, gpu_points = key
        pres = PodResource.__new__(PodResource)  # 绕过 __init__
        pres.cpu_request = cpu_request
        pres.memory_request = memory_request
        pres.gpu_count = gpu_count
        pres.gpu_points = gpu_points
        percentage = count / total_pods
        target_pod_list.append(TargetPod(pres, percentage))
    
    return target_pod_list


        