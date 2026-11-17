# Release 0.1.0 — handover candidate

The handover gate remains blocked by the required Phase 00 RMA 2010 ZIP live
recheck (HTTP 502 through both proxy and direct transport). The nine adapter live
tests passed; the extra required inventory/holdout recheck is still required.
See the execution ledger and Phase 10 summary for the exact acceptance status.

The accepted data run is frozen at November 16, 2026. Release package installation
is verified in an isolated Python 3.13.5 environment without system packages and
without editable source imports. Python >=3.11 is declared; other interpreter and
platform combinations have not been independently exercised by this acceptance.
POSIX is required for the operating-system writer lock. The full job memory budget
is the user-approved 1 GiB, superseding the earlier 512 MiB experiment.

## Publication timing and availability

These are the saved official rules and observations; they are not a continuously
updated release service. Evidence resides in `test/fixtures/config/source_registry.json`,
`config/calendar.json`, and the source registry. Calendar events carry verification
dates and are labeled stale when appropriate. Never infer source release times
from retrieval timestamps or HTTP Last-Modified.

| Source artifact | Saved publication rule / limitation |
|---|---|
| WASDE report | Official monthly calendar at 12:00 America/New_York; historical CSV is documented for the following day without an exact clock. |
| ESR weekly report | Normally Thursday 08:30 America/New_York, subject to official holiday shifts; actual API synchronization remains unmeasured. |
| PSD API and FAS circulars | Keep the documented 12:00 data-update convention and by-12:15 report convention distinct. Exact report-page events in the saved calendar have their own evidence; they do not establish all historical API availability times. |
| ERS estimates | Preliminary in the first week of May; final in the first week of October. Preserve per-file update dates and methods. |
| ERS forecasts | Generally mid-June and mid-November; per-file Next Update is planned, not a confirmed future release. |
| RMA summary | Most recent five years refreshed Monday morning per the summary description; timezone/minute and bulk ZIP synchronization are unverified. |

Authenticated ESR/PSD access was verified in Phases 04/05 and checked again in
Phase 10. Unknown synchronization times remain unknown despite working access.
Operator scheduling should consult reviewed source events and retry pending
artifacts with bounded backoff. `sync` rechecks every configured partition,
including old years, and saves revisions. Scheduling instructions do not install
a recurring job.

## Economic and version interpretation

WASDE and report tables retain report vintages, classification dimensions and
printed units. ESR sales/shipments/commitments are different measures; cancellations
may be negative. PSD observations are current-revised history, not a reconstructed
historical trading signal. Report-family outputs identify `psd_current` and
`report_table`; compare only aligned dimensions, periods, units and vintages.
ERS costs/returns retain enterprise, methodology and forecast vintages. RMA measures
insurance activity, not a crop-production census; quantity types and overlapping
aggregation levels cannot be blindly summed. See each dataset guide for detailed
units, exact grain and interpretation.

Every acquisition retains raw bytes and source-artifact hashes. Parser/schema and
configuration identity determine normalized versions. Previous snapshots survive
refresh. WASDE structured history starts April 2010; supported report-month/table
gaps remain explicitly recorded in Phase 09. Future crop/forecast years through
2027 are valid source labels in already available files. No historical monthly
API vintages are promised.
