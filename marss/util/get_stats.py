
import csv
import os, glob
import fnmatch

from argparse import ArgumentParser

def setup_options():
    arg = ArgumentParser()
    arg.add_argument("dirpath")
    arg.add_argument("search_key")
    return arg

def get_search_val(filename):
    print("Parsing: ", filename)

    with open(filename) as curr_stat:
        csv_reader = csv.reader(curr_stat)
        for row in csv_reader:
            if row[0] == args.search_key:
                return(row[1])
                break   
    return "N/A"


def parse_all_files():
    app_name = os.path.basename(os.path.normpath(args.dirpath))
    stat_output = app_name + "_" + args.search_key + ".csv"
    subdirs = [x[0] for x in os.walk(args.dirpath)]
    print(subdirs)

    print("Writing output to: ", stat_output)

    with open(stat_output, "a", newline='') as stat:
        writer = csv.writer(stat)
        for subdir in subdirs:
            for filename in sorted(glob.glob(os.path.join(subdir, '*stat*.csv'))):
                val = get_search_val(filename)
                writer.writerow([filename, val])

    stat.close()

if __name__ == "__main__":
    opt = setup_options()

    args = opt.parse_args()
    
    parse_all_files()

