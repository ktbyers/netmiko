#!/bin/bash

# Remove delay for cisco3; must be root or sudo to execute
/sbin/tc qdisc del dev eth0 root
