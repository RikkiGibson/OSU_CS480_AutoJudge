#!/bin/sh
python judge.py $1 2>stderr
rm null null2
echo "---grade list---"
cat "grades_$1"
