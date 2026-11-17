# 农业保险业务（RMA）：中文字段说明

[返回字段说明入口](../field_dictionary.md) · [通用读法与空值](common.md) · [机器可读字段定义](../../schemas/rma_sob.v2.json)

## 这个数据集在说什么

按作物保险年度、州、县、作物、保险计划和保障条件汇总的保险业务数据。一行是一个条件组合的汇总，包含保单／保险单元计数、承保数量、保费、补贴和赔款；不是一张个体保单，也不是一个农户。直接下载为 Schema v2，聚合可升级为 v3，两版的列、类型及 CSV 数值一致。

## 一行数据怎么读

在 [rma-sob.csv](../../examples/rma-sob.csv) 的第一行，2025 年阿拉斯加 Southeast Fairbanks 的“其他作物”、APH 计划、50% 保障水平下，净报送数量是 **200 英亩**，补贴前保费 **1449 美元**，赔款 **29930 美元**，赔付率 **20.66 倍**。不能把它读成赔付率 20.66%，也不能将 2 份售出保单当作 2 个独立农户。

## 先看哪些列

先确定 `commodity_year`、州县、作物、保险计划及 `coverage_level`。承保数量看 `net_reported_quantity` 和 `quantity_type`；金额看各金额列；计数要先检查 `count_availability`。

下面逐列覆盖当前 40 个字段。例值来自仓库固定示例，可能取自不同记录，不能把整列例值拼成一条记录；长 JSON／编号用省略号显示。字段的类型、是否允许为空和完整复合键以导出旁的 `schema.json` 为准。

## 业务字段与核对字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `commodity_year` | 作物／保险年度 | `2025` | 通常对应作物正常收获年份，并指明提供保障的保单年度。不是保险数据发布或下载年份。 |
| `state_code` | 州 FIPS 代码 | `02` | 被保险农场所在州的两位代码，02 为阿拉斯加。保留前导零；单独的州代码不是全国唯一农场编号。 |
| `state_abbreviation` | 州缩写 | `AK` | 美国邮政州缩写，例如 AK（阿拉斯加）、AL（阿拉巴马）。 |
| `county_code` | 县 FIPS／汇总代码 | `240` | 三位县代码，要与 state_code 合用。999 为 All Other Counties 等特殊汇总，不能自动当作普通县。 |
| `county_name` | 县或县级汇总名称 | `Southeast Fairbanks` | 例如 Southeast Fairbanks；All Other Counties 是其他县的合计标签。 |
| `commodity_code` | RMA 农产品代码 | `9999` | 保险业务使用的四位作物／产品代码，例如 0041 为示例中的玉米。与 ESR、PSD 代码不能直接关联。 |
| `commodity_name` | 保险农产品名称 | `All Other Crops` | 保单对应的作物／产品，All Other Crops 表示源表的其他作物合计，不是具体作物品种。 |
| `insurance_plan_code` | 保险计划代码 | `90` | 所选保险保障计划的官方代码，不是保障比例。用 insurance_plan_name 辅助识别。 |
| `insurance_plan_name` | 保险计划简称 | `APH` | 例如 APH（实际生产历史类）、RP（收入保障类）、WFRP（整场收入保障类）。计划不同，保障水平的适用基数也不同。 |
| `coverage_category` | 保障类别 | `A` | A＝Buyup（加购保障），C＝CAT（灾害保障），E＝Existing Coverage Policy（已有保障保单），L＝Limited Coverage（有限保障）。是类别代码，不是评级。 |
| `delivery_type` | 保险承办／再保险类别 | `RBUP` | RBUP＝再保险加购保障，RCAT＝再保险灾害保障，FBUP＝联邦加购保障，FCAT＝联邦灾害保障。保留原代码，避免与 coverage_category 混淆。 |
| `coverage_level` | 保障水平 | `0.5000` | 十进制比例，例如 0.5000＝50%。适用基数随计划变化，可能是产量、收入、金额或存量，不能一律理解为固定产量保障。 |
| `policies_sold` | 已销售保单数 | `2` | 报告给 RMA 的售出保单数量。不是投保农户去重人数；CLIP 计划无法提供这类计数时保存为空。 |
| `policies_earning_premium` | 形成保费的保单数 | `1` | 官方口径为已向 RMA 报送面积的保单数，并不是“实际收到保费付款”的保单数。 |
| `policies_indemnified` | 报告损失的保单数 | `1` | 官方口径为已向 RMA 报送损失的保单数量，不应简单按 indemnity_amount > 0 自行重算。 |
| `units_earning_premium` | 形成保费的保险单元数 | `1` | 已报送面积的保险单元数量。unit 是保险业务中的单元，不是 unit 计量单位，也不是农户数。 |
| `units_indemnified` | 报告损失的保险单元数 | `1` | 已报送损失的保险单元数量，与保单数不同，一份保单可能涉及多个单元。 |
| `quantity_type` | 承保数量的单位／类型 | `Acres` | 例如 Acres（英亩）、Tons（吨）、Pounds（磅）、Trees（树株）。Not Reported 表示未说明类型，不能默认换成英亩。 |
| `net_reported_quantity` | 按投保权益份额调整的数量 | `200` | 报送种植数量乘以投保人的权益份额等调整后的净数量；必须与 quantity_type 一起使用。不是所有行都表示面积。 |
| `endorsed_companion_acres` | 附加保障／配套选项英亩数 | `0` | 通过附加条款或配套选项承保的面积，单位固定为英亩。可能与基础保障面积重叠，不能直接相加当作去重面积。 |
| `liability_amount` | 保险责任金额 | `45100` | 此记录对应的最高保险保障金额，单位美元。不是已经赔付的金额。 |
| `total_premium` | 补贴前总保费 | `1449` | 在应用补贴之前的保费金额，单位美元；不能当成投保人最终自付保费。 |
| `subsidy_amount` | 保费补贴金额 | `971` | 该记录的补贴保费金额，单位美元。其他补贴字段另外保留，不在这里擅自合并。 |
| `state_private_subsidy` | 州／私人机构补贴 | `0` | 州政府或私人机构提供的补贴金额，单位美元，与一般补贴字段区分。 |
| `additional_subsidy` | 额外项目补贴 | `0` | 某个项目或其他流程产生的额外补贴，单位美元。官方布局说明：2021、2022 年此项为 Pandemic Cover Crop Program 金额；不能把这一解释套用到所有年份。 |
| `efa_premium_discount` | EFA 保费折扣金额 | `0` | 单位美元。官方 2026-05-28 布局列出了名称，但定义栏留空；本仓库没有足够依据进一步展开 EFA 的含义，按原字段保留。 |
| `indemnity_amount` | 赔款／损失金额 | `29930` | 该记录的赔款金额，单位美元。来源允许带符号的调整，负数不能自动改成零。 |
| `loss_ratio` | 赔付率（比值） | `20.66` | indemnity_amount ÷ total_premium。1 表示赔款等于保费，0.5 表示约 50%；20.66 表示约 20.66 倍，不是 20.66%。保留源表值，不逐行重算覆盖。 |
| `raw_record` | 原始管道符记录 | `2025&#124;02&#124;AK&#124;240&#124;Southeast Fairbanks           &#124;9999&#124;All Other Crop…` | 保留源 TXT 的整行，字段以竖线分隔。源 NUL 字符为 SQL 可读性写成字面 Unicode 转义，原始精确字节仍在源 ZIP。 |
| `missing_fields` | 哪些字段缺失 | `[]` | JSON 数组，列出原来没有数值或按规则无法提供的字段；[] 表示没有列出缺失项。应与 count_availability 一起看。 |
| `count_availability` | 保单／单元计数是否可用 | `reported_source_values` | reported_source_values 表示保留源计数；CLIP 计数不可用时记录对应状态并将这些计数字段置空，不补成零。 |
| `source_member` | ZIP 中的源 TXT 文件名 | `sobcov_2025.txt` | 例如 sobcov_2025.txt，用来定位原始文件。 |
| `source_line` | 源 TXT 行号 | `1` | 从 1 开始的原始行号，用来核对出处；不是保单编号，也不能代替业务字段识别记录。 |


