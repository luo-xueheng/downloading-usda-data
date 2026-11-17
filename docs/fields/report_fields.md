# 三类 FAS 报告共用的 35 列：中文字段说明

[返回字段说明入口](../field_dictionary.md) · [通用读法与空值](common.md) · [机器可读字段定义](../../schemas/fas_dataset_observations.v1.json)

## 这个数据集在说什么

世界农业生产、谷物贸易和油籽贸易的 CSV 使用相同列名。每个文件包含两种来源：PSD API 的当前修订供需数据，以及原始 PDF 报告中的表格单元格。先看 `observation_kind`，才能知道同名列在这一行具体表示什么。

## 一行数据怎么读

例如：`observation_kind=psd_current`、`row_label=World`、`column_commodity=Corn`、`indicator=Production`、`period_label=2025`，表示 API 中该市场年度的世界玉米产量。另一条 `report_table` 行可能是某月 PDF 中对下一年度的预测变化，不能把两条直接求和。

## 先看哪些列

先选 `observation_kind`。PSD 行重点看商品／地区／指标代码、`period_label`、`value`、`unit`；PDF 行重点看 `report_period`、`table_title`、`section_label`、`row_label`、`column_commodity`、`indicator`、`period_label` 和 `comparison_label`。

下面逐列覆盖当前 35 个字段。例值来自仓库固定示例，可能取自不同记录，不能把整列例值拼成一条记录；长 JSON／编号用省略号显示。字段的类型、是否允许为空和完整复合键以导出旁的 `schema.json` 为准。

## 业务字段与核对字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `report_family` | 报告家族 | `world-production` | world-production＝世界农业生产；grain-trade＝谷物贸易；oilseed-trade＝油籽贸易。三类用同一列结构，但覆盖的商品和指标不同。 |
| `report_period` | 原始报告期次 | `not_applicable` / `2026-11` | report_table 行为报告月份，如 2026-11；psd_current 行为 not_applicable，因为当前 API 数值不能冒充某期原始报告。 |
| `table_title` | 原表标题 | `PSD current-revised observations` | 说明这行属于供需表、变化表还是可靠性表。PSD 行固定为 PSD current-revised observations。 |
| `section_label` | 表内分组标题 | `Yield` | 表内部的指标、商品或区域分组；含义随表变化。如可靠性表的 BARLEY 是大麦，其他表可能是 Domestic Consumption（国内消费）。 |
| `section_product_type` | 表内产品大类 | `not_applicable` / `Oilseed` | 例如 Oilseed（油籽）、Meal（粕）、Oil（油）。用于区分不同大类下重复的 Total／Other；原表不需要此分类时为 not_applicable。 |
| `row_label` | 行标签／统计地区 | `World` | PSD 行为国家或汇总地区名称；PDF 行为原始行标签，可能是国家、World、Other 或其他分类。不能始终当作国家名称。 |
| `column_commodity` | 商品列标签 | `Corn` | PSD 行为商品名称；PDF 行保留列上的商品。某些报告把商品写在 section_label 或表标题中，因此此列可能为 not_applicable。 |
| `indicator` | 统计指标 | `Yield` | 例如 Production（产量）、Yield（单产）、Exports（出口量）。可靠性表也会出现误差、置信区间等指标，不能只按数据集名称判断所有行都是产量。 |
| `period_label` | 数值描述的时期 | `2025` | PSD 行为市场年度编号，例如 2025；PDF 行保留 2025/26 等原标签，也可能是历史统计区间。区别于 report_period 的报告发布月份。 |
| `comparison_label` | 比较列／修订类别 | `not_applicable` / `Change` | Previous＝前次值、Current＝本次值、Change＝变化量；也可能保留 Oct／Nov 等月份标签。不涉及比较时为 not_applicable。变化量可为负。 |
| `unit` | 这一格数值的单位 | `(MT/HA)` | (1000 MT)／Thousand Metric Tons＝千公吨；Million Metric Tons＝百万公吨；(MT/HA)＝公吨／公顷。面积、数量、价格、百分比按各行区分。 |
| `value` | 这一个单元格的数值 | `6.2148` | 需连同指标、时期、比较列和单位理解。Change 行的 -190 可以表示下调 190 千公吨，绝不是出口量为负。 |
| `raw_value` | 源文件中的原值 | `6.2148` | 保存原来看到的数字文字或缺失标记，用来核对 value；正常分析使用解析后的数值。历史 Excel 的原值是读取器读到的存储值，不一定等于界面显示的四舍五入值。 |
| `value_status` | 数值状态 | `reported` | 解释数值是正常公布、缺失、不适用、未公布等。先看此列再决定如何处理空值；只有 reported 才表示正常数值，零仍然可以是 reported。 |
| `period_basis` | 时期及口径说明 | `PSD source marketing-year identifier; TY measures retain their so…` | 保留表头／注释中的年度含义，例如 MY（市场年度）与 TY（贸易年度）的区别。source-labelled period 只表示沿用原标签，不表示已统一成自然年。 |
| `table_metadata_id` | 表头与脚注信息索引 | `PSD dictionary snapshot 69e01ee04f13013d5e0c15fb603275647766c53c1…` | 指向解析时保存的表头、注释和映射信息。PDF 表通常为哈希；PSD 行可能是 PSD dictionary snapshot 加编号。不是表的业务名称。 |
| `source_page` | PDF 页码 | `0` | PDF 来源的物理页码，从 1 开始；PSD 行的 0 表示不来自 PDF，不是 PDF 第零页。 |
| `source_occurrences` | 相同源单元格出现次数 | `1` | 某些原表重复印刷了相同业务维度和数值，经过检查后合并，记录出现次数。通常为 1；不要用它乘以 value。 |
| `source_locations` | 原始位置清单 | `{"countryCode": "00", "attributeId": "184"}` | PDF 行为 JSON 位置列表（页、行、原值）；PSD 行为国家代码和指标代码等源定位信息。用于追溯，不是另一个指标。 |
| `commodity_code` | PSD 商品代码 | `0440000` | 仅 psd_current 行有对应的正式代码，例如 0440000＝玉米。PDF 行当前不强行映射，填 not_applicable；商品需看原标签。 |
| `geography_code` | PSD 地区代码 | `00` | PSD 的国家或汇总代码，00＝世界。PDF 行为 not_applicable，即使 row_label 恰好是国家，也没有声称已经完成代码映射。 |
| `attribute_code` | PSD 指标代码 | `184` | 与 indicator 对应的官方指标代码，例如 28＝Production、184＝Yield。PDF 行不强行映射，填 not_applicable。 |
| `unit_code` | PSD 单位代码 | `26` | 源单位字典代码，需与 unit 配合看。PDF 行为 not_applicable，实际单位仍在 unit 中。 |
| `observation_kind` | 数值来源类型 | `psd_current` | psd_current＝PSD API 当前修订序列；report_table＝原始 PDF 报告表格。分析前优先筛选此列，不要把同一事实的两个来源相加。 |
| `source_calendar_year` | PSD 记录更新年份 | `2026` | API 记录提供的 calendarYear，不是数据所属市场年度。PDF 行为 not_applicable。 |
| `source_month` | PSD 记录更新月份 | `11` | API 记录提供的 month，例如 11。同一次响应的不同记录可能有不同更新月份；不是独立确认的完整发布日期。PDF 行为 not_applicable。 |
| `aggregation_level` | 地区汇总层级 | `world` | PSD 可为 country（国家）、region（区域合计）、world（世界）、residual_aggregate（其他／剩余合计）；PDF 为 report_defined，需按原表判断。 |
| `source_region_code` | PSD 地区归属代码 | `R00` | 记录所属的源区域，例如 R00、R12，只是地区分类信息，不表示额外一条区域合计。PDF 行为 not_applicable。 |


