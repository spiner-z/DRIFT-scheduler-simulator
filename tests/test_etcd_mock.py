from simulator.models.etcd_mock import EtcdMock
from simulator.models.node import Node
from simulator.models.pod import Pod

def test_gpu_packing_prefer_fuller_single_gpu():
    e = EtcdMock()
    n = Node(name="n1", cpu_milli_total=32000, memory_mib_total=131072, gpu_count=2, gpu_share_enabled=True)
    e.add_node(n)

    # p1 先放到 gid=0（tie-break），gpu0: 600 free, gpu1: 1000 free
    e.add_pod(Pod(name="p1", cpu_milli=500, memory_mib=256, num_gpu=1, gpu_milli=400))
    e.bind("p1", "n1")
    assert e.pods["p1"].gpu_alloc == {0: 400}
    assert e.nodes["n1"].gpu_free_milli == [600, 1000]
    assert e.nodes["n1"].cpu_milli_free == 32000 - 500
    assert e.nodes["n1"].memory_mib_free == 131072 - 256

    # p2 (200) 应优先放到更满的 gpu0，而不是 gpu1
    e.add_pod(Pod(name="p2", cpu_milli=500, memory_mib=256, num_gpu=1, gpu_milli=200))
    e.bind("p2", "n1")
    assert e.pods["p2"].gpu_alloc == {0: 200}
    assert e.nodes["n1"].gpu_free_milli == [400, 1000]

    # p3 (700) 放不进 gpu0(400)，应放 gpu1
    e.add_pod(Pod(name="p3", cpu_milli=500, memory_mib=256, num_gpu=1, gpu_milli=700))
    e.bind("p3", "n1")
    assert e.pods["p3"].gpu_alloc == {1: 700}
    assert e.nodes["n1"].gpu_free_milli == [400, 300]

    # 索引一致性
    assert e.node_of_pod("p1") == "n1"
    assert e.node_of_pod("p2") == "n1"
    assert e.node_of_pod("p3") == "n1"
    assert e.pods_on_node("n1") == {"p1", "p2", "p3"}


def test_gpu_packing_prefer_fuller_multi_gpu():
    e = EtcdMock()
    n = Node(name="n2", cpu_milli_total=32000, memory_mib_total=131072, gpu_count=4, gpu_share_enabled=True)
    e.add_node(n)

    # 通过一系列绑定制造不同 GPU “满度”
    # a: gid=0 -> free 100
    e.add_pod(Pod(name="a", cpu_milli=100, memory_mib=64, num_gpu=1, gpu_milli=900))
    e.bind("a", "n2")
    # b: best-fit 会选 gid=0(100 free) -> free 0
    e.add_pod(Pod(name="b", cpu_milli=100, memory_mib=64, num_gpu=1, gpu_milli=100))
    e.bind("b", "n2")
    # c: 500 -> gid=1 -> free 500
    e.add_pod(Pod(name="c", cpu_milli=100, memory_mib=64, num_gpu=1, gpu_milli=500))
    e.bind("c", "n2")
    # d: 300 -> best-fit 选 gid=1(500) -> free 200
    e.add_pod(Pod(name="d", cpu_milli=100, memory_mib=64, num_gpu=1, gpu_milli=300))
    e.bind("d", "n2")
    # e: 500 -> gid=2 -> free 500
    e.add_pod(Pod(name="e", cpu_milli=100, memory_mib=64, num_gpu=1, gpu_milli=500))
    e.bind("e", "n2")
    # f: 300 -> gid=2(500) -> free 200
    e.add_pod(Pod(name="f", cpu_milli=100, memory_mib=64, num_gpu=1, gpu_milli=300))
    e.bind("f", "n2")

    assert e.nodes["n2"].gpu_free_milli == [0, 200, 200, 1000]

    # p 需要 2 张 GPU，每张 200
    # eligible: gid=1(200), gid=2(200), gid=3(1000)
    # best-fit 应选 gid=1 和 gid=2（更满）
    e.add_pod(Pod(name="p", cpu_milli=100, memory_mib=64, num_gpu=2, gpu_milli=200))
    e.bind("p", "n2")
    assert e.pods["p"].gpu_alloc == {1: 200, 2: 200}
    assert e.nodes["n2"].gpu_free_milli == [0, 0, 0, 1000]


def test_no_gpu_sharing_one_pod_per_gpu():
    e = EtcdMock()
    n = Node(name="n3", cpu_milli_total=32000, memory_mib_total=131072, gpu_count=1, gpu_share_enabled=False)
    e.add_node(n)

    e.add_pod(Pod(name="p1", cpu_milli=500, memory_mib=256, num_gpu=1, gpu_milli=200))
    e.bind("p1", "n3")
    assert e.pods["p1"].gpu_alloc == {0: 200}
    assert len(e.nodes["n3"].gpu_pods[0]) == 1
    assert "p1" in e.nodes["n3"].gpu_pods[0]

    # 同一张 GPU 即使还有 milli，也不允许再绑定第二个 pod
    e.add_pod(Pod(name="p2", cpu_milli=500, memory_mib=256, num_gpu=1, gpu_milli=200))
    try:
        e.bind("p2", "n3")
        assert False, "should have raised ValueError when gpu_share_enabled=False"
    except ValueError:
        pass


def test_unbind_restores_all_resources_and_indices():
    e = EtcdMock()
    n = Node(name="n4", cpu_milli_total=32000, memory_mib_total=131072, gpu_count=2, gpu_share_enabled=True)
    e.add_node(n)

    e.add_pod(Pod(name="p1", cpu_milli=1500, memory_mib=1024, num_gpu=1, gpu_milli=300))
    e.bind("p1", "n4")

    # bind 后检查
    assert e.pods["p1"].bound_node == "n4"
    assert e.node_of_pod("p1") == "n4"
    assert "p1" in e.pods_on_node("n4")
    assert e.nodes["n4"].cpu_milli_free == 32000 - 1500
    assert e.nodes["n4"].memory_mib_free == 131072 - 1024
    assert sum(e.nodes["n4"].gpu_free_milli) == 2000 - 300

    alloc_before = dict(e.pods["p1"].gpu_alloc)
    free_before = e.nodes["n4"].gpu_free_milli.copy()

    e.unbind("p1")

    # unbind 后检查 pod 状态
    assert e.pods["p1"].bound_node is None
    assert e.pods["p1"].gpu_alloc == {}

    # 资源恢复
    assert e.nodes["n4"].cpu_milli_free == 32000
    assert e.nodes["n4"].memory_mib_free == 131072
    assert e.nodes["n4"].gpu_free_milli == [1000, 1000]

    # 索引一致性
    assert e.node_of_pod("p1") is None
    assert "p1" not in e.pods_on_node("n4")

    # 确认确实发生过变化（不是空测）
    assert alloc_before != {}
    assert free_before != [1000, 1000]