## 时间、来源与版本字段

| CSV 列名 | 中文含义 | 示例中的实际值 | 如何理解 |
|---|---|---|---|
| `source_release_date` | 来源发布日期 | `\N` | 来源明确提供的发布或更新日期。它不是数据所描述的年份，也不是你下载文件的日期；不同数据集的具体含义见本页说明。 |
| `source_release_at_utc` | 来源发布时刻（UTC） | `\N` | 有依据的完整发布时间，统一为 UTC。只有日期、月份或没有时区时不能补造时刻，通常保存为 \N。 |
| `release_time_precision` | 发布时间精度 | `unknown` | 说明来源发布时间知道得有多细：timestamp 精确时刻，date/day 到日，month 到月，unknown 无法确认。不是数值的小数精度。 |
| `retrieved_at_utc` | 本地获取时间（UTC） | `2026-11-17T12:57:06.466884+00:00` | 该快照关联的源文件首次获取／导入本地缓存的时间。离线重放素材时也会生成本地导入回执；不能用它推断数据何时首次公开。 |
| `source_artifact_id` | 原始文件指纹 | `c66d887d099c437327780238c9679ca1d1fd1350ab1dd42107ecee9382e74a58` | 原始响应、CSV、PDF 或 ZIP 的 SHA-256，用于找到和核对源文件。不是商品、地区、报表行的编号。 |
| `snapshot_id` | 处理结果版本编号 | `a79883b3e51715d328e431b6f9c729208fce160e2c207fea2cbe41b5527a09c9` | 标识源文件与解析器、字段定义、配置共同形成的一次标准化版本。同一来源重新处理可能产生新版本；不能把它当经济时间或业务主键。 |
| `vintage_type` | 数据版本性质 | `current_revised` | report_vintage：保留某期报告当时的数值；current_revised：下载时可见、可能已修订的历史序列；forecast_vintage：保留某次发布的预测版本。 |

## 单位、空值和汇总

- 各金额列单位均为美元；`coverage_level` 和 `loss_ratio` 是比例／比值，不是美元。
- 保单数与保险单元数不是同一件事；CLIP 计划的计数不可用时保持空值，不能当零，也不能用其他字段补算。
- `quantity_type` 为树株、磅、吨等时，`net_reported_quantity` 就不是面积。附加保障英亩可能与基础保障重叠。
- 对多个分组计算整体赔付率，应先确认分组互不重叠和数据口径，再用合计赔款／合计保费；不能把各行 `loss_ratio` 相加。总保费为零时不要强行计算比率。
- 当前源没有足够依据给出每个年度文件的精确发布日期；网络 Last-Modified 也不是已验证的发布日。

字段 1–28 的业务含义对照仓库保存的 [官方布局说明（2026-05-28）](../../test/fixtures/raw/rma-layout.pdf)。其中 EFA 定义栏为空，因此本页明确保留未知。更多细节：[RMA 技术说明](../rma_sob.md)。
