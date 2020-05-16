from scapy.all import *
import threading
import time

def send_packet(x,count):
    s = time.time()
    print("sending between: ",x.src, x.dst)
    send([x]*count,verbose=False)
    print("time take = ", time.time() - s)
    print("done sending between: ",x.src, x.dst)


a=IP(ttl=64)/UDP()
b=IP(ttl=64)/UDP()
c=IP(ttl=64)/UDP()
d=IP(ttl=64)/UDP()
e=IP(ttl=64)/UDP()

a.src="10.0.0.2"
a.dst="10.0.0.15"

b.src="10.0.0.4"
b.dst="10.0.0.16"

c.src="10.0.0.3"
c.dst="10.0.0.12"
count = 200000
traffic_count = count
#th_a = threading.Thread(target=send_packet, args=(a,traffic_count))
th_b = threading.Thread(target=send_packet, args=(b,traffic_count))
th_c = threading.Thread(target=send_packet, args=(c,traffic_count))
print("starting target transfer")
start_time = time.time()
send_packet(a, count)
end_time = time.time()
print("Total time = ", end_time - start_time)

