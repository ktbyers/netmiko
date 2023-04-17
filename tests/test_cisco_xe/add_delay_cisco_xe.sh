#!/bin/bash

# Add delay for cisco3; must be root or sudo to execute
sudo -s /sbin/tc qdisc del dev eth0 root
sudo -s /sbin/tc qdisc add dev eth0 root handle 1: prio
sudo -s /sbin/tc qdisc add dev eth0 parent 1:3 handle 30: tbf rate 20kbit buffer 1600 limit  3000
sudo -s /sbin/tc qdisc add dev eth0 parent 30:1 handle 31: netem  delay 1000ms 10ms distribution normal loss 10%
sudo -s /sbin/tc filter add dev eth0 protocol ip parent 1:0 prio 3 u32 match ip dst 184.105.247.89/32 flowid 1:3

