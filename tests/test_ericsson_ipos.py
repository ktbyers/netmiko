#!/usr/bin/env python
"""
This will run an ssh command successfully on an Ericsson IPPOS.
SSH must be enabled on the device

"""

from netmiko.ssh_dispatcher import ConnectHandler


def main():
  """
  This will run an ssh command successfully on an Ericsson IPPOS.
  SSH must be enabled on the device
  """
  
  ericsson_connect = {
      "device_type": "ericsson_ipos",
      "ip": "10.10.10.10",
      "username": "username",
      "password": "password",
  }

  net_connect = ConnectHandler(**ericsson_connect)
  output = net_connect.send_command("show ip int brief")
  print(output)


if __name__ == "__main__":
    main()
