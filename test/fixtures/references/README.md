# Independent reference observations

`observations.json` contains 38 expectations manually read from official raw source material on 2026-11-12. Each expectation identifies the source URL and SHA-256, vintage or explicit unknown vintage, exact business dimensions, locator, value, unit, and reading method. Values were transcribed before running the verifier. No production source adapter exists.

- WASDE: three sr08 World/Total Grains/2024-25 XML cells for each of November and October 2026; two additional Mexico sugar cells from the November CSV.
- ERS: the first three numeric records in the corn and soybean files, including every identifying source column. These files were listed as updated 2026-10-01; observation year is 2025.
- RMA: three fields of the first raw pipe-delimited record in each of the 2025 and 2010 ZIPs. All 13 grouping fields, zero/leading-zero values and source quantity type are recorded. Unit meaning comes from the saved official 28-field layout. HTTP Last-Modified is transport metadata, not a proven release timestamp.
- World Agricultural Production: page 1 production, yield and harvested-area statements for Argentina wheat (November) and Indonesia palm oil (October).
- Grain: World Markets and Trade: wheat production for Australia, Ukraine and Argentina, last displayed 2026/27 column, pages 18 and 20 respectively.
- Oilseeds: World Markets and Trade: soybean, rapeseed and cottonseed world production, last displayed 2026/27 column, page 10 in each report.

The PDF `pages/` PNGs were rendered with `pdftoppm` and visually read. Their companion text files were extracted with `pypdf` independently of this repository's verifier and are pinned by hash. Earlier columns can merge or be reordered in generic extraction; no correctness is claimed for those columns. The chosen final columns were visually aligned. The verifier checks the frozen page evidence, exact selected text cells and independently authored expectations; it does not parse PDF binary content with a production extractor.

All comparisons use exact Decimal equality, tolerance zero, selected before tests. Thousands separators alone are removed for numeric comparison; string codes and dimensions remain exact after documented source-padding trimming. There are no PSD API/report comparisons and no synthetic observations counted as official references.

Development and holdout acquisition was completed before source adapter implementation. Phase 00 evidence validation is not the first adapter test: dependent phases must run the held-out artifact through their new adapter once, preserve that first result, and investigate failures without weakening expected values. Phase 00's small reference set does not replace the larger cell counts required by later phases.
