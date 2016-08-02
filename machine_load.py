#!/usr/bin/python
# coding=utf-8
# Copyright 2016 PingAn Cloud Branch
# All Rights Reserved.
# Author  : Kang Xiaoning
# Date    : August, 2016

import salt.client
from concurrent.futures import ProcessPoolExecutor
from operator import itemgetter

# get info by shell command
cmd_for_mem = """ free | awk 'FNR == 3 {printf("%.2f\t%d",
                    $3/($3+$4), ($3+$4)/1024/1024)}' """
cmd_for_cpu = " vmstat | awk 'NR == 3 {print $15}' "


def cmd(*args, **kwargs):
    local = salt.client.LocalClient()
    return local.cmd(*args, **kwargs)


def get_load():
    local = salt.client.LocalClient()
    with ProcessPoolExecutor(max_workers=5) as pool:
        cpu_result = pool.submit(cmd, '*', 'cmd.run', [cmd_for_cpu])
        mem_result = pool.submit(cmd, '*', 'cmd.run', [cmd_for_mem])
        serial_number_info = pool.submit(cmd, '*', 'grains.item', ['serialnumber'])
        cpu_result = cpu_result.result()
        mem_result = mem_result.result()
        serial_number_info = serial_number_info.result()
    ret = []
    for host in cpu_result:
        cpu_usage = 1 - float(cpu_result.get(host, 0))/100
        serial_number = serial_number_info.get(host).get('serialnumber')
        mem_info = mem_result.get(host)
        mem_usage, mem_total = mem_info.split()
        ret.append([host,
                    serial_number,
                    mem_total,
                    float(cpu_usage),
                    float(mem_usage)]
                   )
    return ret

if __name__ == '__main__':
    data = sorted(get_load(), key=itemgetter(3, 4), reverse=True)
    print ('{0:15}{1:16}{2:15}{3:12}{4:12}'.format('Host_name',
                                                  'Serial_Number',
                                                  'Mem_Total',
                                                  'Cpu_Use%',
                                                  'Mem_Use%'))
    for d in data:
        print ('{0:15}{1:16}{2:15}{3:<12.2%}{4:<12.2%}'.format(*d))
