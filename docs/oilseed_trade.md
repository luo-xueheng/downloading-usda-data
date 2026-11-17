# Oilseeds: World Markets and Trade

> Reading guide: **[Data meaning, column-by-column explanations, and actual examples](fields/oilseed_trade.md)**. The original English technical documentation is retained below.


See reports.md for shared interfaces and precision/vintage policy. All 28 numbered
table families and body outlook-change tables are required in the tested layout.
The PSD union covers 27 oilseed, meal and oil codes, including local soybean/meal/oil
variants for source local marketing-year tables.

Production, crush, imports, exports, stocks, industrial/food use, domestic consumption
and soybean-meal equivalents remain distinct. Oilseed, protein-meal and vegetable-oil
sections can repeat indicator names; section product type prevents collapsing their
Totals/Others rows. Local marketing-year notes remain attached, including Brazil's
Jan-Dec and Argentina's Apr-Mar labeling conventions. Report labels stay as printed.

Historical rows retain period labels and actual commodity/aggregate sections. Area
columns use million/thousand hectares at the table scale even when the caption gives
metric tons for quantity columns; area is not a weight observation. Original unit
captions remain in metadata. `nr` is unavailable/not reported, not zero. SME is a
44-percent-protein soybean-meal equivalent, not the original mass of every meal.
Source rounding means displayed components need not add to a displayed total.

Some source country rows are printed twice with identical business dimensions and
values. Their occurrence counts and all source locations are preserved; conflicting
repeats would block extraction. Report-vintage values and current PSD values remain
separate rather than overwriting one another.
