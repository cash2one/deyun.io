# -*- coding: utf-8 -*-
'''
Created on 2016-8-2
@author: hustcc
'''
import paramiko
import StringIO
import re


def ssh_log_success(log, fail_regex='.*(fail|error|0)$'):
    matchObj = re.match(fail_regex, log, re.M | re.I | re.S)
    if matchObj:
        return False
    return True


# ssh to exec cmd
def do_ssh_cmd(ip, port, account, pkey, shell, push_data='', timeout=300):
    try:
        port = int(port)
    except:
        port = 22

    pkey = pkey.strip() + '\n'  # 注意最后有一个换行

    pkey_file = StringIO.StringIO(pkey)
    private_key = paramiko.RSAKey.from_private_key(pkey_file)

    s = paramiko.SSHClient()

    s.load_system_host_keys()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    s.connect(ip, port, account, pkey=private_key)
#     if push_data:
#     shell = shell + (" '%s'" % push_data)
    shell = shell.split('\n')
    shell = [sh for sh in shell if sh.strip()]
    shell = ' && '.join(shell)

    stdin, stdout, stderr = s.exec_command(shell, timeout=timeout)

    out = stdout.read()
    err = stderr.read()

    log = '%s%s' % (out, err)  # log
    success = True

    s.close()
    pkey_file.close()

    if success:
        success = ssh_log_success(log)

    return success, log
