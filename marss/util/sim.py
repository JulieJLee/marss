#!/usr/bin/env python3 

import csv
import os, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from argparse import ArgumentParser
from math import log
from collections import OrderedDict
from collections import defaultdict

class LRUSet:
    def __init__(self, capacity: int):
        self.set = OrderedDict()
        self.capacity = capacity

    # return whether latest access was a hit (true)
    # key = tag, value = either dirty or number of times line has been accessed?
    #   dirty is only useful for performance reasons
    #   for now, let's go with number of times
    def update(self, key: int) -> bool:
        # miss
        if key not in self.set:
            # at capacity, need to evict
            if len(self.set) > self.capacity:
                self.set.popitem(last = False)

            # insert new line, update lru
            self.set[key] = 1
            self.set.move_to_end(key)
            return False

        # hit, update lru
        else:
            self.set[key] += 1
            self.set.move_to_end(key)
            return True

    def clear(self) -> None:
        self.set.clear()

def extract_info(filename):
    file_without_ext = os.path.splitext(filename)[0]
    app_name = file_without_ext.partition('_')[0]
    cache_type = file_without_ext.partition('_')[2]
    return app_name, cache_type

def setup_options():
   arg = ArgumentParser() 
   #arg.add_argument("dirpath")
   arg.add_argument("filepath")
   arg.add_argument("set_bits")
   arg.add_argument("associativity", type=int)

   return arg

def setup_sim():
   #print("Number of Sets ", num_sets)
    set_bit_pos = list(map(int, args.set_bits.split(",")))

    set_bit_len = len(set_bit_pos)

    num_sets = 2 ** set_bit_len

    cache = []
    for i in range(num_sets):
        cache.append(LRUSet(args.associativity))
    
    offset_bit_len = 6

    bit_pos_without_offset = set(range(offset_bit_len, 40))
    tag_bit_pos = list(set(set_bit_pos) ^ bit_pos_without_offset)

    #print("Set bit positions: ", set_bit_pos)
    #print("Tag bit positions: ", tag_bit_pos)

    #set_bit_mask = 0
    #for pos in set_bit_pos:
    #    set_bit_mask |= 1 << pos

    return cache, num_sets, set_bit_pos, set_bit_len, tag_bit_pos, offset_bit_len

def setup_stat(num_sets):
    set_addr = np.zeros((num_sets,), dtype=int)
    addr_dict = defaultdict(int)
    hit_ctr = 0
    miss_ctr = 0

    return set_addr, addr_dict, hit_ctr, miss_ctr

# read file containing address trace and extract 
# information into set_arr, addr_dict, or both 
def read_file(filename, set_bit_pos, set_bit_len, tag_bit_pos, offset_bit_len, output_file):
    global hit_ctr
    global miss_ctr
    # read input csv, fill arr of misses 
    with open(filename) as input_csv:
        csv_reader = csv.reader(input_csv)
        for row in csv_reader:
            addr = int(row[0])

            # calculate set index
            set_index = 0
            for i in range(len(set_bit_pos)):
                set_index += (((addr >> set_bit_pos[i]) & 1) << i)

            #print("Set Index: ", set_index)

            # calculate tag value
            tag_val = 0
            for i in range(len(tag_bit_pos)):
                tag_val += (((addr >> tag_bit_pos[i]) & 1) << i)

            #print("Tag Value: ", tag_val)
            # hit
            if cache[set_index].update(tag_val):
                output_file.write(row[0] + ",H\n")    
                # statistics counter
                hit_ctr += 1

            # miss
            else:
                output_file.write(row[0] + ",M\n")    
                # statistics counters
                miss_ctr += 1
                set_arr[set_index] += 1
                addr_dict[addr] += 1

def pdf(arr):
    pdf = arr / np.sum(arr)
    return range(len(arr)), pdf

def sorted_pdf(arr):     
    arr_sorted = np.sort(arr)[::-1]     
    idx_sorted = np.argsort(arr)[::-1]     
    sorted_pdf = arr_sorted / np.sum(arr_sorted)     
    return range(len(arr_sorted)), sorted_pdf 

def cdf(arr):     
    arr_sorted = np.sort(arr)[::-1]     
    cumsum = np.cumsum(arr_sorted)       
    cdf = (cumsum / cumsum[-1]) * 100            
    return range(len(arr_sorted)), cdf  


