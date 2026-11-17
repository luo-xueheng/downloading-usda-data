# downloading-usda-data

下载、处理并导出七类 USDA 数据：WASDE、出口销售、世界农业生产、谷物贸易、油籽贸易、成本收益和 RMA 保险业务。支持 Python DataFrame、流式 CSV、缓存、版本记录和失败恢复。

## 安装与凭证

需要 Python 3.11+ 和 macOS/Linux。运行锁使用 `fcntl`。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
.venv/bin/python -m usda_data list-datasets
```

开发时使用 `.venv/bin/python -m pip install -e '.[dev]'`。出口销售及三个报告数据集使用 FAS API；参照 [.env.example](.env.example) 在本地 `.env` 中设置 `USDA_FAS_API_KEY`，或使用同名环境变量。详见[凭证配置](docs/credential_setup.md)。

## 下载数据

以下命令下载一期完整 WASDE 数据：

```bash
.venv/bin/python -m usda_data fetch --dataset wasde --start 2026-11-10 --end 2026-11-10 --data-dir data --output-dir data/exports
```

最终文件位置由 `data/exports/wasde.latest.json` 指定。CSV 保留字段编码、空值、精确小数、来源和快照信息。

```python
import json
from pathlib import Path
from usda_data.schema import Schema

root = Path("data/exports")
selected = json.loads((root / "wasde.latest.json").read_text())
schema = Schema.load(root / selected["schema_path"])
for chunk in schema.read_csv_chunks(root / selected["csv_path"], chunk_size=1000):
    print(chunk.head())
    break
```

[七个数据集示例](examples/README.md)提供每个数据集的一条示例生成命令、一份 200 行 CSV 节选，以及对应的完整下载命令。示例通过固定官方素材离线重放生成，并非此次联网下载。

| 数据集 ID | 数据说明 | CSV 示例 |
|---|---|---|
| `wasde` | [WASDE](docs/wasde.md) | [wasde.csv](examples/wasde.csv) |
| `export-sales` | [出口销售](docs/export_sales.md) | [export-sales.csv](examples/export-sales.csv) |
| `world-production` | [世界农业生产](docs/world_production.md) | [world-production.csv](examples/world-production.csv) |
| `grain-trade` | [谷物贸易](docs/grain_trade.md) | [grain-trade.csv](examples/grain-trade.csv) |
| `oilseed-trade` | [油籽贸易](docs/oilseed_trade.md) | [oilseed-trade.csv](examples/oilseed-trade.csv) |
| `costs-returns` | [成本收益](docs/costs_returns.md) | [costs-returns.csv](examples/costs-returns.csv) |
| `rma-sob` | [RMA](docs/rma_sob.md) | [rma-sob.csv](examples/rma-sob.csv) |

各列含义见[字段字典](docs/field_dictionary.md)，完整参数和 Python API 见[接口说明](docs/interfaces.md)。`psd` 作为辅助接口单独提供，三个报告数据集已包含对应的 PSD 数据及原始报告表格。

## 批量下载、更新及导出

```bash
.venv/bin/python -m usda_data fetch --dataset all --config config/small_sync.json --dry-run
.venv/bin/python -m usda_data sync --config config/small_sync.json
.venv/bin/python scripts/aggregate_exports.py --input-dir data/exports
.venv/bin/python -m usda_data validate --input-dir data/exports/datasets
```

小配置只演示指定范围。历史全量配置 `config/full_backfill.json` 冻结于 2026-11-16，不自动代表今天的全部数据。新范围的任务发现、下载和聚合流程见[批量下载](docs/backfill.md)。更新策略与恢复方法见[更新与恢复](docs/updates_and_recovery.md)，数据库导入见 [SQL 转换](docs/sql_transfer.md)。

## 测试

```bash
.venv/bin/python -m pytest
```

默认运行离线功能、数据集和回归测试。测试输入统一在 `test/fixtures/`，测试输出写入系统临时目录，不需要旧的 `data/` 或验收日志。联网、性能、历史验收及七接口重放的单独运行方式见 [test/README.md](test/README.md)。

## 仓库结构

- `src/usda_data/`：下载、解析、存储、同步、CSV／SQL 处理和必要元数据。
- `scripts/`：通用采集、任务规划、聚合、示例生成及 SQL 工具。
- `config/`：运行配置与 Schema 迁移规则。
- `schemas/`：当前接口及聚合输出字段定义。
- `test/`：测试代码、测试工具、独立参考值和固定源素材。
- `examples/`：每个主数据集一份 CSV 节选、命令和来源索引。
- `docs/`：使用说明、字段字典、来源限制和保留的历史文档。

`data/` 是运行时生成的本地缓存和输出，不提交 Git。2026-11-17 整理前的完整数据和验收记录已迁至仓库旁的归档目录；[迁移说明](docs/repository_cleanup.md)记录位置、恢复方法及文件映射。全部既有 Markdown 文档均已保留；原始 README 见[历史版本](docs/history/README.before-cleanup.md)。
