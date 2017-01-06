#!/bin/bash
/usr/sbin/rabbitmqctl -q status > /tmp/rabbit-status
/usr/sbin/rabbitmqctl -q cluster_status > /tmp/rabbit-clusterstatus
/usr/sbin/rabbitmqctl eval 'erlang:system_info(info).' | sed -E 's/\\n/\n/g' > /tmp/rabbit-sysinfo
pgrep rabbitmqctl >/dev/null && exit

# queues stats each 5 min only on first node
db="/tmp/rabbit-queues"
m=`date +%M`
if [[ `hostname` == *-1 && "$1" == "queues" ]]; then
  for vhost in `/usr/sbin/rabbitmqctl -q list_vhosts`; do
    q=`/usr/sbin/rabbitmqctl -q list_queues -p "$vhost" name messages_ready messages_unacknowledged consumers memory`
    n=`echo -n "$q" | wc -l`
    if [ $n -gt 0 ]; then
      echo "$vhost queuescount $n" >> "$db".tmp
      echo "$q" | awk -v v="$vhost" '!/^amq.gen/{print v,$0}' >> "$db".tmp
    fi
  done
  mv "$db".tmp "$db" 
fi
