#!/usr/bin/env python
"""
This will run an command via serial on an cisco ios switch and so
serial cable must be attached to the device
"""
from netmiko import ConnectHandler
import serial


def main():
    """
    This will run an command via serial on an cisco ios switch and so
    serial cable must be attached to the device
    """
    serialhandle = {
        "device_type": "cisco_ios_serial",
        "port": "USB Serial",  # can be COM<number> or any line you can get from
        # serial.tools.list_ports.comports()
        "username": "<username>",
        "password": "<password>",
        "secret": "<secret>",
        "serial_settings": {  # this are the default values
            "baudrate": 9600,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
        },
    }
    net_connect = ConnectHandler(**serialhandle)
    net_connect.enable()
    output = net_connect.send_command("show run")
    net_connect.disconnect()

    print(output)


if __name__ == "__main__":
    main()
