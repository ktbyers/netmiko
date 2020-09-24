_name_map_ = {"yaml_formatter": "yaml"}


def yaml_formatter(data, **kwargs):
    """Method returns parsing results in yaml format."""
    try:
        from yaml import dump
    except ImportError:
        log.critical(
            "output.yaml_formatter: yaml not installed, install: 'python -m pip install pyyaml'. Exiting"
        )
        raise SystemExit()
    return dump(data, default_flow_style=False)