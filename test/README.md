# 测试运行与素材

所有测试代码、测试工具及固定输入统一在本目录。开发依赖安装后，从仓库根目录运行：

```bash
.venv/bin/python -m pytest
```

默认排除 `live` 和 `historical`，运行基础模块、数据集、同步、接口和历史版式回归测试。离线测试禁止真实 socket 连接，输出使用 pytest 临时目录，不依赖仓库旁的历史归档或完整下载数据。

## 目录

| 目录 | 用途 |
|---|---|
| `unit/` | HTTP、存储、安全、字段精度和独立证据验证器 |
| `datasets/` | WASDE、ERS、ESR、PSD、报告和 RMA；包含显式标记的联网用例 |
| `integration/` | 同步、CLI、SQL、示例数据及聚合发布 |
| `regression/` | 已发现的历史 PDF 版式、缺失公告和并发恢复问题 |
| `live/` | 历史来源目录与替代附件的真实请求验证 |
| `historical/` | 对旧的完整交付记录进行复查；不作为当前默认回归测试 |
| `performance/` | 大请求的内存检查及定位脚本 |
| `tools/` | 获取测试素材、验证七接口一致性、验证初始独立证据 |
| `fixtures/` | 官方固定源字节、下载回执、独立参考值和测试专用配置 |

`fixtures/phase_*` 保留原来的素材分组，避免重选或混淆独立参考值与开发样本。每个数据集一个 CSV 的规则适用于 `examples/`，不限制测试对历史格式和异常情况的素材覆盖。

## 联网验证

```bash
.venv/bin/python -m pytest -m live
```

FAS 用例需要 `USDA_FAS_API_KEY`。真实来源可能发生修订或暂时不可用；失败或跳过不算通过。本次仓库整理未重新运行联网验证。

## 七个接口的完整输出一致性

```bash
.venv/bin/python test/tools/verify_examples.py --output-dir .cache/interface-check
```

使用固定的官方素材建立独立缓存，在禁止联网的条件下比较每个数据集的 Python 与 CLI 完整输出。会生成较大的临时缓存和完整导出，位于忽略的 `.cache/`；这与提交的 200 行示例不同。请使用新的输出目录重新验证，以免复用旧工具生成的缓存。

## 历史交付复查

```bash
USDA_ARCHIVE_ROOT="../downloading-usda-data-archive-20261117/original" .venv/bin/python -m pytest test/historical -m historical
```

这些用例读取外部归档中的完整数据、原始代码快照及当时的验收记录。归档没有随 Git 克隆提供，需要自行保留或迁回。部分旧测试引用的 `artifacts/acceptance/phase-10/examples/`、`artifacts/acceptance/phase-05/sample/exports/` 在整理前已经缺失，因此旧交付复查不能保证全部通过；整理没有伪造或补写历史通过记录。

## 性能检查

```bash
.venv/bin/python test/performance/verify_full_export_memory.py --data-dir /path/to/full-data --output .cache/performance/full_export_memory.json
.venv/bin/python test/performance/profile_report_memory.py --data-dir /path/to/full-data --config config/full_backfill.json --task world-production-full
```

这两项会重放大规模请求，需要完整源缓存和对应任务状态，且可能更新缓存状态；建议对工作副本运行。本次整理没有重跑完整历史性能测试。
