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


#consts
SQUID_HOSTS ='/etc/squid3/hosts'


class Host:
    """
    basic class to for a host/address. Also handles dns lookups
    """
    def __init__(self, name, url):
        object.init(self)
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

class HostDict(object):
    """
        It sort of looks and acts like a dict, but with a little cleverness thrown
        in. I hope.
    """
    def __init__(self):
        object.init(self)
        self._dict = {}

    def __getitem__(self, url):
        return self._dict[url]

    def __setitem__(self, url, host):
        self._dict[url] = host
        return self

    def has_key(self, key):
        return key in self._dict

    def items(self):
        return self._dict.items()

    def iteritems(self):
        return self._dict.iteritems()

    def iterkeys(self):
        return self._dict.iterkeys()

    def itervalues(self):
        return self._dict.itervalues()

    def keys(self):
        return self._dict.keys()

    def addHost(self, name, url):
        self._dict[url] = Host(name, url)

    def getIp(self):
        for i in self.itervalues():
            i.getIp()

def hosts_init():
    global hosts
    hosts = HostDict()
    hosts.addHost("apple", "apple.com")
    hosts.addHost("apple2", "captive.apple.com")
    hosts.addHost("apple3", "www.ibook.info")
    hosts.addHost("apple4", "www.itools.info")
    hosts.addHost("apple5", "www.airport.us")
    hosts.addHost("apple6", "www.thinkdifferent.us")
    hosts.addHost("apple7", "www.appleiphonecell.com")
    hosts.addHost("google", "clients3.google.com")
    hosts.getIp()

class DNSmasqconf(object):
    file_name = '/etc/dnsmasq.conf'
    proc_name = '/etc/init.d/dnsmasq'
    line_re   =  re.compile(r'address=/(.*)/(.*)')
    def __init__(self):
        self.object.__init__()
        self.lines = False

    def read(self):
        "open file and read lines"
        with open(self.file_name) as f:
            # each line inside a one element list so it can be a reference
            self.lines = [[i.strip()] for i in f.readlines()]
        return self

    def replace(self, hosts):
        "replace relevant lines"
        for a_line in self.lines:
            if not a_line[0] or a_line[0].startswith('#'):
                continue
            match = self.line_re.search(a_line[0])
            if not match:
                continue
            a_line[0] = hosts[match.groups()[1]].dnsString()


    def close(self):
        "close and rename"
        self.lines = (i[0] + "\n" for i in self.lines)
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
    hosts_init()
    ip_list = [line.strip() for line in open(SQUID_HOSTS)]

    #if any address in the host list isn't in the ip_list
    needs_updating = any([not i.inList(ip_list) for i in hosts.iteritems()])

    if needs_updating or FORCE:
        D = DNSmasqconf()
        D.run(hosts)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '-f':
        FORCE = True
    main()
