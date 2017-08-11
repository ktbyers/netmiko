### Show commands that prompt for more information

In these cases, I generally use the send_command_timing() method (which doesn't look for prompts)


For example, a CLI interaction that looks like this:

```
pynet-rtr1#copy running-config flash:test1.txt
Destination filename [test1.txt]? 
5587 bytes copied in 1.316 secs (4245 bytes/sec)

pynet-rtr1#
```

```python
cmd1 = "copy running-config flash:test1.txt
output = net_connect.send_command_timing(cmd1)
if 'Destination filename' in output:
    output += net_connect.send_command_timing("\n")
print(output)
```

### Enable Netmiko logging of all reads and writes of the communications channel

This will create a file named 'test.log' in the current working directory.

```python
import logging
logging.basicConfig(filename='test.log', level=logging.DEBUG)
logger = logging.getLogger("netmiko")
```

### Does Netmiko support connecting via a terminal server

There is a 'terminal_server' device_type that basically does nothing post SSH connect. This means you have to manually handle the interaction with the terminal server to connect to the end device. After you are fully connected to the end network device, you can then 'redispatch' and Netmiko will behave normally

```python
from __future__ import unicode_literals, print_function
import time
from netmiko import ConnectHandler, redispatch

net_connect = ConnectHandler(
    device_type='terminal_server',        # Notice 'terminal_server' here
    ip='10.10.10.10', 
    username='admin', 
    password='admin123', 
    secret='secret123')

# Manually handle interaction in the Terminal Server 
# (fictional example, but hopefully you see the pattern)
# Send Enter a Couple of Times
net_connect.write_channel("\r\n")
time.sleep(1)
net_connect.write_channel("\r\n")
time.sleep(1)
output = net_connect.read_channel()
print(output)                             # Should hopefully see the terminal server prompt

# Login to end device from terminal server
net_connect.write_channel("connect 1\r\n")
time.sleep(1)

# Manually handle the Username and Password
max_loops = 10
i = 1
while i <= max_loops:
    output = net_connect.read_channel()
    
    if 'Username' in output:
        net_connect.write_channel(net_connect.username + '\r\n')
        time.sleep(1)
        output = net_connect.read_channel()

    # Search for password pattern / send password
    if 'Password' in output:
        net_connect.write_channel(net_connect.password + '\r\n')
        time.sleep(.5)
        output = net_connect.read_channel()
        # Did we successfully login
        if '>' in output or '#' in output:
            break

    net_connect.write_channel('\r\n')
    time.sleep(.5)
    i += 1

# We are now logged into the end device 
# Dynamically reset the class back to the proper Netmiko class
redispatch(net_connect, device_type='cisco_ios')

# Now just do your normal Netmiko operations
new_output = net_connect.send_command("show ip int brief")
```
