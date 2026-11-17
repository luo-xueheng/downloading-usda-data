**USDA 数据采集项目：完整实施计划**

版本：v1.0  
调研日期：2026-11-12（Asia/Shanghai）  
适用范围：本次截图列出的 7 项数据  
文档性质：实施方案。函数、命令、目录和字段名为拟定设计；尚未完成 API 鉴权测试、样本解析或下载器开发。

**1. 项目目标与交付标准**

建立可重复运行的 Python 数据采集包，完成“官方数据发现 → 下载 → 原始文件归档 → 清洗和校验 → DataFrame/CSV 输出 → 后续更新”。

| 实习要求 | 本项目的具体交付 | 完成标准 |
|---|---|---|
| 了解发布时间 | 发布规则、官方日历入口、时区与抓取策略 | 区分报告发布时间、数据更新时间和实际抓取时间 |
| 优先使用 API | FAS ESR、PSD API 下载器；其他来源使用官方结构化文件 | API 鉴权与真实请求通过；文件下载可自动发现链接 |
| 理解经济含义 | 数据说明、指标字典、单位与口径说明 | 能解释每列含义、每行粒度和主要使用限制 |
| 提供 Python 公开函数 | 可导入的下载函数 | 返回 pandas DataFrame，不要求调用者使用终端 |
| 提供 CLI | 统一 `usda-data` 命令 | 参数控制数据集、范围、输出及更新方式 |
| 模块化 | 公共网络、存储、校验模块，以及独立数据源模块 | 单个来源变化不要求改写全部下载器 |
| 方便 SQL 入库 | 固定字段、类型、唯一键、CSV 和 schema 文件 | CSV 按声明类型重新读取后，数值、空值和代码保持一致 |

本期范围是数据采集和交付，不包含生产数据库部署、交易策略、可视化网站或实际上线定时任务。提供调度说明和可被调度器调用的命令。

**2. 数据范围与默认决策**

| 用户指定项目 | 内部数据集名称 | 底层下载模块 | 输出形式 |
|---|---|---|---|
| WASDE | `wasde` | `wasde` | 供需观测表、原始 CSV/Excel/XML |
| Export Sales | `export-sales` | `fas_esr` | 周度出口销售表、原始 JSON |
| World Agricultural Production | `world-production` | `fas_psd` + `reports` | PSD 生产指标视图、月报原件、报告目录 |
| Grain: World Markets and Trade | `grain-trade` | `fas_psd` + `reports` | PSD 谷物指标视图、月报原件、报告目录 |
| Oilseeds: World Markets and Trade | `oilseed-trade` | `fas_psd` + `reports` | PSD 油籽/油粕/植物油指标视图、月报原件、报告目录 |
| Commodity Costs & Returns | `costs-returns` | `ers_costs_returns` | 成本收益长表、原始 CSV/XLSX |
| RMA Summary of Business | `rma-sob` | `rma_sob` | 保险业务汇总表、原始 ZIP、字段布局文件 |

采用 **5 类数值数据下载器 + 1 个共用报告归档模块**。三份 FAS 月报共用 PSD 下载结果，通过配置生成各自的数据视图；同一条 PSD 记录不重复下载、重复入库。

默认决策如下，实施前可修改配置，不作为启动工作的阻碍：

- 首次验收回填范围：2010 年起至运行时可获取的最新数据；WASDE 历史 CSV 从 2010 年 4 月起。[S01][S02]
- `--all-history` 扩展到各来源实际可获取的最早年份，输出覆盖清单；不承诺所有来源拥有相同历史长度。
- 正式采集覆盖配置范围内全部商品和地区。玉米、大豆、小麦仅作为第一轮联调样例，不能代替完整交付。
- WASDE 覆盖所选官方文件中的可解析结构化表；首个联调样例可从作物表开始，最终记录畜产品等其他表的覆盖情况。
- ERS 范围包含主产品页面的 Recent、Historical 成本收益与成本预测文件，保留企业类型等细分；另行链接的 Organic 产品暂不扩展。
- RMA 本期选择 State/County/Crop/Coverage Level 文件。Cause of Loss、FSA 受阻播种及 RMA 更细的 Type/Practice/Unit 文件暂不纳入。
- 已完成的 NASS Crop Progress & Condition、Crop Production 不重复开发。
- 保留原始数据和后续抓取版本；对无法取得的历史发布版本明确标记，不把最新修订值包装成当时已知值。

**3. 已确认事实与待验证事项**

下列官方资料已查阅；来源编号见文末。已经确认下载入口，不等于下载器已经运行成功。

