import logging

log = logging.getLogger(__name__)

_name_map_ = {"tabulate_formatter": "tabulate"}


def tabulate_formatter(data, **kwargs):
    """Method to format data as a table using tabulate module."""
    try:
        from tabulate import tabulate
    except ImportError:
        log.critical(
            "output.formatter_tabulate: tabulate not installed, install: 'python -m pip install tabulate'. Exiting"
        )
        raise SystemExit()
    # form table - list of lists
    table = _ttp_["formatters"]["table"](data, **kwargs)
    headers = table.pop(0)
    attribs = _ttp_["output_object"].attributes.get(
        "format_attributes", {"args": [], "kwargs": {}}
    )
    # run tabulate:
    return tabulate(table, headers=headers, *attribs["args"], **attribs["kwargs"])
