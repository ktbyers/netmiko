import logging
import logging.handlers
import json

log = logging.getLogger(__name__)


def syslog(data, **kwargs):
    # get kwargs
    servers = kwargs.get("servers", None)
    servers = [servers] if isinstance(servers, str) else servers
    if not servers:
        log.error(
            "ttp.returners.syslog: no syslog servers addresses found, doing nothing..."
        )
        return
    port = int(kwargs.get("port", 514))
    facility = kwargs.get("facility", 77)
    path = kwargs.get("path", [])
    iterate = kwargs.get("iterate", True)
    # normalize source_data to list:
    source_data = data if isinstance(data, list) else [data]
    # initiate isolated logger
    syslog_logger = logging.getLogger("_Custom_Syslog_Logger_")
    syslog_logger.propagate = False
    syslog_logger.setLevel(logging.INFO)
    for server in servers:
        handler = logging.handlers.SysLogHandler(
            address=(server, port), facility=facility
        )
        handler.append_nul = False
        syslog_logger.addHandler(handler)
        # send data
        for datum in source_data:
            item = _ttp_["output"]["traverse"](datum, path)
            if not item:  # skip empty results
                continue
            elif isinstance(item, list) and iterate:
                [syslog_logger.info(json.dumps(i)) for i in item]
            else:
                syslog_logger.info(json.dumps(item))
        # clean up
        handler.close()
        syslog_logger.removeHandler(handler)
    del syslog_logger