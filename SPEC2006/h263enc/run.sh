#!/bin/bash
cd data
../src/benchmark -x 4 -a 0 -b 8 -s 15 -G -R 30.00 -r 3508000 -S 3 -Z 30.0 -O 0 -i input_base_4CIF_0to8.yuv -o output_base_4CIF_96bps_15.raw -B output_base_4CIF_96bps_15.263
