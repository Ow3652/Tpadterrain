#!/usr/bin/env python3
"""สร้างแผ่นข้อมูลความสูง (Terrarium PNG) สำหรับ Tpad Helicopter Planner จาก Copernicus DEM GLO-30

- ซูม 11 (~74 ม./พิกเซล) ทุกแผ่นบนบกในกรอบประเทศไทย
- ซูม 12 (~37 ม./พิกเซล) เฉพาะใต้แผ่นซูม 11 ที่มีความสูงสูงสุด >= THR เมตร (เขตภูเขา)
- ซูม ZMIN–10 สร้างจากซูม 11 โดยเอาค่าสูงสุดของ 2x2 พิกเซล (ไม่ทำให้ยอดเขาหาย)
- ลดขนาดจากต้นฉบับใช้ "ค่าสูงสุด" (max) ทุกระดับ: เผื่อไว้ฝั่งปลอดภัยสำหรับ TAWS
- ความสูงเก็บเป็นเมตรเต็ม: R*256 + G + B/256 - 32768 โดย B = 0 (ไฟล์เล็กลง)
- แผ่นที่เป็นทะเล/ไม่มีข้อมูลทั้งแผ่น (ทุกพิกเซล <= 0) ไม่สร้าง แอปถือว่าเป็นระดับน้ำทะเล
- coverage.json บอกกรอบ ช่วงซูม และรายชื่อแผ่นซูม 11 ที่มีแผ่นซูม 12 อยู่ข้างใต้

ใช้: python build_tiles.py --src dem/ --out site/ [--thr 300] [--zmin 5] [--bbox S W N E] [--jobs 4]
"""
import argparse, glob, json, math, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject
from PIL import Image

R = 6378137.0
ORIG = math.pi * R
SRC = []  # [(path, (left, bottom, right, top))]


def tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    r = math.radians(lat)
    y = (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n
    return int(x), int(y)


def tile_merc_bounds(x, y, z):
    s = 2 * ORIG / 2 ** z
    return (-ORIG + x * s, ORIG - (y + 1) * s, -ORIG + (x + 1) * s, ORIG - y * s)


def tile_ll_bounds(x, y, z):
    n = 2 ** z
    lon0, lon1 = x / n * 360 - 180, (x + 1) / n * 360 - 180
    lat = lambda yy: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy / n))))
    return lon0, lat(y + 1), lon1, lat(y)  # left, bottom, right, top


def render(x, y, z):
    """ความสูง (เมตร int16) 256x256 ของแผ่น z/x/y จากไฟล์ต้นฉบับที่ทับซ้อน (ค่าสูงสุดเมื่อซ้อนกัน)"""
    l, b, r, t = tile_ll_bounds(x, y, z)
    out = None
    dst_t = from_bounds(*tile_merc_bounds(x, y, z), 256, 256)
    for path, (sl, sb, sr, st) in SRC:
        if sr <= l or sl >= r or st <= b or sb >= t:
            continue
        dst = np.full((256, 256), np.nan, dtype=np.float32)
        with rasterio.open(path) as ds:
            reproject(source=rasterio.band(ds, 1), destination=dst, dst_transform=dst_t, dst_crs="EPSG:3857",
                      dst_nodata=np.nan, resampling=Resampling.max)
        out = dst if out is None else np.fmax(out, dst)
    if out is None:
        return None
    out = np.nan_to_num(out, nan=0.0)
    out[out < -500] = 0  # nodata ที่หลุดมา
    return np.clip(np.round(out), -500, 9000).astype(np.int16)


def write_png(arr, path):
    v = arr.astype(np.int32) + 32768
    rgb = np.zeros((256, 256, 3), dtype=np.uint8)
    rgb[..., 0] = (v >> 8) & 255
    rgb[..., 1] = v & 255
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(rgb, "RGB").save(path, optimize=True, compress_level=9)