| 项目 | 已确认 | 实施时仍需验证 |
|---|---|---|
| WASDE | 官方提供合并历史 CSV、当期结构化文件；月度发布 [S01] | 各年份表头、脚注、合并单元格和特殊值；当期文件与历史 CSV 的映射 |
| ESR | 当前门户要求 api.data.gov Key，接口文档提供商品、国家、单位和数据路径 [S03][S04] | 用真实 Key 验证响应字段、历史覆盖、空响应含义和限流 |
| PSD | 支持按商品、国家、营销年度获取指标 [S04] | 报告表格与 API 指标覆盖关系；各商品的历史长度与发布时间信息粒度 |
| FAS 月报 | 官方列出三份报告的发布安排 [S06] | 历史附件链接发现；哪些表可由 PSD 精确重建 |
| ERS | 主页面提供 CSV/XLSX；说明文档给出发布节奏 [S08][S09] | 历史与近期口径衔接、每份文件单位、预测文件布局 |
| RMA | 官方提供年度 ZIP、分隔文本、字段布局 [S10][S11][S12] | ZIP 实际成员、字段数、编码、各年份布局适用性 |

本轮未确认 WASDE、ERS 本产品或 RMA SOB 有更合适的专用公开 API，计划优先使用已确认的官方结构化文件；这不等同于断言它们不存在 API。

**4. 发布日历与抓取时间设计**

官方时间统一按 `America/New_York` 解释，数据库时间统一保存 UTC，面向使用者可显示 `Asia/Shanghai`。精确时刻未知时保存日期与精度标记，不补造 00:00 或固定分钟。

| 数据/文件 | 官方发布规律 | 本项目建议检查策略 | 依据 |
|---|---|---|---|
| WASDE 当期报告 | 按官方月历，12:00 ET | 发布后 5 分钟开始检查；失败或旧文件按退避策略复查 | [S01] |
| WASDE 合并历史 CSV | 报告发布次日更新，具体分钟未说明 | 次日开始检查；内容未变保持等待，超过预期窗口告警 | [S01] |
| ESR | 通常周四 08:30 ET，公告与节假日可能调整 | 读取官方安排，发布后检查 API 更新标记与数据 | [S05] |
| PSD 谷物、油籽等 | 官方生产月报说明相关 PSD 数据在 WASDE 日 12:00 ET 更新 | 12:00 后检查对应商品的更新元数据；不推定所有商品同步 | [S07] |
| 三份 FAS 月报 | 当前官方日历安排为 12:15 ET | 独立检查报告附件，不能用 PSD 成功代替报告归档成功 | [S06] |
| ERS 年度成本收益 | 5 月第一周初步估计、10 月第一周最终估计 | 优先读取各文件的 Next Update；计划日检查，并保留低频巡检 | [S08][S09] |
| ERS 成本预测 | 通常 6 月中旬、11 月中旬 | 与年度估计分开跟踪；确切日期以文件页面为准 | [S09] |
| RMA SOB | 最近五年通常每周一上午刷新，无明确分钟 | 周一中午 ET 开始检查；先核实批量 ZIP 是否同步更新 | [S10] |

上表中的“发布后 5 分钟”“中午检查”是工程配置，不是 USDA 对可用性的保证。报告上网、文件替换和 API 更新可能不同步；应验证内容与版本。

建立 `release_calendar` 表，至少包含：

```text
source, dataset, artifact_kind, event_id,
expected_release_date, expected_release_at_utc, source_timezone,
time_precision, calendar_url, checked_at_utc, status
```

`artifact_kind` 区分 report、api、historical_csv。`status` 区分 scheduled、available、delayed、cancelled、unknown。日历抓取失败时保留旧记录并标记过期，不能编造下一次发布日期。

**5. 各来源的下载实施方案**

**5.1 WASDE**

主要用途：整理各期报告的供需估计，支持分析产量、使用、贸易、期末库存及其修订。指标解释应按具体商品和表格编写。[S01][S02]

实施步骤：

1. 从官方主页面发现历史 CSV 与当期文件链接，保存原始页面、最终下载地址和文件哈希。
2. 用合并历史 CSV 建立历史主表，保留报告期、数据所属年度、表格标识和全部分组维度。
3. 增加当期 Excel/XML 解析器，实现发布当日获取；选择样本验证更稳定的格式作为主路径。
4. 次日历史 CSV 到达后与当期结果核对。保留差异和来源，不静默覆盖两个来源的不一致数值。
5. PDF 保存为参考原件；只有发现关键表没有结构化来源时，再为该表评估专用提取。

WASDE 历史文件保存报告发布时的值；PSD 历史序列可能包含后续修订，两者不能互相替换。[S02]

验收：选择近期、较早年份、年度切换三类报告；各抽查至少 10 个数据点。记录数、表清单和解析失败单元格均有报告。任何未覆盖表必须在覆盖清单说明，不能标记为“全报告完成”。