## 时间、来源与版本字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `source_release_date` | 来源发布日期 | `\N` / `2026-11-10` | 来源明确提供的发布或更新日期。它不是数据所描述的年份，也不是你下载文件的日期；不同数据集的具体含义见本页说明。 |
| `source_release_at_utc` | 来源发布时刻（UTC） | `\N` / `2026-11-10T17:15:00+00:00` | 有依据的完整发布时间，统一为 UTC。只有日期、月份或没有时区时不能补造时刻，通常保存为 \N。 |
| `release_time_precision` | 发布时间精度 | `month` | 说明来源发布时间知道得有多细：timestamp 精确时刻，date/day 到日，month 到月，unknown 无法确认。不是数值的小数精度。 |
| `retrieved_at_utc` | 本地获取时间（UTC） | `2026-11-17T12:57:06.444204+00:00` | 该快照关联的源文件首次获取／导入本地缓存的时间。离线重放素材时也会生成本地导入回执；不能用它推断数据何时首次公开。 |
| `source_artifact_id` | 原始文件指纹 | `c664fb044e5f0ab81262960152b354d9ace9852e60926ddc753aedb4b1cae992` | 原始响应、CSV、PDF 或 ZIP 的 SHA-256，用于找到和核对源文件。不是商品、地区、报表行的编号。 |
| `snapshot_id` | 处理结果版本编号 | `69e01ee04f13013d5e0c15fb603275647766c53c1c45961af8d2def568677b36` | 标识源文件与解析器、字段定义、配置共同形成的一次标准化版本。同一来源重新处理可能产生新版本；不能把它当经济时间或业务主键。 |
| `vintage_type` | 数据版本性质 | `current_revised` | report_vintage：保留某期报告当时的数值；current_revised：下载时可见、可能已修订的历史序列；forecast_vintage：保留某次发布的预测版本。 |

## 两种来源的字段差别

| 事项 | `psd_current` | `report_table` |
|---|---|---|
| 数值版本 | 当前能取得的修订序列 | 指定报告当时公布的值 |
| 发布月份 | 不假装属于某期 PDF，report_period 为 not_applicable | report_period 为原报告月份 |
| 代码 | 保留正式 PSD 商品／地区／指标／单位代码 | 当前不强制对齐 PSD 代码，填 not_applicable |
| 来源页码 | 0，表示不是 PDF | 从 1 开始的 PDF 物理页码 |
| 地区解释 | aggregation_level 明确标识国家／区域／世界 | report_defined，按原表标签判断 |
| 数据更新年月 | source_calendar_year / source_month | 不适用 |

世界、区域和成员国有重叠；Other／Total／Subtotal 也可能有重叠。不要对文件全部行无条件求和。MY 是市场年度、TY 是贸易年度，年度的起止应按原表及商品解释。

独立的 `fas_report_observations.v1.json` 只包含本页的前 26 列：从 `report_family` 到 `vintage_type`；它用于 PDF 解析层。本页后九列是三个最终数据集额外添加的来源／代码字段。
