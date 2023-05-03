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

class mLRUSet:
    def __init__(self, capacity: int):
        self.tags = [None] * capacity
        self.mlru = [0] * capacity
        self.dirty = [0] * capacity
        self.capacity = capacity

    def update(self, tag: int, access_type: str) -> (bool, int):
        hit = False
        victim_tag = -1
        victim_way = 0

        # miss
        if tag not in self.tags:
            # need to evict
            if None not in self.tags:
                # index of victim
                vicitm_way = self.mlru.index(0)
                # write-back?
                if self.dirty[victim_way]:
                    victim_tag = self.tags[victim_way]
            else:
                victim_way = self.tags.index(None)

            way = victim_way
            
        # hit
        else:
            hit = True
            way = self.tags.index(tag)
        
        # fill in new request
        self.tags[way] = tag
        self.mlru[way] = 1
        if (access_type == "W" or access_type == "U"):
            self.dirty[way] = 1 
    

        # deadlock prevention
        if 0 not in self.mlru:
            # reset the mrlu 
            self.mlru = [0] * self.capacity
            self.mlru[way] = 1
        
        
        return (hit, victim_tag)

class LRUSet:
    def __init__(self, capacity: int):
        self.set = OrderedDict()
        self.capacity = capacity

    # return whether latest access was a hit (true)
    def update(self, tag: int, access_type: str) -> (bool, int):
        hit = False
        victim_tag = -1

        # miss
        if tag not in self.set:
            # if an update request misses in the cache,
            # it should be forwarded to a lower level
            if (access_type == "U"):
                return (hit, victim_tag)
            else:
                # at capacity, need to evict
                if len(self.set) >= self.capacity:
                    victim = self.set.popitem(last = False)
                    # if write
                    if victim[1]:
                        victim_tag = victim[0]

                self.set[tag] = 0
                # update dirty bit
                if (access_type == "W"):
                    self.set[tag] = 1

                # allocate line
                self.set.move_to_end(tag)

        # hit, update lru
        else:
            if (access_type == "W" or access_type == "U"):    
                self.set[tag] = 1
            self.set.move_to_end(tag)
            hit = True

        return (hit, victim_tag)

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
        hit, victim_tag = self.cache[set_index].update(tag_val, access_type)

        if hit:
            self.trace.append([addr, access_type, "H"])
            # only log for R/W requests
            if (access_type != "U"):
                self.hit_ctr += 1
        else: 
            self.trace.append([addr, access_type, "M"])
            # this is to make sure that only L1 marks a line as modified
            if ("L1" in self.type):
                access_type = "R"

            access_lower[0] = (addr, access_type)

            # only log for R/W requests
            if (access_type != "U"): 
                self.miss_ctr += 1
                self.set_arr[set_index] += 1
                self.addr_dict[addr] += 1

            # eviction needed
            if (victim_tag >= 0):
                # calculate the address of the eviction victim
                victim_addr = 0
                for i in range(len(self.set_bit_pos)): 
                    victim_addr += (((set_index >> i ) & 1) << self.set_bit_pos[i])
                for i in range(len(self.tag_bit_pos)): 
                    victim_addr += (((victim_tag >> i ) & 1) << self.tag_bit_pos[i])

                access_lower[1] = (victim_addr, "U")
                
        return access_lower
        
    def write_sim(self, output: str): 
        sim_output = output_filename(output, self.type, "sim", id, "csv")
        print("Writing output to: ", sim_output)

        with open(sim_output, 'w') as sim:
            write = csv.writer(sim)
            write.writerows(self.trace)
     
    def write_stat(self, output: str):
        # statistics output
        stat_output = output_filename(output, self.type, "stat", id, "csv")
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
           

    def write_plot(self, output: str):
        # plot output
        plot_output = output_filename(output, self.type, "plot", id, "png")
        print("Writing output to: ", plot_output)

        pdf_x, pdf_y = pdf(self.set_arr)
        sorted_pdf_x, sorted_pdf_y = sorted_pdf(self.set_arr)

        fig, axs = plt.subplots(2, 2, figsize=(16,6))
        axs[0,0].set_title('PDF')
        axs[0,0].plot(pdf_x, pdf_y)
        axs[0,0].set_xlabel('Sets')
        axs[0,0].set_ylabel('% of Total Cache Misses')
        axs[0,0].set_xlim([0,pdf_x[-1]])
        axs[0,0].grid(True)

        axs[0,1].set_title('Sorted PDF')
        axs[0,1].plot(sorted_pdf_x, sorted_pdf_y)
        axs[0,1].set_xlabel('Sets Sorted in Descending Order of Misses')
        axs[0,1].set_ylabel('% of Total Cache Misses')
        axs[0,1].set_xlim([0,sorted_pdf_x[-1]])
        axs[0,0].grid(True)
        axs[0,1].grid(True)

        addr_dict_values = np.array(list(self.addr_dict.values()))
        pdf_x, pdf_y = pdf(addr_dict_values)
        sorted_pdf_x, sorted_pdf_y = sorted_pdf(addr_dict_values)

        axs[1,0].set_title('PDF')
        axs[1,0].plot(pdf_x, pdf_y)
        axs[1,0].set_xlabel('Addresses')
        axs[1,0].set_ylabel('% of Total Cache Misses')
        axs[1,0].set_xlim([0,pdf_x[-1]])
        axs[1,0].grid(True)

        axs[1,1].set_title('Sorted PDF')
        axs[1,1].plot(sorted_pdf_x, sorted_pdf_y)
        axs[1,1].set_xlabel('Addresses Sorted in Descending Order of Misses')
        axs[1,1].set_ylabel('% of Total Cache Misses')
        axs[1,1].set_xlim([0,sorted_pdf_x[-1]])
        axs[1,1].grid(True)

        fig.suptitle(app_name + " " + self.type + " " + str(id))
        fig.tight_layout()
        fig.savefig(plot_output)
        fig.clf() 



