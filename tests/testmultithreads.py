#!/usr/bin/python
# This should go into pynag's unit testing at some point
# This script tries multithreaded writes to the pynag Model
# and prints error to screen if any writes fail


import pynag.Model
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool


def change(host):
    host.address = "127.0.0.1"
    host.save()
    pynag.Model.ObjectDefinition.objects.get_all()
    print "Set address", host.address, "to", host.host_name
    

if __name__ == '__main__':
    hosts = pynag.Model.Host.objects.filter(host_name__startswith="web04")
    for i in hosts:
        i.address = "127.0.0.2"
        i.save()
    hosts = pynag.Model.Host.objects.filter(host_name__startswith="web04")

    p = ThreadPool(4)
    p.map(change, hosts)

    hosts = pynag.Model.Host.objects.filter(host_name__startswith="web04")
    for i in hosts:
        if i.address != "127.0.0.1":
            print "ERROR", i.host_name, "has address", i.address
