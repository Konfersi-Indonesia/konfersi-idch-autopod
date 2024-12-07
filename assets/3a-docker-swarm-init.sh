#!/bin/bash

ip4=$(/sbin/ip -o -4 addr list ens3 | 
awk '{print $4}' | cut -d/ -f1)

docker swarm init --advertise-addr $ip4