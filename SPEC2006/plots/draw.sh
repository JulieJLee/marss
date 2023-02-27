echo "set terminal png
set output '$2'
set title 'Dat'
set xlabel 'run time'
set ylabel 'compile time'
set grid
plot '$1' with  lines smooth unique , '$1' with labels " | gnuplot

