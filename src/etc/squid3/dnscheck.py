#!/usr/bin/env python2.7

import socket
import sys
from os import path, remove, close, chmod, rename
import subprocess
import re
import stat
from tempfile import mkstemp, NamedTemporaryFile
from shutil import move
import iptables_config

class Host:
    def __init__(self, name, url):
        self.name = name
        self.url  = url
        self.ip   = None

    def inList(self, ip_list):
        return self.ip in iplist

    def getIp(self):
        self.ip = gethostbyname(self.url)
        return self

hosts = [Host("apple", "apple.com"),
         Host("apple2", "captive.apple.com"),
         Host("apple3", "www.ibook.info"),
         Host("apple4", "www.itools.info"),
         Host("apple5", "www.airport.us"),
         Host("apple6", "www.thinkdifferent.us"),
         Host("apple7", "www.appleiphonecell.com"),
         Host("google", "clients3.google.com")]



# From http://stackoverflow.com/questions/39086/search-and-replace-a-line-in-a-file-in-python
# and modified to replace whole line
def replace(file_path, pattern, subst):
    with NamedTemporaryFile(delete=False) as new_file, open(file_path) as old_file:
        for line in old_file:
            if line and line[0] in '#\n':
                new_file.write(line)
                continue
            if not pattern in line:
                new_file.write(line)
            else:
                new_file.write(subst + '\n')
    move(new_file.name, file_path)


def main():

    hosts = [i.getIp() for i in hosts]
    ip_list = [line.strip() for line in open('/etc/squid3/hosts')]
    needs_updating  = any([not i.inList(ip_list) for i in hosts])

    if needs_updating or FORCE:
        rename('/etc/squid3/hosts', '/etc/squid3/hosts.old')
        with open('/etc/squid3/hosts', 'w') as f:
            for host in hosts:
                f.write(host.ip + '\n')
                dns_string = 'address=/' + host.url + '/' + host.ip
                replace('/etc/dnsmasq.conf', 'address=/' + host.url, dns_string) 

        chmod('/etc/dnsmasq.conf', 0644)
        iptables_config.add_rules()
        subprocess.call(['/etc/init.d/dnsmasq', 'restart'])



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '-f':
        FORCE = True
    main()
