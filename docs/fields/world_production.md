# 世界农业生产：如何读 CSV

[返回字段说明入口](../field_dictionary.md) · [示例 CSV](../../examples/world-production.csv) · **[全部 35 列中文定义](report_fields.md)**

## 这个文件回答什么问题

某作物在某地区种了多少面积、单产是多少、总产量是多少，以及某期报告怎样调整预测。原始报告还包含预测可靠性统计，所以不是每一行都是生产数量。

## 从示例读两条记录

**PSD 行：** `observation_kind=psd_current`，`row_label=World`，`column_commodity=Corn`，`indicator=Yield`，`period_label=2025`，`value=6.2148`，`unit=(MT/HA)`。

这表示：当前 PSD 数据中，市场年度编号 2025 的**世界玉米单产为每公顷 6.2148 公吨**。它不是 2025 年某一期历史报告的原值，也不是总产量。

**PDF 行：** `observation_kind=report_table`，`report_period=2026-11`，表名为 `TABLE 18 Reliability of Production Projections`，`section_label=BARLEY`，`row_label=United States`，指标为 `90 percent confidence interval`，数值为 `2.5 Percent`。

这表示：2026 年十一月报告的**美国大麦产量预测可靠性表**列出了一项 90% 置信区间相关统计，表中数值为 2.5%。它不是美国大麦产量 2.5；这一行的商品写在 `section_label` 中，因此 `column_commodity=not_applicable` 并不表示缺少商品信息。

## 按任务选择字段

| 想看什么 | 应先检查 |
|---|---|
| 某国某作物的供需／生产序列 | 先选 `psd_current`，再选商品、地区、`period_label`、`indicator`、`unit` |
| 某期报告当时给出的预测 | 先选 `report_table`，再选 `report_period`、原表和比较列 |
| 预测调整了多少 | 确认 `comparison_label` 和 `indicator` 是否为变化量／变化率，不把它当总产量 |
| 稻米、棉花等特殊产品 | 按原表的产品口径和单位解释，不能直接套用其他谷物的计算方式 |

面积、单产与产量只有在商品、口径、时期、单位、版本完全一致时才可能进行关系核对。原表稻米的单产与生产量可能分别采用稻谷／精米口径，不能直接相乘。

本文件使用的全部列都在[共用字段表](report_fields.md)逐项解释；时间、空值与数量级见[通用读法](common.md)。原有详细来源说明保留在 [world_production.md](../world_production.md)。
