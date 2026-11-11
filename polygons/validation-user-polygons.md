# GO 停车场 SAR 试点 — 用户版 Polygon 验证报告

日期：2026-11-07（2026-11-08 补记见下）

## 2026-11-08 补记：Clarkson North 车位数修正

全网清点核对 GO 官网后，Clarkson North Lot 由 Parkopedia 的 1020 修正为 GO 官网的 **627**（Main 1274 + North 627 + Garage 1573 = 3474）。按 627 算，这块 polygon 的面积比是 32,796 / 627 = **52.3 m²/车位**，不再落在上表 27–32 的一致区间内。polygon 几何本身没变、验证结论（闭合、无自交、无重叠）仍然成立，但 North Lot 的边界在按车位加权之前需要复核：可能框进了 North Lot 以外的沥青面，或 GO 的 627 只是北侧多个 lot 中的一个。其他 5 个 lot 的面积比不受影响。
文件：`polygons-user.geojson`（用户从可编辑卫星图导出，原文件 `workspace/user/files/go-parking-lots-user.geojson`）
时间范围：2018-01-01 至 2026-11-07

## 验证结果：全部通过

- 6 个 feature，全部是 Polygon，全部闭合，无自相交（边交叉检查），6 个 lot 之间无重叠（边交叉检查）。
- 每个 lot 的面积 / 车位数比值在 27–32 m2/车位之间，非常一致，说明画的是真实停车场沥青面，不是把周围道路/建筑也框进来了。草稿矩形的比值是 47–70 m2/车位，明显偏大。

| Lot | 顶点 | 面积 | 车位 | m2/车位 | 中心点移动（相对草稿） |
|---|---|---|---|---|---|
| Oakville GO — Main Lot | 24 | 74,151 m2 | 2712 | 27.3 | 234 m |
| Oakville GO — South Lot | 14 | 8,215 m2 | 291 | 28.2 | 208 m |
| Clarkson GO — Main Lot | 19 | 36,264 m2 | 1274 | 28.5 | 156 m |
| Clarkson GO — North Lot | 19 | 32,796 m2 | 1020 | 32.2 | 52 m |
| Bronte GO — Main / East Lot | 22 | 58,212 m2 | 1824 | 31.9 | 150 m |
| Bronte GO — South Lot | 13 | 31,869 m2 | 1149 | 27.7 | 44 m |

## 关键修正（相对草稿）

- **Oakville South Lot（原红色框）已解决**：中心点向南移了约 208 m，现在在轨道南侧（43.45373, -79.68281），面积 8,215 m2 / 291 个车位 = 28.2 m2/车位，与其他 lot 一致。不再是占位符。
- **Oakville Main Lot**：不再是矩形，沿实际边界描了 24 个点，面积从草稿 126,783 m2 缩到 74,151 m2。
- **Bronte Main / East Lot**：22 个点，面积从 128,355 m2 缩到 58,212 m2，U 形已按实际边界描。
- **Clarkson Main / North、Bronte South**：面积都比草稿矩形小约一半，符合真实 lot 形状。

## 下一步（SARpanel）

1. 先跑 `plan`：`python -m sarpanel.cli plan configs/go_parking_2018_2026.yaml`，看 2018–2026 年共多少景、下载多大，再决定是否全跑。
   - 注意：9 年、3 个站、6 个小 lot，场景数会不少；README 建议先从短时间段试跑，再扩到全段。
   - 建议先试跑一个短窗口（例如 2019-06-01 至 2019-08-31）验证流程，再跑全段。
2. 需要的前提（README 步骤 3–4）：ESA SNAP 已装（`gpt -h` 能跑）、NASA Earthdata 账号 + token（`EARTHDATA_TOKEN`）。
3. 配置文件：`sarpanel-go-parking-2018-2026.yaml`，aoi.source 指向 `polygons-user.geojson`，id_column 为 `id`，target_crs 为 UTM 17N `EPSG:32617`，间距 10 m，VV+VH，GRD。
