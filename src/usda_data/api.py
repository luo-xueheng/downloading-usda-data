"""Public Python entry points; unsupported options are rejected explicitly."""
import pandas as pd
from .errors import ConfigurationError
from .sources.wasde import iter_download, SCHEMA

def download_wasde(start, end, *, data_dir="data", refresh=False):
    """Return WASDE report vintages within inclusive publication-date bounds.

    Downloads and preserves raw source artifacts, receipts and versioned normalized
    snapshots under data_dir. An unchanged cached request avoids network calls;
    refresh=True rechecks source bytes without deleting old versions. This function
    materializes its requested result; use iter_wasde for large/backfill requests.
    """
    frames=list(iter_wasde(start,end,data_dir=data_dir,refresh=refresh))
    return pd.concat(frames,ignore_index=True) if frames else SCHEMA.frame([])

def iter_wasde(start, end, *, data_dir="data", refresh=False):
    """Yield one report DataFrame at a time with the same cache/archive side effects."""
    yield from iter_download(start,end,data_dir=data_dir,refresh=refresh)

def download_dataset(dataset, *, data_dir="data", **validated_dataset_options):
    """Dispatch to the accepted source adapter; raw archives/snapshots are retained.

    All seven frozen dataset IDs are supported. Dataset-specific date/year
    options retain their source meanings. Unsupported datasets/options fail
    rather than producing a misleading empty successful export.
    """
    if dataset=='rma-sob':
        if set(validated_dataset_options)-{'commodity_years','refresh'} or 'commodity_years' not in validated_dataset_options:
            raise ConfigurationError('RMA requires commodity_years and supports refresh')
        return download_rma_sob(data_dir=data_dir,**validated_dataset_options)
    if dataset in {'world-production','grain-trade','oilseed-trade'}:
        allowed={'market_years','report_start','report_end','commodities','countries','refresh'}
        if set(validated_dataset_options)-allowed or not {'market_years','report_start','report_end'}<=set(validated_dataset_options):
            raise ConfigurationError('Report datasets require market_years and separate report_start/report_end bounds')
        from .sources.report_datasets import iter_dataset,SCHEMA
        frames=list(iter_dataset(dataset,data_dir=data_dir,**validated_dataset_options))
        return pd.concat(frames,ignore_index=True) if frames else SCHEMA.frame([])
    if dataset=='export-sales':
        if set(validated_dataset_options)-{'commodities','market_years','countries','refresh'} or not {'commodities','market_years'}<=set(validated_dataset_options):
            raise ConfigurationError('ESR requires commodities and market_years; supports countries/refresh')
        return download_export_sales(data_dir=data_dir,**validated_dataset_options)
    if dataset=='costs-returns':
        if set(validated_dataset_options)-{'years','commodities','refresh'} or 'years' not in validated_dataset_options:
            raise ConfigurationError('ERS requires years and supports only commodities/refresh')
        return download_costs_returns(data_dir=data_dir,**validated_dataset_options)
    if dataset!='wasde':
        raise ConfigurationError("Unknown dataset ID")
    unknown=set(validated_dataset_options)-{'start','end','refresh'}
    if unknown or not {'start','end'}<=set(validated_dataset_options):
        raise ConfigurationError("WASDE requires start/end and supports only refresh")
    return download_wasde(data_dir=data_dir,**validated_dataset_options)


def iter_costs_returns(years, *, commodities="all", data_dir="data", refresh=False):
    """Yield ERS file partitions, preserving raw revisions and snapshots under data_dir."""
    from .sources.ers_costs_returns import iter_download
    yield from iter_download(years,commodities=commodities,data_dir=data_dir,refresh=refresh)


