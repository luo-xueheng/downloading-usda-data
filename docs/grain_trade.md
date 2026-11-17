# Grain: World Markets and Trade

> 中文阅读入口：**[数据含义、逐列解释和真实示例](fields/grain_trade.md)**。下面保留原有英文技术说明。


See reports.md for shared interfaces and source/version semantics. The tested
appendix contains 25 numerical supply/trade table families. Body trade-change tables
are also required, including older-year changes when present. Nine PSD grain codes
include Millet and Mixed Grain as reported coarse-grain components.

Source table captions retain local marketing year versus trade year: wheat trade
uses July/June, rice trade January/December, and coarse-grain trade October/September.
A year label is not silently converted across these bases. Regional import tables
use trade-year imports while their other indicators use local marketing years.
The all-grain summary's unadjusted consumption differs from adjusted global totals;
its original source meaning is preserved, not reconciled through an invalid identity.

Report trade tables retain original regional groupings, Others, Subtotal and World
Total. These overlap; do not add aggregates to component countries. Changes retain
Previous, Current and Change fields and source commodity/country merged-cell labels.
Negative changes are valid. All source values remain in their displayed million or
thousand metric tons, with complete caption/footnote metadata.
