# -*- coding: utf-8 -*-
#
# kangxiaoning495
#

import re

file_name = 'UCloud.txt'

cnt = 0

with open(file_name, 'r') as f:
    for line in f:
        match = re.findall(r'UCanUup', line)
        cnt += len(match)
    print cnt