def parse_file(filename):
    print("Parsing: ", filename)

    app_name, cache_type = extract_info(os.path.basename(filename))

    # generate unique filename
    sim_output = app_name + "_sim_00.csv"
    counter = 0
    while os.path.isfile(sim_output):
        counter += 1
        sim_output  = app_name + "_sim" + "_" + str(counter).zfill(2) + ".csv"

    print("Writing output to: ", sim_output)

    sim_output = open(sim_output, "a")
    read_file(filename, set_bit_pos, set_bit_len, tag_bit_pos, offset_bit_len, sim_output)
    sim_output.close()

    # statistics parsing
    stat_output = app_name + "_stat" + "_" + str(counter) + ".csv" 
    total_access = hit_ctr + miss_ctr
    hit_ratio = (float(hit_ctr) / float(total_access)) * 100
    miss_ratio = (float(miss_ctr) / float(total_access)) * 100

    stat_summary = {
            'total_hit' : hit_ctr,
            'total_miss' : miss_ctr,
            'total_access' : total_access,
            'hit_ratio' : hit_ratio,
            'miss_ratio' : miss_ratio
            }

    with open(stat_output, 'a', newline='') as stat:
        stat.write("Set bits: " + args.set_bits + "\n")
        stat.write("Associativity: " + str(args.associativity) + "\n")
        writer = csv.writer(stat)
        for key, value in stat_summary.items():
            writer.writerow([key, value])

    stat.close()
        

    plot_output = app_name + "_plot" + "_" + str(counter) + ".png" 
    pdf_x, pdf_y = pdf(set_arr)
    sorted_pdf_x, sorted_pdf_y = sorted_pdf(set_arr)

    fig, axs = plt.subplots(2, 2, figsize=(16,6))             
    axs[0,0].set_title('PDF')             
    axs[0,0].plot(pdf_x, pdf_y)             
    axs[0,0].set_xlabel('Sets')             
    axs[0,0].set_ylabel('Percentage of Total Cache Misses')             
    axs[0,0].grid(True)             

    axs[0,1].set_title('Sorted PDF')             
    axs[0,1].plot(sorted_pdf_x, sorted_pdf_y)             
    axs[0,1].set_xlabel('Sets Sorted in Descending Order of Misses')             
    axs[0,1].set_ylabel('Percentage of Total Cache Misses')             
    axs[0,1].grid(True)             

    addr_dict_values = np.array(list(addr_dict.values()))
    pdf_x, pdf_y = pdf(addr_dict_values)
    sorted_pdf_x, sorted_pdf_y = sorted_pdf(addr_dict_values)

    axs[1,0].set_title('PDF')             
    axs[1,0].plot(pdf_x, pdf_y)             
    axs[1,0].set_xlabel('Addresses')             
    axs[1,0].set_ylabel('Percentage of Total Cache Misses')             
    axs[1,0].grid(True)             

    axs[1,1].set_title('Sorted PDF')             
    axs[1,1].plot(sorted_pdf_x, sorted_pdf_y)             
    axs[1,1].set_xlabel('Addresses Sorted in Descending Order of Misses')             
    axs[1,1].set_ylabel('Percentage of Total Cache Misses')             
    axs[1,1].grid(True)             

    fig.suptitle(app_name)             
    fig.tight_layout()             
    fig.savefig(plot_output)             
    fig.clf() 


def parse_all_files():
    print(args.dirpath)
    for filename in glob.glob(os.path.join(args.dirpath, '*L3*.csv')):
        parse_file(filename)

if __name__ == "__main__":
    opt = setup_options() 

    args = opt.parse_args()

    cache, num_sets, set_bit_pos, set_bit_len, tag_bit_pos, offset_bit_len = setup_sim()

    set_arr, addr_dict, hit_ctr, miss_ctr = setup_stat(num_sets)

    #parse_all_files()

    #filename = "./results/test_L3.csv"
    #filename = "./results/bzip_L3_0.csv"
    #filename = "./results/test.csv"
    #filename = "/hdd0/julie/results/SPEC2006_runbench4/lbm_L3_0.csv"

    parse_file(args.filepath)
    #output_file = open("lbm_sim.csv", "a")

    #output_file.close()