def setup_options():
    arg = ArgumentParser()
    arg.add_argument('trace_path')
    arg.add_argument('config_path')
    arg.add_argument('output_dirpath')

    return arg

# instantiate the cache levels
def setup_cache():
    global l1d
    l1_conf = config["L1"]
    l1d = Cache("L1_D", l1_conf["SET_BITS"], l1_conf["LINE_SIZE"], l1_conf["ASSOC"])
    
    global l1i
    l1i = Cache("L1_I", l1_conf["SET_BITS"], l1_conf["LINE_SIZE"], l1_conf["ASSOC"])

    global l2
    l2_conf = config["L2"]
    l2 = Cache("L2", l2_conf["SET_BITS"], l2_conf["LINE_SIZE"], l2_conf["ASSOC"])

    global l3
    l3_conf = config["L3"]
    l3 = Cache("L3", l3_conf["SET_BITS"], l3_conf["LINE_SIZE"], l3_conf["ASSOC"])

# returns a filename 
def output_filename(app_name, cache_type, data_type, id, ext):
    return app_name + "_" + cache_type + "_" + data_type + "_" + str(id).zfill(2) + "." + ext

# setup the statistics files
def setup_stat():
    global id
    global app_name
    print("Parsing: ", args.trace_path)

    # make output directory if it doesn't exist
    if not os.path.exists(args.output_dirpath):
        os.makedirs(args.output_dirpath)

    app_name = os.path.splitext(os.path.basename(args.trace_path))[0].partition('_')[0]

    # allocate ID to simulation run
    id = 0
    output = app_name + "*" + str(id).zfill(2) + "*"
    while glob.glob(os.path.join(args.output_dirpath, output)):
        id += 1
        output = app_name + "*" + str(id).zfill(2) + "*"


def simulate():
    with open(args.trace_path) as input_trace:
        csv_reader = csv.reader(input_trace)
        for row in csv_reader:
            addr = int(row[0])
            access_type = row[1]
            is_instruction = True if row[2] == "I" else False
            #print("Address: " + str(addr)  + "Instruction type: " + row[2])
            
            if (is_instruction):
                [l1i_miss, l1i_evict] = l1i.access(addr, access_type)

                if (l1i_miss[1] != "N"):
                    [l2_miss, l2_evict] = l2.access(l1i_miss[0], l1i_miss[1])

                    if (l2_miss[1] != "N"):
                        [l3_miss_2, l3_evict_2] = l3.access(l2_miss[0], l2_miss[1])
                    if (l2_evict[1] != "N"):
                        [l3_miss, l3_evict] = l3.access(l2_evict[0], l2_evict[1])

                if (l1i_evict[1] != "N"):
                    [l2_miss, l2_evict] = l2.access(l1i_evict[0], l1i_evict[1])

                    if (l2_miss[1] != "N"):
                        [l3_miss_2, l3_evict_2] = l3.access(l2_miss[0], l2_miss[1])
                    if (l2_evict[1] != "N"):
                        [l3_miss, l3_evict] = l3.access(l2_evict[0], l2_evict[1])

            else:
                [l1d_miss, l1d_evict] = l1d.access(addr, access_type)

                if (l1d_miss[1] != "N"):
                    [l2_miss, l2_evict] = l2.access(l1d_miss[0], l1d_miss[1])

                    if (l2_miss[1] != "N"):
                        [l3_miss_2, l3_evict_2] = l3.access(l2_miss[0], l2_miss[1])
                    if (l2_evict[1] != "N"):
                        [l3_miss, l3_evict] = l3.access(l2_evict[0], l2_evict[1])

                if (l1d_evict[1] != "N"):
                    [l2_miss, l2_evict] = l2.access(l1d_evict[0], l1d_evict[1])

                    if (l2_miss[1] != "N"):
                        [l3_miss_2, l3_evict_2] = l3.access(l2_miss[0], l2_miss[1])
                    if (l2_evict[1] != "N"):
                        [l3_miss, l3_evict] = l3.access(l2_evict[0], l2_evict[1])


            # print("t: ", l2.cache[0].tags)
            # print(l2.cache[0].mlru)
                
            # MARSS handles miss before eviction
            # if there was a miss
 
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


def write_output():
    output = os.path.join(args.output_dirpath, app_name)

    # write l1i
    #l1i.write_sim(output)
    l1i.write_stat(output)
    l1i.write_plot(output)

    # write l1d
    #l1d.write_sim(output)
    l1d.write_stat(output)
    l1d.write_plot(output)

    # write l2 
    #l2.write_sim(output)
    l2.write_stat(output)
    l2.write_plot(output)

    # write l3
    #l3.write_sim(output)
    l3.write_stat(output)
    l3.write_plot(output)


if __name__ == "__main__":
    # parse input arguments
    opt = setup_options()
    args = opt.parse_args()
    
    # parse the config file
    config = configparser.ConfigParser()
    config.read(args.config_path)

    # setup cache
    setup_cache()

    # setup sim
    setup_stat()

    # simulate cache
    simulate()

    # statistics parsing
    write_output()
