# 出口销售（ESR）：中文字段说明

[返回字段说明入口](../field_dictionary.md) · [通用读法与空值](common.md) · [机器可读字段定义](../../schemas/esr_weekly_sales.v1.json)

## 这个数据集在说什么

描述美国农产品对某目的地的出口销售和装运进度。一行是“商品 × 目的地 × 市场年度 × 统计周 × 单位”，同时带八个销售／出口指标。这里的 sales 是商品数量，不能按美元收入理解。

## 一行数据怎么读

在 [export-sales.csv](../../examples/export-sales.csv) 中，市场年度编号 2026、截至 2025-09-11 的一周，美国对墨西哥高粱实际出口 `4678` 公吨，年度累计出口 `4678` 公吨，未装运销售余额 `64000` 公吨，总承诺 `68678` 公吨。**4678 + 64000 = 68678**。同周净销售为 `4475` 公吨，不等于当周装运量。

## 先看哪些列

先选 `commodity_name`、`destination_name`、`marketYear`，按 `weekEndingDate` 排列。看本周装运用 `weeklyExports`；看本周销售变化用 `currentMYNetSales`；看尚未装运订单用 `outstandingSales`。

下面逐列覆盖当前 29 个字段。例值来自仓库固定示例，可能取自不同记录，不能把整列例值拼成一条记录；长 JSON／编号用省略号显示。字段的类型、是否允许为空和完整复合键以导出旁的 `schema.json` 为准。

## 业务字段与核对字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `commodityCode` | ESR 商品代码 | `701` | 出口销售系统自己的商品编号。示例 701 对应 Sorghum（高粱）；它不是 PSD 或 RMA 的商品代码。 |
| `countryCode` | 目的地代码 | `2010` | 出口目的国家、地区合计或未确定目的地的官方代码。2010 在示例中是墨西哥；不是年份。 |
| `marketYear` | 销售所属市场年度编号 | `2026` | 本次 API 查询使用的市场年度标识。商品年度起止各不相同，例如 marketYear=2026 的记录可以出现在 2025 年，不能按 weekEndingDate 的自然年替换。 |
| `weekEndingDate` | 统计周截止日 | `2025-09-04` | 本条周报覆盖的统计周结束日期，不是周报发布日期。市场年度边界的同一周可能出现在两个年度分区。 |
| `unitId` | 数量单位代码 | `1` | 官方单位字典编号，应连同 unit 使用。代码本身不代表数量。 |
| `commodity_name` | 商品名称 | `Sorghum` | 与商品代码对应的官方名称，可是小麦细分类等。总类与其子类不能重复相加。 |
| `destination_name` | 目的地名称 | `MEXICO` | 例如 MEXICO（墨西哥）。也可能是地区合计或未知目的地，不保证每行都是独立国家。 |
| `region_id` | 目的地所属大区代码 | `11` | 目的地字典中的区域归属，只是分类信息，不额外表示一条地区出口总量。 |
| `region_name` | 目的地所属大区名称 | `WESTERN HEMISPHERE` | 例如 WESTERN HEMISPHERE（西半球）。按源字典保留，不能当作已经完成地区历史口径统一。 |
| `genc_code` | GENC 地理代码 | `MEX` | 源字典提供的地理标识，例如 MEX。没有提供时为 \N；不能随意用另一个编码体系补齐。 |
| `unit` | 八个销售指标的共同单位 | `Metric Tons` | 示例 Metric Tons＝公吨。其他商品可能使用棉包、件等，因此不能把所有商品都当吨。 |
| `weeklyExports` | 本周实际出口量 | `0` | 在本条统计周内已经装运出口的数量，属于已履行部分，不是本周新签合同数量。 |
| `accumulatedExports` | 本市场年度累计出口量 | `0` | 从该市场年度开始到这周截止，已经出口的累计数量。不同周是累计进度，不能逐周相加。 |
| `outstandingSales` | 本年度未装运销售量 | `64203` | 截至本周，约定在当前市场年度交付但还未装运的销售承诺余额。是余额，不是本周新增量。 |
| `grossNewSales` | 本周新增销售总量 | `203` | 新增销售的总量指标，与扣除取消及调整后的净销售额外分开报告。它仍是数量而不是美元销售收入。 |
| `currentMYNetSales` | 本周当前年度净销售量 | `203` | 本周归属于当前市场年度的净销售变化，反映新增、取消及相关调整后的净额。可以为负；它不等于本周实际出口量。 |
| `currentMYTotalCommitment` | 当前年度总出口承诺量 | `64203` | 当前年度已出口与尚未装运销售的合计。可用 accumulatedExports + outstandingSales 理解；原字段保留官方值，不在下载时用公式替代。 |
| `nextMYOutstandingSales` | 下一市场年度未装运销售量 | `0` | 截至本周，约定在下一市场年度交付的未装运销售承诺余额，不能并入当前年度 outstandingSales。 |
| `nextMYNetSales` | 本周下一年度净销售量 | `0` | 本周归属于下一市场年度交付的净销售变化。与当前年度净销售分别记录，也可受取消或调整影响。 |
| `raw_metrics` | 八项指标的源数值记录 | `{"accumulatedExports": "0", "currentMYNetSales": "203", "currentM…` | JSON 字符串，保留 API 对这八个指标的原始数字／空值表示，便于核对精度。 |
| `source_week_raw` | 原始周截止时间文字 | `2025-09-04T00:00:00` | API 的 weekEndingDate 原文，例如带 T00:00:00 的字符串。不是发布时刻，不把这个午夜自行解释为 UTC。 |
| `commodity_release_timestamp_raw` | 商品最新发布信息原文 | `2026-11-13T08:30:22.49` | 商品级 releaseTimeStamp 的原始文字。它对应字典里的最新发布信息，不能当作此行历史统计周的发布日期，也没有擅自补时区。 |


