# Copyright (C) 2016 Li Cheng at Beijing University of Posts
# and Telecommunications. www.muzixing.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from builtins import range
import copy
from operator import attrgetter
from ryu import cfg
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet
from . import setting
from ryu.app.network_awareness3.queue_monitor import QueueMonitor


CONF = cfg.CONF


class NetworkMonitor(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkMonitor, self).__init__(*args, **kwargs)
        self.name = 'monitor'
        self.datapaths = {}
        self.port_stats = {}
        self.port_speed = {}
        self.port_packet_rate = {}
        self.port_errors = {}
        self.flow_stats = {}
        self.flow_speed = {}
        self.stats = {}
        self.port_link = {}
        self.free_bandwidth = {}
        self.awareness = lookup_service_brick('awareness')
        self.graph = None
        self.error_graph = None
        self.packet_rate_graph = None
        self.q_monitor = QueueMonitor()
        self.monitor_thread = hub.spawn(self._monitor)
        self.save_freebandwidth_thread = hub.spawn(self._save_graphs)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            self.stats['flow'] = {}
            self.stats['port'] = {}
            for dp in list(self.datapaths.values()):
                self.port_link.setdefault(dp.id, {})
                self._request_stats(dp)
            hub.sleep(setting.MONITOR_PERIOD)
            if self.stats['flow'] or self.stats['port']:
                self.show_all_collected_info()
                #self.show_bandwidth()
                #self.show_packet_rate()
                #self.show_errors()
                #commenting out the stats to reduce clutter
                #self.show_stat('flow')
                #self.show_stat('port')
                hub.sleep(1)

    def _save_graphs(self):
        #while CONF.weight == 'bw': Cheenu
        while True:
            self.graph = self.create_bw_graph(self.free_bandwidth)
            self.error_graph = self.create_error_graph(self.port_errors)
            self.packet_rate_graph = self.create_packet_rate_graph(self.port_packet_rate)
            self.logger.debug("save_freebandwidth")
            self.awareness.queue_list = self.q_monitor.get_qlen_list()
            self.awareness.version += 1
            hub.sleep(setting.MONITOR_PERIOD)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortDescStatsRequest(datapath, 0)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    def get_min_bw_of_links(self, graph, path, min_bw):
        _len = len(path)
        if _len > 1:
            minimal_band_width = min_bw
            for i in range(_len-1):
                pre, curr = path[i], path[i+1]
                if 'bandwidth' in graph[pre][curr]:
                    bw = graph[pre][curr]['bandwidth']
                    minimal_band_width = min(bw, minimal_band_width)
                else:
                    continue
            return minimal_band_width
        return min_bw

    def get_best_path_by_bw(self, graph, paths):
        capabilities = {}
        best_paths = copy.deepcopy(paths)

        for src in paths:
            for dst in paths[src]:
                if src == dst:
                    best_paths[src][src] = [src]
                    capabilities.setdefault(src, {src: setting.MAX_CAPACITY})
                    capabilities[src][src] = setting.MAX_CAPACITY
                    continue
                max_bw_of_paths = 0
                best_path = paths[src][dst][0]
                for path in paths[src][dst]:
                    min_bw = setting.MAX_CAPACITY
                    min_bw = self.get_min_bw_of_links(graph, path, min_bw)
                    if min_bw > max_bw_of_paths:
                        max_bw_of_paths = min_bw
                        best_path = path

                best_paths[src][dst] = best_path
                capabilities.setdefault(src, {dst: max_bw_of_paths})
                capabilities[src][dst] = max_bw_of_paths
        return capabilities, best_paths

    def create_packet_rate_graph(self, packet_rate_dict):
        try:
            graph = self.awareness.graph
            link_to_port = self.awareness.link_to_port
            for link in link_to_port:
                (src_dpid, dst_dpid) = link
                (src_port, dst_port) = link_to_port[link]
                if src_dpid in packet_rate_dict and dst_dpid in packet_rate_dict:
                    packet_rate_src = packet_rate_dict[src_dpid][src_port]
                    packet_rate_dst = packet_rate_dict[dst_dpid][dst_port]
                    packet_rates = packet_rate_src + packet_rate_dst
                    graph[src_dpid][dst_dpid]['packet_rate'] = packet_rates 
                else:
                    graph[src_dpid][dst_dpid]['packet_rate'] = 0
            return graph
        except Exception as e:
            self.logger.info("Create packet_rate graph exception")
            if self.awareness is None:
                self.awareness = lookup_service_brick('awareness')
            return self.awareness.graph



    def create_error_graph(self, error_dict):
        try:
            graph = self.awareness.graph
            link_to_port = self.awareness.link_to_port
            for link in link_to_port:
                (src_dpid, dst_dpid) = link
                (src_port, dst_port) = link_to_port[link]
                if src_dpid in error_dict and dst_dpid in error_dict:
                    error_src = error_dict[src_dpid][src_port]
                    error_dst = error_dict[dst_dpid][dst_port]
                    errors = error_src + error_dst
                    graph[src_dpid][dst_dpid]['error'] =errors 
                else:
                    graph[src_dpid][dst_dpid]['error'] = 0
            return graph
        except Exception as e:
            self.logger.info("Create error graph exception")
            print(e.__class__.__name__)
            if self.awareness is None:
                self.awareness = lookup_service_brick('awareness')
            return self.awareness.graph

    def create_bw_graph(self, bw_dict):
        try:
            graph = self.awareness.graph
            link_to_port = self.awareness.link_to_port
            for link in link_to_port:
                (src_dpid, dst_dpid) = link
                (src_port, dst_port) = link_to_port[link]
                if src_dpid in bw_dict and dst_dpid in bw_dict:
                    bw_src = bw_dict[src_dpid][src_port]
                    bw_dst = bw_dict[dst_dpid][dst_port]
                    bandwidth = min(bw_src, bw_dst)
                    graph[src_dpid][dst_dpid]['bandwidth'] = bandwidth
                else:
                    graph[src_dpid][dst_dpid]['bandwidth'] = 0
            return graph
        except Exception as e:
            self.logger.info("Create bw graph exception")
            print(e.__class__.__name__)
            if self.awareness is None:
                self.awareness = lookup_service_brick('awareness')
            return self.awareness.graph

    def _save_freebandwidth(self, dpid, port_no, speed):
        port_state = self.port_link.get(dpid).get(port_no)
        if port_state:
            capacity = port_state[2]
            curr_bw = self._get_free_bw(capacity, speed)
            self.free_bandwidth[dpid].setdefault(port_no, None)
            self.free_bandwidth[dpid][port_no] = curr_bw
        else:
            self.logger.info("Fail in getting port state")

    def _save_error_and_packet_rate(self, dpid, port_no, error, packet_rate):
        port_state = self.port_link.get(dpid).get(port_no)
        if port_state:
            self.port_errors[dpid].setdefault(port_no, None)
            self.port_errors[dpid][port_no] = error 

            self.port_packet_rate[dpid].setdefault(port_no, None)
            self.port_packet_rate[dpid][port_no] = packet_rate 
        else:
            self.logger.info("Fail in getting port state")

    def _save_stats(self, dist, key, value, length):
        if key not in dist:
            dist[key] = []
        dist[key].append(value)

        if len(dist[key]) > length:
            dist[key].pop(0)

    def _get_speed(self, now, pre, period):
        if period:
            return (now - pre) / (period)
        else:
            return 0

    def _get_free_bw(self, capacity, speed):
        # BW:Mbit/s
        return max(capacity / 10**3 - speed * 8, 0)

    def _get_time(self, sec, nsec):
        return sec + nsec / (10 ** 9)

    def _get_period(self, n_sec, n_nsec, p_sec, p_nsec):
        return self._get_time(n_sec, n_nsec) - self._get_time(p_sec, p_nsec)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.stats['flow'][dpid] = body
        self.flow_stats.setdefault(dpid, {})
        self.flow_speed.setdefault(dpid, {})
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match.get('in_port'),
                                             flow.match.get('ipv4_dst'))):
            key = (stat.match['in_port'],  stat.match.get('ipv4_dst'),
                   stat.instructions[0].actions[0].port)
            value = (stat.packet_count, stat.byte_count,
                     stat.duration_sec, stat.duration_nsec)
            self._save_stats(self.flow_stats[dpid], key, value, 5)

            # Get flow's speed.
            pre = 0
            period = setting.MONITOR_PERIOD
            tmp = self.flow_stats[dpid][key]
            if len(tmp) > 1:
                pre = tmp[-2][1]
                period = self._get_period(tmp[-1][2], tmp[-1][3],
                                          tmp[-2][2], tmp[-2][3])

            speed = self._get_speed(self.flow_stats[dpid][key][-1][1],
                                    pre, period)

            self._save_stats(self.flow_speed[dpid], key, speed, 5)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.stats['port'][dpid] = body
        self.free_bandwidth.setdefault(dpid, {})
        self.port_errors.setdefault(dpid, {})
        self.port_packet_rate.setdefault(dpid, {})
        self.logger.debug("Received port status for switch", dpid)

        for stat in sorted(body, key=attrgetter('port_no')):
            port_no = stat.port_no
            if port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (dpid, port_no)
                value = (stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                         stat.duration_sec, stat.duration_nsec,
                         stat.rx_errors, stat.tx_errors, stat.rx_dropped,
                         stat.tx_dropped, stat.rx_packets, stat.tx_packets)

                self._save_stats(self.port_stats, key, value, 5)

                # Get port speed.
                pre = 0
                curr_packet = 0
                period = setting.MONITOR_PERIOD
                pre_packet = 0
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    pre = tmp[-2][0] + tmp[-2][1]
                    period = self._get_period(tmp[-1][3], tmp[-1][4],
                                              tmp[-2][3], tmp[-2][4])
                    pre_packet = tmp[-2][9] + tmp[-2][10]

                curr_packet = self.port_stats[key][-1][9] + self.port_stats[key][-1][10]

                speed = self._get_speed(
                    self.port_stats[key][-1][0] + self.port_stats[key][-1][1],
                    pre, period)

                packet_rate = self._get_speed(curr_packet,
                     pre_packet, period)

               # Get port packet errors
                errors_in_period = 0
                if len(tmp) > 1:
                    curr_port_errors = tmp[-1]
                    prev_port_errors = tmp[-2]
                    curr_total_errors = sum(curr_port_errors[5:8+1]) 
                    prev_total_errors = sum(prev_port_errors[5:8+1]) 
                    errors_in_period = prev_total_errors - curr_total_errors

                self._save_stats(self.port_speed, key, speed, 5)
                self._save_error_and_packet_rate(dpid, port_no, errors_in_period, packet_rate)
                self._save_freebandwidth(dpid, port_no, speed)

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        msg = ev.msg
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        config_dist = {ofproto.OFPPC_PORT_DOWN: "Down",
                       ofproto.OFPPC_NO_RECV: "No Recv",
                       ofproto.OFPPC_NO_FWD: "No Forward",
                       ofproto.OFPPC_NO_PACKET_IN: "No Packet-in"}

        state_dist = {ofproto.OFPPS_LINK_DOWN: "Down",
                      ofproto.OFPPS_BLOCKED: "Blocked",
                      ofproto.OFPPS_LIVE: "Live"}

        ports = []
        for p in ev.msg.body:
            ports.append('port_no=%d hw_addr=%s name=%s config=0x%08x '
                         'state=0x%08x curr=0x%08x advertised=0x%08x '
                         'supported=0x%08x peer=0x%08x curr_speed=%d '
                         'max_speed=%d' %
                         (p.port_no, p.hw_addr,
                          p.name, p.config,
                          p.state, p.curr, p.advertised,
                          p.supported, p.peer, p.curr_speed,
                          p.max_speed))

            if p.config in config_dist:
                config = config_dist[p.config]
            else:
                config = "up"

            if p.state in state_dist:
                state = state_dist[p.state]
            else:
                state = "up"

            port_feature = (config, state, p.curr_speed)
            self.port_link[dpid][p.port_no] = port_feature

    @set_ev_cls(ofp_event.EventOFPQueueStatsReply, MAIN_DISPATCHER)
    def queue_stats_reply_handler(self, ev):
        queues = []
        for stat in ev.msg.body:
            queues.append('port_no=%d queue_id=%d '
                    'tx_bytes=%d tx_packets=%d tx_errors=%d '
                    'duration_sec=%d duration_nsec=%d' %
                    (stat.port_no, stat.queue_id,
                     stat.tx_bytes, stat.tx_packets, stat.tx_errors,
                     stat.duration_sec, stat.duration_nsec))
        self.logger.debug('QueueStats: %s', queues)


    @set_ev_cls(ofp_event.EventOFPGetAsyncReply, MAIN_DISPATCHER)
    def get_async_reply_handler(self, ev):
        msg = ev.msg

        self.logger.info('OFPGetAsyncReply received: '
                    'packet_in_mask=0x%08x:0x%08x '
                    'port_status_mask=0x%08x:0x%08x '
                    'flow_removed_mask=0x%08x:0x%08x',
                    msg.packet_in_mask[0],
                    msg.packet_in_mask[1],
                    msg.port_status_mask[0],
                    msg.port_status_mask[1],
                    msg.flow_removed_mask[0],
                    msg.flow_removed_mask[1])


    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        reason_dict = {ofproto.OFPPR_ADD: "added",
                       ofproto.OFPPR_DELETE: "deleted",
                       ofproto.OFPPR_MODIFY: "modified", }

        if reason in reason_dict:

            print("switch%d: port %s %s" % (dpid, reason_dict[reason], port_no))
            if reason is ofproto.OFPPR_MODIFY:
                '''
                For debugging, uncomment if you want to test
                #send_async_request()
                '''
                
        else:
            print("switch%d: Illeagal port state %s %s" % (port_no, reason))

    def send_async_request(self):
        ofp_parser = msg.datapath.ofproto_parser
        req = ofp_parser.OFPGetAsyncRequest(msg.datapath)
        msg.datapath.send_msg(req)
        self.logger.info("sent async request")

    def show_all_collected_info(self):
        '''
        Prints the all collected info for each of the links in the 
        graph/topology
        '''
        self.logger.info("\nsrc   dst      bandwidth                      packet_rate             error")
        self.logger.info("------------------------------------------------------------------------------")
 
        for src in self.graph:
            for dst in self.graph[src]:
                bandwidth = -1
                error = -1
                packet_rate = -1
                if 'bandwidth' in self.graph[src][dst]:
                    bandwidth = self.graph[src][dst]['bandwidth']
                if 'packet_rate' in self.graph[src][dst]:
                    packet_rate = self.graph[src][dst]['packet_rate']
                if 'error' in self.graph[src][dst]:
                    error = self.graph[src][dst]['error']
                if packet_rate is -1 and error is -1 and bandwidth is -1:
                    continue
                else:
                    self.awareness.is_ready = True
                    self.logger.info("%s<-->%s : %d                        %d        %d" % (src, dst, bandwidth, packet_rate, error))

    def show_bandwidth(self):
        '''
        Prints the bandwith for each of the links in the 
        graph/topology
        '''
        self.logger.info("\nsrc   dst      bandwidth")
        self.logger.info("---------------------------")
 
        for src in self.graph:
            for dst in self.graph[src]:
                if 'bandwidth' in self.graph[src][dst]:
                    bandwidth = self.graph[src][dst]['bandwidth']
                    self.logger.info("%s<-->%s : %s" % (src, dst, bandwidth))
                else:
                    continue

    def show_packet_rate(self):
        '''
        Prints the packet rate for each of the links in the 
        graph/topology
        '''
        self.logger.info("\nsrc   dst      packet_rate")
        self.logger.info("---------------------------")
 
        for src in self.graph:
            for dst in self.graph[src]:
                if 'packet_rate' in self.graph[src][dst]:
                    packet_rate = self.graph[src][dst]['packet_rate']
                    self.logger.info("%s<-->%s : %s" % (src, dst, packet_rate))
                else:
                    continue

    def show_errors(self):
        '''
        Prints the errors for each of the links in the 
        graph/topology
        '''
        self.logger.info("\nsrc   dst      errors")
        self.logger.info("---------------------------")
 
        for src in self.graph:
            for dst in self.graph[src]:
                if 'error' in self.graph[src][dst]:
                    packet_rate = self.graph[src][dst]['error']
                    self.logger.info("%s<-->%s : %s" % (src, dst, packet_rate))
                else:
                    continue

    def show_stat(self, type):
        '''
            type: 'port' 'flow'
        '''
        if setting.TOSHOW is False:
            return

        bodys = self.stats[type]
        if(type == 'flow'):
            print('datapath         ''   in-port        ip-dst      '
                  'out-port packets  bytes  flow-speed(B/s)')
            print('---------------- ''  -------- ----------------- '
                  '-------- -------- -------- -----------')
            for dpid in list(bodys.keys()):
                for stat in sorted(
                    [flow for flow in bodys[dpid] if flow.priority == 1],
                    key=lambda flow: (flow.match.get('in_port'),
                                      flow.match.get('ipv4_dst'))):
                    print('%016x %8x %17s %8x %8d %8d %8.1f' % (
                        dpid,
                        stat.match['in_port'], stat.match['ipv4_dst'],
                        stat.instructions[0].actions[0].port,
                        stat.packet_count, stat.byte_count,
                        abs(self.flow_speed[dpid][
                            (stat.match.get('in_port'),
                            stat.match.get('ipv4_dst'),
                            stat.instructions[0].actions[0].port)][-1])))
            print('\n')

        if(type == 'port'):
            print('datapath             port   ''rx-pkts  rx-bytes rx-error '
                  'tx-pkts  tx-bytes tx-error  port-speed(B/s)'
                  ' current-capacity(Kbps)  '
                  'port-stat   link-stat')
            print('----------------   -------- ''-------- -------- -------- '
                  '-------- -------- -------- '
                  '----------------  ----------------   '
                  '   -----------    -----------')
            format = '%016x %8x %8d %8d %8d %8d %8d %8d %8.1f %16d %16s %16s'
            for dpid in list(bodys.keys()):
                for stat in sorted(bodys[dpid], key=attrgetter('port_no')):
                    if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                        print(format % (
                            dpid, stat.port_no,
                            stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                            stat.tx_packets, stat.tx_bytes, stat.tx_errors,
                            abs(self.port_speed[(dpid, stat.port_no)][-1]),
                            self.port_link[dpid][stat.port_no][2],
                            self.port_link[dpid][stat.port_no][0],
                            self.port_link[dpid][stat.port_no][1]))
            print('\n')
