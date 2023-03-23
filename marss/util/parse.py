#!/usr/bin/env python3
# todo - file overwrite option

import csv
import sys
import os, glob
import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt

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


# setup the mask and miss arr necessary to track misses per set
def setup_parse(cache_type):
    # want to track misses per sets
    # number of bits necessary for offset, set, tag

    set = hash_set(cache_type)
   
    tag = addr_len - offset - set

    # keep array where value in index of array = number of misses in set of same index
    #set_list = [0] * (2**set)
    set_arr = np.zeros((2**set,), dtype=int)
    addr_dict = defaultdict(int)

    # okay i'm gonna use a hacky way of generating my mask,
    # by just taking a really long binary number of length 20 and shifting it
    # to get the desired bit length
    mask = 0b11111111111111111111
    mask >>= 20 - set

    return mask, set_arr, addr_dict

# since the parsed data as array type is too large, 
# cluster the results into num_clusters
def bin_result(arr, num_bins):
    [freq, bins] = np.histogram(arr, num_bins)
    #data = zip(*np.histogram(set_arr, num_bins))
    #np.savetxt('test.csv', list(data), fmt='%d', delimiter=',', header='frequency, bins')
    return [freq, bins]


def pdf(arr):
    pdf = arr / np.sum(arr)
    return range(len(arr)), pdf

def cdf(arr):
    arr_sorted = np.sort(arr)[::-1]
    cumsum = np.cumsum(arr_sorted)  
    cdf = (cumsum / cumsum[-1]) * 100       
    return range(len(arr_sorted)), cdf
    
# since the parsed data as dict type is too large, 
# cluster the results 
#def cluster_dict_result(addr_dict):

# read file containing address trace and extract
# information into set_arr, addr_dict, or both
def read_file(filename, mask, set_arr, addr_dict):
    # read input csv, fill arr of misses
    with open(filename) as input_csv:
        csv_reader = csv.reader(input_csv)
        for row in csv_reader:
            if "s" in args.parse_type:
                set_arr[((int(row[0]) >> offset) & mask)] += 1
            if "a" in args.parse_type:
                addr_dict[(int(row[0]) >> offset)] += 1
        input_csv.close()
    return set_arr, addr_dict

# write result to a csv (ds for datastructure)
# where the name of the file is the application
def write_file(output_filename, cache_type, ds):
    # write result to a new csv
    with open(output_filename, 'a', newline='') as output_csv:
        #get just the level of cache
        writer = csv.writer(output_csv)
        writer.writerow([cache_type])

        if isinstance(ds, np.ndarray):
            writer.writerow(ds)

        elif isinstance(ds, list):
            writer.writerows(ds)
            #output_csv.close()
            #with open(output_filename, 'ab') as output_csv:
            #    np.savetxt(output_csv, ds, fmt='%d', delimiter=',')

        else:
            for key, value in ds.items():
                writer.writerow([key, value])
        output_csv.close()

def parse_file(filename):
    print("Parsing: ", filename)
    # extract the application name and cache type from the filename
    app_name, cache_type = extract_info(os.path.basename(filename))

    mask, set_arr, addr_dict = setup_parse(cache_type)
    set_arr, addr_dict = read_file(filename, mask, set_arr, addr_dict)

    # determine output file name
    if "s" in args.parse_type:
        if args.process == 'n':
            output_filename = app_name + '_mps_raw.csv'
            write_file(output_filename, cache_type, set_arr)
        else:
            output_filename = app_name + '_mps_pr.csv'
            output_pngname = app_name + '_set.png'

            cdf_x, cdf_y = cdf(set_arr)
            pdf_x, pdf_y = pdf(set_arr)

            fig, axs = plt.subplots(1, 2, figsize=(16,6))

            axs[0].set_title('PDF')
            axs[0].plot(pdf_x, pdf_y)
            axs[0].set_xlabel('Sets')
            axs[0].set_ylabel('Percentage of Total Cache Misses')
            axs[0].grid(True)

            axs[1].set_title('CDF')
            axs[1].plot(cdf_x, cdf_y)
            axs[1].set_xlabel('Sets Sorted in Descending Order of Misses')
            axs[1].set_ylabel('Percentage of Total Cache Misses')
            axs[1].grid(True)

            fig.suptitle(app_name)

            fig.tight_layout()
            fig.savefig(output_pngname)
            fig.clf()

        print("Writing output to: ", output_filename)

    if "a" in args.parse_type:
        if args.process == 'n':
            output_filename = app_name + '_mpa_raw.csv'
            write_file(output_filename, cache_type, addr_dict)
        else:
            output_filename = app_name + '_mpa_pr.csv'
            output_pngname = app_name + '_addr.png'
            addr_dict_values = np.array(list(addr_dict.values()))
            #addr_dict_process = bin_result(addr_dict_values, 4)
            #write_file(output_filename, cache_type, addr_dict_process)
        
            cdf_x, cdf_y = cdf(addr_dict_values)
            pdf_x, pdf_y = pdf(addr_dict_values)

            fig, axs = plt.subplots(1, 2, figsize=(16,6))

            axs[0].set_title('PDF')
            axs[0].plot(pdf_x, pdf_y)
            axs[0].set_xlabel('Addresses')
            axs[0].set_ylabel('Percentage of Total Cache Misses')
            axs[0].grid(True)

            axs[1].set_title('CDF')
            axs[1].plot(cdf_x, cdf_y)
            axs[1].set_xlabel('Addresses Sorted in Descending Order of Misses')
            axs[1].set_ylabel('Percentage of Total Cache Misses')
            axs[1].grid(True)

            fig.suptitle(app_name)

            fig.tight_layout()
            fig.savefig(output_pngname)
            fig.clf()


        print("Writing output to: ", output_filename)

    #if "s" in args.parse_type:
    #    write_file(output_filename, cache_type, set_arr)
    #if "a" in args.parse_type:
    #    write_file(output_filename, cache_type, addr_dict)


# parse cache trace for all L3 csvs in a directory
def parse_all_files():
    for filename in glob.glob(os.path.join(args.dirpath, '*L3*.csv')):
        parse_file(filename)

def setup_options():
    arg = ArgumentParser()
    arg.add_argument("parse_type")
    arg.add_argument("process")
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
    #parse_file('./results/bzip_L3_0.csv')
    #parse_file('./results/test_L3.csv')
    # else if args.parse_type == "address":

