#!/bin/sh
python judge.py $1 $2 2>stderr
echo "---grade list---"
cat "grades_$1"
