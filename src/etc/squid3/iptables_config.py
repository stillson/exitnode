import netfilter.rule as rule
import netfilter.table as table
import sys
from   collections import deque

CLEAR       = False
PORT        = '3128'
pr          = 'PREROUTING'
rd          = 'REDIRECT'
squid_hosts = '/etc/squid3/hosts'
iff         = 'bat0'
to_port     = '--to-port %s' % (PORT,)
d_port      = '--dport 80'
TCP         = 'tcp'

def consume(iterator):
    deque(iterator, maxlen=0)

def add_rules():
    clear_rules()

    ip_list = [line.strip() for line in open(squid_hosts)]
    jump    = rule.Target(rd, to_port)
    nat     = table.Table('nat')

    for ip in ip_list:
        rule = rule.Rule(in_interface=iff,
                                   protocol=TCP,
                                   destination=ip,
                                   matches=[rule.Match(TCP, d_port)],
                                   jump=jump)
        nat.append_rule(pr, rule)

def clear_rules():
    nat = table.Table('nat')
    rule_gen = (nat.delete_rule(pr, rule) for rule in nat.list_rules(pr) if rule.in_inerface == 'bat0')
    consume(rule_gen)

def main():
    if (CLEAR):
        clear_rules()
    else:
        add_rules()

if __name__ == '__main__':
    global CLEAR
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        CLEAR = True
    main()
