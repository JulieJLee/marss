folders =  "464.h264ref 470.lbm h263dec h263enc mpeg2dec mpeg2enc".split(" ")
for folder in folders:
	try:
		file=open('{0}/final/BenchRunTimes'.format(folder))
		lines=0
		for x in file:
			lines += 1
		print '{0} has {1} benchmarks run'.format(folder, lines)
	except IOError as e:
		print "{0} Has no benchmark file".format(folder)

