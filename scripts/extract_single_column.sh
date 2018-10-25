#!/bin/bash

################################################################################
# Used seldom. Extract a single column from a commaseparated csv file. Feel free
# to adapt to other use cases
#
# Usage:
# ./script/extract_single_column.sh <columnno> < file_to_extract_from.csv
################################################################################

awk -F "\"*,\"*" '{print $'"$1"'}' < /dev/stdin
