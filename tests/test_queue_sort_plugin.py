from simulator.plugins.queue_sort.fifo import QueueSortFIFO
from simulator.plugins.queue_sort.sjf import QueueSortShortJobFirst
from simulator.models.etcd_mock import EtcdMock
from simulator.models.node import Node
from simulator.models.pod import Pod, PodStatus

def test_queue_sort_fifo():
    e = EtcdMock()
    e.add_node(Node(name="n1", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=True))
    e.add_node(Node(name="n2", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=1, gpu_share_enabled=False))
    
    e.add_pod(Pod(name="p1", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=2, duration=10))
    e.add_pod(Pod(name="p2", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=3, duration=5))
    e.add_pod(Pod(name="p3", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=500, creation_time=1, duration=15))
    
    fifo_sorter = QueueSortFIFO()
    sorted_pods = fifo_sorter.sort(e)
    
    assert [pod.name for pod in sorted_pods] == ["p3", "p1", "p2"]

def test_queue_sort_sjf():
    e = EtcdMock()
    e.add_node(Node(name="n1", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=True))
    e.add_node(Node(name="n2", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=1, gpu_share_enabled=False))
    
    e.add_pod(Pod(name="p1", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=2, duration=10))
    e.add_pod(Pod(name="p2", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=3, duration=5))
    e.add_pod(Pod(name="p3", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=500, creation_time=1, duration=15))
    
    sjf_sorter = QueueSortShortJobFirst()
    sorted_pods = sjf_sorter.sort(e)
    
    assert [pod.name for pod in sorted_pods] == ["p2", "p1", "p3"]