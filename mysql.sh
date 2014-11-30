#!/bin/bash
# Zabbix MySQL trap sender
# UserParameter=mysql[*],/etc/zabbix/mysql.sh $1 $2
# run '/etc/zabbix/mysql.sh uptime debug' to debug trap sending

ZABBIX_CONFIG_FILE=/etc/zabbix/zabbix_agentd.conf
TMPV=/tmp/zabbix_variables.tmp
TMPS=/tmp/zabbix_status.tmp

variables=(
max_connections
query_cache_size
table_open_cache
)

status=(
Com_begin
Com_commit
Com_delete
Com_delete_multi
Com_insert
Com_insert_select
Com_lock_tables
Com_replace
Com_replace_select
Com_rollback
Com_select
Com_update
Connections
Created_tmp_disk_tables
Created_tmp_files
Created_tmp_tables
Innodb_buffer_pool_reads
Innodb_buffer_pool_read_requests
Innodb_buffer_pool_wait_free
Innodb_data_pending_fsyncs
Innodb_data_pending_reads
Innodb_data_pending_writes
Innodb_data_reads
Innodb_data_writes
Innodb_log_writes
Innodb_pages_read
Innodb_row_lock_current_waits
Open_tables
Qcache_free_memory
Qcache_hits
Qcache_inserts
Queries
Slow_queries
Table_locks_immediate
Table_locks_waited
Threads_cached
Threads_connected
Threads_created
Threads_running
)

#send variables (once per hour by default)
if [ "$1" == "max_connections" ]; then
  MYSQLV=`echo "SHOW GLOBAL VARIABLES" | /usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf`
  for var in ${variables[*]}; do
    echo "$MYSQLV" | grep "^$var\s" >> $TMPV
  done
  sed -i "s/^/- mysql.variables./" $TMPV
  if [ "$2" == "debug" ]; then
    cat $TMPV
    /usr/bin/zabbix_sender -c $ZABBIX_CONFIG_FILE -i $TMPV -vv
  else
    /usr/bin/zabbix_sender -c $ZABBIX_CONFIG_FILE -i $TMPV >/dev/null 2>&1
  fi
  #return max_connections
  echo "$MYSQLV" | grep "^max_connections\s" | awk '{print $2}'
  rm  $TMPV

#send status (once per 5min by default)
elif [ "$1" == "uptime" ]; then
  MYSQLS=`echo "SHOW GLOBAL STATUS" | /usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf`
  for stat in ${status[*]}; do
    echo "$MYSQLS" | grep "^$stat\s" >> $TMPS
  done
  echo "SHOW SLAVE STATUS\G" | /usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf | grep Seconds_Behind_Master | sed -r 's/^ *//' | sed 's/://' | sed 's/NULL/0/' >> $TMPS
  sed -i "s/^/- mysql.status./" $TMPS
  if [ "$2" == "debug" ]; then
    cat $TMPS
    /usr/bin/zabbix_sender -c $ZABBIX_CONFIG_FILE -i $TMPS -vv
  else
    /usr/bin/zabbix_sender -c $ZABBIX_CONFIG_FILE -i $TMPS >/dev/null 2>&1
  fi
  #return Uptime
  echo "$MYSQLS" | grep "^Uptime\s" | awk '{print $2}'
  rm  $TMPS

#extensions below (could be removed, used by template_app_mysql_transactions)

#number of transactions with rows_locked >X (default 10000)
elif [ "$1" == "trans-locking" ]; then
  if [ "$2" == "" ]; then t='10000'; else t="$2"; fi
  echo "select count(*) from INFORMATION_SCHEMA.INNODB_TRX where trx_rows_locked>$t" | /usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf | tail -n 1

#number of transactions started > X sec ago
elif [ "$1" == "trans-old" ]; then
  if [ "$2" == "" ]||[ "$2" == "0" ]; then w=''; else w="where TIME_TO_SEC(TIMEDIFF(NOW(),trx_started))>$2"; fi
  echo "select count(*) from INFORMATION_SCHEMA.INNODB_TRX $w" | /usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf | tail -n 1

#number of transactions with query running > X sec
elif [ "$1" == "trans-running" ]; then
  if [ "$2" == "" ]||[ "$2" == "0" ]; then w=''; else w="AND p.TIME>$2"; fi
  echo "select count(*) from INFORMATION_SCHEMA.INNODB_TRX t, INFORMATION_SCHEMA.PROCESSLIST p WHERE t.trx_mysql_thread_id=p.ID AND p.COMMAND='Query' $w" | /usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf | tail -n 1

fi