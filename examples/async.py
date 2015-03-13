#!/usr/bin/env python2.7
"""Example of asynchronously running "show version".

async(): decorator to make further functions asynchronous
command_runner(): creates a connection and runs an arbitrary command
main(): entry point, runs the command_runner
"""
import netmiko
from inspect import getmodule
from multiprocessing import Pool

def async(decorated):
    """Wraps a top-level function around an asynchronous dispatcher.

    When the decorated function is called, a task is submitted to a process
    pool, and a future object is returned, providing access to an eventual
    return value.

    The future object has a blocking get() method to access the task result:
    it will return immediately if the job is already done, or block until it
    completes.

    See http://stackoverflow.com/questions/1239035/asynchronous-method-call-in-python
    """
    # Keeps the original function visible from the module global namespace,
    # under a name consistent to its __name__ attribute. This is necessary for
    # the multiprocessing pickling machinery to work properly.
    module = getmodule(decorated)
    decorated.__name__ += '_original'
    setattr(module, decorated.__name__, decorated)

    def send(*args, **opts):
        """Returns asynchronously."""
        return async.pool.apply_async(decorated, args, opts)

    return send

@async
def command_runner(dispatcher, cmd):
    """Run show version on many devices."""
    # Prepare the dispatcher
    dsp = netmiko.ssh_dispatcher(dispatcher["device_type"])
    # Run the dispatcher and get the device ready
    dev = dsp(**dispatcher)
    # returns the output of the variable `cmd` that was passed
    return dev.send_command(cmd)

def main():
    """Program entry point."""
    async.pool = Pool(10)
    devices = ["10.10.10.1", "10.10.10.2", "10.10.10.3", "10.10.10.4", "10.10.10.5",
               "10.10.10.6", "10.10.10.7", "10.10.10.8", "10.10.10.9", "10.10.10.10"]
    cmd = "show version"
    results = []
    for device in devices:
        # Assumes all devices are Juniper devices
        dispatcher = {"device_type": "juniper",
                      "ip": device,
                      "username": "user",
                      "password": "pass"}
        result = command_runner(dispatcher, cmd)
        results.append(result)
    # Must use the `get()` method or you will just get a list of pool objects
    results = [i.get() for i in results]
    print results

if __name__ == "__main__":
    main()
