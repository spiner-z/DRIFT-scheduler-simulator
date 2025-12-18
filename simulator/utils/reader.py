from simulator.models.node import Node
from simulator.models.pod import Pod, PodStatus
from typing import List
import pandas as pd
import numpy as np

h_nodes_csv_path = "./data/H/csv/openb_node_list_all_node.csv"
h_pods_csv_path = "./data/H/csv/openb_pod_list_default.csv"

# nodes csv:
# sn,cpu_milli,memory_mib,gpu,model
# openb-node-0000,32000,262144,0,
# openb-node-0001,32000,262144,0,
# ...
def get_h_nodes(count: int, allow_gpu_share: bool) -> List[Node]:
    df_nodes = pd.read_csv(h_nodes_csv_path)
    nodes: List[Node] = []
    for i in range(min(count, len(df_nodes))):
        row = df_nodes.iloc[i]
        node = Node(
            name=row["sn"],
            cpu_milli_total=int(row["cpu_milli"]),
            memory_mib_total=int(row["memory_mib"]),
            gpu_count=int(row["gpu"]),
            gpu_share_enabled=allow_gpu_share,
        )
        nodes.append(node)
    return nodes

# pods csv:
# name,cpu_milli,memory_mib,num_gpu,gpu_milli,gpu_spec,qos,pod_phase,creation_time,deletion_time,scheduled_time
# openb-pod-0000,12000,16384,1,1000,,LS,Running,0,12537496,0
# openb-pod-0001,6000,12288,1,460,,LS,Running,427061,12902960,427061
# openb-pod-0002,12000,24576,1,1000,,LS,Running,1558381,12902960,1558381

def get_h_pods(count: int) -> List[Pod]:
    df_pods = pd.read_csv(h_pods_csv_path)
    pods: List[Pod] = []
    for i in range(min(count, len(df_pods))):
        row = df_pods.iloc[i]
        pod = Pod(
            name=row["name"],
            cpu_milli=int(row["cpu_milli"]),
            memory_mib=int(row["memory_mib"]),
            num_gpu=int(row["num_gpu"]),
            gpu_milli=int(row["gpu_milli"]),
            creation_time=0,
            duration=3600,
        )
        pods.append(pod)
    return pods