# Optimal Routing in SDN using Reinforcement Learining

This is a python project built using RYU SDN controller and Reinforcement Learning.

## Installation

Optional: Create a virtual python environment:
```bash
apt-get update
apt-get install python3-venv mininet python3-pip
pip3 install scapy
python3 -m venv sdn_rl_venv
source sdn_rl_venv/bin/activate
```

Install the python dependencies and build the ryu-project
```bash
pip3 install -r requirments.txt
python3 setup.py build
python3 setup.py install
```

## Usage
Open two terminals
1. In one terminal start the ryu controller
```
./start run
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

To exit the  mininet console type "exit" in the console (without the quotes)
To close the ryu controller use the close.sh script
```bash
./close.sh
```

## License
[Apache 2.0](http://www.apache.org/licenses/)
