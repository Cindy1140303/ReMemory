#!/usr/bin/env bash
# 列出 HEAD 版本下被 git 追蹤檔案，依大小排序，顯示前 30
git ls-tree -r -l --full-tree HEAD \
  | awk '{size=$4; $1=$2=$3=$4=""; sub(/^ +/, ""); printf "%12d %s\n", size, $0}' \
  | sort -n -r \
  | head -n 30 \
  | awk '{printf "%10.2f MB\t%s\n", $1/1024/1024, substr($0, index($0,$2))}'
