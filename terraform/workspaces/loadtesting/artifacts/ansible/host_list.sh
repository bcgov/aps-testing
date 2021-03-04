#!/bin/bash

while IFS="" read -r p || [ -n "$p" ]
do
  printf '%s\n' "$p"
  ssh-keyscan -T 1 $p 2> /dev/null >> ~/.ssh/known_hosts
done < hosts 
