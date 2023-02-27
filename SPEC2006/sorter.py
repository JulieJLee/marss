
f = open('CompileRuntimes')
file = f.read()
data = [line.strip().split(" ") for line in file.split("\n")]
# print data

for line in data:
	print line[0] + line[2] + line[5]

