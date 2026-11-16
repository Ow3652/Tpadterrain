#!/usr/bin/env bash
# ดาวน์โหลด Copernicus DEM GLO-30 (ไฟล์ละ 1°x1°) ที่ครอบคลุมกรอบประเทศไทยจาก AWS Open Data (ไม่ต้องใช้บัญชี)
# แผ่นที่เป็นทะเลล้วนไม่มีไฟล์ (404) ข้ามไปเอง
set -u
OUT=${1:-dem}; mkdir -p "$OUT"
LAT0=${LAT0:-5}; LAT1=${LAT1:-20}; LON0=${LON0:-97}; LON1=${LON1:-105}
BASE=${BASE:-https://copernicus-dem-30m.s3.amazonaws.com}
for la in $(seq $LAT0 $LAT1); do for lo in $(seq $LON0 $LON1); do
  printf 'Copernicus_DSM_COG_10_N%02d_00_E%03d_00_DEM\n' "$la" "$lo"; done; done |
xargs -P 8 -I{} sh -c 'curl -fsS --retry 3 --retry-delay 5 -o "'"$OUT"'/{}.tif" "'"$BASE"'/{}/{}.tif" 2>/dev/null || rm -f "'"$OUT"'/{}.tif"'
n=$(ls "$OUT"/*.tif 2>/dev/null | wc -l); echo "ดาวน์โหลดได้ $n ไฟล์ ($(du -sh "$OUT" | cut -f1))"
[ "$n" -ge 40 ] || { echo "ไฟล์น้อยผิดปกติ หยุด"; exit 1; }
