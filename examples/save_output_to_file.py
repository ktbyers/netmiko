from netmiko import ConnectHandler
from getpass import getpass

# The command for to run.
command = "sh ip int brief"

# The credentials to the first device.
# Add 'secret': getpass() if you are using an enable only command.
cisco_ios = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

net_connect  = ConnectHandler(**cisco_ios)
# Add this if you want to use enable mode.
# net_connect.enable()

# Output for the device.
output = net_connect.send_command(command)

# Creates the file and writes the output to it.
backupFile = open("output_cmds.txt", "w+")
backupFile.write(output)

print("Outputted to output_cmds.txt!")