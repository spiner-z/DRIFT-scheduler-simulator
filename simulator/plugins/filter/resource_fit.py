from simulator.plugins.interface import FilterPlugin
from simulator.models.pod import Pod
from simulator.models.node import Node
from typing import List
from simulator.models.etcd_mock import EtcdMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class FilterResourceFit(FilterPlugin):
    def filter(self, pod: Pod, e: EtcdMock) -> List[Node]:
        feasible_nodes: List[Node] = []
        # 线程锁：保证多线程向列表追加元素时的线程安全
        lock = threading.Lock()
        
        # 定义单节点检查的函数（并行执行的最小单元）
        def check_node(node_name: str, node: Node) -> Node | None:
            """检查单个节点是否满足条件，满足则返回节点，否则返回None"""
            if e.check_bindable(pod.name, node_name):
                return node
            return None
        
        # 配置线程池（建议根据CPU核心数/节点数量合理设置，默认用5个线程）
        max_workers = min(10, len(e.nodes) if e.nodes else 1)  # 避免线程数过多
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有节点检查任务，保存任务与节点的映射
            future_to_node = {
                executor.submit(check_node, node_name, node): (node_name, node)
                for node_name, node in e.nodes.items()
            }
            
            # 遍历已完成的任务，收集结果
            for future in as_completed(future_to_node):
                try:
                    result_node = future.result()  # 获取单个任务的结果
                    if result_node is not None:
                        with lock:  # 加锁保证列表操作线程安全
                            feasible_nodes.append(result_node)
                except Exception as e:
                    # 捕获单个任务的异常，避免影响整体流程
                    node_name, _ = future_to_node[future]
                    print(f"检查节点 {node_name} 时发生异常: {e}")
        
        return feasible_nodes