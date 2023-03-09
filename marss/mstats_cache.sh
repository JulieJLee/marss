#/bin/bash
./util/mstats.py -y --cache-summary --cache-summary-type=csv -t total /hdd0/julie/results/SPEC2006_runbench2/bzip.yml > base_stats/bzip_base.csv  &
./util/mstats.py -y --cache-summary --cache-summary-type=csv -t total /hdd0/julie/results/SPEC2006_runbench2/mcf.yml > base_stats/mcf_base.csv &
./util/mstats.py -y --cache-summary --cache-summary-type=csv -t total /hdd0/julie/results/SPEC2006_runbench2/hmmer.yml > base_stats/hmmer_base.csv &
./util/mstats.py -y --cache-summary --cache-summary-type=csv -t total /hdd0/julie/results/SPEC2006_runbench2/sjeng.yml > base_stats/sjeng_base.csv &
./util/mstats.py -y --cache-summary --cache-summary-type=csv -t total /hdd0/julie/results/SPEC2006_runbench2/lbm.yml > base_stats/lbm_base.csv &
./util/mstats.py -y --cache-summary --cache-summary-type=csv -t total /hdd0/julie/results/SPEC2006_runbench2/libquantum.yml > base_stats/libquantum_base.csv &
