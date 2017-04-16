# -*- coding:utf-8 -*-

import subprocess
import os
import re
import datetime
import sys
import logging
import hashlib
import zipfile
from logging.handlers import RotatingFileHandler
import shutil
import time
import random
import pickle
import socket

import requests

LOG = logging.getLogger(__name__)


def get_vmagent_zip_path():
    if is_windows():
        return r'C:\Windows\Cloudtools\vmagent\vmagent.zip'
    else:
        return '/opt/cloud/vmagent/vmagent.zip'


def get_monitor_script_path():
    if is_windows():
        return r'C:\Windows\Cloudtools\vmagent\monitor.py'
    else:
        return '/opt/cloud/vmagent/monitor.py'


def get_file_path(name):
    if name == 'vmagent':
        return get_vmagent_zip_path()
    elif name == 'monitor':
        return get_monitor_script_path()


def get_user_data():
    if is_windows():
        return r'C:\Windows\Cloudtools\scripts\user-data'
    else:
        return '/opt/cloud/scripts/user-data'


# TODO： 待实现运行powershell的函数



def setup_log():
    """Configure LOG"""

    # 日志记录到文件
    log_file = os.path.join(os.path.dirname(get_vmagent_zip_path()),
                            'monitor.log')
    file_handler = RotatingFileHandler(log_file,
                                       maxBytes=10 * 1024 * 1024,
                                       backupCount=3)
    file_handler.setLevel(logging.DEBUG)
    fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt, datefmt)
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(logging.DEBUG)


def is_windows():
    '''
    Simple function to return if a host is Windows or not
    '''
    return sys.platform.startswith('win')


def download_file(file_name, dst):
    user_data = get_user_data()
    prefix = 'pkgServer:'
    port = 8080
    path = 'vmagent'
    pkg_server_ip = '0.0.0.0'
    with open(user_data) as data:
        for line in data:
            if line.startswith(prefix):
                pkg_server_ip = line.split(":")[1].strip()
                LOG.info('Pkg server ip: %s', pkg_server_ip)
                break
    pkg_server = 'http://{0}:{1}'.format(pkg_server_ip, port)
    file_url = pkg_server + '/' + path + '/' + file_name
    LOG.info('file url: %s', file_url)
    try:
        resp = requests.get(file_url)
        if resp.status_code == 200:
            with open(dst, 'wb') as f:
                f.write(resp.content)
            LOG.info('Download %s successfully', file_name)
        else:
            raise resp.raise_for_status()
    except Exception as e:
        LOG.exception('Download %s failed', file_name)
        sys.exit(-1)


def _shell(command):
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output, error = process.communicate()
    if error and 'No Instance(s) Available.' not in error:
        raise RuntimeError(error)
    return output


def get_pid(name):
    """get pid of process which commandline contain name"""
    GET_PID_FOR_WIN = """wmic process where "commandline like '%vmagent/{0}%' and""" \
                      """ name='python.exe'" get processid /value"""
    # 不加grep -v out的话会有2进程
    GET_PID_FOR_LINUX = "ps -ef|grep -v grep|grep vmagent/{0}|grep -v out|grep python|awk '{{print $2}}'"
    if is_windows():
        command = GET_PID_FOR_WIN.format(name)
    else:
        command = GET_PID_FOR_LINUX.format(name)
    try:
        output = _shell(command)
    except Exception:
        LOG.exception('Execute %s failed', command)
        sys.exit(1)
    # make sure output only contain pid and space(\r\n)
    output = re.sub('ProcessId=', '', output)
    pid = output.split()
    return pid


def is_self_running():
    if is_windows():
        pattern = os.path.abspath(__file__).replace('\\', '\\\\')
    else:
        pattern = os.path.abspath(__file__)
    pid = get_pid(pattern)
    if not pid or len(pid) == 1:
        return False
    elif len(pid) == 2:
        LOG.info('%s is running, pid: %s', pattern, pid[0])
        return True


def is_agent_running():
    try:
        client = socket.socket()
        client.connect(('127.0.0.1', 15086))
        client.sendall('Monitor')
        response = client.recv(1024)
        client.close()
        if response == 'ACK':
            return True
        else:
            return False
    except Exception:
        LOG.info('agent not running')
        return False


def is_upgrade_time(start, end):
    """
    Return true if now is in the range [start, end]
    Example:
        start = datetime.time(22, 0)
        end = datetime.time(2, 0)
        is_upgrade_time(start, end)
    """
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end


check_record = os.path.join(os.path.dirname(get_monitor_script_path()),
                            '.check.pk')


def update_check_record():
    with open(check_record, 'w') as f:
        update_time = datetime.datetime.now()
        pickle.dump(update_time, f)
        LOG.info('update check record: %s', update_time)


def have_checked_today():
    now = datetime.datetime.now()
    if os.path.exists(check_record):
        with open(check_record) as f:
            last_check_time = pickle.load(f)
        if last_check_time.date() == now.date():
            return True
        else:
            return False
    else:
        return False


