#!/usr/bin/env python2.7

import socket
import sys
from   os import path, remove, close, chmod, rename
import subprocess
import re
import stat
from   tempfile import mkstemp, NamedTemporaryFile
from   shutil import move
import iptables_config
from   itertools import product

class Host:
    def __init__(self, name, url):
        self.name = name
        self.url  = url
        self.ip   = None

    def inList(self, ip_list):
        return self.ip in iplist

    def getIp(self):
        # hopefully , this doesn't go through dnsmasq, or it will be kind of pointless
        self.ip = socket.gethostbyname(self.url)
        return self

    def dnsString(self):
        return 'address=/' + self.url + '/' + self.ip

    def searchString(self):
        return 'address=/' + self.url

hosts = [Host("apple", "apple.com"),
         Host("apple2", "captive.apple.com"),
         Host("apple3", "www.ibook.info"),
         Host("apple4", "www.itools.info"),
         Host("apple5", "www.airport.us"),
         Host("apple6", "www.thinkdifferent.us"),
         Host("apple7", "www.appleiphonecell.com"),
         Host("google", "clients3.google.com")]

class DNSmasqconf(object):
    file_name = '/etc/dnsmasq.conf'
    proc_name = '/etc/init.d/dnsmasq'
    def __init__(self):
        self.object.__init__()
        self.lines = False

    def read(self):
        "open file and read lines"
        with open(self.file_name) as f:
            self.lines = f.readlines()
        return self

    def replace(self, hosts):
        "replace relevant lines"
        def h_filt(line, host):
            if host.searchString in line:
                return host.dnsString
            return line

        # o(n^2). nothing's sorted. so sue me.
        for i in product(self.lines, hosts):
            hfilt(*i)


    def close(self):
        "close and rename"
        with open(self.file_name + '.tmp', 'w') as f:
            f.writeline(self.lines)
        rename(self.file_name + '.tmp', self.file_name)
        chmod(self.file_name, 0644)
        iptables_config.add_rules()
        subprocess.call([self.proc_name, 'restart'])

    def run(self, hosts):
        self.read()
        self.replace(hosts)
        self.close()



def main():
    hosts = [i.getIp() for i in hosts]
    ip_list = [line.strip() for line in open('/etc/squid3/hosts')]
    needs_updating  = any([not i.inList(ip_list) for i in hosts])

    if needs_updating or FORCE:
        D = DNSmasqconf()
        rename('/etc/squid3/hosts', '/etc/squid3/hosts.old')
        with open('/etc/squid3/hosts', 'w') as f:
            for host in hosts:
                f.write(host.ip + '\n')

        D.run(hosts)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '-f':
        FORCE = True
    main()
