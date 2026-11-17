# 成本与收益（ERS）：中文字段说明

[返回字段说明入口](../field_dictionary.md) · [通用读法与空值](common.md) · [机器可读字段定义](../../schemas/ers_costs_returns.v1.json)

## 这个数据集在说什么

描述某种农业生产活动在某地区、某年份的成本、收益及相关生产指标。一行通常是一个具体项目，例如每种植英亩的种子成本；不是一户农场的账单，也不是整个地区的总支出。

## 一行数据怎么读

在 [costs-returns.csv](../../examples/costs-returns.csv) 中，2025 年 Eastern Uplands 地区玉米的 `Capital recovery of machinery and equipment`（机械设备资本回收费用）为 `162.2 dollars per planted acre`。读作 **每种植英亩 162.2 美元**。`Base survey of 2021` 说明基础调查版本，数据描述的年份仍是 2025。

## 先看哪些列

先选 `commodity`、`enterprise_type`、`region`、`year`，再选 `category` 与 `item`。比较数值前检查 `unit`、`methodology`、`series_family` 和 `forecast_vintage` 是否一致。

下面逐列覆盖当前 29 个字段。例值来自仓库固定示例，可能取自不同记录，不能把整列例值拼成一条记录；长 JSON／编号用省略号显示。字段的类型、是否允许为空和完整复合键以导出旁的 `schema.json` 为准。

## 业务字段与核对字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `commodity` | 农产品 | `Corn` | 统计对象，例如 Corn（玉米）、Soybeans（大豆）、Milk（奶）。 |
| `enterprise_type` | 生产经营类型 | `Corn` | 区分同一产品下不同生产环节／经营类型。作物通常与 commodity 相同；养猪等必须保留育仔、育肥等原有类型，不能合并成一条猪肉成本。 |
| `region` | 统计地区 | `Eastern Uplands` | 例如 Eastern Uplands 是 ERS 的区域分组，U.S. total 是全美国。区域名称不一定对应州。 |
| `country` | 国家 | `United States` | 所属国家，当前这些数据主要为 United States。区域与国家应一起看。 |
| `size` | 经营规模分组 | `No specific size` | 原表的农场／经营规模类别。No specific size 或 not_specified 表示没有指定规模分组，不代表规模为零。 |
| `year_label` | 原始年份标签 | `2025` | 保留原文，如 2025F；F 表示预测标签。它与纯数字 year 不完全相同，不能丢掉标签后把预测和估计混为一条。 |
| `series_family` | 资料系列 | `Recent` | Recent＝近期系列；Historical＝历史系列；forecast＝当前预测；previously released forecasts＝历史发布过的预测。分类不同可能有不同方法或版本。 |
| `methodology` | 调查基础／核算口径 | `Base survey of 2021` | 例如 Base survey of 2021 表示以 2021 年基础调查为依据，不表示此行统计的是 2021 年。历史现金成本、经济成本等口径也由此区分。 |
| `table_title` | 原表标题或格式标签 | `machine readable` | 用于区分来源表。machine readable 表示来自机器可读表，不是一个经济指标。 |
| `category` | 指标大类 | `Allocated overhead` | 例如 Operating costs（经营成本）、Allocated overhead（分摊的间接成本）、Gross value of production（生产总值）。 |
| `item` | 具体成本／收益项目 | `Capital recovery of machinery and equipment` | 例如机械设备资本回收费用、雇工费用、种子费用。已清理多余空格及部分脚注标号，原文见 source_item。 |
| `unit` | 每项指标的计量单位 | `dollars per planted acre` | dollars per planted acre＝美元／种植英亩；percent of acres＝面积占比的百分数；planted acres＝种植英亩。并非每行都是美元。 |
| `forecast_vintage` | 预测发布版本 | `not_applicable` / `Historical Forecast Zip Folder/cop_forecast_Dec 2025.xlsx` | 区分对同一年在不同时间作出的预测。历史预测通常保留 ZIP 内文件名，current_forecast 为当前预测，非预测为 not_applicable。 |
| `classification` | 原表附加分类 | `not_applicable` | 保留烟草类型等列级细分，避免把不同类型当成同一指标。没有该分类时为 not_applicable。 |
| `year` | 指标描述的年份 | `2025` | 从 year_label 解析的整数年份，例如 2025。它不是调查基准年，也不是下载年份。 |
| `value` | 该成本／收益指标的值 | `162.2` | 按本行 unit 解释。例如 162.2 美元／种植英亩，不能读成该地区总支出 162.2 美元。 |
| `raw_value` | 源文件中的原值 | `162.2` | 保存原来看到的数字文字或缺失标记，用来核对 value；正常分析使用解析后的数值。历史 Excel 的原值是读取器读到的存储值，不一定等于界面显示的四舍五入值。 |
| `value_status` | 数值状态 | `reported` | 解释数值是正常公布、缺失、不适用、未公布等。先看此列再决定如何处理空值；只有 reported 才表示正常数值，零仍然可以是 reported。 |
| `estimate_status` | 估计或预测性质 | `unknown` | forecast＝明确的预测；estimate＝明确标为估计；unknown＝源文件没有提供足够标签。当前解析不会仅凭年份推断。 |
| `source_item` | 原始项目名称 | `Capital recovery of machinery and equipment` | 未经 item 清理的原文字段，可包含脚注标号及空格，核对来源时使用。 |
| `source_extra` | 其他原始字段 | `{}` | JSON 字符串，保留源表中额外的代码、注释等。{} 表示没有额外内容。 |
| `source_locator` | 原始单元格位置 | `{"record": 52}` | JSON 字符串，记录 CSV 记录号或 Excel 工作表、行列位置，用来找到出处。它不是业务类别。 |


