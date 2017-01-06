Zabbix extensions
======

Read more about each extension below:
* Zabbix graphs improvements patch  
http://blog.sepa.spb.ru/2015/08/zabbix-graphs-improvements-patch.html  
Update here: https://github.com/sepich/zabbixGrapher

* Network sockets  
http://blog.sepa.spb.ru/2014/11/zabbix-network-socket-state-statistics.html

* RabbitMQ  
http://blog.sepa.spb.ru/2014/11/rabbitmq-internals-monitoring-by-zabbix.html  
Alternative version also provided, which uses `rabbitmqctl` instead of REST API of `management-plugin`.
This could be useful when management-plugin leaks memory or timeouts requests. Also rabbitmqctl provides `atom tab` stats, but as it is ran by root - you also need to add to cron:  
```
$ cat /etc/cron.d/rabbit-status
*/3 * * * * root /etc/zabbix/rabbitmqctl-status.sh
*/5 * * * * root /etc/zabbix/rabbitmqctl-status.sh queues
```

* MySQL  
http://blog.sepa.spb.ru/2014/12/mysql-internals-monitoring-by-zabbix.html

* ElasticSearch  
http://blog.sepa.spb.ru/2014/12/elasticsearch-internals-monitoring-by.html

* AWS ELB using CloudWatch  
http://blog.sepa.spb.ru/2015/09/aws-elb-monitoring-by-zabbix-using.html

* nginx  
Collect stats provided by mod_status, your nginx.conf should have this somewhere for 127.0.0.1:  
```
        location /nginx_status {
            stub_status on;
            access_log off;
            allow 127.0.0.1;
            deny all;
        }
```

* NFS Client  
Discover NFS3 and NFS4 mounts and submits stats from /proc/net/rpc/nfs  

* Template App Linux  
Official template boiled down to important things  

