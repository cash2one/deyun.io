#!/bin/bash
 
 
source /fenghua/git/Salt-MWDS/env/bin/activate
# echo $PWD

if [ $1 == 'run' ]; then
    echo "running"
#    /fenghua/git/Salt-MWDS/env/bin/python /fenghua/git/Salt-MWDS/smwds/app.py &
    cd /fenghua/Git/Salt-MWDS/smwds
    /fenghua/git/Salt-MWDS/env/bin/gunicorn -b 127.0.0.1:5000 --worker-class eventlet -w 1 "app:create_app()"
    echo $!  > "/fenghua/git/Salt-MWDS/pid.tmp"
    exit 0
fi


if [ $1 == 'stop' ]; then
    echo "stopping"
    lsof -i:5000|grep python|awk '{print $2}'|xargs kill -9    
    exit 0
fi
