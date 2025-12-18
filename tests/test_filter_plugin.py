from simulator.plugins.filter.resource_fit import FilterResourceFit
from simulator.models.etcd_mock import EtcdMock
from simulator.models.node import Node
from simulator.models.pod import Pod, PodStatus

def test_resource_fit_filter_plugin():
    e = EtcdMock()
    n1 = Node(name="n1", cpu_milli_total=16000, memory_mib_total=32768, gpu_count=2, gpu_share_enabled=True)
    n2 = Node(name="n2", cpu_milli_total=16000, memory_mib_total=32768, gpu_count=0, gpu_share_enabled=False)
    e.add_node(n1)
    e.add_node(n2)

    pod1 = Pod(name="pod1", cpu_milli=2000, memory_mib=2048, num_gpu=1, gpu_milli=500)
    pod2 = Pod(name="pod2", cpu_milli=2000, memory_mib=2048, num_gpu=0, gpu_milli=0)

    e.add_pod(pod1)
    e.add_pod(pod2)

    filter_plugin = FilterResourceFit()

    feasible_nodes_pod1 = filter_plugin.filter(pod1, e)
    feasible_nodes_pod2 = filter_plugin.filter(pod2, e)

    assert len(feasible_nodes_pod1) == 1
    assert feasible_nodes_pod1[0].name == "n1"

    assert len(feasible_nodes_pod2) == 2
    assert set(node.name for node in feasible_nodes_pod2) == {"n1", "n2"}
    