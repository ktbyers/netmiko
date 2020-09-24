import logging

log = logging.getLogger(__name__)

_name_map_ = {"jinja2_formatter": "jinja2"}


def jinja2_formatter(data, **kwargs):
    """Method to render output template using results data."""
    try:
        from jinja2 import Environment
    except ImportError:
        log.critical(
            "output.formatter_jinja2: Jinja2 not installed, install: 'python -m pip install jinja2'. Exiting"
        )
        raise SystemExit()
    # load template:
    template_obj = Environment(
        loader="BaseLoader", trim_blocks=True, lstrip_blocks=True
    ).from_string(_ttp_["output_object"].tag_load)
    # render data making whole results accessible from _data_ variable in Jinja2
    result = template_obj.render(_data_=data)
    return result