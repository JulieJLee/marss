#!/bin/sh

cd data/
../src/benchmark --quiet --mode gtp < capture.tst
../src/benchmark --quiet --mode gtp < connect.tst
../src/benchmark --quiet --mode gtp < connect_rot.tst
../src/benchmark --quiet --mode gtp < connection.tst
../src/benchmark --quiet --mode gtp < connection_rot.tst
../src/benchmark --quiet --mode gtp < cutstone.tst
../src/benchmark --quiet --mode gtp < dniwog.tst
