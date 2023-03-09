#!/bin/bash
rm debug.log

for algo in "alanezi" "cunche"
do
    for network in "ble" "lora"
    do
          python3 main.py -a ${algo} --n ${network}
    done
done