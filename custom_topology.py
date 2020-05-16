from mininet.topo import Topo

class MyTopo( Topo ):
        "Simple topology"

        def __init__( self ):
                "Creat topo"

                Topo.__init__( self )

                firstSwitch = self.addSwitch( 's1' )
                secondSwitch = self.addSwitch( 's2' )
                thridSwitch = self.addSwitch( 's3' )
                fourthSwitch = self.addSwitch('s4')
                firstHost = self.addHost( 'h1' )
                secondHost = self.addHost( 'h2' )
                thirdHost = self.addHost( 'h3' )
                fourthHost = self.addHost( 'h4' )
                fifthHost = self.addHost( 'h5' )

                #add links
                self.addLink(firstHost, firstSwitch)
                self.addLink(secondHost, firstSwitch)
                self.addLink(thirdHost, secondSwitch)
                self.addLink(fourthHost, thridSwitch)
                self.addLink(fifthHost, thridSwitch)
                self.addLink(firstSwitch, secondSwitch)
                self.addLink(secondSwitch, thridSwitch)
                self.addLink(fourthSwitch, firstSwitch)
                self.addLink(fourthSwitch, thridSwitch)

topos = { 'mytopo': ( lambda: MyTopo() ) }