def checksum_md5(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def has_new_version(name):
    version_file = name + '.md5'
    version_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                version_file)
    try:
        sleep_seconds = gen_random_seconds(1, 60 * 5)
        LOG.info('get %s from remote server after %s seconds', version_file,
                 sleep_seconds)
        time.sleep(sleep_seconds)
        download_file(version_file, version_path)
    except Exception:
        msg = 'Download {0} from pkg server failed'.format(version_file)
        LOG.exception(msg)
        sys.exit(-1)
    current_version = checksum_md5(get_file_path(name))
    with open(version_path) as f:
        remote_version = f.read().strip()
    LOG.info('current version: %s, remote version: %s',
             current_version, remote_version)
    return current_version != remote_version


def kill_process(pid):
    if is_windows():
        command = 'taskkill /F /T /PID {pid}'.format(pid=pid)
    else:
        command = 'kill -9 {pid}'.format(pid=pid)
    try:
        _shell(command)
        LOG.info('%s killed', pid)
    except Exception:
        LOG.exception('kill %s failed', pid)


def download_agent():
    agent_file = 'vmagent.zip'
    agent_zip_path = get_vmagent_zip_path()
    backup = agent_zip_path + '.bak'
    if os.path.exists(agent_zip_path):
        os.rename(agent_zip_path, backup)
        LOG.info('backup %s to %s', agent_zip_path, backup)
    try:
        download_file(agent_file, agent_zip_path)
    except Exception as e:
        if os.path.exists(backup):
            os.rename(backup, agent_zip_path)
            LOG.info('restore %s to %s', backup, agent_zip_path)
        raise e


def download_monitor():
    monitor_script = 'monitor.py'
    monitor_script_path = get_monitor_script_path()
    backup = monitor_script_path + '.bak'
    if os.path.exists(monitor_script_path):
        os.rename(monitor_script_path, backup)
        LOG.info('backup %s to %s', monitor_script_path, backup)
    try:
        download_file(monitor_script, monitor_script_path)
    except Exception as e:
        if os.path.exists(backup):
            os.rename(backup, monitor_script_path)
            LOG.info('restore %s to %s', backup, monitor_script_path)
        raise e


def kill_agent():
    if is_agent_running():
        pid = int(get_pid('agent.py')[0])
        LOG.info('agent is running, pid: %s', pid)
        kill_process(pid)
    if not is_agent_running():
        LOG.info('agent is killed')
    else:
        msg = 'kill agent failed'
        LOG.info(msg)
        raise RuntimeError(msg)


def unzip_agent():
    agent_zip_path = get_vmagent_zip_path()
    agent_dir = os.path.join(os.path.dirname(agent_zip_path), 'vmagent')
    LOG.info('agent directory: %s', agent_dir)
    if os.path.exists(agent_dir):
        shutil.rmtree(agent_dir)
    target_dir = os.path.dirname(agent_zip_path)
    zip = zipfile.ZipFile(agent_zip_path)
    zip.extractall(target_dir)
    LOG.info('extract %s complete', agent_zip_path)


def try_get_server_ip_and_uuid():
    cwd = os.path.dirname(get_user_data())
    if is_windows():
        pass  # TODO
    else:
        func = os.path.join(cwd, 'func.sh')
        init_func = 'source {func}'.format(func=func)
        server_ip = 'ip=$(getServerIp vmagentServer);echo $ip'
        uuid = 'uuid=$(getVmUUid);echo $uuid'
        server_ip_cmd = ';'.join([init_func, server_ip])
        uuid_cmd = ';'.join([init_func, uuid])
        ip, error = _shell_ignore_error(server_ip_cmd, cwd=cwd)
        if ip:
            try:
                server_ip = ip.split()[0]
            except Exception:
                server_ip = None
        else:
            server_ip = None
        id, error = _shell_ignore_error(uuid_cmd, cwd=cwd)
        if id:
            try:
                uuid = id.split()[0]
            except Exception:
                uuid = None
        else:
            uuid = None
        if server_ip and uuid:
            return server_ip, uuid
        else:
            return None, None


def get_server_ip_and_uuid():
    init_data = os.path.join(os.path.dirname(get_user_data()),
                             '.init.dat')
    if os.path.exists(init_data):
        with open(init_data) as f:
            data = pickle.load(f)
        server_ip = data.get('server_ip')
        uuid = data.get('uuid')
        if server_ip and uuid:
            return server_ip, uuid
        server_ip, uuid = try_get_server_ip_and_uuid()
        if server_ip and uuid:
            return server_ip, uuid
        else:
            LOG.error('no server ip and uuid, can not start agent')
            sys.exit(-1)
    else:
        server_ip, uuid = try_get_server_ip_and_uuid()
        if server_ip and uuid:
            return server_ip, uuid
        LOG.error('no server ip and uuid, can not start agent')
        sys.exit(-1)


def is_agent_starting():
    init_data = os.path.join(os.path.dirname(get_vmagent_zip_path()),
                             '.init.dat')
    if not os.path.exists(init_data):
        return False
    with open(init_data) as f:
        data = pickle.load(f)
    lock_status = data.get('lock')
    if lock_status == 'locked':
        return True
    return False


