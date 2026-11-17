# World Agricultural Production

> Reading guide: **[Data meaning, column-by-column explanations, and actual examples](fields/world_production.md)**. The original English technical documentation is retained below.


See reports.md for shared interfaces, exact source keys and revision policy.
The production report includes 18 numbered table families in the tested layout:
world crop production; area, yield and production by crop; copra/palm-kernel/palm-oil
production; cotton; and production-projection reliability. PSD scope includes all
18 verified report-relevant commodity codes, with shared grain/oilseed overlap.

Report extraction retains prior-month/current-month projections, year-over-year
and month-over-month absolute/percentage changes, regional totals, seasonal crop
subclasses such as Russian winter/spring wheat, and reliability statistics. These
are original report values, not fabricated from today's PSD. Regional headings
without numeric observations are grouping labels. Original report footnotes remain
attached through table metadata.

Area uses million hectares; crop yield uses metric tons per hectare, except cotton's
kilograms per hectare. Cotton production/absolute changes use million 480-lb bales;
other production tables use million metric tons. Reliability columns distinguish
percent errors, quantity differences and integer years above/below final. Rice yield
is rough-basis while displayed production is milled-basis: do not multiply them as
if they represented one homogeneous unit. World and Total Foreign overlap with
countries and must not be summed into another world total.
