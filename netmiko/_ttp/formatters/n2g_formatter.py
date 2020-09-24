import logging

log = logging.getLogger(__name__)


def n2g(data, **kwargs):
    # load kwargs
    module = kwargs.get("module", "yed")
    method = kwargs.get("method", "from_list")
    path = kwargs.get("path", [])
    node_dups = kwargs.get("node_duplicates", "skip")
    link_dups = kwargs.get("link_duplicates", "skip")
    method_kwargs = kwargs.get("method_kwargs", {})
    algo = kwargs.get("algo", None)
    # import N2G library
    try:
        if module.lower() == "yed":
            from N2G import yed_diagram as create_diagram
        elif module.lower() == "drawio":
            from N2G import drawio_diagram as create_diagram
        else:
            log.error(
                "No N2G module '{}', supported values are 'yEd', 'DrawIO'".format(
                    module
                )
            )
            return data
    except ImportError:
        log.error("Failed to import N2G '{}' module".format(module))
        return data
    diagram_obj = create_diagram(node_duplicates=node_dups, link_duplicates=link_dups)
    # normalize results_data to list:
    if isinstance(data, dict):  # handle the case for group specific output
        data = [data]
    # make graph
    for result in data:
        result_datum = _ttp_["output"]["traverse"](result, path)
        getattr(diagram_obj, method)(result_datum, **method_kwargs)
    # layout graph
    if algo:
        diagram_obj.layout(algo=algo)
    # return results XML
    data = diagram_obj.dump_xml()
    return data