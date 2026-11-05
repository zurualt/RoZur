#!/usr/bin/env bash
nombre="$1"
segundos="$2"
dir="/c/Users/ZuruT/AppData/Local/Temp/claude/C--Users-ZuruT-Documents-RoZur/089bd5fb-c513-403e-bc6e-c8e0ab8c855e/scratchpad/trailer/tomas"
mkdir -p "$dir"
ffmpeg -v error -y -f gdigrab -framerate 30 -t "$segundos" -i title="Overbooked! - Roblox Studio" \
  -vf "crop=1300:1204:379:140" -c:v libx264 -preset ultrafast -crf 15 -pix_fmt yuv420p "$dir/$nombre.mp4"
echo "hecho $nombre $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$dir/$nombre.mp4")"
