#!/bin/bash
# usage: dl.sh URL OUTFILE  -- resumes until size matches server Content-Length
url="$1"; out="$2"
want=$(curl -sIL "$url" | grep -i '^content-length' | tail -1 | tr -dc 0-9)
for i in $(seq 1 40); do
  have=$(stat -c %s "$out" 2>/dev/null || echo 0)
  [ -n "$want" ] && [ "$have" -ge "$want" ] && echo "OK $out $have" && exit 0
  curl -sL -C - --retry 5 -o "$out" "$url"
done
echo "INCOMPLETE $out"; exit 1
