#!/bin/bash
 
 
source /fenghua/git/Salt-MWDS/env/bin/activate
# echo $PWD

if [ $1 == 'run' ]; then
    echo "running"
    /fenghua/git/Salt-MWDS/env/bin/python /fenghua/git/Salt-MWDS/smwds/app.py &
    echo $!  > "/fenghua/git/Salt-MWDS/pid.tmp"
    exit 0
fi


if [ $1 == 'stop' ]; then
    echo "stopping"
    tmp=`cat /fenghua/git/Salt-MWDS/pid.tmp`
    kill -9 $tmp $[$tmp+1]
    rm -rf /fenghua/git/Salt-MWDS/pid.tmp
    exit 0
fi