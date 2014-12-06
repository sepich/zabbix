#!/usr/bin/env python
# curl -ik -u guest:guest https://localhost:15672/api/overview
# http://hg.rabbitmq.com/rabbitmq-management/raw-file/rabbitmq_v3_3_4/priv/www/api/index.html
import json
import sys, os
import socket
import urllib2

username='guest'                     #rabbitmq user able to read data
password='guest'                     #rabbitmq user's password$VAR{rabbitmq_zabbix_password}
hostname = socket.gethostname()      #localhost or interface name
port=15672                           #rabbitmq port
sender='/usr/bin/zabbix_sender'      #path zabbix_sender
cfg='/etc/zabbix/zabbix_agentd.conf' #path to zabbix-agent config
tmp='/tmp/rb_stats.tmp'              #temp file to use

#Call the REST API and convert the results into JSON
def call_api(path):
    url = 'https://{0}:{1}/api/{2}'.format(hostname, port, path)
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, username, password)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    return json.loads( urllib2.build_opener(handler).open(url).read() )

def main():
  #List all of the RabbitMQ queues
  if len(sys.argv)<2:
    print "Run as:\n{0} [list_queues | server check]".format(sys.argv[0])

  elif sys.argv[1]=='list_queues':
    if not socket.gethostname().endswith("-1"): return []  #only discover queues on first node
    queues = []
    for queue in call_api('queues'):
      if not queue['name'].startswith("amq.gen-"):
        element = {'{#VHOSTNAME}': queue['vhost'], '{#QUEUENAME}': queue['name']}
        queues.append(element)
    print json.dumps({'data': queues},indent=4)

  elif sys.argv[1]=='server':
    print call_api('nodes/rabbit@{0}'.format(hostname)).get(sys.argv[2])
    #send all queues info as traps
    if sys.argv[2]=='uptime':
      out=''
      num=0
      for queue in call_api('queues'):
        num+=1
        if queue['name'].startswith("amq.gen-"): continue
        for item in ['messages', 'messages_unacknowledged', 'consumers', 'message_stats.deliver', 'message_stats.redeliver']:
          i=item.split('.')
          val=queue
          while len(i): val=val.get(i.pop(0),{})
          if val=={}: continue
          out += "- rabbitmq[{0},{1},{2}] {3}\n".format(queue['vhost'], queue['name'], item, val)
      out += "- rabbitmq.queue.count {0}\n".format(num)

      #write data for zabbix sender
      try:
        with open(tmp,'w') as f: f.write(out)
      except:
        print "Unable to save data to send!"
        sys.exit(1)

      #send data with debug
      if len(sys.argv)>3 and sys.argv[3]=='debug':
        print out
        os.system("{0} -c {1} -i {2} -vv".format(sender, cfg, tmp))
      else:
        os.system("{0} -c {1} -i {2} >/dev/null 2>&1".format(sender, cfg, tmp))
      #cleanup
      os.remove(tmp)

if __name__ == '__main__':
    main()
