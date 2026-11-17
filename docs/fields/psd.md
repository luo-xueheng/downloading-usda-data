# 独立 PSD 辅助接口：中文字段说明

[返回字段说明入口](../field_dictionary.md) · [通用读法与空值](common.md) · [机器可读字段定义](../../schemas/psd_observations.v1.json)

## 这个数据集在说什么

PSD 是生产、供应和分配数据库，提供商品在某地区、市场年度的产量、面积、消费、贸易和库存等指标。一行对应一个供需指标。它也是三个报告数据集的共享数据来源，不额外增加一个主数据集示例 CSV。

## 一行数据怎么读

`commodityCode=0440000` 对应玉米；一行的地区、`marketYear`、`attribute_name` 和 `unit` 共同决定 `value` 是产量、面积还是其他指标。`calendarYear` 和 `month` 表示源记录的更新年月，不是这项产量所属的年份。

## 先看哪些列

先看 `commodity_name`、`geography_name`、`marketYear`、`attribute_name`、`value`、`unit`；比较前检查 `aggregation_level`，不要把地区合计与成员国相加。

下面逐列覆盖当前 27 个字段。例值来自仓库固定示例，可能取自不同记录，不能把整列例值拼成一条记录；长 JSON／编号用省略号显示。字段的类型、是否允许为空和完整复合键以导出旁的 `schema.json` 为准。

## 业务字段与核对字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `commodityCode` | PSD 商品代码 | `0440000` | 供需数据库自己的商品代码，0440000＝玉米。保留前导零，不能与 ESR／RMA 商品代码直接连接。 |
| `countryCode` | PSD 国家／汇总代码 | `AF` | 国家、区域或其他汇总代码，00 为世界汇总。必须配合 aggregation_level，不能把每个代码都当作独立国家。 |
| `aggregation_level` | 地区汇总层级 | `country` | PSD 可为 country（国家）、region（区域合计）、world（世界）、residual_aggregate（其他／剩余合计）；PDF 为 report_defined，需按原表判断。 |
| `marketYear` | 市场年度编号 | `2025` | 源 API 的市场年度标识。具体起止随商品／地区／指标口径变化，不默认等于自然年，也不直接等同 ESR 的同名参数。 |
| `attributeId` | 指标代码 | `4` | 源字典中的指标编号，应配合 attribute_name 使用。 |
| `unitId` | 单位代码 | `4` | 源单位编号，应配合 unit 使用。不同商品或指标的单位可能不同。 |
| `calendarYear` | 源记录更新年份 | `2026` | 记录更新批次的年份，不是市场年度，也不证明该年已经存在同样的历史报告数值。 |
| `month` | 源记录更新月份 | `09` | 记录更新批次的月份，保留源字符串；与 calendarYear 合起来表达更新年月。 |
| `commodity_name` | 商品名称 | `Corn` | 代码对应的官方商品／产品名称，例如 Corn。 |
| `geography_name` | 地区名称 | `Afghanistan` | 国家或汇总地区的官方名称；世界合计不是程序自行对国家求和得到。 |
| `region_code` | 所属区域代码 | `R12` | 国家字典给出的区域归属，不额外生成一个区域总量。 |
| `region_name` | 所属区域名称 | `South Asia` | 通过区域字典查到的名称。若源国家字典指向的区域在区域字典中缺失，则为空，不能编造名称。 |
| `region_mapping_status` | 区域名称是否查到 | `resolved` | resolved＝成功对应；absent_in_source_dictionary＝源字典缺少相应区域。原 region_code 仍保留。 |
| `genc_code` | GENC 地理代码 | `AFG` | 源字典提供的地理标识，例如 MEX。没有提供时为 \N；不能随意用另一个编码体系补齐。 |
| `attribute_name` | 供需指标名称 | `Area Harvested` | 例如 Production（产量）、Area Harvested（收获面积）、TY Exports（贸易年度出口量）。MY 与 TY 的指标不能随意替换。 |
| `unit` | 清理后的单位名称 | `(1000 HA)` | 只清理源单位名称两端空格，不做数值换算。例如 (1000 MT) 是千公吨。 |
| `unit_raw` | 原始单位文字 | `(1000 HA)           ` | 保留源单位描述中的空格等原始写法；用于追溯，与 unit 指向同一个单位。 |
| `value` | 指标数值 | `140.0000` | 按源单位保存的精确数值，空值不是零。与商品、地区、市场年度、指标及单位一起使用。 |
| `raw_value` | 源文件中的原值 | `140.0000` | 保存原来看到的数字文字或缺失标记，用来核对 value；正常分析使用解析后的数值。历史 Excel 的原值是读取器读到的存储值，不一定等于界面显示的四舍五入值。 |
| `source_release_period` | 源记录更新年月 | `2026-09` | 由 calendarYear 和 month 组成的年月标签；只知道月份，不能补成该月 1 日或月末发布。 |


## 时间、来源与版本字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `source_release_date` | 来源发布日期 | `\N` | 来源明确提供的发布或更新日期。它不是数据所描述的年份，也不是你下载文件的日期；不同数据集的具体含义见本页说明。 |
| `source_release_at_utc` | 来源发布时刻（UTC） | `\N` | 有依据的完整发布时间，统一为 UTC。只有日期、月份或没有时区时不能补造时刻，通常保存为 \N。 |
| `release_time_precision` | 发布时间精度 | `month` | 说明来源发布时间知道得有多细：timestamp 精确时刻，date/day 到日，month 到月，unknown 无法确认。不是数值的小数精度。 |
| `retrieved_at_utc` | 本地获取时间（UTC） | `2026-11-15 13:24:52.794186+00:00` | 该快照关联的源文件首次获取／导入本地缓存的时间。离线重放素材时也会生成本地导入回执；不能用它推断数据何时首次公开。 |
| `source_artifact_id` | 原始文件指纹 | `0ae6a975fde796058332efac6d16703a75f5834a07b717d8de99502e549bcb15` | 原始响应、CSV、PDF 或 ZIP 的 SHA-256，用于找到和核对源文件。不是商品、地区、报表行的编号。 |
| `snapshot_id` | 处理结果版本编号 | `unpublished` | 标识源文件与解析器、字段定义、配置共同形成的一次标准化版本。同一来源重新处理可能产生新版本；不能把它当经济时间或业务主键。 |
| `vintage_type` | 数据版本性质 | `current_revised` | report_vintage：保留某期报告当时的数值；current_revised：下载时可见、可能已修订的历史序列；forecast_vintage：保留某次发布的预测版本。 |

## 使用边界

- `source_release_period` 只到月份；当前接口的精确发布日期和 UTC 时刻保持为空。
- `vintage_type=current_revised` 表示当前修订序列，不能把它改个时间标签就当作早期报告原值。
- `region_mapping_status=absent_in_source_dictionary` 表示上游区域字典有缺项；不擅自补名称。

例值来自已固定的 PSD 官方响应素材。更多详情：[PSD 技术说明](../psd.md)。
