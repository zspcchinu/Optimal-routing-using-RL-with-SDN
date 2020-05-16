from mininet.topo import Topo

class MyTopo( Topo ):
        "Simple topology"

        def __init__( self ):
                "Creat topo"
                size = 11

                Topo.__init__( self )
                switches = [None]*size
                for i in  range(1,size):
                   switches[i] = self.addSwitch('s{}'.format(i))

                src = self.addHost("h1")
                dest = self.addHost("h2")
                #add links

                self.addLink(switches[1], switches[2])
                self.addLink(switches[2], switches[3])
                self.addLink(switches[3], switches[4])
                self.addLink(switches[4], switches[5])
                self.addLink(switches[5], switches[10])
                self.addLink(switches[2], switches[6])
                self.addLink(switches[6], switches[7])
                #self.addLink(switches[7], switches[8])
                self.addLink(switches[8], switches[9])
                self.addLink(switches[9], switches[10])
                '''
                self.addLink(switches[6], switches[10])
                self.addLink(switches[10], switches[11])
                self.addLink(switches[11], switches[12])
                self.addLink(switches[12], switches[13])
                self.addLink(switches[13], switches[14])
                '''

                self.addLink(src, switches[1])
                self.addLink(dest, switches[size-1])
                '''
                This is for a 6 node topology
                self.addLink(switches[1], switches[2])
                self.addLink(switches[5], switches[2])
                #self.addLink(switches[1], switches[3])
                #self.addLink(switches[3], switches[2])
                self.addLink(switches[3], switches[5])
                #self.addLink(switches[3], switches[4])
                self.addLink(switches[1], switches[4])
                self.addLink(switches[5], switches[4])
                self.addLink(src, switches[1])
                self.addLink(dest, switches[5])
                '''
                '''
                Following are links for 8 node topology
                self.addLink(switches[1], switches[2])
                self.addLink(switches[2], switches[3])
                self.addLink(switches[3], switches[4])
                self.addLink(switches[5], switches[6])
                self.addLink(switches[6], switches[7])
                self.addLink(switches[7], switches[8])
                self.addLink(switches[1], switches[5])
                self.addLink(switches[4], switches[8])
                self.addLink(switches[2], switches[6])
                self.addLink(switches[3], switches[7])
                self.addLink(switches[1], switches[6])
                self.addLink(switches[2], switches[5])
                self.addLink(switches[2], switches[7])
                self.addLink(switches[3], switches[6])
                self.addLink(switches[3], switches[7])
                self.addLink(switches[4], switches[8])
                self.addLink(src, switches[1])
                self.addLink(dest, switches[8])
                '''
topos = { 'mytopo': ( lambda: MyTopo() ) }
