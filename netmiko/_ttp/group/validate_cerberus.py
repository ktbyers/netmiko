import logging

log = logging.getLogger(__name__)

try:
    from cerberus import Validator

    HAS_LIBS = True
except ImportError:
    log.error(
        "ttp.cerberus, failed to import Cerberus library, make sure it is installed"
    )
    HAS_LIBS = False

if HAS_LIBS:
    validator_engine = Validator()

_name_map_ = {"cerberus_validate": "cerberus"}


def cerberus_validate(
    data, schema, log_errors=False, allow_unknown=True, add_errors=False
):
    """Function to validate data using validation libraries, such as Cerberus."""
    if not HAS_LIBS:
        return data, None
    # get validation schema
    schema_data = _ttp_["vars"].get(schema, None)
    if not schema_data:
        log.error("ttp.validate, schema '{}' not found".format(schema))
        return data, None
    # run validation
    validator_engine.allow_unknown = allow_unknown
    ret = validator_engine.validate(document=data, schema=schema_data)
    if ret == False:
        if log_errors:
            log.warning(
                "ttp.validate, data: '{}', Cerberus validation errors: {}".format(
                    data, str(validator_engine.errors)
                )
            )
        if add_errors:
            data["validation_errors"] = validator_engine.errors
            return data, None
    return data, ret


def validate(data, schema, result="valid", info="", errors="", allow_unknown=True):
    """Function to validate data using Cerberus validation library and
    updated data with this dictionary
    {
        result field: True|False
        info: user defined information string
        errors field: validation errors
    }
    Args::
        * schema - schema template variable name
        * result - name of the field to assign validation result
        * info - string, contain additional information about test,
            will be formatted using <info sting>.format(data)
        * errors - name of the field to assign validation errors
        * allow_unknown - informs cerberus to ignore uncknown keys
    """
    if not HAS_LIBS:
        return data, None
    # get validation schema
    schema_data = _ttp_["parser_object"].vars.get(schema, None)
    if not schema_data:
        log.error("ttp.validate, schema '{}' not found".format(schema))
        return data, None
    # run validation
    validator_engine.allow_unknown = allow_unknown
    ret = validator_engine.validate(document=data, schema=schema_data)
    # form results
    data[result] = ret
    # add validation errors if requested to do so
    if info:
        data, _ = _ttp_["group"]["sformat"](data, string=info, add_field="info")
    if errors:
        data[errors] = validator_engine.errors
    return data, None
