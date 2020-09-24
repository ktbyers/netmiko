import logging

log = logging.getLogger(__name__)


def geoip_lookup(data, db_name, add_field="geoip_lookup"):
    lookup_data = _ttp_["parser_object"].lookups
    path = [i.strip() for i in db_name.split(".")]
    # get reference to geoip2 reader object
    for i in path:
        lookup_data = lookup_data.get(i, {})
    if not lookup_data:
        return data, None
    found_value = None
    # lookup country
    if path[-1].lower() == "country":
        try:
            found_value = lookup_data.country(data)
            found_value = {
                "continent": found_value.continent.names.get("en", ""),
                "continent_code": found_value.continent.code,
                "country_iso_code": found_value.country.iso_code,
                "country": found_value.country.names.get("en", ""),
                "network": found_value.traits.network.with_prefixlen,
            }
        except:
            log.error(
                "ttp.match.geoip_lookup: something went wrong searching for '{}' IP in database '{}'".format(
                    data, db_name
                )
            )
    # lookup city
    elif path[-1].lower() == "city":
        try:
            found_value = lookup_data.city(data)
            found_value = {
                "city": found_value.city.name,
                "continent": found_value.continent.names.get("en", ""),
                "country_iso_code": found_value.country.iso_code,
                "country": found_value.country.names.get("en", ""),
                "latitude": found_value.location.latitude,
                "longitude": found_value.location.longitude,
                "accuracy_radius": found_value.location.accuracy_radius,
                "postal_code": found_value.postal.code,
                "state": found_value.subdivisions.most_specific.name,
                "state_iso_code": found_value.subdivisions.most_specific.iso_code,
                "network": found_value.traits.network.with_prefixlen,
            }
        except:
            log.error(
                "ttp.match.geoip_lookup: something went wrong searching for '{}' IP in database '{}'".format(
                    data, db_name
                )
            )
    # lookup asn
    elif path[-1].lower() == "asn":
        try:
            found_value = lookup_data.asn(data)
            found_value = {
                "ASN": found_value.autonomous_system_number,
                "organization": found_value.autonomous_system_organization,
                "network": found_value.network.with_prefixlen,
            }
        except:
            log.error(
                "ttp.match.geoip_lookup: something went wrong searching for '{}' IP in database '{}'".format(
                    data, db_name
                )
            )
    # return data
    if found_value:
        return data, {"new_field": {add_field: found_value}}
    return data, None