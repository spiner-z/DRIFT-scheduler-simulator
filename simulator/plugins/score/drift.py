from simulator.plugins.interface import ScorePlugin
from simulator.models.node import Node
from simulator.models.pod import Pod
import math
import numpy as np
from typing import Optional, List
from simulator.models.resource import PodResource, NodeResource
from simulator.models.etcd_mock import EtcdMock

class ScoreDrift(ScorePlugin):
    def __init__(self, typical_pods: List[PodResource]):
        """初始化插件，typical_pods 可用于计算资源碎片化得分的参考"""
        self.typical_pods = typical_pods

    def name(self) -> str:
        return "drift"

    def score(self, pod: Pod, node: Node, e: EtcdMock) -> float:
        node_res = NodeResource(node)
        pod_res = PodResource(pod)
        score, _ = self.calculate_gpu_share_frag_score(node_res, pod_res)
        return float(score)

    def calculate_gpu_share_frag_score(self, node_res: NodeResource, pod_res: PodResource):
        """计算 GPU 分配的碎片化得分"""
        node_gpu_share_frag_score = self.node_gpu_share_frag_amount_score(node_res)

        if pod_res.gpu_count == 1 and pod_res.gpu_points < 1000:  # 部分 GPU 请求
            score, gpu_id = 0, ""
            for i in range(node_res.total_gpus):
                if node_res.free_gpus_points_list[i] >= pod_res.gpu_points:
                    new_node_res = node_res.copy()
                    new_node_res.free_cpu -= pod_res.cpu_request
                    new_node_res.free_memory -= pod_res.memory_request
                    new_node_res.free_gpus_points_list[i] -= pod_res.gpu_points
                    
                    new_node_gpu_share_frag_score = self.node_gpu_share_frag_amount_score(new_node_res)
                    frag_score = int(self.sigmoid((node_gpu_share_frag_score - new_node_gpu_share_frag_score) / 1000) * 1000)

                    if gpu_id == "" or frag_score > score:
                        score = frag_score
                        gpu_id = str(i)

            return score, gpu_id
        else:
            # 处理需要多张 GPU 的情况
            new_node_res = node_res.copy()
            new_node_res.free_cpu -= pod_res.cpu_request
            new_node_res.free_memory -= pod_res.memory_request
            cnt = 0
            for i in range(node_res.total_gpus):
                if node_res.free_gpus_points_list[i] >= pod_res.gpu_points:
                    new_node_res.free_gpus_points_list[i] -= pod_res.gpu_points
                    cnt += 1
                    if cnt == pod_res.gpu_count:
                        break
            new_node_gpu_share_frag_score = self.node_gpu_share_frag_amount_score(new_node_res)
            return int(self.sigmoid((node_gpu_share_frag_score - new_node_gpu_share_frag_score) / 1000) * 1000), str(0)  # 选择第一个 GPU

    def node_gpu_share_frag_amount_score(self, node_res: NodeResource):
        """计算节点的 GPU 资源碎片化得分"""
        from simulator.models.frag import Fragment
        frag = Fragment(node_res, self.typical_pods)
        return frag.get_frag_amount_sum_except_q3()

    def sigmoid(self, x):
        """Sigmoid 函数用于平滑分数"""
        return 1 / (1 + math.exp(-x))