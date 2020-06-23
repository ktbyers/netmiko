#!/usr/bin/env python
"""
Use processes and Netmiko to connect to each of the devices. Execute
'show version' on each device. Use a queue to pass the output back to the parent process.
Record the amount of time required to do this.
"""
from __future__ import print_function, unicode_literals
from multiprocessing import Process, Queue

from datetime import datetime
from netmiko import ConnectHandler
from my_devices import device_list as devices


def show_version_queue(a_device, output_q):
    """
    Use Netmiko to execute show version. Use a queue to pass the data back to
    the main process.
    """
    output_dict = {}
    remote_conn = ConnectHandler(**a_device)
    hostname = remote_conn.base_prompt
    output = ("#" * 80) + "\n"
    output += remote_conn.send_command("show version") + "\n"
    output += ("#" * 80) + "\n"
    output_dict[hostname] = output
    output_q.put(output_dict)


def main():
    """
    Use processes and Netmiko to connect to each of the devices. Execute
    'show version' on each device. Use a queue to pass the output back to the parent process.
    Record the amount of time required to do this.
    """
    start_time = datetime.now()
    output_q = Queue(maxsize=20)

    procs = []
    for a_device in devices:
        my_proc = Process(target=show_version_queue, args=(a_device, output_q))
        my_proc.start()
        procs.append(my_proc)

    # Make sure all processes have finished
    for a_proc in procs:
        a_proc.join()

    while not output_q.empty():
        my_dict = output_q.get()
        for k, val in my_dict.items():
            print(k)
            print(val)

    print("\nElapsed time: " + str(datetime.now() - start_time))


if __name__ == "__main__":
    main()
