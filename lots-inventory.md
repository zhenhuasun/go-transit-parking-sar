# GO 停车场 SAR 试点 — 三站露天停车场清单

日期：2026-11-07
范围：Oakville GO、Clarkson GO、Bronte GO，2018–2026（用户 2026-11-07 确认）
原则：**每个露天停车场单独一个 polygon，室内停车楼排除** — SAR 看不到楼里面的车。

## 1. Oakville GO — 214 Cross Ave, Oakville

GO 官网车位数：Main Lot 2712、Parking Garage 1398、South Lot 291。

| Lot | 类型 | 车位 | 中心点（约） | SAR 处理 |
|---|---|---|---|---|
| Main Lot | 露天 | 2712 | 43.45612, -79.68378 | ✅ 主分析对象。注意：Cross Ave 沿线 148–222 号是三个连片大面积露天场，可先合为一个 polygon，之后再看要不要拆。 |
| South Lot | 露天 | 291 | 43.45555, -79.68223 | ⚠️ 小，像素少、speckle 噪声大；先跑，但权重低。中心点与 Main Lot 很近，geocoder 可能不准，画 polygon 前需卫星图核对。 |
| Parking Garage | 室内楼 | 1398 | 待核对（geocoder 误返回 Church St Parkade，不可用） | ❌ 排除。约占全站车位 32%，VV 完全看不到楼内占用。 |

## 2. Clarkson GO — 1110 Southdown Rd, Mississauga

| Lot | 类型 | 车位 | 中心点（约） | SAR 处理 |
|---|---|---|---|---|
| Main Lot | 露天 | 1274（Parkopedia） | 43.5123, -79.63185 | ✅ 南侧主 lot，站房东侧向南展开。 |
| North Lot | 露天 | **627（GO 官网，2026-11-08 核对）** | 43.51393, -79.63511（2070 Bromsgrove Rd） | ✅ 北侧，轨道另一边；与 Main Lot 分开算。文献称 north parking lots（复数），画 polygon 时注意可能不止一块。 |
| Garage | 室内楼 | 1573（GO 官网） | 与 Main Lot 同一 geocoder 坐标，不可信，待核对 | ❌ 排除。占全站车位 45.3%，是最大的混淆源：冬天/下雨车往楼里挪，露天 VV 会掉，但全站占用未必掉。 |

注（2026-11-08 修正）：GO 官网现列 North Lot **627**（不是 Parkopedia 的 1020），Main 1274 + North 627 + Garage 1573 = **3474**，正好等于另一来源的全站总数，Parkopedia 的 1020 已被取代。**但有个待核对的矛盾**：用户画的 North Lot polygon 面积 32,796 m²，按 627 个车位算是 52.3 m²/车位，远高于其他 5 个 lot 的 27–32 m²/车位；按 1020 算才是 32.2。说明 polygon 可能框进了 North Lot 以外的沥青面（或 GO 的 627 只是其中一部分）。VV 均值本身不受车位数影响，但按车位加权 / 算站合计之前，必须先核对 North Lot 的实际边界。

## 3. Bronte GO — 2104 Wyecroft Rd, Oakville

| Lot | 类型 | 车位 | 中心点（约） | SAR 处理 |
|---|---|---|---|---|
| Main / East Lot | 露天 | 1824（Parkopedia） | 43.41864, -79.72498 | ✅ 北侧主 lot。规划文件称 East Parking Lot，呈 U 形绕着 2070/2100 Wyecroft 的建筑。 |
| South Lot | 露天 | 1149（Parkopedia） | 43.416254, -79.721525（2135 Speers Rd） | ✅ 南侧，轨道另一边，Speers Rd 进入；与北侧分开算。 |
| Parking Garage | — | — | — | 未见可靠来源证实 Bronte 有室内楼；本次按无楼处理，如用户确认有楼再补。 |

注：Wikipedia 称 Bronte 全站 2424 个车位，与 Parkopedia 两项相加 2973 不符；南 lot 历史上 2011 年约 175 个、建成目标 300 个、2016 年又加 200 个，说明车位数随时间变过。**做长时间序列时，lot 边界/车位数本身会变，要在时间轴上标注扩建年份，不能当成固定不变。**

## 待办（下一步）

1. 用户确认时间范围（已确认 2018–2026，2026-11-07）。
2. 用卫星图/OSM 逐个画出 6 个露天 lot 的精确 polygon（不用 bounding box，避免把轨道、站房、道路、树木混进来）。
3. 核对 Oakville Garage、Clarkson Garage 的精确位置，仅作排除用（画一个 mask，不进分析）。
4. 生成 SARpanel 配置：6 个 polygon × 1 个日期范围；每个 lot 单独一条 VV 时间序列，再加一条全站露天合计（按车位加权）。
5. 标注已知变化点：Bronte 南 lot 扩建、Clarkson/Oakville 施工/封闭期（如有）。

## 来源与可信度

- GO 官网 Oakville 车位数：Main 2712 / Garage 1398 / South 291。
- Clarkson Main 1274 / Garage 1573、Bronte 两项 1824 / 1149 已由 GO 官网核对确认（2026-11-08 全网清点）；Clarkson North 由 Parkopedia 1020 修正为 GO 官网 627，见上注。
- Bronte 南 lot 坐标 43.416254, -79.721525 来自 listing；其余中心点来自 geocoder，均为约值，不是 polygon。