def job_z11(args):
    x, y, out, thr = args
    a = render(x, y, 11)
    if a is None or a.max() <= 0:
        return (x, y, None, False, 0)
    write_png(a, f"{out}/terrarium/11/{x}/{y}.png")
    z12 = False
    n12 = 0
    if a.max() >= thr:
        z12 = True
        for dx in (0, 1):
            for dy in (0, 1):
                c = render(2 * x + dx, 2 * y + dy, 12)
                if c is not None and c.max() > 0:
                    write_png(c, f"{out}/terrarium/12/{2*x+dx}/{2*y+dy}.png")
                    n12 += 1
    return (x, y, a, z12, n12)


def init(src):
    global SRC
    SRC = src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--thr", type=float, default=300)
    ap.add_argument("--zmin", type=int, default=5)
    ap.add_argument("--bbox", type=float, nargs=4, default=[5.5, 97.2, 20.6, 105.8], metavar=("S", "W", "N", "E"))
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    t0 = time.time()
    src = []
    for p in sorted(glob.glob(os.path.join(a.src, "**", "*.tif"), recursive=True)):
        with rasterio.open(p) as ds:
            src.append((p, tuple(ds.bounds)))
    if not src:
        sys.exit("ไม่พบไฟล์ .tif ใน " + a.src)
    print(f"ไฟล์ต้นฉบับ {len(src)} ไฟล์", flush=True)
    S, W, N, E = a.bbox
    x0, y0 = tile_xy(N, W, 11)
    x1, y1 = tile_xy(S, E, 11)
    todo = [(x, y, a.out, a.thr) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    print(f"แผ่นซูม 11 ที่ต้องตรวจ {len(todo)}", flush=True)
    z11 = {}
    parents12 = []
    n12 = 0
    with ProcessPoolExecutor(a.jobs, initializer=init, initargs=(src,)) as ex:
        for i, (x, y, arr, has12, c12) in enumerate(ex.map(job_z11, todo, chunksize=8)):
            if arr is not None:
                z11[(x, y)] = arr
            if has12 and c12:
                parents12.append([x, y])
                n12 += c12
            if i % 500 == 0:
                print(f"  {i}/{len(todo)} · บก {len(z11)} · ซูม12 {n12}", flush=True)
    counts = {11: len(z11), 12: n12}
    level = z11
    for z in range(10, a.zmin - 1, -1):
        nxt = {}
        for (x, y) in {(cx // 2, cy // 2) for (cx, cy) in level}:
            big = np.zeros((512, 512), dtype=np.int16)
            for dx in (0, 1):
                for dy in (0, 1):
                    c = level.get((2 * x + dx, 2 * y + dy))
                    if c is not None:
                        big[dy * 256:(dy + 1) * 256, dx * 256:(dx + 1) * 256] = c
            m = big.reshape(256, 2, 256, 2).max(axis=(1, 3))
            if m.max() > 0:
                nxt[(x, y)] = m
                write_png(m, f"{a.out}/terrarium/{z}/{x}/{y}.png")
        counts[z] = len(nxt)
        level = nxt
    cov = {
        "v": 1,
        "source": "Copernicus DEM GLO-30 (DSM)",
        "notice": "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved",
        "encoding": "terrarium-int-m",
        "agg": "max",
        "bbox": [S, W, N, E],
        "zmin": a.zmin,
        "zfull": 11,
        "zmax": 12,
        "z12thr": a.thr,
        "z12parents": sorted(parents12),
        "counts": {str(k): v for k, v in sorted(counts.items())},
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(f"{a.out}/coverage.json", "w") as f:
        json.dump(cov, f, separators=(",", ":"))
    size = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fs in os.walk(a.out) for fn in fs)
    print(json.dumps({"counts": cov["counts"], "z12parents": len(parents12), "bytes": size, "MB": round(size / 1048576, 1),
                      "seconds": round(time.time() - t0)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
