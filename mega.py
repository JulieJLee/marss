#!/usr/bin/env python3

import csv
import os, glob
import numpy as np
import configparser
import matplotlib
matplotlib.use('agg')

import matplotlib.pyplot as plt

from argparse import ArgumentParser
from math import log
from collections import OrderedDict
from collections import defaultdict

MAX_ADDR_LEN = 40

class LRUSet:
    def __init__(self, capacity: int):
        self.set = OrderedDict()
        self.capacity = capacity

    # return whether latest access was a hit (true)
    # key = tag, value = dirty
    def update(self, key: int, dirty: bool) -> (bool, int):
        hit = False
        victim_addr = -1
        # miss
        if key not in self.set:
            # at capacity, need to evict
            if len(self.set) >= self.capacity:
                victim = self.set.popitem(last = False)
                # if dirty
                if victim[1]:
                    victim_addr = victim[0]

            # insert new line, update lru
            self.set[key] = dirty
            self.set.move_to_end(key)

        # hit, update lru
        else:
            self.set[key] = dirty
            self.set.move_to_end(key)
            hit = True

        return (hit, victim_addr)

    def clear(self) -> None:
        self.set.clear()

def pdf(arr):
    pdf = arr / np.sum(arr) * 100
    return range(len(arr)), pdf

def sorted_pdf(arr):     
    arr_sorted = np.sort(arr)[::-1]     
    sorted_pdf = arr_sorted / np.sum(arr_sorted) * 100
    return range(len(arr_sorted)), sorted_pdf 

def cdf(arr):     
    arr_sorted = np.sort(arr)[::-1]     
    cumsum = np.cumsum(arr_sorted)       
    cdf = (cumsum / cumsum[-1]) * 100            
    return range(len(arr_sorted)), cdf  

def quartile(cdf):
    first = (sum(cdf <= 25) / len(cdf)) * 100
    second = (sum(cdf <= 50) / len(cdf)) * 100
    third = (sum(cdf <= 75) / len(cdf)) * 100
    return first, second, third
 
class Cache(LRUSet):
    def __init__(self, cache_type: str, set_bit_pos: str, line_size: str, associativity: str):
        # initialize cache level
        self.type = cache_type
        self.set_bit_pos_str = set_bit_pos
        self.assoc = associativity
        self.set_bit_pos = list(map(int, set_bit_pos.split(",")))
        self.set_bit_len = len(self.set_bit_pos)
        self.num_sets = 2 ** self.set_bit_len
        self.cache = []
        for i in range(self.num_sets):
            self.cache.append(LRUSet(int(associativity)))
        self.offset_bit_len = int(log(int(line_size)) / log(2))
        bit_pos_without_offset = set(range(self.offset_bit_len, MAX_ADDR_LEN))
        self.tag_bit_pos = list(set(self.set_bit_pos) ^ bit_pos_without_offset)
        # initialize statistics collection
        self.trace = []
        self.set_arr = np.zeros((self.num_sets,), dtype=int) 
        self.addr_dict = defaultdict(int)
        self.hit_ctr = 0
        self.miss_ctr = 0

    def hash_address(self, addr: int, bit_pos_list: list) -> int: 
        val = 0
        for i in range(len(bit_pos_list)):
            val += (((addr >> bit_pos_list[i]) & 1) << i)
        return val

    # access cache, returns addresses to forward
    def access(self, addr: int, access_type: str) -> list:
        # forward requests on a miss or eviction
        access_lower = [(0, "N"), (0, "N")]
        # calculate set index and tag value
        set_index = self.hash_address(addr, self.set_bit_pos)
        tag_val = self.hash_address(addr, self.tag_bit_pos)

        # access cache
        is_write = True if access_type == "W" else False
        hit, victim_tag = self.cache[set_index].update(tag_val, is_write)

        if hit:
            self.trace.append([addr, access_type, "H"])
            self.hit_ctr += 1
        else: 
            # if an eviction occurred
            if (victim_tag >= 0):
                # calculate the address of the eviction victim
                victim_addr = 0
                for i in range(len(self.set_bit_pos)): 
                    victim_addr += (((set_index >> i ) & 1) << self.set_bit_pos[i])
                for i in range(len(self.tag_bit_pos)): 
                    victim_addr += (((victim_tag >> i ) & 1) << self.tag_bit_pos[i])

                access_lower[0] = (victim_addr, "W")


            self.trace.append([addr, access_type, "M"])
            access_lower[1] = (addr, access_type)

            # statistics logging 
            self.miss_ctr += 1
            self.set_arr[set_index] += 1
            self.addr_dict[addr] += 1
                
        return access_lower
        
    def write_sim(self, app_name: str): 
        global counter
        counter = 0
        sim_output = output_filename(app_name, self.type, "sim", counter, "csv")
        while os.path.isfile(sim_output):
            counter += 1
            sim_output = output_filename(app_name, self.type, "sim", counter, "csv")
        print("Writing output to: ", sim_output)

        with open(sim_output, 'w') as sim:
            write = csv.writer(sim)
            write.writerows(self.trace)
    
    def write_stat(self, app_name: str):
        # statistics output
        stat_output = output_filename(app_name, self.type, "stat", counter, "csv")
        print("Writing output to: ", stat_output)
        
        total_access = self.hit_ctr + self.miss_ctr
        hit_ratio = (float(self.hit_ctr) / float(total_access)) * 100
        miss_ratio = (float(self.miss_ctr) / float(total_access)) * 100

        set_cdf_x, set_cdf_y = cdf(self.set_arr)
        set_first, set_second, set_third = quartile(set_cdf_y)

        addr_dict_values = np.array(list(self.addr_dict.values()))
        addr_cdf_x, addr_cdf_y = cdf(addr_dict_values)
        addr_first, addr_second, addr_third = quartile(addr_cdf_y)

        stat_summary = OrderedDict()
        stat_summary['total_hit'] = self.hit_ctr
        stat_summary['total_miss'] = self.miss_ctr
        stat_summary['total_access'] = total_access
        stat_summary['hit_ratio'] = hit_ratio
        stat_summary['miss_ratio'] = miss_ratio
        stat_summary['set_25%'] = set_first
        stat_summary['set_50%'] = set_second
        stat_summary['set_75%'] = set_third
        stat_summary['addr_25%'] = addr_first
        stat_summary['addr_50%'] = addr_second
        stat_summary['addr_75%'] = addr_third

        with open(stat_output, 'w', newline='') as stat:
            stat.write("Set bits: " + self.set_bit_pos_str + "\n")
            stat.write("Associativity: " + self.assoc + "\n")
            writer = csv.writer(stat)
            for key, value in stat_summary.items():
                writer.writerow([key, value])
           

    def write_plot(self, app_name: str):
        # plot output
        plot_output = output_filename(app_name, cache_type, "plot", counter, "png")
        print("Writing output to: ", plot_output)



