# Phase 05 acceptance report

Phase: 05 — Shared PSD data layer  
Status: **passed**  
Completed UTC: 2026-11-15T14:26:03.297145+00:00  
Configuration hash: `78d00fe0ea7189dced084bf31ac069b13b85820f92f5175f578efdd216b9fecd`  
Git revision: `726fa52aab88f187fd28d742277b918a26821785`  
Source-tree hash: `05046184a9d4f1376deecaf2678932feb106750ea54210a541603eec7f877876`

## Deliverables and mandatory results

PSD dictionary/release/observation client, exact source-unit schema, scoped commodity
union, shared family-partition refresh, independent world endpoint, raw/versioned
archives, public download_psd and iter_psd, diagnostic PSD CLI, docs/psd.md, pinned
source/dictionary fixtures, independent references, first-run holdout evidence,
source balance checks and a real 1,890-row sample CSV/schema/manifest.

P05-A1 through P05-A8: **8 passed / 0 failed / 0 blocked**.
8 offline cases and 1 authenticated live case pass. Live: A1; offline: A2-A8.
90 independently read cells across corn, soybeans, soybean meal/oil, US/Brazil/world,
two marketing years and multiple attributes match exact values/dimensions/units.
The preselected Cotton 2025 holdout passes on its first adapter run with six further
independent checks, preserving cotton's distinct units and all scoped attributes.
A missing-attribute synthetic fixture stays absent; unknown attributes fail.

Country, regional aggregate and world rows remain separate; code 00 and seven-digit
commodity codes retain leading zeros. Requests through overlapping production/grain
family selections fetch each commodity/year once per refresh, proven by mock call
accounting. World values come from the source world endpoint, not an invented sum.
Two US Corn years pass three aligned local-year supply/distribution identities each
at zero tolerance. TY measures are not substituted into MY balances.

Authenticated live dictionary, all-country, independent US-country and world
requests return valid JSON. US subsets match their separate endpoint exactly.
Complete field/record accounting, strict dictionary validation and fixture counts
are checked. Current-revised provenance retains year-month source update metadata;
no historical report date, exact day/time, or retrieval-based vintage is fabricated.
Python/CLI/CSV values match; complete-partition revisions retain old snapshots.
Prior phase regression suite: 42 passed.

## Scope and evidence

config/psd_scope.json and its packaged copy freeze 37 distinct commodities from
18 production, 9 grain and 27 oilseed/meal/oil family lists. Report page/table/hash
locators justify the union. Unrelated families remain excluded. API dictionaries
contain 63 commodities, 251 countries/geographies, 15 regions, 42 units and 85
attributes; full dictionaries are retained, but business data is report-scoped.
Per-commodity release inventory records preserve actual country/year availability
and their source update month for later backfill discovery.

Independent checks: source_checks.csv, tests/fixtures/phase_05/references.json.
Official hashes: *.acquisition.json and catalog.json in the same fixture folder.
Live access/completeness: live/checks.json. Balance checks: balance_checks.json.
Holdout: holdout_first_run.json. Exact commands and exit codes: commands.txt.
Real sample and partition/schema/hash manifests: sample/exports/ and sample/data/.

Known source limitation: the country dictionary refers to region R15 for four
residual/historical geographies, absent from the region dictionary. Original codes
are retained with explicitly nullable region names and missing-dictionary status;
no geography or region label is invented. Complete-array/independent-country
checks cannot prove that the upstream service never omits an internal record.

Implementation defects open for mandatory Phase 05: none.  
External blockers: none.  
Next eligible phase: 06 — archive and map all three report families, independently
validate at least two report dates each, and implement all required supplementary
numerical tables. Passing the shared PSD layer is NOT completion of those reports.
