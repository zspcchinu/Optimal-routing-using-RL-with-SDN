#!/bin/sh

export PYTHONPATH=$PYTHONPATH:.

if [ "$#" -ne 1 ]; then
	echo "Illegal number of parameters"
	exit -1
fi

if [ $1 = "all" ]; then
	./sdn_rl_venv/bin/ryu-manager --observe-links ryu.app.sdnhub_apps.fileserver ryu.app.sdnhub_apps.host_tracker_rest  ryu.app.rest_topology ryu.app.sdnhub_apps.stateless_lb_rest ryu.app.sdnhub_apps.tap_rest ryu.app.ofctl_rest ryu.app.network_awareness.shortest_forwarding --k-paths=2 --weight=hop
elif [ $1 = "run" ]; then
	./sdn_rl_venv/bin/ryu-manager --observe-links ryu.app.network_awareness3.shortest_forwarding --k-paths=10 --weight=hop
fi
