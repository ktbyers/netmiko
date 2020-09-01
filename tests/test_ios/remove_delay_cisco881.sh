#!/bin/bash

# Remove delay for all; must be root or sudo to execute
sudo -s /sbin/tc qdisc del dev eth0 root
