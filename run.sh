#!/bin/bash
rm debug.log
rm results.csv

for algo in "alanezi" "cunche"
do
    for network in "ble" "lora"
    do
      for scenario in "ShoppingMall" "Hospital"
      do
          python3 main.py -a ${algo} --n ${network} --s ${scenario}
      done
    done
done