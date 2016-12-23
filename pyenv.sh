#!/bin/bash
DEYUN_PATH="/fenghua/Git/Salt-MWDS"
ENV_PATH="/fenghua/Git/Salt-MWDS/env"
 
source $ENV_PATH/bin/activate
# echo $PWD

if [ $1 == 'run' ]; then
    echo "running"
#    /fenghua/git/Salt-MWDS/env/bin/python /fenghua/git/Salt-MWDS/smwds/app.py &
    cd $DEYUN_PATH/smwds
    $DEYUN_PATH/env/bin/gunicorn -b 127.0.0.1:5000 --worker-class eventlet -w 1 "app:create_app()"
    echo $!  > "$DEYUN_PATH/pid.tmp"
    exit 0
fi


if [ $1 == 'stop' ]; then
    echo "stopping"
    lsof -i:5000|grep python|awk '{print $2}'|xargs kill -9    
    exit 0
fi