def _shell_ignore_error(command, cwd=None):
    os_env = os.environ.copy()
    if is_windows():
        pass
    else:
        os_env['PATH'] += ':/usr/local/sbin:/usr/local/bin:/sbin:/usr/sbin:'
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=os_env
    )
    output, error = process.communicate()
    cmd = 'env'
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=os_env
    )
    o, e = p.communicate()
    LOG.info('out: %s, err: %s', o, e)
    LOG.info('os env: %s', os_env)
    return output, error


def start_agent():
    cwd = os.path.dirname(get_vmagent_zip_path())

    server_ip, uuid = get_server_ip_and_uuid()

    if is_windows():
        command = r'start /b python vmagent/agent.py {server_ip} {uuid}'.format(
            server_ip=server_ip, uuid=uuid)
    else:
        command = 'nohup python vmagent/agent.py {server_ip} {uuid}' \
                  ' > vmagent.out 2>&1 &'.format(server_ip=server_ip,
                                                 uuid=uuid)
    try:
        LOG.info('start agent command: %s', command)
        if is_windows():
            os.system(command)
            time.sleep(2)
            if is_agent_running():
                LOG.info('start agent successfully')
        else:
            output, error = _shell_ignore_error(command, cwd=cwd)
            time.sleep(2)
            if is_agent_running():
                LOG.info('start agent successfully')
            else:
                LOG.info('start agent failed')
            if error:
                LOG.info('start agent has error:\n %s', error)
            if output:
                LOG.info('start agent has output:\n %s', output)
    except Exception as e:
        raise e


def upgrade(name):
    LOG.info('upgrade %s start', name)
    is_successful = False
    retry_count = 3
    retry_number = 1
    while retry_number <= retry_count and not is_successful:
        try:
            LOG.info('retry number: %s', retry_number)
            if name == 'vmagent':
                download_agent()
                kill_agent()
                unzip_agent()
                start_agent()
                time.sleep(2)
                if is_agent_running():
                    update_check_record()
                    is_successful = True
            elif name == 'monitor':
                download_monitor()
                update_check_record()
                is_successful = True
            LOG.info('upgrade %s successful', name)
        except Exception:
            LOG.exception('upgrade %s failed', name)
        retry_number += 1


def try_start_agent():
    """尝试启动3次，如果vmagent正在启动中，每次启动最多等待5*62秒后放弃"""
    is_successful = False
    retry_count = 3
    retry_number = 1
    while retry_number <= retry_count and not is_successful:
        LOG.info('retry number: %s', retry_number)
        try:
            sleep_time = 0
            while sleep_time <= 62:
                if sleep_time == 62:
                    LOG.info('reach the maximum sleep time, give up start')
                    break
                if not is_agent_starting():
                    start_agent()
                    break
                time.sleep(5)
                sleep_time += 1
            time.sleep(2)
            if is_agent_running():
                is_successful = True
        except Exception:
            LOG.info('start agent failed')
        retry_number += 1


def gen_random_seconds(sleep_min, sleep_max):
    sleep_seconds = random.randint(sleep_min, sleep_max)
    return sleep_seconds


def check_agent():
    if is_agent_running():
        LOG.info('normal exit due to agent is running')
        sys.exit(0)
    elif is_agent_starting():
        LOG.info('normal exit due to agent is starting')
        sys.exit(0)
    else:
        LOG.info('try start agent')
        try_start_agent()


def check():
    base_dir = os.path.dirname(get_vmagent_zip_path())
    os.chdir(base_dir)
    start = datetime.time(3, 0)
    end = datetime.time(6, 0)
    setup_log()
    if is_self_running():
        LOG.info('normal exit due to self is running')
        sys.exit(0)
    # 如果vmagent目录不存在则升级，确保初始化失败的情况下vmagent能启动
    vmagent_zip = get_vmagent_zip_path()
    vmagent_dir = os.path.join(os.path.dirname(vmagent_zip), 'vmagent')
    if not os.path.exists(vmagent_dir):
        upgrade('vmagent')
    # 一天检测一次版本
    if not have_checked_today() and is_upgrade_time(start, end):
        LOG.info('now in the upgrade time period, between %s and %s',
                 str(start), str(end))
        if has_new_version('vmagent'):
            sleep_seconds = gen_random_seconds(1, 60 * 30)
            LOG.info(
                'found a new version, upgrade agent start after %s seconds',
                sleep_seconds)
            time.sleep(sleep_seconds)
            upgrade('vmagent')
        elif has_new_version('monitor'):
            sleep_seconds = gen_random_seconds(1, 60 * 5)
            LOG.info(
                'found a new version, upgrade monitor start after %s seconds',
                sleep_seconds)
            time.sleep(sleep_seconds)
            upgrade('monitor')
        else:
            LOG.info('no new version')
            update_check_record()
            check_agent()
    else:
        check_agent()


if __name__ == '__main__':
    check()
