from time import sleep, time
from subprocess import *
import re

class QueueMonitor:
    def __init__(self):
        self.queue_len = []
        self.iface_list = ["s2-eth2", "s3-eth2", "s4-eth2", "s5-eth3", "s15-eth2", "s3-eth3", "s13-eth2", "s14-eth2"]
        self.iface_dict = {}
        self.iface_dict["s2-eth2"] = "2--3"
        self.iface_dict["s3-eth2"] = "3--4"
        self.iface_dict["s4-eth2"] = "4--5"
        self.iface_dict["s5-eth3"] = "5--15"
        self.iface_dict["s15-eth2"] = "15--16"
        self.iface_dict["s3-eth3"] = "3--13"
        self.iface_dict["s13-eth2"] = "13--14"
        self.iface_dict["s14-eth2"] = "14--15"
        self.monitor_qlen(self.iface_list)
        #monitor_qlen(["s5-eth3", "s5-eth2"], 1)

    def get_qlen_list(self):
        self.monitor_qlen(self.iface_list)
        print("Queue Monitor: get_qlen_list:", self.queue_len)
        return self.queue_len
    def monitor_qlen(self, iface):
        pat_queued = re.compile(r'backlog\s[^\s]+\s([\d]+)p')
        i = 0
        cmd_list = []
        for x in iface:
            cmd = "tc -s qdisc show dev %s" % (x)
            #print("command is:", cmd)
            cmd_list.append((cmd, x))
            
        print("----------------------------------------------------")
        self.queue_len = []
        for i in range(len(cmd_list)):
            self.queue_len.append(self.get_qlen(cmd_list[i], pat_queued))

    def get_qlen(self, cmd, pat_queued):
        p = Popen(cmd[0], shell=True, stdout=PIPE)
        output = p.stdout.read()

        # Not quite right, but will do for now
        matches = pat_queued.findall(output.decode('utf-8'))
        if len(matches) > 0:
            #print("output is:", output.decode('utf-8'))
            #print("matches = ",int(matches[0]))
            percentage = self.get_percentage(int(matches[0]))
            #print("Percentage free queue is for link:", self.iface_dict[cmd[1]], percentage)
            return percentage
        return 100

    def get_percentage(self, matches):
        percentage = ((1000-matches)/1000)*100
        return percentage
