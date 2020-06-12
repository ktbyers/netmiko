#!/usr/bin/env python3
"""
This example is using Multithread Working Class.

The example based on: https://developer.ibm.com/articles/au-threadingpython/

There are some ways for concurrency:
- Multi-threading:
  - with a Worker class.    <-- this example about it.
  - with a Worker funcion.
- Multi-processing.

Docs for Python 3.6:
* Thread-based parallelism - https://docs.python.org/3.6/library/threading.html
* Queue - https://docs.python.org/3.6/library/queue.html
"""

# Netmiko is the same as ConnectHandler
import netmiko
# Need for multithreading
import threading
import queue
# Just for execution time evaluation
import time


time_start = time.time()

# Define all the Network Devices.
cisco1 = {
    "host": "172.31.31.2",
    "username": "cisco",
    "password": "cisco",
    "device_type": "cisco_ios_telnet",
}

cisco2 = {
    "host": "172.31.31.3",
    "username": "cisco",
    "password": "cisco",
    "device_type": "cisco_ios_telnet",
}

cisco3 = {
    "host": "172.31.31.4",
    "username": "cisco",
    "password": "cisco",
    "device_type": "cisco_ios_telnet",
}

# Create the list of the Network Devices.
list_netmiko_connection_data = [cisco1, cisco2, cisco3]

# Define the Worker Class.
class Worker(threading.Thread):
    """ The Thread class represents an activity that is run in a separate thread of control.
    Only override the __init__() and run() methods of this class."""
    
    def __init__(self, queue):
        """Initializaiont"""
        threading.Thread.__init__(self)
        self.queue = queue

    
    def run(self):
        """Run"""
        while True:
            # Wait until an item in the Queue is available
            # then get an item (data for connection) from the queue.
            netmiko_connection_data = self.queue.get()
            
            # Do something.
            net_connect = netmiko.ConnectHandler(**netmiko_connection_data)
            output = net_connect.send_command("sh ip int brief | i Loopback")
            net_connect.disconnect()
            print(output)

            # inform the queue that the task is complete.
            # i.e. that the item we got from the Queue was processed.
            self.queue.task_done()


# Define our queue of items - in our case this is a list of devices we should process.
q = queue.Queue()

# Fill the queue with items = netmiko dicts with connection data.
for i in list_netmiko_connection_data:
    q.put(i)

# How many concurrent threads will be run.
# This number may be less or more than the length of Queue (number of Routers that should be processed).
NUM_OF_THREADS = 5

# Run all the necessary number of threads.
# Every created thread will begin to get an item from the queue and process it.
for i in range(NUM_OF_THREADS):
    t = Worker(q)
    # Docs: The significance of this flag is that the entire Python program
    #  exits when only daemon threads are left.
    t.daemon = True
    t.start()

# This is absolutely unnecessary block of code for this example.
# Just for getting some information about created Threads.
print("Some debug info about Threads. 1.")
c = [i for i in threading.enumerate() if isinstance(i, Worker)]
for i in c:
    print("Thread Info. Name:{}, Ident:{}, IsAlive:{}".format(i.getName(), i.ident, i.is_alive()))

# We are inside The Main Thread (__main__)
# We created Queue and filled it with the list of Devices for processing.
# We created Threads, ran it and showed where they have to get data for processing.
# Now we should inform the Main Thread that we have to wait until the Queue is EMPTY.
q.join()


# Note. The Threads are working at this moment (thread.is_alive=True) even the Queue is empty.
# The Threads will be destroyed with the Main Thread because we set "daemon=True".
# Note. We can destroy unneccessary Threads by ourselves.
# It means that we can create the list of Threads we created and pause them, refill the queue, etc.


# This is absolutely unnecessary block of code for this example.
# Just for getting some information about created Threads.
print("Some debug info about Threads. 2.")
c = [i for i in threading.enumerate() if isinstance(i, Worker)]
for i in c:
    print("Thread Info. Name:{}, Ident:{}, IsAlive:{}".format(i.getName(), i.ident, i.is_alive()))


print(time.time()-time_start)
