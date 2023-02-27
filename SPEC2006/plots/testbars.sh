echo "set terminal png
set output '$2'
set style data histogram
set style histogram cluster gap 1
set boxwidth 0.25
set grid ytics
set yrange[0:*]
set xrange[-0.5:12.75]
set xlabel 'Optimisations used'
set ylabel 'Runtime (ms)'
set xtics border in scale 1,0.5 nomirror rotate by 90 offset character 0, 0, 0  
plot '$1' using :1:2:xtic(3)  with boxerrorbars title 'Run time' " | gnuplot