def download_costs_returns(years, *, commodities="all", data_dir="data", refresh=False):
    """Return ERS observations for source observation years, with all source variants.

    Raw files and complete-file snapshots are saved under data_dir. refresh rechecks
    source bytes while keeping older versions. Use iter_costs_returns for large jobs.
    Observation years, series families and forecast publication vintages stay distinct.
    """
    from .sources.ers_costs_returns import SCHEMA
    frames=list(iter_costs_returns(years,commodities=commodities,data_dir=data_dir,refresh=refresh))
    return pd.concat(frames,ignore_index=True) if frames else SCHEMA.frame([])


def iter_export_sales(commodities, market_years, *, countries="all", data_dir="data", refresh=False):
    """Yield ESR commodity/year partitions; retain complete raw responses and revisions."""
    from .sources.fas_esr import iter_download
    yield from iter_download(commodities,market_years,countries=countries,data_dir=data_dir,refresh=refresh)


def download_export_sales(commodities, market_years, *, countries="all", data_dir="data", refresh=False):
    """Return ESR weekly metrics using the source's marketing-year identifiers.

    Raw API responses, dictionaries and versioned full commodity/year snapshots are
    stored under data_dir. refresh rechecks every requested year, preserving old
    snapshots. Country selection is applied after complete partition validation.
    USDA_FAS_API_KEY is read from the environment or current-directory .env only
    when a network request is needed. Use iter_export_sales for large jobs.
    """
    from .sources.fas_esr import SCHEMA
    frames=list(iter_export_sales(commodities,market_years,countries=countries,data_dir=data_dir,refresh=refresh))
    return pd.concat(frames,ignore_index=True) if frames else SCHEMA.frame([])


def iter_psd(commodities, market_years, *, countries="all", data_dir="data", refresh=False):
    """Yield report-scoped PSD partitions, retaining raw files, dictionaries and revisions."""
    from .sources.fas_psd import iter_download
    yield from iter_download(commodities,market_years,countries=countries,data_dir=data_dir,refresh=refresh)


def download_psd(commodities, market_years, *, countries="all", data_dir="data", refresh=False):
    """Return current-revised PSD observations for the three frozen report families.

    Source year labels and units are preserved. Raw API responses, release inventories,
    dictionaries and complete commodity/year snapshots are saved under data_dir;
    refresh rechecks requested partitions without deleting earlier snapshots. World
    totals use the official world endpoint and remain distinct from country/region
    rows. Use iter_psd for bounded-memory jobs.
    """
    from .sources.fas_psd import SCHEMA
    frames=list(iter_psd(commodities,market_years,countries=countries,data_dir=data_dir,refresh=refresh))
    return pd.concat(frames,ignore_index=True) if frames else SCHEMA.frame([])


def download_reports(report_family, start, end, *, data_dir="data", refresh=False):
    """Return verified attachment manifests; raw PDF files and revisions persist under data_dir.

    This function archives reports. Their structured observations are returned by
    download_dataset using separate marketing-year and publication-date ranges.
    """
    from .sources.reports import download_reports as download
    return download(report_family,start,end,data_dir=data_dir,refresh=refresh)


def iter_rma_sob(commodity_years, *, data_dir="data", refresh=False, chunk_size=5000, all_history=False):
    """Yield RMA chunks after complete annual publication; retain raw/versioned archives."""
    from .sources.rma_sob import iter_download
    yield from iter_download(commodity_years,data_dir=data_dir,refresh=refresh,chunk_size=chunk_size,all_history=all_history)


def download_rma_sob(commodity_years, *, data_dir="data", refresh=False):
    """Return complete RMA State/County/Crop/Coverage Level annual observations.

    Original ZIPs, layouts and annual normalized versions persist under data_dir.
    refresh rechecks every requested commodity year without deleting old versions.
    Quantity types, full grouping dimensions, missing values and signed indemnity
    adjustments are preserved. Use iter_rma_sob for bounded-memory multi-year jobs.
    """
    from .sources.rma_sob import SCHEMA
    frames=list(iter_rma_sob(commodity_years,data_dir=data_dir,refresh=refresh))
    return pd.concat(frames,ignore_index=True) if frames else SCHEMA.frame([])
