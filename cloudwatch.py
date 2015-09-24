#!/usr/bin/env python
import argparse
import os, time, datetime, subprocess
import boto, boto.ec2.elb, boto.ec2.cloudwatch
import json
import math

sender = '/usr/bin/zabbix_sender'       # path zabbix_sender
cfg = '/etc/zabbix/zabbix_agentd.conf'  # path to zabbix-agent config
aws_key='INSERT KEY'                    # AWS API key id
aws_secret='INSERT SECRET'              # AWS API key

parser = argparse.ArgumentParser(description='Zabbix CloudWatch client')
parser.add_argument('-e', '--elb', metavar='NAME', help='ELB name')
parser.add_argument('-i', '--interval', type=int, default=60, metavar='N', help='Interval to get data back (Default: 60)')
parser.add_argument('-s', '--srv', metavar='NAME', default='-', help='Hostname in zabbix to receive traps')
parser.add_argument('-r', '--region', metavar='NAME', default='eu-west-1', help='AWS region (Default: eu-west-1)')
parser.add_argument('-d', '--discover', choices=['elb'], help='Discover items (Only discover for ELB supported now)')
parser.add_argument('-v', '--verbose', action='store_true', help='Print debug info')
args = parser.parse_args()
if not args.elb and not args.discover:
  parser.print_help()
  os._exit(0)

def exe(cmd, stdin=None):
  p=subprocess.Popen(cmd , shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
  return p.communicate(stdin) + (p.returncode,)

if args.discover:
  if 'elb' in args.discover:
    c = boto.ec2.elb.connect_to_region(args.region, aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, debug=args.verbose)
    elbRetData = { "data": [ ] }
    for elb in c.get_all_load_balancers():
      elbRetData['data'].append( { '{#LOADBALANCERNAME}': elb.name } )
    print json.dumps(elbRetData, indent=2)

if args.elb:
  c=boto.ec2.cloudwatch.connect_to_region(args.region, aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, debug=args.verbose)

  #amazon uses UTC at cloudwatch
  os.environ['TZ'] = 'UTC'
  time.tzset()
  out=[]
  metrics={
  'RequestCount':'Sum',
  'BackendConnectionErrors':'Sum',
  'HTTPCode_Backend_2XX':'Sum',
  'HTTPCode_Backend_3XX':'Sum',
  'HTTPCode_Backend_4XX':'Sum',
  'HTTPCode_ELB_5XX':'Sum',
  'Latency':'Average',
  'SurgeQueueLength':'Maximum',
  'HealthyHostCount':'Average',
  'UnHealthyHostCount':'Average'
  }
  now = datetime.datetime.now()
  start_time = now - datetime.timedelta(seconds=args.interval)

  while start_time < now:
    end_time = min(now, start_time + datetime.timedelta(seconds=3600))
    for m in metrics:
      data=c.get_metric_statistics(60, start_time, end_time, m, 'AWS/ELB', metrics[m], {'LoadBalancerName': args.elb})
      # for periodic chech no data = 0
      if len(data)==0 and end_time == now:
        data = [{'Timestamp': now, metrics[m]: 0}]
      for d in data:
        out.append( "{0:s} cw[{1:s},{2:s}] {3:.0f} {4:f}".format(args.srv, args.elb, m, time.mktime(d['Timestamp'].timetuple()), d[metrics[m]]) )
    start_time = start_time + datetime.timedelta(seconds=3600)
  out.sort()
  out="\n".join(out)
  res, err, code = exe("{} -c {} -T -i -".format(sender,cfg) , stdin=out)
  if args.verbose: print "\n".join([out, res])
  print code
