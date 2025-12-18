from simulator.models.etcd_mock import EtcdMock
from simulator.models.node import Node
from simulator.models.pod import Pod, PodStatus
from simulator.plugins.score.k8s import ScoreKubernetes
from simulator.plugins.score.binpack import ScoreBinPack
from simulator.plugins.score.drift import ScoreDrift
from simulator.models.resource import get_target_pod_list_from_pods

def test_score_kubernetes():
    e = EtcdMock()
    n1 = Node(name="n1", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=True)
    n2 = Node(name="n2", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=1, gpu_share_enabled=False)
    e.add_node(n1)
    e.add_node(n2)
    
    p1 = Pod(name="p1", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=1, duration=10)
    p2 = Pod(name="p2", cpu_milli=1500, memory_mib=2048, num_gpu=1, gpu_milli=500, creation_time=2, duration=10)
    e.add_pod(p1)
    e.add_pod(p2)
    e.bind("p2", "n2")
    
    scorer = ScoreKubernetes()

    assert scorer.score(p1, n1, e) == 100
    assert scorer.score(p1, n2, e) == 50
    assert scorer.pick(p1, [n1, n2], e) == n1

def test_score_binpack():
    e = EtcdMock()
    n1 = Node(name="n1", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=True)
    n2 = Node(name="n2", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=False)
    e.add_node(n1)
    e.add_node(n2)
    
    p1 = Pod(name="p1", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=1, duration=10)
    p2 = Pod(name="p2", cpu_milli=200, memory_mib=2048, num_gpu=1, gpu_milli=500, creation_time=2, duration=10)
    e.add_pod(p1)
    e.add_pod(p2)
    e.bind("p2", "n2")
    
    scorer = ScoreBinPack()

    assert scorer.score(p1, n1, e) == 0
    assert scorer.score(p1, n2, e) == 50

def test_score_drift():
    e = EtcdMock()
    n1 = Node(name="n1", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=True)
    n2 = Node(name="n2", cpu_milli_total=2000, memory_mib_total=4096, gpu_count=4, gpu_share_enabled=False)
    e.add_node(n1)
    e.add_node(n2)
    
    p1 = Pod(name="p1", cpu_milli=500, memory_mib=1024, num_gpu=1, gpu_milli=1000, creation_time=1, duration=10)
    p2 = Pod(name="p2", cpu_milli=200, memory_mib=2048, num_gpu=1, gpu_milli=500, creation_time=2, duration=10)
    e.add_pod(p1)
    e.add_pod(p2)
    e.bind("p2", "n2")
    
    typical_pods = get_target_pod_list_from_pods([p1, p2])
    scorer = ScoreDrift(typical_pods)
    scorer.pick(p1, [n1, n2], e)

    


    