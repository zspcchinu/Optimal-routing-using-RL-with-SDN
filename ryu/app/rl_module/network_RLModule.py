#Q-Learning Reinforcement Module

import logging
import os
from queue import Queue
from threading import Thread, Lock
from time import time, sleep
import networkx as nx
import numpy as np
import random
import configparser
import matplotlib.pyplot as plt

Q_table_list = None

class QLearningThread(Thread):

    def __init__(self, network_data, goal, lock, topology, thread_iteration_checker, network_parameter, reward,penalty,threshold, action_selection):
        Thread.__init__(self)
        self.topology = topology
        self.awareness = network_data
        self.dest = goal
        self.lock = lock
        self.episodes_completed = thread_iteration_checker
        self.network_param = network_parameter
        self.condition = "greater"
        #for bandwidth and free queue parameters, congestion occurs when the measured data is lesser than the pre-defined threshold
        if(network_parameter == "bandwidth" or network_parameter == "free_queue"):	
            self.condition = "lesser"
        self.reward = reward
        self.penalty = penalty
        self.threshold = threshold
        self.action_selection_approach = action_selection
        self.initialize_Q_matrix()
        self.initialize_reward_matrix()
        print("RL Module: Thread created for destination: ",self.dest)

    def initialize_reward_matrix(self):        
        global Q_table_list
        self.R = np.matrix(np.zeros(shape=(len(Q_table_list[self.dest]),len(Q_table_list[self.dest]))))
        for x in self.topology[self.dest]:
            self.R[x,self.dest] = 100                #assign reward of 100 for direct links to the destination node
            
    def initialize_Q_matrix(self):
        global Q_table_list
        Q_table_list[self.dest] = np.matrix(np.zeros(shape=(len(Q_table_list[self.dest]),len( Q_table_list[self.dest]))))
        Q_table_list[self.dest] -= 100
        for node in self.topology.nodes:
            for x in self.topology[node]:
                Q_table_list[self.dest][node,x]=0
                Q_table_list[self.dest][x,node]=0        
        
    def run(self):
        global Q_table_list
        current_version=-1
        while True:
            sleep(10)
            ryu_version = self.awareness.version
            if current_version >= ryu_version:
                continue            
            current_version = ryu_version
            topology_info = self.awareness.graph
            try:
                #initialize the hyper-parameters for the algorithm
                er=0.5
                lr=0.8
                discount=0.8                
                gamma=0.7
                iterations=1500

                self.initialize_reward_matrix()

                if self.network_param == "free_queue":
                    temp_edge_list=[(2,3),(3,4),(4,5),(5,15),(15,16),(3,13),(13,14),(14,15)] 
                    for i in range(len(self.awareness.queue_list)):
                        start = temp_edge_list[i][0]
                        next_node = temp_edge_list[i][1]
                        if(self.checkIfThresholdExceeded(self.awareness.queue_list[i])):                             
                            if next_node==self.dest:                                    
                                self.R[start,next_node]=self.reward
                            else:                                    
                                self.R[start,next_node]=self.penalty
                else:
                    for x in topology_info:
                        for y in topology_info[x]:
                            start = x
                            next_node = y
                            pkt_rate = 0
                            if self.network_param in topology_info[x][y]: 
                                measured_param = topology_info[x][y][self.network_param]
                                if(self.checkIfThresholdExceeded(measured_param)):
                                    if next_node==self.dest:
                                        self.R[start,next_node]=self.reward
                                    else:
                                        self.R[start,next_node]=self.penalty                                                                                                             

                self.initialize_Q_matrix()
                Q_table = Q_table_list[self.dest]
                for i in range(iterations):
                    start=np.random.randint(1,(len(Q_table)-1))              
                    next_node=self.next_number(start,er,Q_table)                   
                    try:
                        Q_table = self.updateQ(start,next_node,lr,discount,Q_table)   
                    finally:               
                        pass
                    if self.action_selection_approach == "epsilon-greedy-decay":
                        epsilon_decay = 0.999   # decay parameter can be tuned
                        if i%200 == 0:              # decay epsilon for every 200 iterations (can be tuned)
                            er = er * epsilon_decay
                self.lock.acquire()
                Q_table_list[self.dest] = Q_table
                self.lock.release()
                self.episodes_completed = True
            finally:
               pass 
        
    # compare measured data with threshold
    def checkIfThresholdExceeded(self, param):
        res = True
        if self.condition is "greater":
            res = param > self.threshold
        elif self.condition is "lesser":
            res = param < self.threshold
        return res         
                

    def next_number(self,start,er,Q_table):
        next_node = -1

        if self.action_selection_approach == "epsilon-greedy" or self.action_selection_approach == "epsilon-greedy-decay":
            self.random_value=random.uniform(0,1)    
            if self.random_value<er:
                    sample=self.topology[start]
            else:
                    sample=np.where(Q_table[start,]==np.max(Q_table[start,]))[1]            
            next_node=int(np.random.choice(list(sample),1))    
        elif self.action_selection_approach == "boltzmann":  #softmax
            Q_values = Q_table[start,]
            T = 1  # temperature parameter can be tuned
            exp_q_values = np.exp(Q_values/T)
            prob_t = exp_q_values/ np.sum(exp_q_values)    # calculate probability using softmax distribution
            sorted_prob_t = np.sort(prob_t)
            sample = np.where(prob_t == np.max(sorted_prob_t)) # choose action with highest probability
            next_node=int(sample[1])
        elif self.action_selection_approach == "greedy":
            sample=np.where(Q_table[start,]==np.max(Q_table[start,]))[1] 
            next_node=int(np.random.choice(list(sample),1))
        elif self.action_selection_approach == "random": 
            sample=self.topology[start]
            next_node=int(np.random.choice(list(sample),1))

        return next_node

    # calculate Q-values for (node1,node2) and update in Q-table	
    def updateQ(self,node1,node2,lr,discount,Q_table):
        max_index=np.where(Q_table[node2,]==np.max(Q_table[node2,]))[1]
        if max_index.shape[0]>1:
            max_index=int(np.random.choice(max_index,size=1))
        else:
            max_index=int(max_index)
        max_value=Q_table[node2,max_index]
        Q_table[node1,node2]=int((1-lr)*Q_table[node1,node2]+lr*(self.R[node1,node2]+discount*max_value))
        return Q_table



