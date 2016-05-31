#!/usr/bin/env bash

for file in link_graphs/*.dot
    do
        F=$(basename $file)
        F=` echo $F | sed -r "s/\.dot//" `
        dot -Tpng "$file" -o link_graphs/"$F".png
    done