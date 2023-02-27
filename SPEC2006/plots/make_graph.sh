echo "set terminal png
set output '$2'
plot  '$1' using 1:2 with labels " | gnuplot