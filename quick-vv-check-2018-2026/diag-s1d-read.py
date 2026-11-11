"""Diagnostic: test reading the stuck Sentinel-1D scene
S1D_IW_GRDH_1SDV_20260628T231543_20260628T231608_003443_006139_rtc
(rel 77, 2026-06-28 23:15:55 UTC) with a bounded timeout.
Run with: timeout 90 <venv>/bin/python diag-s1d-read.py
"""
import json
from pystac_client import Client
import planetary_computer

gj = json.load(open("/home/hatch/workspace/go-parking-sarpanel/polygons-user.geojson"))
geom = next(f["geometry"] for f in gj["features"] if f["properties"]["id"] == "oakville-main")
client = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                     modifier=planetary_computer.sign_inplace)
search = client.search(collections=["sentinel-1-rtc"], intersects=geom,
                       datetime="2026-06-28T23:00:00Z/2026-06-28T23:59:59Z",
                       query={"sar:polarizations": {"eq": ["VV", "VH"]}}, limit=50)
item = [it for it in search.items() if "S1D_" in it.id][0]
href = planetary_computer.sign_url(item.assets["vv"].href)
print("signed href:", href[:200], flush=True)
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
with rasterio.Env(GDAL_HTTP_UNSAFESSL="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
    with rasterio.open(href) as src:
        print("opened:", src.crs, src.width, src.height, src.nodata, src.dtypes, flush=True)
        bx0, by0, bx1, by1 = transform_bounds("EPSG:4326", src.crs, -79.69, 43.45, -79.68, 43.46)
        win = from_bounds(bx0, by0, bx1, by1, src.transform)
        print("window:", win, flush=True)
        arr = src.read(1, window=win)
        print("read ok, shape:", arr.shape, "min/max:", float(arr.min()), float(arr.max()), flush=True)