**5.2 Export Sales：FAS ESR API**

主要用途：分别跟踪销售合同、实际出口和未交付订单。净销售、当周出口、累计出口属于不同指标，不能用未交付订单直接代替最终出口预测。[S05][S13]

鉴权：使用实习生的 Nexus 公司邮箱，通过 FAS 官方入口申请 api.data.gov Key；本人完成邮箱验证。程序从环境变量 `USDA_FAS_API_KEY` 读取，不写入源码、日志或样例 CSV。[S03]

核心请求路径已经在官方 Swagger 中确认：[S04]

```text
Host: https://api.fas.usda.gov
Header: X-Api-Key: <从环境变量读取>

GET /api/esr/commodities
GET /api/esr/countries
GET /api/esr/unitsOfMeasure
GET /api/esr/datareleasedates
GET /api/esr/exports/commodityCode/{commodityCode}/allCountries/marketYear/{marketYear}
```

实施步骤：缓存字典 → 构建商品与营销年度任务 → 按任务下载所有目的地 → 保存原始 JSON → 标准化字段 → 校验并发布分区。

增量策略：商品的更新标记变化后，重新获取配置范围内该商品的所有营销年度。官方说明修订可能涉及多个年度，仅追加最新一周会漏数据。[S04] 后续如需优化，必须保留定期全范围核对与明确的修订延迟指标。

营销年度、报告周结束日、发布日期分开保存；商品年度起点根据官方定义配置，不统一假定为自然年。允许净销售为负值；其他负值按具体字段定义判断。

验收：至少 3 个商品、多个目的地、营销年度切换样例；抽查与官方查询结果一致；历史修订与取消销售不会被错误删除或置零。

**5.3 三份 FAS 月报：PSD 数值 + 报告原件**

按三份报告的业务范围建立配置：

| 视图 | 初始指标范围 | 解释重点 |
|---|---|---|
| `world-production` | 面积、产量、单产，按报告逐项匹配 | 供应变化来自面积还是单产变化 |
| `grain-trade` | 谷物的生产、供给、消费、贸易、库存 | 不同国家和营销年度的供需结构 |
| `oilseed-trade` | 油籽、油粕、植物油的生产、加工、消费、贸易、库存 | 区分原料、加工产品与不同单位 |

以上是项目拟覆盖指标，最终以 API 字典和报告表格核对结果为准，不能假定某个指标对所有商品都存在。

核心路径：[S04]

```text
GET /api/psd/commodities
GET /api/psd/countries
GET /api/psd/commodityAttributes
GET /api/psd/unitsOfMeasure
GET /api/psd/commodity/{commodityCode}/country/all/year/{marketYear}
GET /api/psd/commodity/{commodityCode}/world/year/{marketYear}
GET /api/psd/commodity/{commodityCode}/dataReleaseDates
```

实施步骤：

1. 获取字典，生成商品、地区、指标、单位映射；ESR 与 PSD 代码分别命名，不能假定相同。
2. 按“商品 × 营销年度”获取一次数据，三个报告视图共享缓存。
3. 世界、区域、国家记录区分聚合层级；不将区域汇总和其成员国家重复求和。
4. 每次来源变化保存当前快照；同步报告原件及目录。
5. 为三份报告建立 `report_coverage.csv`：报告日期、表名、指标、PSD 映射、匹配状态、差异原因。
6. PSD 无法对应的数值表，优先寻找官方可下载表格；必要时实现专用提取。只归档 PDF 不能宣称该数值表已经结构化。

PSD 提供的当前历史序列不能自动恢复过去每月的发布版本。首次回填标记为“当前修订序列”；后续运行积累本地快照。要求精确历史发布版本时，需要另建报告档案提取任务。[S02]

验收：三份报告各选至少 2 期，各抽查至少 10 个可映射数据点。因时间、单位、年度定义或修订产生的差异必须能解释；关键数值表未覆盖则该报告适配器不算完成。

**5.4 ERS Commodity Costs & Returns**

主要用途：比较生产成本构成与收益。应区分成本项、收益项、产量、价格，以及每英亩、每单位产品等口径。官方区分 Recent、Historical 与预测系列，历史方法和区域定义存在变化。[S08][S09]

实施步骤：

1. 从产品页面枚举下载文件，记录商品、子系列、格式、Last Updated、Next Update。
2. 优先解析 CSV，必要时使用 XLSX 对照；预测文件若只有 Excel，就使用对应解析器。
3. 将以年份展开的列整理成长表；若原文件已经是长表，直接按字段映射标准化。
4. 保留商品、企业类型、区域、年份、核算项目、单位、方法时期及数据状态。
5. Recent/Historical 重叠期分别保留，不因同一年同商品而直接去重。
6. 每次文件变化重处理完整文件，保留上个版本，输出新增、修改、删除记录的数量。

