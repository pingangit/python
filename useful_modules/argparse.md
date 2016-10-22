argparse 简单使用
================

        练习 argparse 用法，从命令行获取参数值，并将值应用到具体函数中，可对命令行参数数据类型进行约束。
# 1. 实现tail命令的Python脚本
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
2. 测试
```bash
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
