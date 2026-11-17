# 批量下载与聚合

`config/full_backfill.json` 保存 2026-11-16 截止的 805 个任务，适合重放该范围。`config/small_sync.json` 是七数据集的小范围使用示例。原有全量交付说明及内存预算记录完整保存在 [历史版本](history/backfill.before-cleanup.md)。

## 运行已有配置

```bash
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --dry-run
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json
```

失败后在相同数据目录恢复：

```bash
.venv/bin/python -m usda_data fetch --dataset all --config config/full_backfill.json --resume
```

更新已配置的范围：

```bash
.venv/bin/python -m usda_data sync --config config/full_backfill.json
```

这些命令在 `data/` 保存源文件、标准化快照及任务恢复状态。不要在仍需恢复同一次下载时移除它们。

## 发现新的下载范围

任务规划会联网读取当前官方目录和 FAS 元数据，需要 API Key。它保存发现时的截止时间，不将现在的目录伪装为过去的发布状态。

```bash
.venv/bin/python scripts/plan_backfill.py --start-year 2010 --data-dir data --config-output data/plans/download.json --evidence-dir data/plans/evidence
.venv/bin/python -m usda_data fetch --dataset all --config data/plans/download.json --dry-run
.venv/bin/python -m usda_data fetch --dataset all --config data/plans/download.json
```

`--start-year` 控制起始范围；实际支持范围仍取决于数据源和解析器。报告目录缺项记录在规划证据中，缺少目录条目不等于已经证明该报告从未发布。

## 聚合七个最终 CSV

成功的多任务运行先生成 `data/exports/complete.latest.json`。聚合工具检查完整状态、七数据集覆盖、输入哈希、表头及 Schema 一致性，再发布聚合指针：

```bash
.venv/bin/python scripts/aggregate_exports.py --input-dir data/exports --output-dir data/exports/datasets
.venv/bin/python -m usda_data validate --input-dir data/exports/datasets
```

聚合过程支持 `config/schema_migrations.json` 中明确列出的 RMA 描述迁移；不转换业务数值。它不再依赖旧的阶段验收日志。运行完成和 CSV 校验通过并不替代独立源数值审计，也不自动延长解析器对新历史版式的支持。

## 历史数据与证据

整理前的完整数据位于仓库旁 `downloading-usda-data-archive-20261117/original/data/`，历史验收证据位于同一归档的 `original/artifacts/`。这些目录不参与默认离线测试，且不会随新 Git 克隆自动附带。详见[迁移说明](repository_cleanup.md)。