`series_family` 区分 recent、historical、forecast；`estimate_status` 另行区分 preliminary、final、unknown。不能把 recent 误当作“预测”，也不能仅凭今天的月份推断某行已经是最终值。

验收：覆盖主页面全部纳入范围的文件；抽查作物、畜牧、历史方法、预测和不同企业类型；单位及空值正确；只有在官方定义明确可加总时才检查总成本关系。

**5.5 RMA Summary of Business**

主要用途：观察保险参与、保费、保障责任和赔付情况。数量字段可能代表面积、重量或其他数量；必须结合 Quantity Type 解释。[S12]

实施步骤：

1. 从官方页面发现 State/County/Crop/Coverage Level 年度 ZIP 和对应 Record Layout。
2. 保存 ZIP、字段布局版本和哈希；按 `|` 分隔符及布局解析，不把文件当作逗号分隔 CSV。[S11]
3. 根据布局明确年份、州县代码、作物、保险计划、保障类别、交付类型和保障水平等维度。[S12]
4. 金额、数量、保单数分开处理；保留原始缺失标记和数量类型。
5. 先实现 1989 年以来布局；默认回填 2010 年以来，`--all-history` 扩到该布局可用起点。1948—1988 布局另列历史扩展，不与新布局直接拼接。[S11]
6. 常规更新刷新官方所述最近五年，并检测新出现的年度文件；更早年度低频检查。[S10]

官方网页的“周一更新”说明针对 SOB 产品。实施时必须确认 ZIP 的更新时间和内容变化；若批量文件延迟，记录实际延迟，不将网页刷新时间冒充文件发布时间。

验收：抽查近期、较早年度和不同保险计划；核对字段数与汇总口径；保留州县前导零；不把所有数量都改名为 acres。官方布局允许赔款金额带符号，因此不能设置一刀切的“所有数值必须非负”规则。[S12]

**6. DataFrame 与未来 SQL 表结构**

以下是设计字段，不是官方原字段。阶段 A 获取样本后，补齐逐字段映射、类型、可空性、单位、枚举和来源。字段缺失时不能凭空填充含义不确定的值。

**6.1 通用约定**

| 字段/约定 | 设计 |
|---|---|
| 命名 | 英文 `snake_case`；中文解释放入字段字典 |
| 代码 | 使用字符串；保留前导零及各来源命名空间 |
| 年度 | 分别使用 `marketing_year`、`calendar_year`、`commodity_year`，避免一个 `year` 混用 |
| 日期 | `YYYY-MM-DD`；精确时间为带 UTC 标记的 ISO 8601 |
| 数值 | 保留 `raw_value` 与可空数值列；金额精度依据源文件，小数不经不必要舍入 |
| 缺失 | 缺失与零分开；`value_status` 记录 unavailable、suppressed、not_applicable 等已确认含义 |
| 单位 | `unit_code`、`unit_label`，必要时附数量级；换算只产生新增列 |
| 来源 | `source`、`source_artifact_id`、`schema_version` |
| 版本 | `snapshot_id`、`content_hash`、`retrieved_at_utc` |
| 发布时间 | `source_release_date`、可空的 `source_release_at_utc`、`release_time_precision` |
| 来源版本属性 | `vintage_type` 区分 published_report、current_revised、captured_snapshot |

DataFrame 使用可空字符串、整数、数值及明确时间类型。未来 SQL 类型在 schema 中声明为 TEXT、INTEGER/BIGINT、NUMERIC/DOUBLE、DATE、TIMESTAMP 等逻辑类型，并补充目标数据库适配说明。CSV 本身不携带类型，因此必须配套 schema 文件和读取示例。

**6.2 业务表粒度与候选唯一键**

| 表 | 每行粒度 | 核心业务字段 | 候选唯一键，不含版本 |
|---|---|---|---|
| `wasde_observations` | 一期报告中一个完整分组下的指标 | 报告日期、表标识、商品、地区、年度、指标、分类、数值、单位、脚注 | 报告日期 + 表标识 + 商品 + 地区 + 年度 + 指标 + 全部分类维度 + 单位 |
| `esr_weekly_sales` | 一个报告周、商品、目的地、营销年度 | 周结束日、商品代码、国家代码、营销年度、单位、销售/出口各指标 | 商品 + 国家 + 营销年度 + 周结束日 + 单位，附样本中的其他真实分组字段 |
| `psd_observations` | 一个地区、商品、营销年度、指标 | 商品代码、地区代码、地区层级、营销年度、指标代码、数值、单位 | 商品 + 地区 + 地区层级 + 营销年度 + 指标 + 单位 |
| `ers_costs_returns` | 一个核算口径下的年度项目 | 商品、企业类型、区域、年份、系列、方法时期、核算项目、数值、单位 | 商品 + 企业类型 + 区域 + 年份 + 系列 + 方法时期 + 核算项目 + 单位 |
| `rma_sob` | 官方完整分组下的一条保险汇总 | 作物年度、州县、作物、保险计划、保障类别、交付类型、保障水平、数量类型、各项金额及数量 | 年度 + 州县 + 作物 + 保险计划 + 保障类别 + 交付类型 + 保障水平 + 数量类型，按布局校验 |

