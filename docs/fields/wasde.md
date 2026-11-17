# WASDE：中文字段说明

[返回字段说明入口](../field_dictionary.md) · [通用读法与空值](common.md) · [机器可读字段定义](../../schemas/wasde_observations.v2.json)

## 这个数据集在说什么

WASDE 是每期发布的农产品供需估计报告。CSV 通常把原表中的一个数值单元格展开为一行：某期报告对某个地区、商品、市场年度、指标给出了多少。它同时含价格和预测可靠性等表，所以不能把所有 `Value` 都理解成产量。

## 一行数据怎么读

在 [wasde.csv](../../examples/wasde.csv) 中，第 677 期、2026-11-10 发布的报告，对墨西哥糖的 2025/26 市场年度列出 `Beginning Stocks`（期初库存）为 `1123.00`，单位为千公吨（实际重量）。读作 **期初库存 112.3 万公吨**，不是 1123 吨；`Est.` 表示估计值。

## 先看哪些列

先筛选 `ReportTitle`、`Commodity`、`Region`、`MarketYear` 和 `Attribute`，再看 `Value` 与 `Unit`。需要比较不同期预测时，再保留 `source_release_date`，不要只按市场年度去重。

下面逐列覆盖当前 30 个字段。例值来自仓库固定示例，可能取自不同记录，不能把整列例值拼成一条记录；长 JSON／编号用省略号显示。字段的类型、是否允许为空和完整复合键以导出旁的 `schema.json` 为准。

## 业务字段与核对字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `WasdeNumber` | 报告期号 | `677` | USDA 对这期 WASDE 的编号。677 表示第 677 期，不是年份。 |
| `ReportDate` | 报告月份标签 | `November 2026` | 原始报告的月份文字，例如 November 2026。它告诉你是哪期报告；精确发布日期另看 ReleaseDate。 |
| `ReportTitle` | 原表标题 | `Mexico Sugar Supply and Use and High Fructose Corn Syrup Consumption` | 这一行来自报告中的哪张表。相同商品可同时出现在供需表、价格表、预测可靠性表，必须连同标题理解。 |
| `Attribute` | 统计指标 | `Beginning Stocks` | 这一行测量什么，例如 Beginning Stocks＝期初库存、Production＝产量、Ending Stocks＝期末库存。不能只看 Value 判断指标。 |
| `ReliabilityProjection` | 预测可靠性统计类别 | `not_applicable` / `above_final` | 仅可靠性／误差表使用，例如 average（平均差异统计）、above_final（预测高于最终结果的年数类别）。其他表为 not_applicable。必须结合原表和 Unit 解释，不能把误差统计当产量。 |
| `Commodity` | 商品或产品类别 | `Sugar` | 原表统计的商品，例如 Sugar（糖）、Corn（玉米）。保留原来的品种／细分类，不统一改成大类。 |
| `Region` | 统计地区或汇总范围 | `Mexico` | 例如 Mexico（墨西哥）、United States（美国）、World（世界）。也可能是汇总组，不能默认每个名称都代表一个独立国家。 |
| `MarketYear` | 数据所属市场年度 | `2025/26` | 例如 2025/26：按该商品的市场年度统计，不等于报告发布年份。可靠性表等没有单一年度时为 not_applicable。 |
| `ProjEstFlag` | 估计／预测标记 | `Est.` | Est.＝估计值，Proj.＝预测值；not_labelled 表示原表未标注。不能因为年份已过去就自行认定是最终值。 |
| `AnnualQuarterFlag` | 年度／季度口径 | `Annual` | 原表给出的年度或季度统计标签。Annual 表示全年口径；季度记录与全年记录不能混合求和。 |
| `Value` | 该指标的数值 | `1123.00` | 与 Attribute、Commodity、Region、MarketYear 和 Unit 一起使用。数值本身不含单位，也未统一换算成吨。 |
| `Unit` | 单位和数量级 | `1000 Metric Tons, Actual Weight` | 例如 1000 Metric Tons, Actual Weight＝千公吨、实际重量口径；1123.00 表示 1,123,000 公吨。其他表可能是价格、年数或百分比。 |
| `ReleaseDate` | 原始发布日期文字 | `2026-11-10` | 源 CSV 中的发布日期，例如 2026-11-10。source_release_date 是据此解析出的日期字段；两者都不是 MarketYear。 |
| `ReleaseTime` | 原始发布钟点 | `12:00:00.0000000` | 源 CSV 中保留的时间文字。没有独立确认时区时，不把它直接当作 UTC，也不据此填写 source_release_at_utc。 |
| `ForecastYear` | 预测／报告批次年份 | `2026` | 源 CSV 标识这次预测批次的年份；不要把它当作数值所属市场年度，后者看 MarketYear。 |
| `ForecastMonth` | 预测／报告批次月份 | `11` | 源 CSV 标识这次预测批次的月份，11 为十一月；与 ForecastYear 一起识别批次，不代表作物收获月份。 |
| `raw_value` | 源文件中的原值 | `1123.00` | 保存原来看到的数字文字或缺失标记，用来核对 value；正常分析使用解析后的数值。历史 Excel 的原值是读取器读到的存储值，不一定等于界面显示的四舍五入值。 |
| `value_status` | 数值状态 | `reported` | 解释数值是正常公布、缺失、不适用、未公布等。先看此列再决定如何处理空值；只有 reported 才表示正常数值，零仍然可以是 reported。 |
| `raw_optional_dimensions` | 可选分类的原始写法 | `{"MarketYear": "2025/26", "ProjEstFlag": "Est.", "ReliabilityProj…` | JSON 字符串，保留 MarketYear、ProjEstFlag、ReliabilityProjection 的原始空白或标签。便于检查 not_applicable 等是如何填入的。 |
| `source_member` | ZIP 内文件名 | 空字符串 | 来源是 ZIP 时记录内部 CSV 文件名；直接下载的独立 CSV 通常是空字符串。 |
| `source_dimension_repair` | 维度修正依据编号 | 空字符串 | 只有命中经过核对的特定源文件缺陷时才填写。空字符串表示未修正；这不是自动修改数值的记录。 |
| `source_original_dimensions` | 修正前的字段内容 | `{}` | JSON 字符串，记录维度修正前的原始内容。{} 表示没有需记录的修正内容。 |
| `source_conflict` | 已知跨格式差异 | 空字符串 | 记录同一位置的 CSV／XML 与 PDF 已知数值差异及依据。空字符串表示未记录此类差异；发生已登记差异时 CSV 数值仍按所选结构化来源保留。 |