def setup_options():
    arg = ArgumentParser()
    arg.add_argument('trace_path')
    arg.add_argument('config_path')

    return arg

# instantiate the cache levels
def setup_cache():
    # global l1
    global l2
    l2_conf = config["L2"]
    l2 = Cache("L2", l2_conf["SET_BITS"], l2_conf["LINE_SIZE"], l2_conf["ASSOC"])
    global l3
    l3_conf = config["L3"]
    l3 = Cache("L3", l3_conf["SET_BITS"], l3_conf["LINE_SIZE"], l3_conf["ASSOC"])

# returns a filename 
def output_filename(app_name, cache_type, data_type, counter, ext):
    return app_name + "_" + cache_type + "_" + data_type + "_" + str(counter).zfill(2) + "." + ext

# setup the statistics files
def stats():
    print("Parsing: ", args.trace_path)

    app_name = (os.path.splitext(args.trace_path)[0]).partition('_')[0]

def simulate():
    with open(args.trace_path) as input_trace:
        csv_reader = csv.reader(input_trace)
        for row in csv_reader:
            addr = int(row[0])
            access_type = row[1]
            [l2_evict, l2_miss] = l2.access(addr, access_type)

            # if there was an eviction
            if (l2_evict[1] != "N"):
                [l3_evict_1, l3_miss_1] = l3.access(l2_evict[0], l2_evict[1])
            # if there was a miss
            if (l2_miss[1] != "N"):
                [l3_evict_2, l3_miss_2] = l3.access(l2_miss[0], l2_miss[1])



def test():
    [l2_evict, l2_miss] = l2.access(0, "R")
    print(l2_evict)
    print(l2_miss)
    # if there was an eviction
    if (l2_evict[1] != "N"):
        [l3_evict_1, l3_miss_1] = l3.access(l2_evict[0], l2_evict[1])
    # if there was a miss
    if (l2_miss[1] != "N"):
        [l3_evict_2, l3_miss_2] = l3.access(l2_miss[0], l2_miss[1])

    print(l2.trace)
    print(l3.trace)

if __name__ == "__main__":
    # parse input arguments
    opt = setup_options()
    args = opt.parse_args()
    
    # parse the config file
    config = configparser.ConfigParser()
    config.read(args.config_path)

    # setup cache
    setup_cache()

    # simulate cache
    simulate()

    # statistics parsing
    #stats()
    l2.write_sim('sanity')
    l2.write_stat('sanity')