主键在样本确认后冻结。若候选键有冲突，优先寻找遗漏的业务维度；不能直接 `drop_duplicates()` 或用行号掩盖问题。归档表唯一键为“完整业务键 + snapshot_id”。可建立稳定的 `observation_key` 哈希，但必须保留组成哈希的原始维度。

ESR 拟标准化指标包括净销售、当周出口、累计出口、未交付销售及官方响应提供的相关指标；逐列意义由样本和官方说明验证。RMA 拟保留保单数、数量类型及净申报数量、责任金额、保费、补贴、赔款等字段，完整映射按布局实施。[S12][S13]

**6.3 辅助表**

- `source_artifacts`：下载地址、文件类型、文件哈希、原始路径、抓取时间、HTTP 元数据、官方日期及精度。
- `report_documents`：报告类型、报告日期、标题、附件地址、本地路径、哈希。
- `report_coverage`：报告表到数值字段的映射和覆盖状态。
- `download_runs`：任务、参数、开始结束时间、状态、行数、失败分区、版本。
- `coverage_manifest`：预期与实际商品/年度/地区分区，最早和最新日期、缺口及原因。
- `release_calendar`：见第 4 节。
- 商品、地区、指标、单位字典：按来源分别存储，跨来源对应关系另建映射。

**7. 模块与目录设计**

```text
usda-data/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── config/
│   ├── datasets.toml
│   ├── commodities.toml
│   └── report_mappings.toml
├── src/usda_data/
│   ├── __init__.py              # 导出公开函数
│   ├── __main__.py              # python -m usda_data
│   ├── api.py                   # 对外调用及参数验证
│   ├── cli.py                   # CLI 参数解析
│   ├── config.py
│   ├── http.py                  # 超时、限流、重试、脱敏
│   ├── storage.py               # 文件、CSV、原子发布
│   ├── state.py                 # 下载清单、断点与更新水位
│   ├── validation.py
│   ├── calendar.py
│   └── sources/
│       ├── wasde.py
│       ├── fas_esr.py
│       ├── fas_psd.py
│       ├── ers_costs_returns.py
│       ├── rma_sob.py
│       └── reports.py
├── schemas/                    # 字段、类型、键与空值规则
├── docs/                       # 来源、经济含义、发布时间、使用说明
├── test/fixtures/             # 小型官方样本和代表性异常样本
└── data/
    ├── raw/                    # 原始文件/响应，按来源与版本归档
    ├── normalized/             # 标准化分区及快照
    ├── exports/                # 面向使用者的 CSV
    ├── reports/                # 月报原件
    └── manifests/              # 覆盖、校验和运行记录
```

依赖方案：以 pandas 为 DataFrame 接口，选定一种 HTTP 客户端，CLI 优先使用标准库 `argparse`；按已验证格式引入 Excel/XML 解析依赖。阶段 A 固定经过验证的 Python 与依赖版本，提供安装说明，避免同时维护多套网络或 CLI 框架。

每个来源模块负责 `discover → fetch → parse → normalize → validate`。网络重试、日志、CSV 输出和版本管理由公共模块负责。CLI 只处理参数、调用公开函数和展示结果。

**8. Python 公开函数与 CLI 契约**

以下接口是拟实现契约，当前不能执行。

```python
from usda_data import (
    download_wasde,
    download_export_sales,
    download_psd,
    download_costs_returns,
    download_rma_sob,
    download_dataset,
    download_reports,
)

# 返回标准化 pandas.DataFrame；起止日期包含边界。
df = download_wasde(start="2020-01-01", end="2026-11-12")

# 商品名称由配置映射到 ESR 官方代码；market_years 不是发布日期。
esr = download_export_sales(
    commodities=["corn", "soybeans"],
    market_years=[2024, 2025, 2026],
    countries="all",
)

# 三份月报视图通过同一 PSD 数据层生成。
production = download_dataset(
    "world-production",
    market_years=[2024, 2025, 2026],
)

# 返回报告目录 DataFrame，附件保存到 output_dir。
reports = download_reports(
    "grain-trade", start="2026-01-01", end="2026-11-12",
    output_dir="data/reports",
)

df.to_csv("data/exports/wasde.csv", index=False, encoding="utf-8")
```

