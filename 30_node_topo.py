from mininet.topo import Topo

class MyTopo( Topo ):
        "Simple topology"

        def __init__( self ):
                "Creat topo"

                Topo.__init__( self )
                switches = [None]*31
                hosts = [None]*31
                for i in  range(1,31):
                   switches[i] = self.addSwitch('s{}'.format(i))

                for i in [1, 2, 7, 10, 15, 18, 21, 27, 30]:
                   hosts[i] = self.addHost('h{}'.format(i))

                #add links
                self.addLink(switches[1], switches[2])
                self.addLink(switches[2], switches[3])
                self.addLink(switches[3], switches[4])
                self.addLink(switches[4], switches[5])
                self.addLink(switches[5], switches[6])
                self.addLink(switches[6], switches[1])
                self.addLink(switches[7], switches[8])
                self.addLink(switches[8], switches[9])
                self.addLink(switches[9], switches[10])
                self.addLink(switches[10], switches[11])
                self.addLink(switches[11], switches[12])
                self.addLink(switches[12], switches[7])
                self.addLink(switches[13], switches[14])
                self.addLink(switches[14], switches[15])
                self.addLink(switches[15], switches[16])
                self.addLink(switches[16], switches[17])
                self.addLink(switches[17], switches[18])
                self.addLink(switches[18], switches[13])
                self.addLink(switches[19], switches[20])
                self.addLink(switches[20], switches[21])
                self.addLink(switches[21], switches[22])
                self.addLink(switches[22], switches[23])
                self.addLink(switches[23], switches[24])
                self.addLink(switches[24], switches[19])
                self.addLink(switches[25], switches[26])
                self.addLink(switches[26], switches[27])
                self.addLink(switches[27], switches[28])
                self.addLink(switches[28], switches[29])
                self.addLink(switches[29], switches[30])
                self.addLink(switches[30], switches[25])
                self.addLink(switches[3], switches[12])
                self.addLink(switches[10], switches[14])
                self.addLink(switches[17], switches[22])
                self.addLink(switches[19], switches[28])
                self.addLink(switches[25], switches[5])
                self.addLink(switches[4], switches[13])
                self.addLink(switches[4], switches[20])
                self.addLink(switches[27], switches[11])
                self.addLink(switches[18], switches[28])
                self.addLink(switches[12], switches[21])
                
                for i in [1, 2, 7, 10, 15, 18, 21, 27, 30]:
                    self.addLink(hosts[i], switches[i])
topos = { 'mytopo': ( lambda: MyTopo() ) }
