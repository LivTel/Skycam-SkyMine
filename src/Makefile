#############################
# compilers, archivers etc. #
#############################

CC		= /usr/bin/gcc
AR		= /usr/bin/ar

BIN_DIR		= ../bin/

##################
# compiler flags #
##################

CFLAGS		= -Wall -g -std=c99

#########################
# csh terminal commands #
#########################

MV		= /bin/mv

################
# $(LIBS) flag #
################

####################
# $(INCLUDES) flag #
####################

CC=gcc
CFLAGS=-I.

usnob1: usnob1.c
	$(CC) $(CFLAGS) usnob1.c usnob_sub.c -o query_usnob -lm 
	$(MV) query_usnob $(BIN_DIR)