class network_RLModule:    

    def __init__(self,network_data):
        global Q_table_list         
        self.awareness = network_data
        self.lock = Lock()
        self.episodes_completed = False        
        
        while self.awareness.is_ready is False:
            sleep(1)
        self.edges = []

        # create topology graph
        for src in self.awareness.graph:
            for dest in self.awareness.graph[src]:
                edge = (src,dest)
                self.edges.append(edge)
        self.G = nx.Graph()
        self.G.add_edges_from(self.edges)
        self.pos=nx.spring_layout(self.G)        
        
        self.N = self.G.number_of_nodes()+1       #num of nodes
        print("RL Module: Graph created is ", self.G.edges)
        
        self.initialize_rl_properties()
        
        self.initialize_Q_matrix_list()
        print("RL Module: num of nodes ", self.N)
        self.start_threads()

    # read initial properties for RL module from the properties file	
    def initialize_rl_properties(self):
        config = configparser.RawConfigParser()
        config.read('set_rl_properties.properties')

        section_dict = {}

        for section in config.sections():
            section_dict[section] = dict(config.items(section))
    
        self.network_parameter = section_dict['rl_properties']['parameter'] 
        self.reward = int(section_dict['rl_properties']['reward'])
        self.penalty = int(section_dict['rl_properties']['penalty'])
        self.threshold = float(section_dict['rl_properties']['threshold'])
        self.action_selection_approach = section_dict['rl_properties']['action_selection']
        self.awareness.logger.info("----------RL PROPERTIES-------------------")
        self.awareness.logger.info("parameter, reward, penalty, threshold, action selection strategy")
        self.awareness.logger.info((self.network_parameter,self.reward,self.penalty,self.threshold,self.action_selection_approach))
        
    def initialize_Q_matrix_list(self):
        global Q_table_list 
        N =self.N  #number of nodes in topology
        res = [ [ 0 for i in range(N) ] for j in range(N) ] 
        Q_table_list=[res]*N        

    
    def start_threads(self):
        starttime = time()
        global Q_table_list 
        
        thread_iteration_checker = {}
        for i in range(1,self.N):
            thread_iteration_checker[i] = False
        
        
        for destination in range(1,self.N):           #no of switches
            worker = QLearningThread(self.awareness,destination,self.lock, self.G, thread_iteration_checker[destination],
                                     self.network_parameter, self.reward,self.penalty,self.threshold, self.action_selection_approach)                
            worker.start()

    # Calculate the optimal routing path between a given source node and destination node based on the Q-table
    def rl_optimal_path(self,begin,end):
        global Q_table_list 
        
        path=[begin]        
        starttime = time()
        self.lock.acquire()
        local_Q = Q_table_list[end]
        self.lock.release()
        time()
        self.awareness.logger.info("RL MODULE: calculating optimal path between: ")
        self.awareness.logger.info((begin, end))
        next_node=np.argmax(local_Q[begin,])
        path.append(next_node)
        while next_node!=end:
            next_node=np.argmax(local_Q[next_node,])
            path.append(next_node) 
        endtime = time()
        self.awareness.logger.info("RL MODULE: time it took to find the optimal path")
        self.awareness.logger.info(endtime - starttime)
        return path
