# Optimal Routing in SDN using Reinforcement Learining

This is a python project built using RYU SDN controller and Reinforcement Learning.

## Installation

Optional: Create a virtual python environment:
```bash
apt-get update
apt-get install python3-venv
python3 -m venv sdn_rl_venv
source sdn_rl_venv/bin/activate
```

Install the python dependencies and build the ryu-project
```bash
pip3 install -r requirments.txt
python3 setup.py build
```

## Usage
Open two terminals
1. In one terminal start the ryu controller
```
./start_ryu.sh run
```
2. In the second terminal start and connect the mininet to the ryu controller
```
sudo mn --custom circular_topo.py  --topo mytopo --mac --controller=remote,127.0.0.1 --switch ovsk,protocol=OpenFlow13 --link=tc
```
3. Observe the thread creation in the ryu terminal output
4. Simulate network traffic inside mininet 
Inside the mininet console
```
h2 python3 gen_traffic.py
```


## License
[Apache 2.0](http://www.apache.org/licenses/)
