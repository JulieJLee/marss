#!/usr/bin/env python3 

import csv
import os
import numpy as np

from argparse import ArgumentParser
from math import log
from collections import OrderedDict

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

def setup_options():
   arg = ArgumentParser() 
   arg.add_argument("num_sets", type=int)
   arg.add_argument("associativity", type=int)
   arg.add_argument("line_size", type=int)

   return arg

def setup_cache():
    #return np.zeros((int(args.num_sets), int(args.associativity)))
    cache = []
    for i in range(args.num_sets):
        cache.append(LRUSet(args.associativity))
    return cache
    
def setup_index():
    index_b_len = int(log(int(args.num_sets)) / log(2))

    offset_shift = int(log(int(args.line_size)) / log(2))

    tag_shift = index_b_len + offset_shift

    index_mask = 0b11111111111111111111 
    index_mask >>= 20 - index_b_len

    return index_mask, index_b_len, tag_shift, offset_shift

# read file containing address trace and extract 
# information into set_arr, addr_dict, or both 
def read_file(filename, index_mask, index_b_len, tag_shift, offset_shift):
    # read input csv, fill arr of misses 
    with open(filename) as input_csv:
        csv_reader = csv.reader(input_csv)
        for row in csv_reader:
            addr = int(row[0])
            # hit
            if cache[(addr >> offset_shift) & index_mask].update(addr >> tag_shift):
                output_file.write(row[0] + ",H\n")    
            # miss
            else:
                output_file.write(row[0] + ",M\n")    
            #print("Set Contents: ", cache[(addr >> offset_shift) & index_mask].set)

if __name__ == "__main__":
    opt = setup_options() 

    args = opt.parse_args()

    addr_len = 64
    
    cache = setup_cache()

    index_mask, index_b_len, tag_shift, offset_shift = setup_index()

    filename = "./results/bzip_L3_0.csv"
    #filename = "./results/test.csv"

    read_file(filename, index_mask, index_b_len, tag_shift, offset_shift)

    output_file = open("test.csv", "a")
    output_file.close()
