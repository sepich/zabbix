#!/usr/bin/env python
# Run without parameters to send traps list below
# Run as `rabbitmq-rates.py debug` to debug zabbix_sender
sender='/usr/bin/zabbix_sender'      #path zabbix_sender
cfg='/etc/zabbix/zabbix_agentd.conf' #path to zabbix-agent config
login='guest'
passwd='guest'
#list of traps to send
traps1={                              #keys for health page
  "message_stats.deliver_details.rate",
  "message_stats.publish_details.rate",
  "message_stats.ack_details.rate",
  "message_stats.redeliver_details.rate",
  "queue_totals.messages",
  "object_totals.consumers",
  "object_totals.queues",
  "object_totals.exchanges",
  "object_totals.connections",
  "object_totals.channels"
}

import urllib2, ssl, base64
import json
import sys, os, time, subprocess

#read specified keys from json data
def getKeys(stats, traps):
  out=''
  for t in traps:
    c=t.split('.')
    s=stats
    while len(c): s=s.get(c.pop(0),{})
    if s=={}: continue
    out += "- rb.{0} {1}\n".format(t,s)
  return out

def exe(cmd, stdin=None):
  p=subprocess.Popen(cmd , shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
  return p.communicate(stdin) + (p.returncode,)

def main():
  #load json data
  try:
    context = ssl._create_unverified_context()
    request = urllib2.Request("https://localhost:15672/api/overview")
    base64string = base64.encodestring(':'.join((login, passwd)))[:-1]
    request.add_header("Authorization", "Basic %s" % base64string)
    f = urllib2.urlopen(request, context=context)
    stats = json.loads( f.read() )
  except:
    print "Unable to load Json data!"
    sys.exit(1)

  data = getKeys(stats,traps1)  #getting health values
  out, err, res = exe("{} -c {} -i - -vv".format(sender, cfg), stdin=data)

  #debug
  if len(sys.argv)>1:
    print data
    print out

if __name__ == "__main__":
    main()
