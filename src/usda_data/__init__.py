"""USDA data ingestion. Raw artifacts and normalized versions are retained."""
__version__ = "0.1.0"


def __getattr__(name):
    if name in {'download_wasde','download_dataset','iter_wasde','download_costs_returns','iter_costs_returns','download_export_sales','iter_export_sales','download_psd','iter_psd','download_reports','download_rma_sob','iter_rma_sob'}:
        from . import api
        return getattr(api,name)
    raise AttributeError(name)
