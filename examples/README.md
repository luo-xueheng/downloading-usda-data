# 七个数据集的 CSV 示例

每个数据集仅保留一份最终处理后的 CSV，每份 200 行。它们是命令完整输出的节选，不代表全部下载结果。所有列、类型、空值和数值精度均保持原输出约定。

这些示例通过 `test/tools/verify_examples.py` 从固定的官方测试素材离线重放生成，并验证了 Python 与 CLI 的完整输出一致。本次没有重新联网获取源数据；抓取时间、快照 ID 和以后修订的数值可能与重新下载不同。

| 数据集 | CSV | 示例行数 / 本次完整请求行数 | 字段定义 |
|---|---|---:|---|
| WASDE | [wasde.csv](wasde.csv) | 200 / 5,054 | [wasde_observations.v2.json](../schemas/wasde_observations.v2.json) |
| 成本收益 | [costs-returns.csv](costs-returns.csv) | 200 / 257 | [ers_costs_returns.v1.json](../schemas/ers_costs_returns.v1.json) |
| 出口销售 | [export-sales.csv](export-sales.csv) | 200 / 553 | [esr_weekly_sales.v1.json](../schemas/esr_weekly_sales.v1.json) |
| RMA 保险业务 | [rma-sob.csv](rma-sob.csv) | 200 / 155,676 | [rma_sob.v2.json](../schemas/rma_sob.v2.json) |
| 世界农业生产 | [world-production.csv](world-production.csv) | 200 / 7,967 | [fas_dataset_observations.v1.json](../schemas/fas_dataset_observations.v1.json) |
| 谷物贸易 | [grain-trade.csv](grain-trade.csv) | 200 / 8,643 | [fas_dataset_observations.v1.json](../schemas/fas_dataset_observations.v1.json) |
| 油籽贸易 | [oilseed-trade.csv](oilseed-trade.csv) | 200 / 9,947 | [fas_dataset_observations.v1.json](../schemas/fas_dataset_observations.v1.json) |

字段中文阅读入口：[字段字典](../docs/field_dictionary.md)。各数据集的单位、年份、汇总边界及来源限制见 [README](../README.md) 中的对应说明。

## 一条命令生成一个示例

从仓库根目录运行，先完成 README 中的安装。出口销售及三个报告数据集需要 FAS API Key；通过环境变量或本地 `.env` 配置。以下命令先完成指定范围的下载和校验，再保存节选。原始文件和标准化缓存保存在 `data/`，临时完整导出自动清理，目标 CSV 只在请求成功后写入，同时更新同目录 `manifest.json` 中该数据集的记录。

### WASDE：`wasde`

```bash
.venv/bin/python scripts/download_example.py --dataset wasde --start 2026-11-10 --end 2026-11-10 --rows 200 --example-output examples/wasde.csv --data-dir data
```

### 成本收益：`costs-returns`

```bash
.venv/bin/python scripts/download_example.py --dataset costs-returns --years 2025 --commodities Corn --rows 200 --example-output examples/costs-returns.csv --data-dir data
```

### 出口销售：`export-sales`

```bash
.venv/bin/python scripts/download_example.py --dataset export-sales --commodities 701 --market-years 2026 --rows 200 --example-output examples/export-sales.csv --data-dir data
```

### RMA 保险业务：`rma-sob`

```bash
.venv/bin/python scripts/download_example.py --dataset rma-sob --commodity-years 2025 --rows 200 --example-output examples/rma-sob.csv --data-dir data
```

### 世界农业生产：`world-production`

```bash
.venv/bin/python scripts/download_example.py --dataset world-production --market-years 2025 --commodities 0440000 --report-start 2026-11-01 --report-end 2026-11-30 --rows 200 --example-output examples/world-production.csv --data-dir data
```

### 谷物贸易：`grain-trade`

```bash
.venv/bin/python scripts/download_example.py --dataset grain-trade --market-years 2025 --commodities 0440000 --report-start 2026-11-01 --report-end 2026-11-30 --rows 200 --example-output examples/grain-trade.csv --data-dir data
```

### 油籽贸易：`oilseed-trade`

```bash
.venv/bin/python scripts/download_example.py --dataset oilseed-trade --market-years 2025 --commodities 2222000 --report-start 2026-11-01 --report-end 2026-11-30 --rows 200 --example-output examples/oilseed-trade.csv --data-dir data
```

## 节选规则与完整数据

- WASDE、出口销售、成本收益、RMA：按完整输出顺序取前 200 行。
- 三个报告数据集：取前 100 行 `psd_current` 和前 100 行 `report_table`，同时展示 API 数据与原始 PDF 表格；某类不足 100 行时保留实际行数。
- `--rows` 可以调整节选上限；这是示例生成器的选项，不是下载 CLI 的记录数限制。
- 报告命令中的商品／国家筛选只限制 PSD 部分；指定报告月份的表格仍完整解析。
- 下载完整 CSV 请使用下面的直接 CLI 形式，或使用 `manifest.json` 中每项的 `fetch_command`。

```bash
.venv/bin/python -m usda_data fetch --dataset wasde --start 2026-11-10 --end 2026-11-10 --data-dir data --output-dir data/exports
```

CLI 输出目录中 `<dataset>.latest.json` 的 `csv_path` 指向最终 CSV，`schema_path` 指向其字段定义。文件名通常是 `<dataset>/<hash>/data.csv`。

`manifest.json` 保存命令、参数、实际行数、完整输出及节选的 SHA-256、Schema 和来源快照 ID。不要将 CSV 用电子表格软件自动转换后覆盖：代码中的前导零、精确小数和 `\N` 空值表示需要保留。

RMA 直接下载当前使用 Schema v2；全量聚合工具可将已授权的历史描述升级到 v3。两版业务字段、类型和 CSV 值一致；字段字典中的 v3 同样解释此示例。