## 时间、来源与版本字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `source_release_date` | 来源发布日期 | `2026-10-01` | 来源明确提供的发布或更新日期。它不是数据所描述的年份，也不是你下载文件的日期；不同数据集的具体含义见本页说明。 |
| `source_release_at_utc` | 来源发布时刻（UTC） | `\N` | 有依据的完整发布时间，统一为 UTC。只有日期、月份或没有时区时不能补造时刻，通常保存为 \N。 |
| `release_time_precision` | 发布时间精度 | `date` | 说明来源发布时间知道得有多细：timestamp 精确时刻，date/day 到日，month 到月，unknown 无法确认。不是数值的小数精度。 |
| `retrieved_at_utc` | 本地获取时间（UTC） | `2026-11-17T12:57:06.299461+00:00` | 该快照关联的源文件首次获取／导入本地缓存的时间。离线重放素材时也会生成本地导入回执；不能用它推断数据何时首次公开。 |
| `source_artifact_id` | 原始文件指纹 | `a42362ce2c9b8f6a5992ae11ef6cb1ed12e25ec59b694782572daea646113951` | 原始响应、CSV、PDF 或 ZIP 的 SHA-256，用于找到和核对源文件。不是商品、地区、报表行的编号。 |
| `snapshot_id` | 处理结果版本编号 | `1283b9a74f19c7d6055eef45a024bc5b0b4a53dbac0cd7d7962b936842e851e2` | 标识源文件与解析器、字段定义、配置共同形成的一次标准化版本。同一来源重新处理可能产生新版本；不能把它当经济时间或业务主键。 |
| `vintage_type` | 数据版本性质 | `current_revised` | report_vintage：保留某期报告当时的数值；current_revised：下载时可见、可能已修订的历史序列；forecast_vintage：保留某次发布的预测版本。 |

## 容易误读的地方

- `year=2025` 并不保证只有一条值：不同预测版本、调查方法、经营类型可以同时存在。
- 每英亩、每头牛、每英担的成本不能直接求和。项目小计与组成项目也不能再次相加。
- 源脚注 `1/` 在已支持的特定历史表中表示“已包括在其他项目”，解析为 `included_elsewhere`，不是零成本。
- `source_release_date` 通常是源页面提供的文件更新日，不自动等于历史预测文件最初发布的精确日期；预测版本优先看 `forecast_vintage`。

更多来源与处理细节：[成本收益技术说明](../costs_returns.md)。