## 时间、来源与版本字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `source_release_date` | 来源发布日期 | `\N` | 来源明确提供的发布或更新日期。它不是数据所描述的年份，也不是你下载文件的日期；不同数据集的具体含义见本页说明。 |
| `source_release_at_utc` | 来源发布时刻（UTC） | `\N` | 有依据的完整发布时间，统一为 UTC。只有日期、月份或没有时区时不能补造时刻，通常保存为 \N。 |
| `release_time_precision` | 发布时间精度 | `unknown` | 说明来源发布时间知道得有多细：timestamp 精确时刻，date/day 到日，month 到月，unknown 无法确认。不是数值的小数精度。 |
| `retrieved_at_utc` | 本地获取时间（UTC） | `2026-11-17T12:57:06.312829+00:00` | 该快照关联的源文件首次获取／导入本地缓存的时间。离线重放素材时也会生成本地导入回执；不能用它推断数据何时首次公开。 |
| `source_artifact_id` | 原始文件指纹 | `20fa6d65e545db3be2e5ee3c3b610e27f1b1b1e6b9c795df0bd043a272ad820f` | 原始响应、CSV、PDF 或 ZIP 的 SHA-256，用于找到和核对源文件。不是商品、地区、报表行的编号。 |
| `snapshot_id` | 处理结果版本编号 | `61a32f014b4cb87e3320cca2a1bb56c36be64522d448cdad8da537e8930fff28` | 标识源文件与解析器、字段定义、配置共同形成的一次标准化版本。同一来源重新处理可能产生新版本；不能把它当经济时间或业务主键。 |
| `vintage_type` | 数据版本性质 | `current_revised` | report_vintage：保留某期报告当时的数值；current_revised：下载时可见、可能已修订的历史序列；forecast_vintage：保留某次发布的预测版本。 |

## 八个数字为什么不能相加

- 周量：`weeklyExports`、`grossNewSales`、`currentMYNetSales`、`nextMYNetSales`。它们衡量的事情不同。
- 年度累计：`accumulatedExports`。相邻周包含前面周的结果，不能求和当全年量。
- 截至该周的余额：`outstandingSales`、`nextMYOutstandingSales`。不是每周新增。
- 总承诺：`currentMYTotalCommitment` 已包含当前年度累计出口和未装运销售，再加这两项会重复计算。
- 负净销售可以反映取消／调整，不表示发生了“负装运”；当前年度与下一年度也必须分开。
- API 保留的是当前可取得的修订序列，不自动还原“当周最初公布的版本”。商品级最新时间戳不填入每个历史周的发布日期。

更多来源与处理细节：[出口销售技术说明](../export_sales.md)。
