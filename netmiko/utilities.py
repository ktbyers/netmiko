"""Miscellaneous utility functions."""
import sys
import io


def load_yaml_file(yaml_file):
    """Read YAML file."""
    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")
    try:
        with io.open(yaml_file, encoding='utf-8') as fname:
            return yaml.load(fname)
    except IOError:
        sys.exit("Unable to open YAML file: {0}".format(yaml_file))
