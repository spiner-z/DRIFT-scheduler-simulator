from simulator.models.etcd_mock import EtcdMock
from simulator.models.pod import Pod, PodStatus
from simulator.models.node import Node
from simulator.models.event import Event, EventType
from simulator.plugins.interface import QueueSortPlugin, FilterPlugin, ScorePlugin
from simulator.utils.logger import logger
import heapq
from typing import List

class Scheduler:
    def __init__(
        self,
        nodes: List[Node],
        pods: List[Pod],
        queue_sorter: QueueSortPlugin,
        filter_plugin: FilterPlugin,
        score_plugin: ScorePlugin,
    ):
        self.nodes = nodes
        self.all_pods = pods
        self.queue_sorter = queue_sorter
        self.filter_plugin = filter_plugin
        self.score_plugin = score_plugin
        
        self.etcd = EtcdMock()
        self.etcd.add_nodes(nodes)

        self.current_time: int = 0
        self._event_heap: List[Event] = []
        self._event_seq: int = 0  # 保证堆中事件稳定顺序

    def _push_event(self, time: int, etype: EventType, pod: Pod):
        self._event_seq += 1
        heapq.heappush(self._event_heap, Event(time=time, order=self._event_seq, type=etype, pod=pod))

    def initialize_events(self):
        if not self.all_pods:
            return
        # 将所有 Pod 的到达事件加入堆
        for p in self.all_pods:
            self._push_event(p.creation_time, EventType.ARRIVAL, p)
        self.current_time = 0
    
    def _try_schedule_loop(self) -> bool:
        """尝试调度 pending 列表中的 Pod。
        返回：本轮是否至少成功调度了一个 Pod。
        """
        scheduled_any = False

        # queueSort
        queue = self.queue_sorter.sort(self.etcd)

        for pod in queue:
            # filter
            feas = self.filter_plugin.filter(pod, e=self.etcd)

            if not feas:
                continue # 无可行节点，尝试下一个 Pod
            
            # score
            target = self.score_plugin.pick(pod, feas, self.etcd)
            if target is None:
                continue # 无法选出节点，尝试下一个 Pod

            # bind
            self.etcd.bind(pod.name, target.name, self.current_time)
            self._push_event(pod.scheduled_time + pod.duration, EventType.COMPLETION, pod)
            # logger.info(f'Time {self.current_time}: Pod {pod.name} scheduled to Node {pod.bound_node}.')
            scheduled_any = True

        return scheduled_any
    
    def run(self):
        self.initialize_events()

        while self._event_heap:
            ev = heapq.heappop(self._event_heap)
            self.current_time = ev.time

            if ev.type == EventType.ARRIVAL:
                assert ev.pod.status == PodStatus.Pending
                # logger.info(f'Time {self.current_time}: Pod {ev.pod.name} arrived.')
                self.etcd.add_pod(ev.pod)
            elif ev.type == EventType.COMPLETION:
                # Pod 完成：释放资源
                pod = ev.pod
                assert pod.status == PodStatus.Running
                node_name = pod.bound_node
                self.etcd.unbind(pod.name) # todo: reschedule
                # logger.info(f'Time {self.current_time}: Pod {pod.name} completed and released from node {node_name}.')

            # 每个事件后尝试调度尽可能多的 Pending Pod
            scheduled = True
            while scheduled:
                scheduled = self._try_schedule_loop()

        self.report()

    def _show_event_heap(self):
        print(f"Event Heap at time {self.current_time}:")
        for event in self._event_heap:
            print(event)
        print("End of Event Heap\n")

    def report(self):
        makespan = self.current_time
        completed_pods_count = len(self.etcd.completed_pods)
        cpu_used_time = 0
        gpu_used_time = 0
        for pod_name in self.etcd.completed_pods:
            pod = self.etcd.get_pod(pod_name)
            cpu_used_time += pod.cpu_milli * pod.duration
            gpu_used_time += pod.num_gpu * pod.gpu_milli * pod.duration
        total_cpu_used_time = makespan * self.etcd.get_total_cpu_milli()
        total_gpu_used_time = makespan * self.etcd.get_total_gpu_milli()
        cpu_utilization = cpu_used_time / total_cpu_used_time if total_cpu_used_time > 0 else 0
        gpu_utilization = gpu_used_time / total_gpu_used_time if total_gpu_used_time > 0 else 0
        print(f"Total makespan: {makespan} seconds")
        print(f"Scheduling {len(self.all_pods)} pods in {len(self.nodes)} nodes")
        print(f"Total completed pods: {completed_pods_count} / {len(self.all_pods)}")
        print(f"CPU Utilization: {cpu_utilization*100:.2f}%")
        print(f"GPU Utilization: {gpu_utilization*100:.2f}%")
        print()

                

                





