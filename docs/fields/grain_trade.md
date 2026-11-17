# 谷物贸易：如何读 CSV

[返回字段说明入口](../field_dictionary.md) · [示例 CSV](../../examples/grain-trade.csv) · **[全部 35 列中文定义](report_fields.md)**

## 这个文件回答什么问题

小麦、稻米、玉米等谷物的生产、消费、贸易、库存情况，以及某期报告如何修订这些数值。文件同时有 PSD 当前修订序列和原始报告表格，先看 `observation_kind`。

## 从示例读两条记录

**PSD 行：** `row_label=World`，`column_commodity=Corn`，`indicator=TY Exports`，`period_label=2025`，`value=207552.0000`，`unit=(1000 MT)`。

这表示：PSD 中该年度编号下的**世界玉米贸易年度出口量为 207,552 千公吨**。TY 表示贸易年度口径，不能随意替换为自然年或当地市场年度口径。

**PDF 行：** 来自 2026 年十一月的 `All Grain Summary Comparison` 表，`row_label=Other`，`column_commodity=Corn`，`indicator=Domestic Consumption`，`period_label=2024/25`，`value=941.0`，`unit=Million Metric Tons`。

这表示：该原表中 **Other 这一汇总类别的玉米国内消费为 941 百万公吨**。Other 是原表的分组，不是一个叫“Other”的国家；需要结合表中的其他分组解释其范围。

## 容易误读的地方

- `Exports` 是出口指标；`TY Exports` 明确带贸易年度口径；同名的“进口／出口”在不同表里未必采用相同期间。
- `Previous`、`Current`、`Change` 分别是前次、本次和变化量，不能相加作为出口总量。
- World、地区合计、成员国、Other、Subtotal 之间可能有重叠，不能直接对整个 CSV 求和。
- `Domestic Consumption` 与 `Feed Dom. Consumption` 不是同一级别的独立总量；饲料消费可能已包含在国内消费中。

本文件全部列见[共用字段表](report_fields.md)，单位和时期读法见[通用说明](common.md)。原有详细来源说明保留在 [grain_trade.md](../grain_trade.md)。
