#!/bin/bash
NFS=/proc/net/rpc/nfs
CFG=/etc/zabbix/zabbix_agentd.conf
if [ ! "$1" ]; then
  echo "Run as: $0 [nfs3|nfs4|discover] [debug]"
  exit
fi

#nfs3
if [ "$1" == "discover" ]; then
  echo '{"data":['
  awk '/^proc3/ {
      split($0,values)
      for (v in values) { sum+=values[++i+3] }
      if(sum) print "{\"{#NFS3}\":\"nfs3\"}"
  }' $NFS
  echo ']}'
  exit
fi
#nfs4
if [ "$1" == "discover4" ]; then
  echo '{"data":['
  awk '/^proc4/ {
      split($0,values)
      for (v in values) { sum+=values[++i+3] }
      if(sum) print "{\"{#NFS4}\":\"nfs4\"}"
  }' $NFS
  echo ']}'
  exit
fi

if [ "$1" == "nfs3" ]; then
  proc="getattr setattr lookup access readlink read write create mkdir symlink mknod remove rmdir rename link readdir readdirplus fsstat fsinfo pathconf"
  out=`awk '/proc3/ {
      split("'"$proc"'", names)
      split($0,values)
      for (e in names) {
          printf("- nfs[nfs3,%s] %d\n", names[++i], values[i+3]);
      }
  }' $NFS`
  if [ "$2" == "debug" ]; then
    echo "$out"
    echo "$out" | zabbix_sender -vv -c "$CFG" -i -
  else
    echo "$out" | zabbix_sender -c "$CFG" -i - &>/dev/null
    awk '/^proc3/{print $NF}' $NFS #commit
  fi
fi

if [ "$1" == "nfs4" ]; then
  proc="read write open open_conf close setattr confirm lock getattr lookup lookup_root remove rename link symlink create pathconf statfs"
  nums="4 5 7 8 11 12 15 16 20 21 22 23 24 25 26 27 28 29"
  out=`awk '/proc4/ {
      split("'"$proc"'", names)
      split("'"$nums"'", nums)
      split($0,values)
      for (e in names) {
          printf("- nfs[nfs4,%s] %d\n", names[++i], values[nums[i]]);
      }
  }' $NFS`
  if [ "$2" == "debug" ]; then
    echo "$out"
    echo "$out" | zabbix_sender -vv -c "$CFG" -i -
  else
    echo "$out" | zabbix_sender -c "$CFG" -i - &>/dev/null
    awk '/^proc3/{print 30}' $NFS #readlink
  fi
fi
