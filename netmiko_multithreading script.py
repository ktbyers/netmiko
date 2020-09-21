###########################################################################################################
#
#This is a sample netmiko multithreading script to access multiple devices simultaneously through telnet
#
#
###########################################################################################################

from netmiko import ConnectHandler
from datetime import datetime
import getpass
import os
import sys
import time
import re
import telnetlib
from netmiko.ssh_exception import NetMikoTimeoutException
from paramiko.ssh_exception import SSHException
from netmiko.ssh_exception import AuthenticationException
import json
from random import random
import threading
from io import StringIO
from time import gmtime, strftime
from pprint import pprint
from time import time


class NetmikoMultithreading:
    
    def read_devices(self, devices_filename):
        devices = {} # create our dictionary for storing devices and their info

        with open(devices_filename) as devices_file:
             for device_line in devices_file:

                 device_info = device_line.strip().split(',')  #extract device info from line

                 device = {'ipaddr': device_info[0],
                           'type':   device_info[1],
                           'name':   device_info[2],
                           'username':   device_info[3],
                           'password':   device_info[4],
                           'config_file':   device_info[5]}  # create dictionary of device objects ...

                 devices[device['ipaddr']] = device  # store our device in the devices dictionary
                                                # note the key for devices dictionary entries is ipaddr

        print ('\n----- devices --------------------------')
        pprint(devices)

        return devices

#------------------------------------------------------------------------------
    def config_worker(self, a, b, c, d, e):

        #---- Connect to the device ----
        if b == 'cisco-ios-telnet': device_type = 'cisco_ios_telnet'
        else:                               device_type = 'cisco_ios_telnet'    # attempt Cisco IOS telnet as default


        #---- Connect to the device
        session = ConnectHandler(device_type=device_type, ip=a, username=c, password=d)

        if device_type == 'cisco_ios_telnet' and a == '10.22.11.16':
           #---- Use CLI command to get configuration data from device
           print ('---- Getting configuration from device')
           config_data_ip1 = session.send_config_from_file(e)
           print(config_data_ip1)

        if device_type == 'cisco_ios_telnet' and a == '10.22.11.17':
           #---- Use CLI command to get configuration data from device
           print ('---- Getting configuration from device')
           config_data_ip2 = session.send_config_from_file(e)
           print(config_data_ip2)

        if device_type == 'cisco_ios_telnet' and a == '10.22.11.18':
           #---- Use CLI command to get configuration data from device
           print ('---- Getting configuration from device')
           config_data_ip3 = session.send_config_from_file(e)
           print(config_data_ip3)

        if device_type == 'cisco_ios_telnet' and a == '10.22.11.19':
           #---- Use CLI command to get configuration data from device
           print ('---- Getting configuration from device')
           config_data_ip4 = session.send_config_from_file(e)
           print(config_data_ip4)

        session.disconnect()

        return
        

BGP = NetmikoMultithreading()

def connect_to_device():

    devices = BGP.read_devices('/path/to/device_list.txt(conataining below 6 paramaeters)')
    starting_time = time()

    config_threads_list = []
    for ipaddr,device in devices.items():
        a, b, c, d, e = device['ipaddr'], device['type'], device['username'], device['password'], device['config_file']
        print ('Creating thread for: ', device)
        config_threads_list.append(threading.Thread(target=BGP.config_worker, args=(a,b,c,d,e)))

    print ('\n---- Begin get config threading ----\n')
    for config_thread in config_threads_list:
        config_thread.start()

    for config_thread in config_threads_list:
        config_thread.join()

    print ('\n---- End get config threading, elapsed time=', time() - starting_time)

