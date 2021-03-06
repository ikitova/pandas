""" feather-format compat """

from pandas._typing import StorageOptions
from pandas.compat._optional import import_optional_dependency

from pandas import DataFrame, Int64Index, RangeIndex

from pandas.io.common import get_filepath_or_buffer


def to_feather(df: DataFrame, path, storage_options: StorageOptions = None, **kwargs):
    """
    Write a DataFrame to the binary Feather format.

    Parameters
    ----------
    df : DataFrame
    path : string file path, or file-like object
    storage_options : dict, optional
        Extra options that make sense for a particular storage connection, e.g.
        host, port, username, password, etc., if using a URL that will
        be parsed by ``fsspec``, e.g., starting "s3://", "gcs://". An error
        will be raised if providing this argument with a local path or
        a file-like buffer. See the fsspec and backend storage implementation
        docs for the set of allowed keys and values.

        .. versionadded:: 1.2.0

    **kwargs :
        Additional keywords passed to `pyarrow.feather.write_feather`.

        .. versionadded:: 1.1.0
    """
    import_optional_dependency("pyarrow")
    from pyarrow import feather

    path, _, _, should_close = get_filepath_or_buffer(
        path, mode="wb", storage_options=storage_options
    )

    if not isinstance(df, DataFrame):
        raise ValueError("feather only support IO with DataFrames")

    valid_types = {"string", "unicode"}

    # validate index
    # --------------

    # validate that we have only a default index
    # raise on anything else as we don't serialize the index

    if not isinstance(df.index, Int64Index):
        typ = type(df.index)
        raise ValueError(
            f"feather does not support serializing {typ} "
            "for the index; you can .reset_index() to make the index into column(s)"
        )

    if not df.index.equals(RangeIndex.from_range(range(len(df)))):
        raise ValueError(
            "feather does not support serializing a non-default index for the index; "
            "you can .reset_index() to make the index into column(s)"
        )

    if df.index.name is not None:
        raise ValueError(
            "feather does not serialize index meta-data on a default index"
        )

    # validate columns
    # ----------------

    # must have value column names (strings only)
    if df.columns.inferred_type not in valid_types:
        raise ValueError("feather must have string column names")

    feather.write_feather(df, path, **kwargs)


def read_feather(
    path, columns=None, use_threads: bool = True, storage_options: StorageOptions = None
):
    """
    Load a feather-format object from the file path.

    Parameters
    ----------
    path : str, path object or file-like object
        Any valid string path is acceptable. The string could be a URL. Valid
        URL schemes include http, ftp, s3, and file. For file URLs, a host is
        expected. A local file could be:
        ``file://localhost/path/to/table.feather``.

        If you want to pass in a path object, pandas accepts any
        ``os.PathLike``.

        By file-like object, we refer to objects with a ``read()`` method,
        such as a file handler (e.g. via builtin ``open`` function)
        or ``StringIO``.
    columns : sequence, default None
        If not provided, all columns are read.

        .. versionadded:: 0.24.0
    use_threads : bool, default True
        Whether to parallelize reading using multiple threads.

       .. versionadded:: 0.24.0
    storage_options : dict, optional
        Extra options that make sense for a particular storage connection, e.g.
        host, port, username, password, etc., if using a URL that will
        be parsed by ``fsspec``, e.g., starting "s3://", "gcs://". An error
        will be raised if providing this argument with a local path or
        a file-like buffer. See the fsspec and backend storage implementation
        docs for the set of allowed keys and values.

        .. versionadded:: 1.2.0

    Returns
    -------
    type of object stored in file
    """
    import_optional_dependency("pyarrow")
    from pyarrow import feather

    path, _, _, should_close = get_filepath_or_buffer(
        path, storage_options=storage_options
    )

    df = feather.read_feather(path, columns=columns, use_threads=bool(use_threads))

    # s3fs only validates the credentials when the file is closed.
    if should_close:
        path.close()

    return df
