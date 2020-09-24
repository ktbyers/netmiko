import os
import logging

log = logging.getLogger(__name__)

try:
    import geoip2.database

    HAS_LIBS = True
except ImportError:
    log.error(
        "ttp.lookup.geoip2: failed to import geoip2 library, install: pip install geoip2"
    )
    HAS_LIBS = False


def geoip2_db_loader(lookup_tag_data):
    """
    Function takes lookup_tag_data python dictionary, loads
    geoip2 moduleand creates reader objects to lookup data.

    lookup_tag_data::
        {
            'city': './path/to/GeoLite2-City.mmdb',
            'asn': './path/to/GeoLite2-ASN.mmdb',
            'country': './path/to/GeoLite2-Country.mmdb'
        }

    Returns deictionary of::
        {
            "city": GeoLite2-City.mmdb reader object,
            "ASN": GeoLite2-ASN.mmdb rteader object,
            "country": GeoLite2-Country.mmdb reader object
        }
    """
    ret = {"city": None, "asn": None, "country": None}
    if HAS_LIBS:
        for dbname, path_to_db in lookup_tag_data.items():
            if dbname.lower() in ret:
                _ = ret.pop(dbname.lower())
                try:
                    ret[dbname] = geoip2.database.Reader(path_to_db)
                except:
                    log.error(
                        "ttp.lookup.geoip2: something went wrong, failed to load '{}' mmdb from '{}' path".format(
                            dbname, path_to_db
                        )
                    )
    return ret