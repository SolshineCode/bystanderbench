#!/bin/bash
# Restart the GPU1 Hermes worker cleanly: stop any old worker + its llama-server, relaunch one.
cd /home/darkstar/bluedot-unit2-impossiblebench
for p in $(ps -eo pid,args | grep "[g]pu1_hermes_worker.sh" | awk '{print $1}'); do kill -KILL "$p"; done
for p in $(ps -eo pid,args | grep "[a]lias hermes-offline" | awk '{print $1}'); do kill "$p"; done
sleep 4
[ -f "$1" ] && python3 "$1"
bash -n tools/offline/gpu1_hermes_worker.sh || exit 1
RES_ID="${RES_ID:-50965565}" setsid nohup bash tools/offline/gpu1_hermes_worker.sh > logs/offline/gpu1_hermes_worker.nohup 2>&1 < /dev/null &
disown
sleep 2
echo "workers: $(ps -eo pid,args | grep -c '[g]pu1_hermes_worker.sh')"
tail -2 logs/offline/gpu1_hermes_worker.log
