from netmiko import ConnectHandler
from getpass import getpass

# The command for both, assuming you want to run the same command on both of them.
command = "sh ip int brief"

# The credentials to the first device.
# Add 'secret': getpass() if you are using an enable only command.
cisco_ios_1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

# The credentials to the second device.
# add 'secret': getpass() if you are using an enable only command.
cisco_ios_2 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

net_connect_1  = ConnectHandler(**cisco_ios_1)
# Add this if you want to use enable mode.
# net_connect_1.enable()

net_connect_2  = ConnectHandler(**cisco_ios_2)
# Add this if you want to use enable mode.
# net_connect_2.enable()

# Output for the first device and the second device.
output_1 = net_connect_1.send_command(command)
output_2 = net_connect_2.send_command(command)

print(output_1)
print("\n \n \n \n \n")
print(output_2)