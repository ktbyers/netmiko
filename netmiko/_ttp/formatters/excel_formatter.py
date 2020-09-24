import logging

log = logging.getLogger(__name__)

try:
    from openpyxl import Workbook
except ImportError:
    log.critical(
        "output.formatter_excel: openpyxl not installed, install: 'python -m pip install openpyxl'. Exiting"
    )
    raise SystemExit()

_name_map_ = {"excel_formatter": "excel"}


def excel_formatter(data, **kwargs):
    """Method to format data as an .xlsx table using openpyxl module."""
    # form table_tabs - list of dictionaries
    try:
        table = _ttp_["output_object"].tag_load["table"]
    except KeyError:
        log.critical(
            "output.formatter_excel: output tag missing table definition. Exiting"
        )
        raise SystemExit()
    table_tabs = []
    for index, tab_det in enumerate(table):
        tab_name = (
            tab_det.pop("tab_name")
            if "tab_name" in tab_det
            else "Sheet{}".format(index)
        )
        headers = tab_det.get("headers", None)
        if isinstance(headers, str):
            headers = [i.strip() for i in headers.split(",")]
        # get attributes out of tab_det
        tab_kwargs = {
            "path": [i.strip() for i in tab_det.get("path", "").split(".")],
            "headers": headers,
            "missing": tab_det.get("missing", ""),
            "key": tab_det.get("key", ""),
        }
        # form tab table
        tab_table_data = _ttp_["formatters"]["table"](data, **tab_kwargs)
        table_tabs.append({"name": tab_name, "data": tab_table_data})
    # create workbook
    wb = Workbook(write_only=True)
    for tab in table_tabs:
        ws = wb.create_sheet(title=tab["name"])
        [ws.append(row) for row in tab["data"]]
    return wb