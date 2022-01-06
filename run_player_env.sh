#!/bin/bash

echo $0

full_path=$(realpath $0)
echo $full_path

dir_path=$(dirname $full_path)
echo $dir_path

$dir_path'/mon_env/bin/python3' $dir_path'/music_player.py'
