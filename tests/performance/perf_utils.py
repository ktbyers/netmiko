from test_utils import parse_yaml
from os import path


def commands(platform):
    """Parse the commands.yml file to get a commands dictionary."""
    PWD = path.dirname(path.realpath(__file__))
    test_platform = platform
    commands_yml = parse_yaml(PWD + "/../etc/commands.yml")
    return commands_yml[test_platform]
