argparse 简单使用
================

        练习 argparse 用法，从命令行获取参数值，并将值应用到具体函数中，可对命令行参数数据类型进行约束。
# 1. 实现tail命令的Python脚本

        这里编写一个类似 tail 命令的脚本，当我们给出不同选项的时候做出不同的响应。
        要求：
            1. 不指定 -n 则默认显示文件后 5 行
            2. 如果指定了 -n 并且给定了正整数 N，则显示最后 N 行
            3. 如果 -n 后不是正整数，进行提示并退出
```python
#!/bin/env python

import sys
import argparse
from collections import deque

def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
         raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue

def get_last():
    """Returns the last n lines from the file."""
    parser = argparse.ArgumentParser(
        description="A command like tail on Linux.",
        epilog="""Example:
                    ./tail.py FILENAME -n N
               """
    )

    parser.add_argument('filename', help="Filename", action="store")
    parser.add_argument('-n', help="Number (default is 5)", type=positive_int, default=5)
    args = parser.parse_args()
    filename = args.filename
    n = args.n
    try:
        with open(filename) as f:
            lines = deque(f, n)
        for line in lines:
            print(line),
    except OSError:
        print("Error opening file: {}".format(filename))
        raise


if __name__ == '__main__':
    get_last()
```
# 2. 测试参数
        给定各种非法参数，测试结果显示 argparse 可以给出友好提示，默认支持 help 选项。还有很多
    其它选项，需要的时候查看文档即可。
    
```shell
[root@SZB-L0009803 py201]# ./tail.py -h
usage: tail.py [-h] [-n N] filename

A command like tail on Linux.

positional arguments:
  filename    Filename

optional arguments:
  -h, --help  show this help message and exit
  -n N        Number (default is 5)

Example: ./tail.py FILENAME -n N
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py --help
usage: tail.py [-h] [-n N] filename

A command like tail on Linux.

positional arguments:
  filename    Filename

optional arguments:
  -h, --help  show this help message and exit
  -n N        Number (default is 5)

Example: ./tail.py FILENAME -n N
[root@SZB-L0009803 py201]#
[root@SZB-L0009803 py201]# ./tail.py 
usage: tail.py [-h] [-n N] filename
tail.py: error: too few arguments
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py -n 'abc'
usage: tail.py [-h] [-n N] filename
tail.py: error: argument -n: invalid positive_int value: 'abc'
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py -n -1000
usage: tail.py [-h] [-n N] filename
tail.py: error: argument -n: -1000 is an invalid positive int value
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py -n 10
usage: tail.py [-h] [-n N] filename
tail.py: error: too few arguments
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py -n 10 install.log 
Installing iwl3945-firmware-15.32.2.9-4.el6.noarch
Installing ql2200-firmware-2.02.08-3.1.el6.noarch
Installing rt73usb-firmware-1.8-7.el6.noarch
Installing ipw2100-firmware-1.3-11.el6.noarch
Installing ipw2200-firmware-3.1-4.el6.noarch
Installing rootfiles-8.1-6.1.el6.noarch
Installing oraclelinux-release-notes-6Server-14.x86_64
Installing man-pages-3.22-20.el6.noarch
Installing words-3.0-17.el6.noarch
*** FINISHED INSTALLING PACKAGES ***
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py -n 'abc' install.log   
usage: tail.py [-h] [-n N] filename
tail.py: error: argument -n: invalid positive_int value: 'abc'
[root@SZB-L0009803 py201]# 
[root@SZB-L0009803 py201]# ./tail.py -n -1000 install.log        
usage: tail.py [-h] [-n N] filename
tail.py: error: argument -n: -1000 is an invalid positive int value
[root@SZB-L0009803 py201]# 
```

# 3. 实际使用
## 3.1 脚本
        从 ltm 的 bigip.conf 中提取需要的信息，指定文件名，指定多个 ssl profile 名字。
