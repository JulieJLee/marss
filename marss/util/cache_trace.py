#!/usr/bin/env python3
# todo - file overwrite option

import csv
import sys
import os, glob

from argparse import ArgumentParser
from collections import defaultdict

def hash_set(cache_type):
    if "L1" in cache_type:
            set = int(args.L1_set)
    if "L2" in cache_type:
            set = int(args.L2_set)
    if "L3" in cache_type:
            set = int(args.L3_set)
    return set

# extract application name and cache type from filename 
def extract_info(filename):
    file_without_ext = os.path.splitext(filename)[0]
    app_name = file_without_ext.partition('_')[0]
    cache_type = file_without_ext.partition('_')[2]
    return app_name, cache_type


# setup the mask and miss list necessary to track misses per set
def setup_parse(filename, cache_type):
    # want to track misses per sets
    # number of bits necessary for offset, set, tag

    set = hash_set(cache_type)
   
    tag = addr_len - offset - set

    # keep list where value in index of list = number of misses in set of same index
    s_ds = [0] * (2**set)
    a_ds = defaultdict(int)

    # okay i'm gonna use a hacky way of generating my mask,
    # by just taking a really long binary number of length 20 and shifting it
    # to get the desired bit length
    mask = 0b11111111111111111111
    mask >>= 20 - set

    return mask, s_ds, a_ds


# read file containing address trace and extract
# information into s_ds, a_ds, or both
def read_file(filename, mask, s_ds, a_ds):
    # read input csv, fill list of misses
    with open(filename) as input_csv:
        csv_reader = csv.reader(input_csv)
        for row in csv_reader:
            if "s" in args.parse_type:
                s_ds[((int(row[0]) >> offset) & mask)] += 1
            if "a" in args.parse_type:
                a_ds[(int(row[0]) >> offset)] += 1
        input_csv.close()
    return s_ds, a_ds

# write ds per set to a csv,
# where the name of the file is the application
def write_file(app_name, cache_type, ds):
    # write result to a new csv
    #output_path = '/home/jiwonl4/School/SP2023/ECE499/marss/parse_py_test/'
    #output_filename = os.path.join(output_path, filename.partition('_')[0] + '_trace.csv')
    if isinstance(ds, list):
        output_filename = app_name + '_mps.csv'
    else: 
        output_filename = app_name + '_mpa.csv'
        fields = ['Address', 'Miss Count']

    print("Writing output to: ", output_filename)
    with open(output_filename, 'a', newline='') as output_csv:
        #get just the level of cache
        writer = csv.writer(output_csv)
        writer.writerow([cache_type])
        if isinstance(ds, list):
            writer.writerow(ds)
        else:
            for key, value in ds.items():
                writer.writerow([key, value])
        output_csv.close()

def parse_file(filename):
    # extract the application name and cache type from the filename
    app_name, cache_type = extract_info(os.path.basename(filename))

    mask, s_ds, a_ds = setup_parse(filename, cache_type)
    s_ds, a_ds = read_file(filename, mask, s_ds, a_ds)
    if "s" in args.parse_type:
        write_file(app_name, cache_type, s_ds)
    if "a" in args.parse_type:
        write_file(app_name, cache_type, a_ds)


# parse cache trace for all csvs in a directory
def parse_all_files():
    for filename in glob.glob(os.path.join(args.dirpath, '*L*.csv')):
        print("Parsing: ", filename)
        parse_file(filename)

def setup_options():
    arg = ArgumentParser()
    arg.add_argument("parse_type")
    arg.add_argument("dirpath")
    arg.add_argument("L1_set")
    arg.add_argument("L2_set")
    arg.add_argument("L3_set")

    return arg

if __name__ == "__main__":
    opt = setup_options()

    args = opt.parse_args()

    addr_len = 64
    offset = 6 

    parse_all_files()
    # else if args.parse_type == "address":

