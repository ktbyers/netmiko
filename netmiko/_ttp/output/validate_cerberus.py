import logging
import json

log = logging.getLogger(__name__)

try:
    from cerberus import Validator

    HAS_LIBS = True
except ImportError:
    log.error(
        "ttp.validate, failed to import Cerberus library, make sure it is installed"
    )
    HAS_LIBS = False

if HAS_LIBS:
    validator_engine = Validator()


def _run_validation(data, schema_data, info, errors, result, validator_engine):
    ret = {result: validator_engine.validate(document=data, schema=schema_data)}
    if info:
        try:
            formatted, _ = _ttp_["group"]["sformat"](data, string=info, add_field="inf")
            ret["info"] = formatted["inf"]
        except:
            ret["info"] = info
    if errors:
        ret[errors] = validator_engine.errors
    return ret


def validate(data, schema, result="valid", info="", errors="", allow_unknown=True):
    """Function to validate data using Cerberus validation library.
    Args::
        * schema - schema template variable name
        * result - name of the field to assign validation result
        * info - string, contains additional information about test
        * errors - name of the field to assign validation errors
        * allow_unknown - informs cerberus to ignore uncknown keys
    """
    if not HAS_LIBS:
        return data
    ret = {}
    # get validation schema from template variables
    schema_data = _ttp_["output_object"].template_obj.vars.get(schema, None)
    if not schema_data:
        log.error("ttp.output.validate, schema '{}' not found".format(schema))
        return data
    validator_engine.allow_unknown = allow_unknown
    # run validation
    if isinstance(data, dict):
        return _run_validation(
            data, schema_data, info, errors, result, validator_engine
        )
    elif isinstance(data, list):
        return [
            _run_validation(i, schema_data, info, errors, result, validator_engine)
            for i in data
            if isinstance(i, dict)
        ]