每个公开函数文档必须包含参数类型、时间范围含义、返回字段、鉴权方式、缓存与落盘行为、异常类型以及最小示例。默认使用共享本地缓存并归档原始响应，返回标准化 DataFrame；通过配置控制根目录。大范围任务按分区处理，另提供迭代接口，CLI 不要求把全部历史加载进一个 DataFrame。

设计的 CLI：

```bash
# 查看帮助与来源配置
usda-data --help
usda-data list-datasets
usda-data calendar --dataset wasde

# 查看计划下载范围，不抓取全部数值数据
usda-data fetch --dataset all --config config/datasets.toml --dry-run

# 按报告发布日期获取 WASDE
usda-data fetch --dataset wasde --start 2020-01-01 --end 2026-11-12 --output-dir data/exports

# 按营销年度获取 ESR
usda-data fetch --dataset export-sales --commodities corn,soybeans --market-years 2024,2025,2026 --output-dir data/exports

# 从 PSD 获取月报视图，同时归档该时间段的报告附件
usda-data fetch --dataset grain-trade --market-years 2024,2025,2026 --with-reports --report-start 2026-01-01 --report-end 2026-11-12

# 按观测年份获取 ERS，按作物年度获取 RMA
usda-data fetch --dataset costs-returns --years 2020:2026
usda-data fetch --dataset rma-sob --commodity-years 2020:2026

# 按配置处理全部来源；支持失败分区恢复
usda-data fetch --dataset all --config config/datasets.toml --resume
usda-data sync --dataset all --config config/datasets.toml
usda-data validate --input-dir data/normalized
```

参数语义：年份区间包含两端；`--start/--end` 仅用于定义明确的发布日期范围，不能在不同来源里悄悄改为营销年度。`--dataset all` 用配置分别定义各来源范围。未实现或不适用的参数必须报错。`--all-history` 扩展覆盖范围，`--force` 允许重新请求但不删除原始归档。

CLI 与 Python 调用必须使用同一数据流程。退出码约定：`0` 全部成功或明确无更新，`1` 至少一个任务失败，`2` 参数/配置错误。运行摘要列出 succeeded、unchanged、not_yet_available、failed，不能用空 CSV 掩盖鉴权失败。

**9. 原始归档、更新、修订和断点续传**

采用三层数据：

```text
raw：官方原始文件/JSON → normalized：带版本的标准化数据 → exports：最新完整分区的 CSV
```

1. 首次回填先生成任务清单，每个商品/年度/文件一个可恢复任务，记录 expected、downloaded、validated、published 状态。
2. 原始文件保存 SHA-256、来源和时间。相同内容可以复用文件，但每次检查记录独立保留。
3. 下载成功后写临时文件；格式、字段和分区校验通过后，才原子发布并更新水位。
4. 每个变化分区保存完整新快照。最新视图整体替换该分区，避免仅 upsert 导致已被来源删除的行残留。
5. 新旧分区比较并统计新增、变更、删除；历史快照不覆盖。
6. 若部分分区失败，成功分区可保留，整次任务标记 partial 并返回非零退出码；完整导出版本只在覆盖检查通过后发布。
7. `--resume` 只续做失败或未完成任务。重新运行同一内容不会制造重复业务记录。
8. 对 ESR/PSD 的跨年修订，本期优先完整刷新变化商品的已配置历史年度；通过限流和断点任务控制成本。
9. 更新端点、ETag、Last-Modified 作为提示，内容哈希与业务检查作为最终证据；文件地址不变不等于内容未变。

`as_of` 只允许基于真实的发布档案或已捕获快照进行查询。抓取时间晚于报告日期时，二者分别保存；从当前接口回填的历史数据不能伪称为历史时点可得。

**10. 错误处理与运行日志**

- 网络超时、临时 5xx 和 429 使用有限次数指数退避；遵守 `Retry-After`。初始并发采用保守配置，再依据实际限流调整。
- 401/403 单独报告鉴权或访问问题；不进行无限重试，不将 HTML 错误页交给表格解析器。
- 未找到文件时区分“尚未发布”“链接变化”“该年确实无数据”。不能把所有 404 视为合法空数据。
- 校验响应状态、内容类型、文件签名、JSON/ZIP 可解析性；ZIP 成员数量、解压大小及路径受控。
- 字段变化或未知布局停止相关分区发布，保留原始响应，输出差异清单。
- 日志记录来源、任务参数、耗时、行数、版本、重试次数、错误类别；过滤 API Key 和鉴权头。
- 每次运行生成机器可读 JSON 摘要及便于阅读的简短摘要。

