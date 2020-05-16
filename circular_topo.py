from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

link = dict(bw = 10, delay='5ms', loss=0, max_queue_size=500, use_htb=True)
links2h2 = dict(bw = 10, delay='5ms', loss=0, max_queue_size=500, use_htb=True)
links1s2 = dict(bw = 10, delay='5ms', loss=0, max_queue_size=500, use_htb=True)
class MyTopo( Topo ):
        "Simple topology"

        def __init__( self ):
                "Creat topo"
                size = 20

                Topo.__init__( self )
                switches = [None]*size
                hosts = [None]*size
                for i in  range(1,size):
                   switches[i] = self.addSwitch('s{}'.format(i))

                for i in range(1,size):
                   hosts[i] = self.addHost('h{}'.format(i))

                #add links
                for i in range(1,size-1):
                    self.addLink(switches[i], switches[i+1])
                self.addLink(switches[size-1], switches[1])
                '''
                This is a more symmetric connection
                '''
                self.addLink(switches[3], switches[13])
                #self.addLink(switches[5], switches[15],loss=15)
                self.addLink(switches[17], switches[8])
                self.addLink(switches[5], switches[15], delay='100ms')
 
                for i in range(1,size):
                    self.addLink(hosts[i], switches[i])
topos = { 'mytopo': ( lambda: MyTopo() ) }
