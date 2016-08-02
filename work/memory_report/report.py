#!/usr/bin/python
# coding=utf-8
# Author  : Kang Xiaoning
# Date    : August, 2016

import salt.client
import os, sys
from concurrent.futures import ProcessPoolExecutor
from operator import itemgetter
from collections import namedtuple, defaultdict

ClusterInfo = namedtuple('ClusterInfo', ['host_name', 'cluster_uuid', 'cluster_name'])
Free = namedtuple('Free', ['x', 'y', 'mem_used', 'mem_free', 'z', 'swap_total', 'swap_used', 'swap_free'])
cmd_for_mem = " free | tail -2 "


def _format_cluster_info(filename):
    cluster_file = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(cluster_file):
        print("Please make sure 'cluster.txt' is exist! ")
        sys.exit()
    d = defaultdict(list)
    with open(cluster_file, 'r') as cluster:
        for line in cluster:
            c = ClusterInfo(*line.split())
            d[c.host_name].append(c.cluster_uuid)
            d[c.host_name].append(c.cluster_name)
    return d


def cmd(*args, **kwargs):
    local = salt.client.LocalClient()
    return local.cmd(*args, **kwargs)


def memory_report(filename):
    cluster_info = _format_cluster_info(filename)
    with ProcessPoolExecutor(max_workers=5) as pool:
        mem_result = pool.submit(cmd, '*', 'cmd.run', [cmd_for_mem])
        assigned_mem = pool.submit(cmd, '*', fun='virt.freemem')
        vm_info = pool.submit(cmd, '*', 'virt.list_domains')
        mem_result = mem_result.result()
        vm_info = vm_info.result()
        assigned_mem = assigned_mem.result()
    ret = []
    for host in mem_result:
        free = Free(*mem_result.get(host).split())
        mem_total = round((int(free.mem_used) + int(free.mem_free))/1024/1024, 0)
        mem_free = round(float(free.mem_free)/1024/1024, 1)
        swap_total = round(float(free.swap_total)/1024/1024, 1)
        swap_free = round(float(free.swap_free)/1024/1024, 1)
        swap_used = round(float(free.swap_used)/1024/1024, 1)
        vm_count = len(vm_info.get(host))
        try:
            assigned_free = round(float(assigned_mem[host])/1024, 0)
        except Exception:
            assigned_free = 'error'
        cluster_uuid,cluster_name = [x for x in cluster_info.get(host, ['Null', 'Null'])]
        used_percent = round((float(mem_total) - float(mem_free))/mem_total, 1)
        ret.append([cluster_uuid,
                    cluster_name,
                    host,
                    mem_total,
                    vm_count,
                    mem_free,
                    used_percent,
                    assigned_free,
                    swap_total,
                    swap_free,
                    swap_used])
    return ret


if __name__ == '__main__':
    filename = 'cluster.txt'
    data = sorted(memory_report(filename), key=itemgetter(1, 5))
    print ('{0:37}{1:25}{2:12}{3:10}{4:7}{5:9}{6:7}{7:14}{8:11}{9:10}{10:12}'.format('Cluster_uuid',
                                                                                      'Cluster_name',
                                                                                      'Hostname',
                                                                                      'Total_Mem',
                                                                                      'VM_cnt',
                                                                                      'Free_mem',
                                                                                      'Use%',
                                                                                      'Assigned_Free',
                                                                                      'Total_swap',
                                                                                      'Free_swap',
                                                                                      'Used_swap'))
    for d in data:
        print ('{0:37}{1:25}{2:12}{3:<10}{4:<7}{5:<9}{6:<67.1%}{7:<14}{8:<11}{9:<10}{10:<12}'.format(*d))
