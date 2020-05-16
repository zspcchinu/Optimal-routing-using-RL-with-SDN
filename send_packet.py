from scapy.all import *

#x=IP(ttl=64)
#x.src="10.0.0.1"
#x.dst="10.0.0.3"
#send([x]*50000)

x=IP(ttl=64)
if h1:
    x.src="10.0.0.1"
    x.dst="10.0.0.3"
if h2:
    x.src="10.0.0.2"
    x.dst="10.0.0.6"
if h3:
    x.src="10.0.0.3"
    x.dst="10.0.0.12"
if h4:
    x.src="10.0.0.4"
    x.dst="10.0.0.15"
if h5:
    x.src="10.0.0.5"
    x.dst="10.0.0.17"
send([x]*50000)
