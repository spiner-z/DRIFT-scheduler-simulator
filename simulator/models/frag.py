from simulator.models.resource import NodeResource, PodResource, TargetPod
from typing import List, Dict
from enum import Enum

class FragmentType(Enum):
    Q1LackBoth  = "q1_lack_both"
    Q2LackGpu   = "q2_lack_gpu"
    Q3Satisfied = "q3_satisfied"
    Q4LackCpu   = "q4_lack_cpu"
    XLSatisfied = "xl_satisfied"
    XRLackCPU   = "xr_lack_cpu"
    NoAccess    = "no_access"

class Fragment:
    def __init__(self, node_resource: NodeResource, typical_pods: List[TargetPod]):
        self.node_resource = node_resource
        self.typical_pods = typical_pods
        self.frag_amount = self.get_node_gpushare_frag_amount()

    def get_fragment_type(self, pod_res: PodResource) -> FragmentType:
        """计算当前节点资源的碎片化类型"""
        node_res = self.node_resource
        if pod_res.gpu_points == 0:
            if node_res.free_cpu >= pod_res.cpu_request:
                return FragmentType.XLSatisfied
            else:
                return FragmentType.XRLackCPU
            
        if self.can_node_host_pod_on_gpu_memory(pod_res):
            if node_res.free_cpu >= pod_res.cpu_request:
                return FragmentType.Q3Satisfied
            else:
                return FragmentType.Q4LackCpu
        else:
            if node_res.free_cpu >= pod_res.cpu_request:
                return FragmentType.Q2LackGpu
            else:
                return FragmentType.Q1LackBoth
        
    def can_node_host_pod_on_gpu_memory(self, pod_res: PodResource) -> bool:
        """判断节点是否有足够的 GPU 资源点数来满足 Pod 的 GPU 需求"""
        gpu_request = pod_res.gpu_count
        for gpu_points in self.node_resource.free_gpus_points_list:
            if gpu_points >= pod_res.gpu_points:
                gpu_request -= 1
                if gpu_request <= 0:
                    return True
        return False
            

    def get_total_gpu_free_points(self) -> int:
        """计算节点上剩余的 GPU 资源点数总和"""
        return sum(self.node_resource.free_gpus_points_list)
    
    def get_node_gpushare_frag_amount(self):
        frag_amount: Dict[FragmentType, float] = {
            FragmentType.Q1LackBoth: 0,
            FragmentType.Q2LackGpu: 0,
            FragmentType.Q3Satisfied: 0,
            FragmentType.Q4LackCpu: 0,
            FragmentType.XLSatisfied: 0,
            FragmentType.XRLackCPU: 0,
            FragmentType.NoAccess: 0
        }
        for target_pod in self.typical_pods:
            freq = target_pod.percentage
            if freq < 0 or freq > 1:
                raise ValueError("TargetPod percentage must be in [0,1]")
            frag_type = self.get_fragment_type(target_pod.target_pod_resource)
            total_gpu_free_points = self.get_total_gpu_free_points()
            if frag_type == FragmentType.Q3Satisfied: # Part of GPUs are treated as Lack GPU fragment
                gpu_frag_points = self.get_gpu_frag_points_by_pod_res(target_pod.target_pod_resource)
                frag_amount[FragmentType.Q2LackGpu] += (freq * gpu_frag_points)
                frag_amount[FragmentType.Q3Satisfied] += (freq * (total_gpu_free_points - gpu_frag_points))
            else: # Q1, Q2, XL, XR, NA => all idle GPU resources are treated as fragment
                frag_amount[frag_type] += (freq * total_gpu_free_points)
        return frag_amount

    def get_gpu_frag_points_by_pod_res(self, pod_res: PodResource) -> float:
        gpu_frag_points = 0.0
        for free_points in self.node_resource.free_gpus_points_list:
            if free_points < pod_res.gpu_points:
                gpu_frag_points += free_points
        return float(gpu_frag_points)
    
    def get_frag_amount_sum_except_q3(self) -> float:
        frag_sum = 0.0
        for ftype, amount in self.frag_amount.items():
            if ftype != FragmentType.Q3Satisfied:
                frag_sum += amount
        return frag_sum