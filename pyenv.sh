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
    lsof -i:5000|grep python|awk '{print $2}'|xargs kill -9    
    exit 0
fi
