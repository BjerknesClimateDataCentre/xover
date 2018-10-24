#!/bin/bash

################################################################################
#
# Wrapper for sort, to sort the GLODAP datafile in a sensible way, on
# cruise, station, cast, depth, bottle
#
#
# Usage:
# ./scripts/db/sort_GLODAPv2_dataset.sh < input_file.csv >sorted_output.csv
#
# Where input_file.csv is the standard GLODAPv2 output file format
# and sorted.output.csv is the sorted output file.
#
################################################################################

sort -n --field-separator=',' -k1,1 -k2,2 -k3,3 -k13,13 -k15,15rn  < /dev/stdin