```python
#!/bin/env python
# -*- coding: utf-8 -*-

import textwrap
import re
import argparse


def _get_vs_by_ssl(ssl_profile, filename):
    print(ssl_profile)
    new_ssl_profile = '/Common/' + ssl_profile +' {'
    with open(filename) as conf:
        ret = []
        # 将配置文件转换为一行字符串
        bigip_conf = conf.read()
        # 提取 virtual_server 相关配置，每个 VS 是 list 中一个 item
        virtual_servers = re.findall(r'(ltm virtual /Common/.*?\n}\n)', bigip_conf, re.S)
        for vs in virtual_servers:
            if new_ssl_profile in vs and "context clientside" in vs:
                vs = vs.split()
                print('{0} {1} {2}'.format(ssl_profile, vs[2].strip('/Common/'),vs[5].strip('/Common/')))
                ret.append(vs)
        print("\nResult: {0} match '{1}' ssl profile count：{2}\n".format(filename, ssl_profile, len(ret)))


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     # 指定缩进格式
                                     description=textwrap.dedent("""
                                     Description:
                                       Get virtual server name、vip、ssl profile
                                       name from ltm bigip conf(default name is
                                       bigip.conf).
                                     """))
    parser.add_argument('filename',
                        action='store',
                        help='the name of bigip.conf'
                        )
    parser.add_argument('-s',
                        '--ssl_profile',
                        action='store',
                        default=[],
                        help='add ssl profile name split by space',
                        dest='ssl_profile',
                        required=True,
                        nargs='+')  # nargs 表示命令行参数可以出现的次数，这里表示多次
    args = parser.parse_args()
    filename = args.filename
    ssl_profile_list = args.ssl_profile
    print(filename)
    print(ssl_profile_list)
    for ssl_profile in ssl_profile_list:
        _get_vs_by_ssl(ssl_profile, filename)

if __name__ == '__main__':
    main()
```
## 3.2 使用

        可以按预期参数使用并得到结果。

```shell
[root@SZB-L0031511 bigip]# ./get_vip_by_ssl_v1.py lfa_dmz_bigip.conf -s dbo.com paic.com.cn dbo.com yun.dbo.com_2048_1116 all.stock.dbo.com all.yun.dbo.com_SSL_profile
dbo.com VS_PACLOUD_443_PRDR2016031405789 10.49.161.122:443

Result: lfa_dmz_bigip.conf match 'dbo.com' ssl profile count£º1


Result: lfa_dmz_bigip.conf match 'paic.com.cn' ssl profile count£º0


Result: lfa_dmz_bigip.conf match 'dbo.com' ssl profile count£º0


Result: lfa_dmz_bigip.conf match 'yun.dbo.com_2048_1116' ssl profile count£º0

all.stock.dbo.com VS_PACLOUD_443_PRDR2016042907546 10.49.161.188:443
all.stock.dbo.com VS_PACLOUD_443_STGR2016042907544 10.49.161.64:443

Result: lfa_dmz_bigip.conf match 'all.stock.dbo.com' ssl profile count£º2

all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016072800144 192.64.190.244:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2015120403490 10.49.161.250:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016072800133 192.64.190.129:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016072800134 192.64.190.60:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016072800135 192.64.190.254:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016072800136 192.64.190.154:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016072800137 192.64.190.192:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016031405770 10.49.161.26:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_PRDR2016071209500 10.49.161.139:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016071209539 192.64.190.53:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016072209921 192.64.190.142:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016072209915 192.64.190.215:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016072209918 192.64.190.164:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016072209919 192.64.190.128:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016070509415 192.64.190.184:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_443_STGR2016061608953 10.49.161.92:443
all.yun.dbo.com_SSL_profile VS_PACLOUD_5050_STGR2016072209920 192.64.190.142:5050
all.yun.dbo.com_SSL_profile VS_PACLOUD_5050_STGR2016072209872 192.64.190.184:5050
all.yun.dbo.com_SSL_profile VS_PACLOUD_8000_STGR2016072209870 192.64.190.184:8000
all.yun.dbo.com_SSL_profile VS_PACLOUD_9090_STGR2016072209871 192.64.190.184:9090

Result: lfa_dmz_bigip.conf match 'all.yun.dbo.com_SSL_profile' ssl profile count£º20

[root@SZB-L0031511 bigip]# ./get_vip_by_ssl_v1.py -h
usage: get_vip_by_ssl_v1.py [-h] -s SSL_PROFILE [SSL_PROFILE ...] filename

Description:
  Get virtual server name¡¢vip¡¢ssl profile
  name from ltm bigip conf(default name is
  bigip.conf).

positional arguments:
  filename              the name of bigip.conf

optional arguments:
  -h, --help            show this help message and exit
  -s SSL_PROFILE [SSL_PROFILE ...], --ssl_profile SSL_PROFILE [SSL_PROFILE ...]
                        add ssl profile name split by space
[root@SZB-L0031511 bigip]# cat main_v1.sh 
#!/bin/bash

for filename in $(ls *.conf)
do
    ./get_vip_by_ssl_v1.py $filename -s dbo.com paic.com.cn \
    dbo.com yun.dbo.com_2048_1116 all.stock.dbo.com all.yun.dbo.com_SSL_profile \
    any.4008000000.com dbo.com. www.4008000000.com mobile.health.dbo.com_SSL_Profile
    echo "---------------------------------------------------"
done
[root@SZB-L0031511 bigip]#
```