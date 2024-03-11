"""
Module for building a complete dataset from local directory with csv files.
"""
import calendar
import os
import sys

import logging
import numpy as np
import pandas as pd
from zipline.utils.calendar_utils import register_calendar_alias
from zipline.utils.cli import maybe_show_progress

from . import core as bundles


handler = logging.StreamHandler()
# handler = logging.StreamHandler(sys.stdout, format_string=" | {record.message}")
logger = logging.getLogger(__name__)
logger.handlers.append(handler)


# def csvdir_binance(tframes=None, csvdir=None):
#     """
#     Generate an ingest function for custom data bundle

#     Parameters
#     ----------
#     tframes: tuple, optional
#         The data time frames, supported timeframes: 'daily' and 'minute'
#     csvdir : string, optional, default: CSVDIR environment variable
#         The path to the directory of this structure:
#         <directory>/<timeframe1>/<symbol1>.csv
#         <directory>/<timeframe1>/<symbol2>.csv
#         <directory>/<timeframe1>/<symbol3>.csv
#         <directory>/<timeframe2>/<symbol1>.csv
#         <directory>/<timeframe2>/<symbol2>.csv
#         <directory>/<timeframe2>/<symbol3>.csv

#     Returns
#     -------
#     ingest : callable
#         The bundle ingest function

#     Examples
#     --------
#     This code should be added to ~/.zipline/extension.py
#     .. code-block:: python
#        from zipline.data.bundles import csvdir_equities, register
#        register('custom-csvdir-bundle',
#                 csvdir_equities(["daily", "minute"],
#                 '/full/path/to/the/csvdir/directory'))
#     """

#     return CryptoBundle(tframes, csvdir).ingest


# class CryptoBundle:
#     """
#     Wrapper class to call crypto bundle with provided
#     list of time frames and a path to the csvdir directory
#     """

#     def __init__(self, tframes=None, csvdir=None):
#         self.tframes = tframes
#         self.csvdir = csvdir

#     def ingest(
#         self,
#         environ,
#         asset_db_writer,
#         minute_bar_writer,
#         daily_bar_writer,
#         adjustment_writer,
#         calendar,
#         start_session,
#         end_session,
#         cache,
#         show_progress,
#         output_dir,
#     ):
#         binance_bundle(
#             environ,
#             asset_db_writer,
#             minute_bar_writer,
#             daily_bar_writer,
#             adjustment_writer,
#             calendar,
#             start_session,
#             end_session,
#             cache,
#             show_progress,
#             output_dir,
#             self.tframes,
#             self.csvdir,
#         )

@bundles.register("binance-bundle-1m", calendar_name="24/7", minutes_per_day=1440)
def binance_bundle_1d(
    environ,
    asset_db_writer,
    minute_bar_writer,
    daily_bar_writer,
    adjustment_writer,
    calendar,
    start_session,
    end_session,
    cache,
    show_progress,
    output_dir,
):
    return binance_bundle(
    environ,
    asset_db_writer,
    minute_bar_writer,
    daily_bar_writer,
    adjustment_writer,
    calendar,
    start_session,
    end_session,
    cache,
    show_progress,
    output_dir,
    tframes=set(["1m"]),
    csvdir=None,
)

@bundles.register("binance-bundle-1d", calendar_name="24/7", minutes_per_day=1440)
def binance_bundle_1d(
    environ,
    asset_db_writer,
    minute_bar_writer,
    daily_bar_writer,
    adjustment_writer,
    calendar,
    start_session,
    end_session,
    cache,
    show_progress,
    output_dir,
):
    return binance_bundle(
    environ,
    asset_db_writer,
    minute_bar_writer,
    daily_bar_writer,
    adjustment_writer,
    calendar,
    start_session,
    end_session,
    cache,
    show_progress,
    output_dir,
    tframes=set(["1d"]),
    csvdir=None,
)


# @bundles.register("binance-bundle", calendar_name="24/7", minutes_per_day=1440)
def binance_bundle(
    environ,
    asset_db_writer,
    minute_bar_writer,
    daily_bar_writer,
    adjustment_writer,
    calendar,
    start_session,
    end_session,
    cache,
    show_progress,
    output_dir,
    tframes=None,
    csvdir=None,
):
    """
    Build a zipline data bundle from the directory with csv files.
    """
    if not csvdir:
        csvdir = environ.get("BINANCECSVDIR")
        if not csvdir:
            raise ValueError("BINANCECSVDIR environment variable is not set")

    if not os.path.isdir(csvdir):
        raise ValueError("%s is not a directory" % csvdir)

    if not tframes:
        tframes = set(["1d", "1m"]).intersection(os.listdir(csvdir))

        if not tframes:
            raise ValueError(
                "'1d' and '1m' directories " "not found in '%s'" % csvdir
            )

    for tframe in tframes:
        ddir = os.path.join(csvdir, tframe)

        symbols = sorted(
            item.split(".csv")[0] for item in os.listdir(ddir) if ".csv" in item
        )
        if not symbols:
            raise ValueError("no <symbol>.csv* files found in %s" % ddir)

        dtype = [
            ("start_date", "datetime64[ns]"),
            ("end_date", "datetime64[ns]"),
            ("auto_close_date", "datetime64[ns]"),
            ("symbol", "object"),
        ]
        metadata = pd.DataFrame(np.empty(len(symbols), dtype=dtype))

        if tframe == "1m":
            writer = minute_bar_writer
        else:
            writer = daily_bar_writer

        writer.write(
            _pricing_iter(ddir, symbols, metadata, show_progress),
            show_progress=show_progress,
        )

        # Hardcode the exchange to "CRYPTO" for all assets and (elsewhere)
        # register "CRYPTO" to resolve to the 24/7 calendar, because these
        # are all equities and thus can use the 24/7 calendar.
        metadata["exchange"] = "BINANCE"

        asset_db_writer.write(equities=metadata)

        adjustment_writer.write()


def _pricing_iter(csvdir, symbols, metadata, show_progress):
    with maybe_show_progress(
        symbols, show_progress, label="Loading custom pricing data: "
    ) as it:
        # using scandir instead of listdir can be faster
        files = os.scandir(csvdir)
        # building a dictionary of filenames
        # NOTE: if there are duplicates it will arbitrarily pick the latest found
        fnames = {f.name.split(".")[0]: f.name for f in files if f.is_file()}

        for sid, symbol in enumerate(it):
            logger.debug(f"{symbol}: sid {sid}")
            fname = fnames.get(symbol, None)

            if fname is None:
                raise ValueError(f"{symbol}.csv file is not in {csvdir}")

            # NOTE: read_csv can also read compressed csv files
            dfr = pd.read_csv(
                os.path.join(csvdir, fname),
                index_col=0,
            ).iloc[:, :5].sort_index()  # only choose ohlcv

            dfr.index = pd.to_datetime(dfr.index, unit='ms')    # from unix to datetime

            start_date = dfr.index[0]
            end_date = dfr.index[-1]

            # The auto_close date is the day after the last trade.
            ac_date = end_date + pd.Timedelta(days=1)
            metadata.iloc[sid] = start_date, end_date, ac_date, symbol

            yield sid, dfr


register_calendar_alias("BINANCE", "24/7")