**11. 验证方案与质量门槛**

测试围绕会造成漏数、错数或不可恢复状态的风险，不为简单文件包装重复编写测试。

| 验证类别 | 具体检查 | 通过标准 |
|---|---|---|
| 官方抽查 | 按来源抽样比较值、单位、年度和地区 | 与同一版本官方数值一致；差异有可验证解释 |
| 主键 | 同一快照完整业务键唯一 | 0 个无法解释的重复 |
| 字典 | 商品、地区、指标代码有映射 | 未识别值进入明确异常清单，不能静默丢弃 |
| 覆盖 | 商品/年度/报告表与计划清单对比 | 必需分区全部成功，真实无数据有证据 |
| 空值 | 0、空白、抑制值、无适用项分别处理 | 不把缺失自动填为 0 |
| 单位 | 各来源单位与数量级保留 | 无跨单位直接求和或比较 |
| 修订 | 用新旧样本模拟改值、删行 | 最新分区正确，历史仍可追溯 |
| 中断恢复 | 下载或写出阶段失败后重跑 | 不发布半个文件，不重复记录 |
| 日期 | 夏令时、年末、营销年度切换 | 发布时间与数据时期不混淆 |
| CSV 往返 | 按 schema 导出、读回 | 前导零、数值精度、日期、空值符合约定 |
| SQL 可用性 | 用本地临时数据库验证典型表和键约束 | 无嵌套对象、无类型冲突；不连接生产库 |
| CLI/函数一致 | 同一配置使用两个入口 | 排序标准化后数据一致 |

若测试涉及供需平衡关系，只对文档明确适用的同一地区、年度、单位与分类执行；残差项、四舍五入和贸易年度差异必须考虑。RMA 保单数不能未经验证跨重叠保障层级直接相加。

**12. 分阶段工作安排**

以下为单人开发的估计，不包含等待邮箱验证、官方故障或大规模历史 PDF 提取。样本验证后更新工期。每阶段完成均应有可运行或可检查的产物。

| 阶段 | 工作内容 | 产物与退出条件 | 预计有效工作日 |
|---|---|---|---|
| A：来源与样本 | 获取各源样本、核实范围、申请 Key、建立字段映射与发布规则 | 每个来源有原始样本；未解决问题和覆盖边界明确 | 1–2 |
| B：基础与 WASDE | 项目结构、HTTP/存储/状态、历史 CSV、当期文件、公开函数/CLI | WASDE 完成一次端到端回填及重复运行验证 | 2–3 |
| C：ERS | 文件发现、系列分类、长表、单位与历史口径 | 所选 ERS 文件可统一导出，口径不混合 | 1–2 |
| D：ESR | 鉴权、字典、年度任务、周数据和修订 | 真实请求通过；历史更新、跨年、负销售样本验证 | 1–2 |
| E：PSD 与月报 | 共用 PSD 下载、三份视图、报告归档、覆盖核对 | 三份报告各有数值输出、原件与覆盖清单 | 2–3 |
| F：RMA | 年度 ZIP、布局、数量/金额/完整维度 | 多年度下载与校验通过，周更新策略明确 | 1–2 |
| G：回填与交付 | 全范围任务、断点恢复、CSV/SQL 校验、文档和演示 | 所有验收项完成，缺口有明确状态 | 2–3 |

合计约 **10–17 个有效工作日**。如果报告存在较多 PSD 无法覆盖的关键表格，额外提取工作单独估算，不能通过省略这些表格来宣称已经完成。

依赖安排：A 完成样本确认后进入 B；Key 尚未收到时继续 B、C、F；D/E 的真实 API 验证依赖有效 Key；G 依赖全部来源模块完成。开发过程先用小样本通过验证，再扩大历史范围。

**13. 最终交付清单**

- [ ] 可安装的 Python 包与依赖配置。
- [ ] 5 类数值下载器、共用月报归档模块、7 个数据集入口。
- [ ] 所有数据集具备 Python 调用和 CLI 调用方式。
- [ ] 默认历史范围的完整 DataFrame/CSV 输出及覆盖清单。
- [ ] 原始文件、原始响应和报告附件归档。
- [ ] 每个表的字段说明、类型、单位、空值规则和唯一键。
- [ ] 各数据经济含义、时间口径、修订与历史版本说明。
- [ ] 官方发布规则、日历来源、时区和调度使用说明。
- [ ] 脱敏的配置模板、API Key 配置说明。
- [ ] 首次回填、增量更新、断点恢复和异常处理说明。
- [ ] 官方抽查结果、关键测试结果、CSV 往返及本地入库验证。
- [ ] README：从安装到下载一个样例的完整步骤。
- [ ] 示例 Notebook 或短 Python 示例，展示导入函数得到 DataFrame。
- [ ] 三份 FAS 月报的表格覆盖清单，未覆盖项及原因透明可见。
- [ ] 已知限制清单，不把未验证、失败或部分完成写成完成。

