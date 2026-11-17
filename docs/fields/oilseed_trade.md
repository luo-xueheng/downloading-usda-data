# 油籽贸易：如何读 CSV

[返回字段说明入口](../field_dictionary.md) · [示例 CSV](../../examples/oilseed-trade.csv) · **[全部 35 列中文定义](report_fields.md)**

## 这个文件回答什么问题

油籽、蛋白粕、植物油的生产、压榨、消费、进出口和库存，以及报告中的预测变化。大豆、豆粕、豆油是不同产品，不是同一商品的三个同义名称。

## 从示例读两条记录

**PSD 行：** `row_label=World`，`column_commodity=Oilseed, Soybean`，`indicator=Domestic Consumption`，`period_label=2025`，`value=433053.0000`，`unit=(1000 MT)`。

这表示：当前 PSD 序列中该市场年度编号的**世界大豆国内消费为 433,053 千公吨**。这是大豆这一产品的消费指标，不能直接加上豆粕／豆油消费当作去重消费总量。

**PDF 行：** 2026 年十一月报告的 `2025/26 OUTLOOK CHANGES` 表，`row_label=Brazil`，`column_commodity=Meal, Soybean`，`indicator=Exports`，`comparison_label=Change`，数值为 `-190 Thousand Metric Tons`。

这表示：这期报告对**巴西 2025/26 年度豆粕出口预测下调了 19 万公吨**。负号表示预测变化方向，不是巴西的出口总量为负。

## 容易误读的地方

- `section_product_type` 可用来区分 Oilseed、Meal、Oil 大类中重复出现的 Total／Other，不能只按 `row_label` 合并。
- `comparison_label=Change` 的数值是变化量；只有先确认指标和比较列，才能决定是否画成出口量时间序列。
- 面积行仍可能是公顷，数量行才是吨；原表主标题提到吨，不代表所有列都使用吨。
- `nr` 等未报告标记不是零；源表经四舍五入，显示的小项之和不一定与显示总计完全相等。

本文件全部列见[共用字段表](report_fields.md)，空值与数量级见[通用说明](common.md)。原有详细来源说明保留在 [oilseed_trade.md](../oilseed_trade.md)。
