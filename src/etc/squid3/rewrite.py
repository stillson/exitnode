#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import psycopg2
import re
import sys
from datetime import datetime, timedelta

DEBUG = False
success_redirect = "http://peoplesopen.net"

# expiration in hours (you see the splash page again after this many hours)
expiration          = timedelta(24)
splash_url          = "http://127.0.0.1/splash.html"
splash_click_regex  = re.compile("splash_click\.html")
LOG                 = "/var/log/squid3/message.log"
android_ip          = "clients3.google.com"
dnsmasq_conf        = '/etc/dnsmasq.conf'

url_regex = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
IP_regex  = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'

# database constansts
db_host     = 'localhost'
db_db       = 'captive'
db_user     = 'captive'
db_pass     = "?fakingthecaptive?"
conn        = None
cur         = None
click_query = r"SELECT ipv4, created FROM pass WHERE ipv4 = '%s';"
reg_query   = r"INSERT INTO pass (ipv4) VALUES (%s)"

log_file = None


class Probe:
    def __init__(self, name, probe_regexes):
        self.name           = name
        self.probe_regexes  = [re.compile(i) for i in probe_regexes]
        self.probe_str      = probe_regexes

probes = [
    Probe("apple",
        ["apple.com",
         "/library/test/success\.html",
         "captive.apple.com",
         "www.ibook.info",
         "www.itools.info",
         "www.airport.us",
         "www.thinkdifferent.us",
         "www.appleiphonecell.com"]),
    Probe("android",
        ["74.125.239.8",
        "generate_204"])];

# Annoying step of having to specifically look up the android ip address
def goog_search():
    global android_ip
    with open(dnsmasq_conf) as search:
        for line in search:
            if android_ip in line:
                print "google in line"
                match = IP_regex(line)
                if match:
                    print "match"
                    android_ip = match.group(0)

def debug(s):
    if(DEBUG):
        print("DEBUG: " + s + "\n")
    else:
        log_file.write("DEBUG: " + s + "\n")
        log_file.flush()

def did_user_already_click(ip):
    debug("Trying sql query: ")
    debug("SELECT ipv4, created FROM pass WHERE ipv4 = '"+ip+"';")

    cur.execute(click_query % (ip,))
    row = cur.fetchone()
    clicked = bool(row) and (datetime.now() - row[1]) < expiration;

    debug("clicked = " + str(clicked))

    return clicked

def register_click(ip):

    cur.execute(reg_query, [ip])
    conn.commit()
    debug("Inserted ip: " + ip)

def run():
    while True:
        debug("loop once")
        redirecting = False

        try:
            #rinput = raw_input()
            rinput = sys.stdin.readline()
            debug("Input = " + rinput)
            d = rinput.split(' ')
            if not d:
                print
                continue

            url = d[0]
            if(len(d) < 2):
                # passthrough
                print url
                continue

            url_match = url_regex.findall(d[0])

            if (len(url_match) == 0):
                print url
                continue

            url         = url_match[0]
            ip_match    = IP_regex.match(d[1])

            try:
                ip = ip_match.group(0)
            except AttributeError: # in case no ip is recognized
                print url
                continue

            debug("ip = " + ip)
            debug("url = " + url)

            if splash_click_regex.search(url):
                debug(" splash page clicked by: " + ip)
                register_click(ip);
                print success_redirect
                redirecting = True
                continue

            if not redirecting:
                for probe in probes:
                    for regex in probe.probe_regexes:
                        if not redirecting and regex.search(url):
                            debug(probe.name + "probe for " + regex + " from: " + ip)
                            if(did_user_already_click(ip)):
                                debug("user already clicked through. letting probe pass.")
                                debug("redirecting to:")
                                debug(url)
                            else:
                                debug("blocking probe")
                                debug("printing: " + splash_url)
                                redirecting = True
                                print splash_url

            if not redirecting:
                print url

        except EOFError:
            debug("End of File")
            break
        except Exception:
            debug("Unexpected error:")
            debug(str(sys.exc_info()[0]))


def main():
    global conn, cur, logfile, DEBUG
    conn = psycopg2.connect(host=db_host, database=db_db, user=db_user, password=db_pass)
    cur = conn.cursor()
    log_file = open(LOG,"a")
    goog_search()
    debug("\n".join(sys.argv))
    debug("android_ip = " + android_ip)

    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        DEBUG = True
        debug("Enabled debug output.")

    run()

    conn.close()
    log_file.close()

if __name__ == '__main__':
    main()
