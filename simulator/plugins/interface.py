from simulator.models.pod import Pod
from simulator.models.node import Node
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from simulator.models.etcd_mock import EtcdMock
import math
import random
from typing import Tuple

class QueueSortPlugin:
    def sort(self, e: EtcdMock) -> List[Pod]:
        raise NotImplementedError
    
class FilterPlugin:
    def filter(self, pod: Pod, e: EtcdMock) -> List[Node]:
        raise NotImplementedError
    
class ScorePlugin:
    def score(self, pod: Pod, node: Node, e: EtcdMock) -> float:
        raise NotImplementedError
    
    # def pick(self, pod: Pod, feasible_nodes: List[Node], e: EtcdMock) -> Optional[Node]:
    #     # 对每一个可行节点打分，返回分数最高的节点（平局时随机选一个）
    #     best_node: Optional[Node] = None
    #     best_score = -math.inf
    #     for node in feasible_nodes:
    #         score = self.score(pod, node, e)
    #         if score > best_score:
    #             best_score = score
    #             best_node = node
    #         elif score == best_score:
    #             # tie-breaker: random choice
    #             if random.random() < 0.5:
    #                 best_node = node
    #     return best_node
    
    def pick(self, pod: Pod, feasible_nodes: List[Node], e: EtcdMock) -> Optional[Node]:
        if not feasible_nodes:
            return None
        
        def _score_single_node(node: Node) -> Tuple[Node, float]:
            """
            对单个节点打分，返回(节点, 分数)
            捕获异常避免单个节点打分失败影响整体流程
            """
            try:
                # 修正：传递e参数到score方法（关键修复笔误问题）
                score = self.score(pod, node, e)
                return (node, score)
            except Exception as exc:
                # 打分失败的节点按最低分处理，避免被选中
                print(f"节点 {getattr(node, 'name', '未知')} 打分失败: {exc}")
                return (node, -math.inf)
        
        # 并行执行所有节点的打分
        scored_nodes: List[Tuple[Node, float]] = []

        max_workers = min(10, len(feasible_nodes))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            
            future_map = {
                executor.submit(_score_single_node, node): node
                for node in feasible_nodes
            }
            
            
            for future in as_completed(future_map):
                node_score_tuple = future.result()
                scored_nodes.append(node_score_tuple)
        
        best_score = max(scored_nodes, key=lambda x: x[1])[1]
        best_nodes = [node for node, score in scored_nodes if score == best_score]
        best_node = random.choice(best_nodes) if best_nodes else None
        
        return best_node