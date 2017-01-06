#!/usr/bin/env python
sender='/usr/bin/zabbix_sender'      #path zabbix_sender
cfg='/etc/zabbix/zabbix_agentd.conf' #path to zabbix-agent config

import os, time, json, subprocess, argparse, re
from ast import literal_eval

parser = argparse.ArgumentParser(description='Zabbix CloudWatch client')
parser.add_argument('-v', '--verbose', action='store_true', help='Print debug info')
parser.add_argument('-d', '--discover', action='store_true', help='Discover items')
args = parser.parse_args()

def exe(cmd, stdin=None):
  p=subprocess.Popen(cmd , shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
  return p.communicate(stdin) + (p.returncode,)

#read data
try:
  with open('/tmp/rabbit-status', 'r') as f: s=f.read()
  s=re.sub('\{\s*([a-z].*?),', r"{'\1':", s)
  s=re.sub(',\s*"[^"]+"}', r'}', s)
  stat=literal_eval(re.sub(':\s*([^"\'0-9]+?)}', r':"\1"}', s))

  if not os.path.isfile('/tmp/rabbit-queues'): q=[]
  else:
    with open('/tmp/rabbit-queues', 'r') as f: q=f.readlines()
except:
  print "Unable get data from rabbitmqctl!"
  os._exit(1)

#discovery
if args.discover:
  disco = { "data": [ ] }
  for i in q:
    v=i.split()
    if v[1]=='queuescount' and len(v)==3: continue
    disco['data'].append( { '{#VHOSTNAME}': v[0], '{#QUEUENAME}': v[1] } )
  print json.dumps(disco, indent=2)

# return uptime, send traps
else:
  out=[]
  out.append("- rabbitmqctl[filedesc.percentused] {:.2f}".format(100.0*stat[11]['file_descriptors'][1]['total_used']/stat[11]['file_descriptors'][0]['total_limit']))
  out.append("- rabbitmqctl[sockets.percentused] {:.2f}".format(100.0*stat[11]['file_descriptors'][3]['sockets_used']/stat[11]['file_descriptors'][2]['sockets_limit']))
  out.append("- rabbitmqctl[mem.percentused] {:.2f}".format(100.0*stat[4]['memory'][0]['total']/stat[8]['vm_memory_limit']))
  for i in stat[4]['memory']:
    k=i.keys()[0]
    if k in {'total'}: continue
    out.append("- rabbitmqctl[mem.{}] {}".format(k, i[k]))
    
  for i in q:
    v=i.split()
    if v[1]=='queuescount' and len(v)==3:
      out.append("- rabbitmqctl[{},queuescount] {}".format(v[0], v[2]))
    else:
      out.append("- rabbitmqctl[{},{},messages_ready] {}".format(v[0], v[1], v[2]))
      out.append("- rabbitmqctl[{},{},messages_unacknowledged] {}".format(v[0], v[1], v[3]))
      out.append("- rabbitmqctl[{},{},consumers] {}".format(v[0], v[1], v[4]))
      out.append("- rabbitmqctl[{},{},memory] {}".format(v[0], v[1], v[5]))

  out="\n".join(out)
  res, err, code = exe("{} -c {} -vv -i -".format(sender,cfg) , stdin=out)
  if args.verbose: print "\n".join([out, res])
  else: print stat[14]['uptime']