**14. 开始开发前的默认值与需要补充的信息**

| 项目 | 当前默认值 | 何时需要补充 |
|---|---|---|
| Nexus 邮箱与 Key | 不虚构账号；由实习生用公司邮箱申请 | ESR/PSD 真实鉴权联调前 |
| 历史跨度 | 2010 年起；支持扩展 | 导师有更长历史要求时修改配置 |
| 商品/地区范围 | 纳入来源全部支持项；先用 3 个商品联调 | 有明确业务限制时缩小配置 |
| 历史版本 | WASDE 发布档案 + 其他来源当前历史值及后续快照 | 要求完整历史时点回测时另评估档案提取 |
| 更新及时性 | 支持按发布检查；不承诺秒级 | 导师指定延迟指标时调整调度与监控 |
| RMA 产品 | State/County/Crop/Coverage Level SOB | 需要损失原因或受阻播种时另加数据源 |
| SQL 目标 | 输出类型明确的 CSV/schema，做本地验证 | 生产接入前确认 PostgreSQL/MySQL 等目标 |

首先实施阶段 A 和 B：建立来源清单、取得样本、确定字段映射，再用 WASDE 跑通一条完整数据链路。

**15. 官方资料与引用索引**

访问核对日期：2026-11-12。正文 `[Sxx]` 对应以下来源。URL 使用代码格式保存，方便复制，也使 Markdown 文件脱离聊天界面后仍能追溯。

- [S01] USDA：WASDE 主页面，发布日期、当期格式、历史 CSV 更新安排。官方页面本次可通过官方分发域名读取。  
  `https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report`  
  `https://usda.azureedge.us/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report`
- [S02] USDA NASS 2021 Spring Data Users’ Meeting：说明 WASDE 发布历史与 PSD 修订历史的区别。本次从官方文档的搜索索引读取说明，原 PDF 直接访问返回 404；实施时需从官方历史数据页面重新发现可用链接。  
  `https://www.nass.usda.gov/Education_and_Outreach/Meeting/2021/2021-spring-questionandanswer.pdf`
- [S03] FAS Open Data 门户：API Key 注册和访问说明。  
  `https://apps.fas.usda.gov/opendataweb/home`
- [S04] FAS 官方 Swagger：ESR/PSD 路径、参数、更新端点及 `X-Api-Key` 定义。接口文档没有完整列出响应字段，字段契约须通过样本确认。  
  `https://apps.fas.usda.gov/opendatawebv2/assets/swagger/swagger.json`
- [S05] FAS Export Sales Reporting Program：周报安排和报告定义。  
  `https://fas-prod.azureedge.us/programs/export-sales-reporting-program`
- [S06] FAS 报告发布日历与 World Agricultural Production 发布页：三份月报的 12:15 ET 安排。  
  `https://fas.usda.gov/`  
  `https://fas-prod.azureedge.us/report-release-announcement/world-agricultural-production-71`
- [S07] FAS World Agricultural Production 报告说明：相关 PSD 12:00 更新、月报 12:15 发布。以下是动态报告链接，实施时应保存实际获取的版本及哈希。  
  `https://apps.fas.usda.gov/psdonline/circulars/production.pdf`
- [S08] ERS Commodity Costs and Returns 产品页：文件、系列、Last Updated 与 Next Update。  
  `https://www.ers.usda.gov/data-products/commodity-costs-and-returns`
- [S09] ERS Commodity Costs and Returns Documentation：更新规律、估计口径及历史方法。  
  `https://www.ers.usda.gov/data-products/commodity-costs-and-returns/documentation`
- [S10] RMA Summary of Business：最近五年周一上午更新的说明。  
  `https://www.rma.usda.gov/summary-business`
- [S11] RMA State/County/Crop Summary of Business：年度 ZIP、分隔格式和布局下载。  
  `https://www.rma.usda.gov/tools-reports/summary-of-business/state-county-crop-summary-business`
- [S12] RMA Crop Insurance Experience with Coverage Level，1989 Forward Record Layout，版本日期 2026-05-28。  
  `https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/state_county_crop/SOB_State_County_Crop_with_Coverage_Level_1989_Forward.pdf`
- [S13] FAS Export Sales Query System 用户手册：报告定义、查询方式和营销年度切换。  
  `https://apps.fas.usda.gov/esrqs/assets/ESRQS_UserManual_PublicUser.pdf`
