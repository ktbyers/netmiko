'''
Requires paramiko >=1.8.0 (paramiko had an issue with multiprocessing prior
to this)

Example code showing how to use netmiko for multiprocessing.  Create a
separate process for each ssh connection.  Each subprocess executes a
'show version' command on the remote device.  Use a multiprocessing.queue to
pass data from subprocess to parent process.

Only supports Python2
'''

# Catch Paramiko warnings about libgmp and RandomPool
import warnings
with warnings.catch_warnings(record=True) as w:
    import paramiko

import multiprocessing
import time
from datetime import datetime

import netmiko
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException

# DEVICE_CREDS contains the devices to connect to
from DEVICE_CREDS import all_devices


def print_output(results):
    
    print "\nSuccessful devices:"
    for a_dict in results:
        for identifier,v in a_dict.iteritems():
            (success, out_string) = v
            if success:
                print '\n\n'
                print '#' * 80
                print 'Device = {0}\n'.format(identifier)
                print out_string
                print '#' * 80

    print "\n\nFailed devices:\n"
    for a_dict in results:
        for identifier,v in a_dict.iteritems():
            (success, out_string) = v
            if not success:
                print 'Device failed = {0}'.format(identifier)

    print "\nEnd time: " + str(datetime.now())
    print


def worker_show_version(a_device, mp_queue):
    '''
    Return a dictionary where the key is the device identifier
    Value is (success|fail(boolean), return_string)
    '''    

    try:
        a_device['port']
    except KeyError:
        a_device['port'] = 22

    identifier = '{ip}:{port}'.format(**a_device)
    return_data = {}

    show_ver_command = 'show version'
    SSHClass = netmiko.ssh_dispatcher(a_device['device_type'])

    try:
        net_connect = SSHClass(**a_device)
        show_version = net_connect.send_command(show_ver_command)
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        return_data[identifier] = (False, e)

        # Add data to the queue (for parent process)
        mp_queue.put(return_data)
        return None

    return_data[identifier] = (True, show_version)
    mp_queue.put(return_data)


def main():
    mp_queue = multiprocessing.Queue()
    processes = []

    print "\nStart time: " + str(datetime.now())

    for a_device in all_devices:
        p = multiprocessing.Process(target=worker_show_version, args=(a_device, mp_queue))
        processes.append(p)
        # start the work process
        p.start()

    # retrieve all the data from the queue
    results = []
    while any(p.is_alive() for p in processes):
        time.sleep(0.1)
        while not mp_queue.empty():
            results.append(mp_queue.get())
            
    # wait until the child processes have completed
    for p in processes:
        p.join()

    print_output(results)

    
if __name__ == '__main__':
    main()
