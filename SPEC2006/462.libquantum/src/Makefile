
SOURCES= classic.c complex.c decoherence.c expn.c gates.c matrix.c \
	 measure.c oaddn.c objcode.c omuln.c qec.c qft.c qureg.c shor.c version.c \
	 specrand.c

CC=gcc
CFLAGS=-O0 -static
COMP_FLAGS=-DSPEC_CPU -DNDEBUG -DSPEC_CPU_LINUX -lm

all: $(SOURCES)
	$(CC) $(SOURCES) $(CFLAGS) $(COMP_FLAGS) -o benchmark