## 时间、来源与版本字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `source_release_date` | 来源发布日期 | `2026-11-10` | 来源明确提供的发布或更新日期。它不是数据所描述的年份，也不是你下载文件的日期；不同数据集的具体含义见本页说明。 |
| `source_release_at_utc` | 来源发布时刻（UTC） | `\N` | 有依据的完整发布时间，统一为 UTC。只有日期、月份或没有时区时不能补造时刻，通常保存为 \N。 |
| `release_time_precision` | 发布时间精度 | `date` | 说明来源发布时间知道得有多细：timestamp 精确时刻，date/day 到日，month 到月，unknown 无法确认。不是数值的小数精度。 |
| `retrieved_at_utc` | 本地获取时间（UTC） | `2026-11-17T12:57:06.172384+00:00` | 该快照关联的源文件首次获取／导入本地缓存的时间。离线重放素材时也会生成本地导入回执；不能用它推断数据何时首次公开。 |
| `source_artifact_id` | 原始文件指纹 | `1a28972ac0c727ce974e0f8217b3cae9e892f6e974f6927033eaffbd5890a8da` | 原始响应、CSV、PDF 或 ZIP 的 SHA-256，用于找到和核对源文件。不是商品、地区、报表行的编号。 |
| `snapshot_id` | 处理结果版本编号 | `483832b47869d6dc7582393dcd5cd4e329c25a574629f91185ee9c242d933327` | 标识源文件与解析器、字段定义、配置共同形成的一次标准化版本。同一来源重新处理可能产生新版本；不能把它当经济时间或业务主键。 |
| `vintage_type` | 数据版本性质 | `report_vintage` | report_vintage：保留某期报告当时的数值；current_revised：下载时可见、可能已修订的历史序列；forecast_vintage：保留某次发布的预测版本。 |

## 容易误读的地方

- 同一个市场年度会在多期报告中出现，是不同发布版本，不是重复下载造成的重复行。
- `Beginning Stocks`、`Ending Stocks` 是库存；`Production`、`Exports` 是期间指标；预测可靠性表的误差和年数不能当供需量相加。
- 本接口按 `ReleaseDate` 确认发布日；源钟点没有足够时区依据时，UTC 发布时刻保持空值。

更多来源与处理细节：[WASDE 技术说明](../wasde.md)。
